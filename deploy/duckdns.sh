#!/bin/bash
# Keeps your DuckDNS domain pointed at this box's current public IP.
# Fill in DOMAIN (the part before .duckdns.org) and TOKEN, then:
#   mkdir -p ~/duckdns && cp deploy/duckdns.sh ~/duckdns/ && chmod +x ~/duckdns/duckdns.sh
#   ( crontab -l 2>/dev/null; echo '*/5 * * * * ~/duckdns/duckdns.sh >/dev/null 2>&1' ) | crontab -
# Tip: assign an Elastic IP to the instance and you barely need this.

DOMAIN="YOURSUB"
TOKEN="YOUR-DUCKDNS-TOKEN"

curl -fsS "https://www.duckdns.org/update?domains=${DOMAIN}&token=${TOKEN}&ip=" \
    -o "$HOME/duckdns/duck.log"
