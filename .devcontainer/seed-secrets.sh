#!/bin/sh
# Runs inside the `infisical run` child process spawned by infisical-start.sh,
# so ANTHROPIC_API_KEY / GITHUB_PERSONAL_ACCESS_TOKEN / LOOP_ENGINE_KEYRING_PASSPHRASE
# arrive as ordinary inherited env vars from Infisical — never read from a file.
#
# Seeds happen through each secret's own existing native store (keyring's
# encrypted blob via its unchanged set_password() path, gh's own credential
# file) rather than introducing a new one. Always overwrite rather than
# check-then-set: set_password() is a whole-file rewrite either way, and
# gh auth login --with-token is idempotent, so a rotated Infisical secret is
# picked up on the next container start with no extra logic.
set -eu

if [ -n "${ANTHROPIC_API_KEY:-}" ]; then
    python -c "import os, keyring; keyring.set_password('loop-engine', 'anthropic_api_key', os.environ['ANTHROPIC_API_KEY'])"
fi

if [ -n "${GITHUB_PERSONAL_ACCESS_TOKEN:-}" ]; then
    echo "${GITHUB_PERSONAL_ACCESS_TOKEN}" | gh auth login --with-token
fi

# Unlike the two secrets above, this one must persist to disk: client.py's
# keyring backend reads it on every get_password()/set_password() call for
# the life of the process, not just once at seed time.
if [ -n "${LOOP_ENGINE_KEYRING_PASSPHRASE:-}" ]; then
    mkdir -p /home/app/.infisical
    chmod 700 /home/app/.infisical
    printf '%s' "${LOOP_ENGINE_KEYRING_PASSPHRASE}" > /home/app/.infisical/keyring_passphrase
    chmod 600 /home/app/.infisical/keyring_passphrase
fi
