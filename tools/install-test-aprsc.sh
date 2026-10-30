#!/bin/bash
# Private aprsc for MeshPRS testing (design/test-plan.md §6.1, stage T5): an APRS-IS server with NO uplink, so nothing
# a test sends can reach the real APRS-IS. Built from source (aprsc's apt repo is amd64 only; RiverReach is arm64).
#
#   run on RiverReach:  sudo bash install-test-aprsc.sh
#
# Listens on localhost and this machine's Tailscale address only (not the LAN):
#   14580  client port (filtered) -- point the Kelly iGate's server at 127.0.0.1 here
#   14501  status page (http://<tailscale ip>:14501/)
# Undo: systemctl disable --now aprsc-test; rm -rf /opt/aprsc /etc/systemd/system/aprsc-test.service; userdel aprsc
set -euo pipefail
V=aprsc-2.1.23.g4ece07a
SRC=/usr/local/src/$V

[ "$(id -u)" = 0 ] || { echo "run with sudo"; exit 1; }
apt-get install -y -q build-essential libevent-dev libssl-dev libcap-dev zlib1g-dev libprotobuf-c-dev protobuf-c-compiler

mkdir -p /usr/local/src && cd /usr/local/src
[ -f $V.tar.gz ] || curl -s -f -O "http://he.fi/aprsc/down/$V.tar.gz"
sha256sum $V.tar.gz
rm -rf "$SRC" && tar xzf $V.tar.gz && cd "$SRC/src"
./configure --prefix=/opt/aprsc
make -j4
make install

id aprsc >/dev/null 2>&1 || useradd --system --home-dir /opt/aprsc --shell /usr/sbin/nologin aprsc
mkdir -p /opt/aprsc/logs /opt/aprsc/data
chown -R aprsc:aprsc /opt/aprsc/logs /opt/aprsc/data

TS=$(tailscale ip -4 2>/dev/null | head -1 || true)
{
  echo "# MeshPRS private test server -- NO Uplink lines: nothing reaches the real APRS-IS (test-plan.md §6.1)"
  echo "ServerId   MPRSTEST"
  echo "PassCode   0"
  echo "MyAdmin    \"Alec VK4AZ\""
  echo "MyEmail    alec@localhost"
  echo "RunDir     /opt/aprsc/data"
  echo "LogRotate  10 5"
  echo "UpstreamTimeout 15s"
  echo "ClientTimeout   48h"
  echo "Listen \"Client-Defined Filters\" igate tcp 127.0.0.1 14580"
  echo "HTTPStatus 127.0.0.1 14501"
  if [ -n "$TS" ]; then
    echo "Listen \"Client-Defined Filters (tailnet)\" igate tcp $TS 14580"
    echo "HTTPStatus $TS 14501"
  fi
} > /opt/aprsc/etc/aprsc.conf
grep -qi '^Uplink' /opt/aprsc/etc/aprsc.conf && { echo "an Uplink line got in -- refusing"; exit 1; }

cat > /etc/systemd/system/aprsc-test.service <<'UNIT'
[Unit]
Description=aprsc, private MeshPRS test server (no uplink)
After=network-online.target tailscaled.service
Wants=network-online.target

[Service]
ExecStart=/opt/aprsc/sbin/aprsc -u aprsc -e info -o file -r /opt/aprsc/logs -c /opt/aprsc/etc/aprsc.conf
Restart=on-failure
LimitNOFILE=4096

[Install]
WantedBy=multi-user.target
UNIT
systemctl daemon-reload
systemctl enable --now aprsc-test
sleep 3
systemctl --no-pager --lines=5 status aprsc-test || true
ss -ltn | grep -E ':(14580|14501) ' || echo "not listening yet -- see /opt/aprsc/logs/aprsc.log"
printf 'user N0CALL pass -1 vers check 1\r\n' | timeout 5 nc 127.0.0.1 14580 | head -2 || true
