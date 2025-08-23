#!/bin/sh
set -e

# Restrict outbound traffic to Maximo and Coupa endpoints only
iptables -P OUTPUT DROP
iptables -A OUTPUT -m conntrack --ctstate ESTABLISHED,RELATED -j ACCEPT
# Allow DNS queries
iptables -A OUTPUT -p udp --dport 53 -j ACCEPT
iptables -A OUTPUT -p tcp --dport 53 -j ACCEPT
# Allow HTTPS to Maximo and Coupa
iptables -A OUTPUT -p tcp -d 203.0.113.10 --dport 443 -j ACCEPT # Maximo
iptables -A OUTPUT -p tcp -d 198.51.100.20 --dport 443 -j ACCEPT # Coupa

exec ./apps/api/entrypoint.sh
