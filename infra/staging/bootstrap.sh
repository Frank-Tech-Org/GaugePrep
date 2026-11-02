#!/usr/bin/env bash
# Takes a fresh Ubuntu ARM server to "ready for Kamal". Safe to run again: it prints "no changes" when nothing moved.
#   sudo SERVER_DEPLOY_PUBLIC_KEY="ssh-ed25519 AAAA..." ./bootstrap.sh
# Inputs: SERVER_DEPLOY_PUBLIC_KEY (required), SERVER_DEPLOY_USER (default deploy), DRY_RUN=1 (plan only),
# ALLOW_ANY_ARCH=1 (skip the arm64 check, for tests).
# shellcheck disable=SC2016  # bash -c bodies are single-quoted on purpose
set -euo pipefail

DEPLOY_USER="${SERVER_DEPLOY_USER:-deploy}"
DEPLOY_KEY="${SERVER_DEPLOY_PUBLIC_KEY:-}"
DRY_RUN="${DRY_RUN:-0}"
DOCKER_KEY_FPR="9DC858229FC7DD38854AE2D88D81803C0EBFCD88"
export DEBIAN_FRONTEND=noninteractive

changes=0
log() { printf '%s\n' "$*"; }
die() { printf 'error: %s\n' "$*" >&2; exit 1; }

# Run an action, or only announce it under DRY_RUN. Every call counts as one change.
change() {
  local what="$1"; shift
  changes=$((changes + 1))
  if [ "$DRY_RUN" = 1 ]; then log "would: $what"; return 0; fi
  log "changing: $what"
  "$@"
}

# Write a file only when its content or mode differs.
put_file() {
  local path="$1" mode="$2" content="$3"
  if [ -f "$path" ] && [ "$(cat "$path")" = "$content" ] && [ "$(stat -c %a "$path")" = "$mode" ]; then return 0; fi
  change "write $path" bash -c 'printf "%s\n" "$1" > "$2" && chmod "$3" "$2"' _ "$content" "$path" "$mode"
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
  [ "$ARCH" = arm64 ] || [ "${ALLOW_ANY_ARCH:-0}" = 1 ] || die "arm64 expected, found $ARCH"
}

step_updates() {
  apt_install unattended-upgrades
  put_file /etc/apt/apt.conf.d/20auto-upgrades 644 'APT::Periodic::Update-Package-Lists "1";
APT::Periodic::Unattended-Upgrade "1";'
}

step_docker() {
  apt_install ca-certificates curl gnupg
  local keyring=/etc/apt/keyrings/docker.gpg
  local fpr=""
  [ -f "$keyring" ] && fpr="$(gpg --show-keys --with-colons "$keyring" 2>/dev/null | awk -F: '$1 == "fpr" {print $10; exit}')"
  if [ "$fpr" != "$DOCKER_KEY_FPR" ]; then
    change "install the Docker apt key" bash -c '
      set -euo pipefail
      tmp="$(mktemp)"; trap "rm -f \"$tmp\"" EXIT
      curl -fsSL https://download.docker.com/linux/ubuntu/gpg | gpg --dearmor > "$tmp"
      got="$(gpg --show-keys --with-colons "$tmp" | awk -F: "\$1 == \"fpr\" {print \$10; exit}")"
      [ "$got" = "$1" ] || { echo "Docker key fingerprint mismatch" >&2; exit 1; }
      install -d -m 755 /etc/apt/keyrings
      install -m 644 "$tmp" "$2"' _ "$DOCKER_KEY_FPR" "$keyring"
  fi
  put_file /etc/apt/sources.list.d/docker.list 644 \
    "deb [arch=$ARCH signed-by=$keyring] https://download.docker.com/linux/ubuntu $UBUNTU_CODENAME stable"
  # Written before the install so the first start already rotates container logs.
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
    change "install the deploy key for $DEPLOY_USER" bash -c 'touch "$2" && chmod 600 "$2" && chown "$3:$3" "$2" && printf "%s\n" "$1" >> "$2"' _ "$DEPLOY_KEY" "$keys" "$DEPLOY_USER"
  fi
  if [ -f "$keys" ] && [ "$(stat -c '%a %U' "$keys")" != "600 $DEPLOY_USER" ]; then
    change "fix permissions on $keys" bash -c 'chmod 600 "$1" && chown "$2:$2" "$1"' _ "$keys" "$DEPLOY_USER"
  fi
}

step_ssh() {
  local conf=/etc/ssh/sshd_config.d/00-lm-hardening.conf
  local want='PasswordAuthentication no
KbdInteractiveAuthentication no
PermitRootLogin no
PubkeyAuthentication yes'
  if [ -f "$conf" ] && [ "$(cat "$conf")" = "$want" ]; then return 0; fi
  # Never reload sshd with a config it rejects, and never before the deploy key is in place.
  change "harden sshd (key-only, no root login)" bash -c '
    set -euo pipefail
    install -d -m 755 /etc/ssh/sshd_config.d
    printf "%s\n" "$1" > "$2.new"
    mv "$2.new" "$2"
    if ! sshd -t; then rm -f "$2"; echo "sshd rejected the config, reverted" >&2; exit 1; fi
    systemctl reload ssh' _ "$want" "$conf"
}

ufw_has() { ufw status 2>/dev/null | grep -Eq "^$1/tcp +ALLOW"; }

step_firewall() {
  apt_install ufw
  # SSH is allowed before the firewall is switched on, so enabling it cannot cut the session.
  local port
  for port in 22 80 443; do
    if ! ufw_has "$port"; then change "ufw allow $port/tcp" ufw allow "$port/tcp"; fi
  done
  if ! ufw status verbose 2>/dev/null | grep -q 'Default: deny (incoming), allow (outgoing)'; then
    change "ufw default deny incoming, allow outgoing" bash -c 'ufw default deny incoming && ufw default allow outgoing'
  fi
  if ! ufw status 2>/dev/null | grep -q '^Status: active'; then
    change "ufw enable" ufw --force enable
  fi
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
