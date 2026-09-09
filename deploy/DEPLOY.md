# Deploying Born to Fight

Target box: the EC2 instance (Ubuntu 22.04) that already runs the **ekstraklasa-betting**
backend (`uvicorn` on `:8000`) behind **Caddy** (`ekstraciapa.duckdns.org`).

Born to Fight runs as `uvicorn` on `127.0.0.1:8001` and gets its own DuckDNS domain.
Caddy proxies it and issues HTTPS automatically. Nothing about the existing site changes.

---

## 1. New DuckDNS domain

On <https://duckdns.org> add a second subdomain (e.g. `borntofight`) and point it at
**`13.53.139.138`** (same IP as ekstraciapa - it's the same box).

> If the instance is ever stopped/started the public IP changes. Either attach an
> Elastic IP in the EC2 console, or install `deploy/duckdns.sh` on a cron (step 6).

Below, replace `YOURSUB` with that subdomain.

---

## 2. Get the code onto the box

You don't use git on the server for ekstraklasa, but it's the cleanest option here
(gives you one-command updates). If you have a GitHub account:

**On your PC**, in the project folder:
```powershell
git init
git add -A
git commit -m "Born to Fight"
# create an empty repo on github.com, then:
git remote add origin https://github.com/<you>/borntofight.git
git branch -M main
git push -u origin main
```
`.gitignore` already excludes `.venv/`, `saves/`, `.idea/`.

**On the server** (EC2 Instance Connect terminal):
```bash
sudo apt-get update && sudo apt-get install -y git python3-venv python3-pip
git clone https://github.com/<you>/borntofight.git ~/borntofight
```

<details><summary>No GitHub? Use a tarball + scp instead</summary>

On your PC (needs the instance's <code>.pem</code> key and 7-Zip or tar):
```powershell
tar --exclude=.venv --exclude=saves --exclude=.git --exclude=.idea -czf bornfight.tgz *
scp -i C:\path\to\key.pem bornfight.tgz ubuntu@13.53.139.138:~
```
On the server:
```bash
mkdir -p ~/borntofight && tar -xzf ~/bornfight.tgz -C ~/borntofight
sudo apt-get update && sudo apt-get install -y python3-venv python3-pip
```
</details>

---

## 3. Build and smoke-test

```bash
cd ~/borntofight
python3 -m venv .venv
.venv/bin/pip install --upgrade pip
.venv/bin/pip install -r requirements.txt

.venv/bin/uvicorn app.main:app --host 127.0.0.1 --port 8001
# open a second EC2 Instance Connect tab and: curl -s localhost:8001 | head -c 60
# then Ctrl+C the uvicorn
```

`saves/` is created on first run and is gitignored.

---

## 4. Run it as a service

```bash
sudo cp ~/borntofight/deploy/borntofight.service /etc/systemd/system/borntofight.service
sudo systemctl daemon-reload
sudo systemctl enable --now borntofight
systemctl status borntofight --no-pager
curl -s localhost:8001 | head -c 60          # should print HTML
```

Logs: `journalctl -u borntofight -f`

---

## 5. Add it to Caddy

```bash
sudo cp /etc/caddy/Caddyfile /etc/caddy/Caddyfile.bak      # backup first
printf '\nYOURSUB.duckdns.org {\n    reverse_proxy localhost:8001\n}\n' | sudo tee -a /etc/caddy/Caddyfile
sudo caddy validate --config /etc/caddy/Caddyfile          # must say "Valid configuration"
sudo systemctl reload caddy
```

Wait ~15 s for Caddy to get the certificate, then open **`https://YOURSUB.duckdns.org`**.

If something's wrong: `journalctl -u caddy -f`, then restore with
`sudo cp /etc/caddy/Caddyfile.bak /etc/caddy/Caddyfile && sudo systemctl reload caddy`.

---

## 6. Updating later

```bash
cd ~/borntofight && git pull
.venv/bin/pip install -r requirements.txt
sudo systemctl restart borntofight
```

(tarball method: scp a new `bornfight.tgz`, extract over `~/borntofight`, restart.)

---

## 7. (only without an Elastic IP) keep DuckDNS current

```bash
mkdir -p ~/duckdns
cp ~/borntofight/deploy/duckdns.sh ~/duckdns/ && chmod +x ~/duckdns/duckdns.sh
nano ~/duckdns/duckdns.sh          # set DOMAIN=YOURSUB and your token
~/duckdns/duckdns.sh && cat ~/duckdns/duck.log     # prints: OK
( crontab -l 2>/dev/null; echo '*/5 * * * * ~/duckdns/duckdns.sh >/dev/null 2>&1' ) | crontab -
```

---

## Notes

- **RAM**: ~480 MB free. The service runs a single uvicorn worker (~70 MB). Fine.
- **Saves**: `~/borntofight/saves/<per-browser-id>/`. No login; a `bt_player` cookie
  separates visitors. Back up that folder to keep the careers.
- **Port 8001** is localhost-only, so it doesn't need a security-group rule and isn't
  reachable except through Caddy.
- **Tighten SSH** once you're done: the SG rule you added (`22` from `0.0.0.0/0`) can go
  back to your IP only.
- **Abuse**: new-career creation is capped at 25 slots per browser; no other rate limit.
