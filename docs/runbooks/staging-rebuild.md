# Rebuild the shared dev and staging server

## Trigger

The Oracle Always Free ARM server is lost, reclaimed or changed by Oracle, or you are moving to another ARM provider. Dev and staging hold only synthetic seed data, so nothing is restored. Target: ready for Kamal in under 1 hour.

## Steps

1. Create an Ubuntu 24.04 LTS arm64 server (Oracle: Ampere A1, 2 OCPU, 12 GB, public IP, your admin SSH key). In the provider network rules allow inbound TCP 22, 80 and 443 only (Oracle: the VCN security list).
2. Note the start time. Log in with the admin key (Oracle: user `ubuntu`, not root).
3. Get the script onto the server: `git clone` the repository, or `scp infra/staging/bootstrap.sh`.
4. Preview, then apply (the deploy public key is `ssh-keygen -y -f <deploy private key>`; `SERVER_DEPLOY_USER` is optional and defaults to `deploy`):

   ```bash
   export SERVER_DEPLOY_PUBLIC_KEY="ssh-ed25519 AAAA..."
   DRY_RUN=1 sudo --preserve-env=SERVER_DEPLOY_PUBLIC_KEY,SERVER_DEPLOY_USER,DRY_RUN ./infra/staging/bootstrap.sh
   sudo --preserve-env=SERVER_DEPLOY_PUBLIC_KEY,SERVER_DEPLOY_USER ./infra/staging/bootstrap.sh
   ```

5. Run it a second time. It must print `no changes` and exit 0.
6. Point DNS for the dev and staging hostnames at the new IP in Cloudflare. Deploying the apps is a separate step (ticket #11).
7. Note the end time and fill the table below.

The script installs unattended security updates, Docker Engine from the official Docker apt repository (key fingerprint checked), a key-only deploy user in the `docker` group, key-only SSH with root login off, and ufw allowing only 22, 80 and 443. Admin login as root stops working after it runs. It also removes Oracle's default INPUT `REJECT icmp-host-prohibited` rule (running and saved), which would otherwise block 80 and 443, and rate-limits SSH with `ufw limit`.

Security notes:

- The VCN security list is the real perimeter. Docker-published ports bypass ufw, so every Kamal accessory (database, Redis, anything private) must publish on `127.0.0.1` only, never `0.0.0.0`.
- The deploy key is root-equivalent on the host (docker group). Keep it only in the CI secrets (`DEV_` and `STAGING_`) and on the owner's machine, and never reuse it for production.

| Run | Server | Start | End | Minutes |
| --- | --- | --- | --- | --- |
| Blank-server timing | not yet run, owner to fill | | | |

## Verify

- From your machine: `ssh -i <deploy private key> deploy@<server> docker ps` lists no error.
- `ssh deploy@<server>` with a password or as `root` is refused.
- On the server: `sudo ufw status` shows only 22, 80 and 443 allowed; `systemctl is-enabled unattended-upgrades` prints `enabled`.
- From your machine: `curl -I http://<server>` gets a connection (a refused or reset connection is fine once nothing listens yet; a timeout or `icmp-host-prohibited` means the VCN list or the Oracle reject rule still blocks 80).
- On the server: `sudo sshd -T | grep -E 'permitrootlogin|passwordauthentication'` shows both `no`.
- Second script run prints `no changes`.

## Rollback

The script only prepares a blank server, so rolling back is discarding it. To undo one change on a live server: remove `/etc/ssh/sshd_config.d/00-lm-hardening.conf` and `sudo systemctl reload ssh` (SSH hardening), or `sudo ufw disable` (firewall). Oracle's reject rule is not restored; to bring it back, `sudo iptables -A INPUT -j REJECT --reject-with icmp-host-prohibited`. If SSH locks you out, use the provider console, or delete the server and rerun from step 1.
