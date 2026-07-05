#!/bin/sh
# Bridges this container's gpg to the real gpg-agent running on the Windows
# host under Gpg4win, so the signing passphrase is only ever entered via the
# host's own pinentry/Kleopatra prompt and never touches the container.
#
# How it works: Gpg4win's %LOCALAPPDATA%\gnupg\S.gpg-agent is not a real
# socket but libassuan's cross-platform "emulated socket" file — a port
# number followed by a 16-byte auth nonce. That file is bind-mounted in
# read-only (see devcontainer.json). gpg inside the container will read it
# and try to connect to 127.0.0.1:<port>, which resolves to the container's
# own loopback, not the host's — so we relay that port to
# host.docker.internal, which Docker Desktop bridges to the Windows host's
# loopback-bound services.
set -eu

HOST_SOCK_FILE="/home/app/.gnupg-host/S.gpg-agent"
GNUPGHOME="${GNUPGHOME:-/home/app/.gnupg}"

if [ ! -f "$HOST_SOCK_FILE" ]; then
    echo "gpg-forward: $HOST_SOCK_FILE not mounted, skipping GPG agent forwarding" >&2
    exit 0
fi

PORT=$(head -n1 "$HOST_SOCK_FILE" | tr -d '\r\n')

# Stop any local gpg-agent so it doesn't recreate a real socket at
# $GNUPGHOME/S.gpg-agent and clobber the relay target, and drop any relay
# left over from a previous container start on the same port.
gpgconf --kill gpg-agent 2>/dev/null || true
pkill -f "socat TCP-LISTEN:${PORT}," 2>/dev/null || true

mkdir -p "$GNUPGHOME"
chmod 700 "$GNUPGHOME"
cp "$HOST_SOCK_FILE" "$GNUPGHOME/S.gpg-agent"
chmod 600 "$GNUPGHOME/S.gpg-agent"

nohup socat "TCP-LISTEN:${PORT},bind=127.0.0.1,fork,reuseaddr" "TCP:host.docker.internal:${PORT}" \
    >/tmp/gpg-relay.log 2>&1 &
disown

echo "gpg-forward: relaying 127.0.0.1:${PORT} -> host.docker.internal:${PORT}" >&2
