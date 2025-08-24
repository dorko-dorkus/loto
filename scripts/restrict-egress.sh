#!/bin/sh
set -e

# Restrict outbound traffic to an allowlist of hosts
iptables -P OUTPUT DROP
iptables -A OUTPUT -m conntrack --ctstate ESTABLISHED,RELATED -j ACCEPT
# Allow loopback and local networks
iptables -A OUTPUT -o lo -j ACCEPT
iptables -A OUTPUT -d 10.0.0.0/8 -j ACCEPT
iptables -A OUTPUT -d 172.16.0.0/12 -j ACCEPT
iptables -A OUTPUT -d 192.168.0.0/16 -j ACCEPT
# Allow DNS queries
iptables -A OUTPUT -p udp --dport 53 -j ACCEPT
iptables -A OUTPUT -p tcp --dport 53 -j ACCEPT

IFS=','
for host in $EGRESS_ALLOWED_HOSTS; do
    host=$(echo "$host" | xargs)
    [ -z "$host" ] && continue
    for ip in $(getent ahosts "$host" | awk '{print $1}' | sort -u); do
        iptables -A OUTPUT -p tcp -d "$ip" --dport 443 -j ACCEPT
    done
done
unset IFS

iptables -A OUTPUT -j LOG --log-prefix "EGRESS BLOCKED: " --log-level 4

exec "$@"
