#!/usr/bin/env bash
# Fresh Ubuntu ARM server to ready for Kamal; a rerun prints "no changes".
# Inputs: SERVER_DEPLOY_PUBLIC_KEY (required), SERVER_DEPLOY_USER (default deploy), DRY_RUN=1 (plan only).
set -euo pipefail

DEPLOY_USER="${SERVER_DEPLOY_USER:-deploy}"
DEPLOY_KEY="${SERVER_DEPLOY_PUBLIC_KEY:-}"
DRY_RUN="${DRY_RUN:-0}"
DOCKER_KEY_FPR="9DC858229FC7DD38854AE2D88D81803C0EBFCD88"
export DEBIAN_FRONTEND=noninteractive

changes=0
log() { printf '%s\n' "$*"; }
die() { printf 'error: %s\n' "$*" >&2; exit 1; }

# Counts one change; under DRY_RUN it only announces it.
change() {
  local what="$1"; shift
  changes=$((changes + 1))
  if [ "$DRY_RUN" = 1 ]; then log "would: $what"; return 0; fi
  log "changing: $what"
  "$@"
}

write_file() { printf '%s\n' "$3" > "$1" && chmod "$2" "$1"; }

put_file() {
  local path="$1" mode="$2" content="$3"
  if [ -f "$path" ] && [ "$(cat "$path")" = "$content" ] && [ "$(stat -c %a "$path")" = "$mode" ]; then return 0; fi
  change "write $path" write_file "$path" "$mode" "$content"
}

pkg_missing() { ! dpkg-query -W -f='${Status}' "$1" 2>/dev/null | grep -q '^install ok installed$'; }

