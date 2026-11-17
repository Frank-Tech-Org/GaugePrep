# Rebuild the shared dev and staging server

Purpose: turn a blank ARM server into the shared dev and staging host, ready for Kamal, in under an hour.

## Trigger

The Oracle Always Free ARM server is lost, reclaimed or changed, or dev and staging move to another ARM provider. Both hold synthetic data only, so nothing is restored.

## Prerequisites

- [ ] An Ubuntu 24.04 LTS arm64 server with a public IP and your admin SSH key (Oracle: Ampere A1, 2 OCPU, 12 GB, user `ubuntu`; AWS: t4g.small, 30 GB gp3, key pair `gaugeprep-deploy`).
- [ ] Provider network rules allow inbound TCP 22, 80 and 443 only (Oracle: VCN security list; AWS: security group). This is the real perimeter: Docker-published ports bypass ufw, so Kamal accessories publish on `127.0.0.1` only.
- [ ] The deploy public key: `ssh-keygen -y -f <deploy private key>`. The key is root-equivalent on the host; it lives only in Doppler and on the owner's machine, never in production.

## Steps

1. Note the start time and log in with the admin key. Expect: a shell as `ubuntu` (Oracle) or the admin user.
2. Copy the script: `git clone` the repository, or `scp infra/server/bootstrap.sh`. Expect: the script on the server.
3. Set the key: `export SERVER_DEPLOY_PUBLIC_KEY="ssh-ed25519 AAAA..."` (`SERVER_DEPLOY_USER` is optional, default `deploy`).
4. Preview: `DRY_RUN=1 sudo --preserve-env=SERVER_DEPLOY_PUBLIC_KEY,SERVER_DEPLOY_USER,DRY_RUN ./infra/server/bootstrap.sh`. Expect: the planned changes, nothing applied.
5. Apply: `sudo --preserve-env=SERVER_DEPLOY_PUBLIC_KEY,SERVER_DEPLOY_USER ./infra/server/bootstrap.sh`. Expect: exit 0; root login stops working.
6. Run step 5 again. Expect: `no changes`, exit 0.
7. In Cloudflare, point the dev and staging hostnames at the new IP. Expect: `dev.gaugeprep.com` resolves to it.
8. Note the end time. Then deploy with the deploy runbook (new server prerequisite and the CI key step).

## Verify

1. `ssh -i <deploy private key> deploy@<server> docker ps`. Pass: no error.
2. `ssh deploy@<server>` with a password, and `ssh root@<server>`. Pass: both refused.
3. `sudo ufw status`. Pass: only 22, 80 and 443 allowed.
4. `systemctl is-enabled unattended-upgrades`. Pass: `enabled`.
5. `curl -I http://<server>` from your machine. Pass: connected, refused or reset. A timeout or `icmp-host-prohibited` means the VCN list or Oracle's reject rule still blocks 80.
6. `sudo sshd -T | grep -E 'permitrootlogin|passwordauthentication'`. Pass: both `no`.
7. `swapon --show` and `sysctl vm.swappiness`. Pass: `/swapfile` at 2G, swappiness 10.
8. End minus start time. Pass: under 60 minutes (last measured 1 minute on AWS t4g.small, 2026-11-10).

## Rollback

1. Blank server: delete it and start again from step 1.
2. SSH hardening only: remove `/etc/ssh/sshd_config.d/00-lm-hardening.conf`, then `sudo systemctl reload ssh`.
3. Firewall only: `sudo ufw disable`.
4. Oracle's rules back: `sudo iptables -A INPUT -j REJECT --reject-with icmp-host-prohibited` and `sudo iptables -I INPUT -p tcp -m state --state NEW -m tcp --dport 22 -j ACCEPT`.
5. Locked out of SSH: use the provider console, or delete the server and go to step 1.