apt_install() {
  local missing=() p
  for p in "$@"; do pkg_missing "$p" && missing+=("$p"); done
  [ ${#missing[@]} -eq 0 ] && return 0
  change "apt install ${missing[*]}" bash -c 'apt-get update -qq && apt-get install -y -qq "$@"' _ "${missing[@]}"
}

validate() {
  [[ "$DEPLOY_USER" =~ ^[a-z_][a-z0-9_-]{0,31}$ ]] || die "SERVER_DEPLOY_USER must be a plain lowercase user name"
  [ "$DEPLOY_USER" != root ] || die "SERVER_DEPLOY_USER cannot be root"
  [ -n "$DEPLOY_KEY" ] || die "SERVER_DEPLOY_PUBLIC_KEY is required (the public key Kamal connects with)"
  [[ "$DEPLOY_KEY" != *$'\n'* ]] || die "SERVER_DEPLOY_PUBLIC_KEY must be a single line"
  [[ "$DEPLOY_KEY" =~ ^(ssh-ed25519|ssh-rsa|ecdsa-sha2-nistp(256|384|521))\ [A-Za-z0-9+/=]+(\ [^[:space:]]+)*$ ]] \
    || die "SERVER_DEPLOY_PUBLIC_KEY is not a public key (a private key must never be passed here)"
  ssh-keygen -l -f /dev/stdin <<<"$DEPLOY_KEY" >/dev/null 2>&1 || die "SERVER_DEPLOY_PUBLIC_KEY does not parse"
  [ "$DRY_RUN" = 1 ] || [ "$(id -u)" -eq 0 ] || die "run as root (sudo)"
  # shellcheck disable=SC1091
  . /etc/os-release
  [ "${ID:-}" = ubuntu ] || die "Ubuntu only, found ${ID:-unknown}"
  UBUNTU_CODENAME="${VERSION_CODENAME:?no VERSION_CODENAME in /etc/os-release}"
  ARCH="$(dpkg --print-architecture)"
  [ "$ARCH" = arm64 ] || die "arm64 expected, found $ARCH"
}

step_updates() {
  apt_install unattended-upgrades
  put_file /etc/apt/apt.conf.d/20auto-upgrades 644 'APT::Periodic::Update-Package-Lists "1";
APT::Periodic::Unattended-Upgrade "1";'
}

# True when the file holds at least one primary key and every primary key is the pinned one.
keyring_ok() {
  gpg --show-keys --with-colons "$1" 2>/dev/null | awk -F: -v want="$DOCKER_KEY_FPR" '
    $1 == "pub" { primary = 1; next }
    $1 == "fpr" && primary { n++; if ($10 != want) bad = 1; primary = 0 }
    END { exit !(n > 0 && !bad) }'
}

install_docker_key() {
  local tmp
  tmp="$(mktemp)"
  curl -fsSL https://download.docker.com/linux/ubuntu/gpg | gpg --dearmor > "$tmp"
  if ! keyring_ok "$tmp"; then rm -f "$tmp"; die "Docker key fingerprint mismatch"; fi
  install -d -m 755 /etc/apt/keyrings
  install -m 644 "$tmp" "$1"
  rm -f "$tmp"
}

step_docker() {
  apt_install ca-certificates curl gnupg
  local keyring=/etc/apt/keyrings/docker.gpg
  if [ ! -f "$keyring" ] || ! keyring_ok "$keyring"; then
    change "install the Docker apt key" install_docker_key "$keyring"
  fi
  put_file /etc/apt/sources.list.d/docker.list 644 \
    "deb [arch=$ARCH signed-by=$keyring] https://download.docker.com/linux/ubuntu $UBUNTU_CODENAME stable"
  # Written before the install so the first start already rotates logs.
  [ -d /etc/docker ] || change "create /etc/docker" install -d -m 755 /etc/docker
  put_file /etc/docker/daemon.json 644 '{
  "log-driver": "json-file",
  "log-opts": { "max-size": "10m", "max-file": "3" }
}'
  if pkg_missing docker-ce; then
    change "apt install Docker Engine" bash -c \
      'apt-get update -qq && apt-get install -y -qq docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin'
  fi
  if ! systemctl is-enabled --quiet docker 2>/dev/null || ! systemctl is-active --quiet docker 2>/dev/null; then
    change "enable and start docker" systemctl enable --now docker
  fi
}

add_key() {
  touch "$1" && chmod 600 "$1" && chown "$DEPLOY_USER:$DEPLOY_USER" "$1" && printf '%s\n' "$DEPLOY_KEY" >> "$1"
}

fix_keys() { chmod 600 "$1" && chown "$DEPLOY_USER:$DEPLOY_USER" "$1"; }

step_user() {
  local home ssh_dir keys
  if ! id "$DEPLOY_USER" >/dev/null 2>&1; then
    change "create user $DEPLOY_USER" adduser --disabled-password --gecos "" "$DEPLOY_USER"
  fi
  if ! id -nG "$DEPLOY_USER" 2>/dev/null | tr ' ' '\n' | grep -qx docker; then
    change "add $DEPLOY_USER to the docker group" usermod -aG docker "$DEPLOY_USER"
  fi
  if [ "$DRY_RUN" = 1 ] && ! id "$DEPLOY_USER" >/dev/null 2>&1; then
    change "install the deploy key for $DEPLOY_USER" true
    return 0
  fi
  home="$(getent passwd "$DEPLOY_USER" | cut -d: -f6)"
  ssh_dir="$home/.ssh"
  keys="$ssh_dir/authorized_keys"
  [ -d "$ssh_dir" ] || change "create $ssh_dir" install -d -m 700 -o "$DEPLOY_USER" -g "$DEPLOY_USER" "$ssh_dir"
  if ! { [ -f "$keys" ] && grep -qxF "$DEPLOY_KEY" "$keys"; }; then
    change "install the deploy key for $DEPLOY_USER" add_key "$keys"
  fi
  if [ -f "$keys" ] && [ "$(stat -c '%a %U' "$keys")" != "600 $DEPLOY_USER" ]; then
    change "fix permissions on $keys" fix_keys "$keys"
  fi
}

sshd_hardened() {
  local cfg
  cfg="$(sshd -T 2>/dev/null)" || return 1
  grep -qx 'permitrootlogin no' <<<"$cfg" && grep -qx 'passwordauthentication no' <<<"$cfg"
}

# Reverts the drop-in if sshd rejects it or the reload fails, so a rerun starts over.
apply_ssh() {
  local conf="$1" want="$2" old="" had=0
  install -d -m 755 "$(dirname "$conf")"
  if [ -f "$conf" ]; then had=1; old="$(cat "$conf")"; fi
  if [ "$had" = 0 ] || [ "$old" != "$want" ]; then
    printf '%s\n' "$want" > "$conf.new"
    mv "$conf.new" "$conf"
  fi
  if ! sshd -t || ! systemctl reload ssh; then
    if [ "$had" = 1 ]; then printf '%s\n' "$old" > "$conf"; else rm -f "$conf"; fi
    die "sshd rejected the config or the reload failed, reverted"
  fi
  sshd_hardened || die "sshd still allows root or password login after reload"
}

step_ssh() {
  local conf=/etc/ssh/sshd_config.d/00-lm-hardening.conf
  local want='PasswordAuthentication no
KbdInteractiveAuthentication no
PermitRootLogin no
PubkeyAuthentication yes'
  if [ -f "$conf" ] && [ "$(cat "$conf")" = "$want" ] && sshd_hardened; then return 0; fi
  change "harden sshd (key-only, no root login)" apply_ssh "$conf" "$want"
}

ufw_has() { ufw status 2>/dev/null | grep -Eq "^$1/tcp +$2"; }

# Oracle images ship this REJECT in INPUT and in the saved rules; it would sit ahead of ufw's allows.
ORACLE_RULE='-A INPUT -j REJECT --reject-with icmp-host-prohibited'

oracle_reject_present() {
  command -v iptables >/dev/null 2>&1 || return 1
  iptables -C INPUT -j REJECT --reject-with icmp-host-prohibited 2>/dev/null \
    || grep -qxF -- "$ORACLE_RULE" /etc/iptables/rules.v4 2>/dev/null
}

drop_oracle_reject() {
  iptables -D INPUT -j REJECT --reject-with icmp-host-prohibited 2>/dev/null || true
  if [ -f /etc/iptables/rules.v4 ]; then
    grep -vxF -- "$ORACLE_RULE" /etc/iptables/rules.v4 > /etc/iptables/rules.v4.new || true
    cat /etc/iptables/rules.v4.new > /etc/iptables/rules.v4
    rm -f /etc/iptables/rules.v4.new
  fi
}

step_firewall() {
  apt_install ufw
  # SSH is allowed before the firewall is switched on, so enabling it cannot cut the session.
  if ! ufw_has 22 LIMIT; then change "ufw limit 22/tcp" ufw limit 22/tcp; fi
  local port
  for port in 80 443; do
    if ! ufw_has "$port" ALLOW; then change "ufw allow $port/tcp" ufw allow "$port/tcp"; fi
  done
  if ! ufw status verbose 2>/dev/null | grep -q 'Default: deny (incoming), allow (outgoing)'; then
    change "ufw default deny incoming, allow outgoing" bash -c 'ufw default deny incoming && ufw default allow outgoing'
  fi
  if ! ufw status 2>/dev/null | grep -q '^Status: active'; then
    change "ufw enable" ufw --force enable
  fi
  if oracle_reject_present; then change "remove Oracle's INPUT reject rule" drop_oracle_reject; fi
}

validate
[ "$DRY_RUN" = 1 ] && log "dry run: nothing will be changed"
step_updates
step_docker
step_user
step_ssh
step_firewall

if [ "$changes" -eq 0 ]; then
  log "no changes"
else
  log "done: $changes change(s)"
fi
