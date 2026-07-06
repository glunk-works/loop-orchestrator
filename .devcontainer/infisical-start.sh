#!/bin/sh
# Authenticates to Infisical via a Universal Auth machine identity and seeds
# this container's credentials from it: no persistent daemon, no secrets
# written to disk except the one file that must persist (see
# seed-secrets.sh). INFISICAL_CLIENT_ID/SECRET are forwarded from the host
# via devcontainer.json's containerEnv, the same ${localEnv:...} pattern
# gpg-forward.sh already relies on for GPG_HOST_DIR.
#
# The project itself is identified by /workspace/.infisical.json
# (workspaceId + defaultEnvironment) rather than a value hardcoded here —
# that file contains no secret, is Infisical's own project-linking
# convention (created via `infisical init`), and is read automatically by
# `infisical run`/`login` without needing a --projectId flag.
set -eu

if [ -z "${INFISICAL_CLIENT_ID:-}" ] || [ -z "${INFISICAL_CLIENT_SECRET:-}" ]; then
    echo "infisical-start: INFISICAL_CLIENT_ID/SECRET not set, skipping Infisical provisioning" >&2
    exit 0
fi

INFISICAL_TOKEN=$(infisical login --method=universal-auth \
    --client-id="${INFISICAL_CLIENT_ID}" \
    --client-secret="${INFISICAL_CLIENT_SECRET}" \
    --silent --plain)
export INFISICAL_TOKEN

# --env is passed explicitly (rather than relying solely on
# .infisical.json's defaultEnvironment) so this script always seeds from
# "dev" even if a developer changes that default locally for other reasons.
infisical run --env=dev \
    -- sh /workspace/.devcontainer/seed-secrets.sh

unset INFISICAL_TOKEN

# gh now owns the GitHub token in its own credential store. Future shells
# derive it fresh from there rather than persisting a second copy anywhere.
grep -qxF 'export GITHUB_PERSONAL_ACCESS_TOKEN="$(gh auth token 2>/dev/null)"' /home/app/.bashrc 2>/dev/null || \
    echo 'export GITHUB_PERSONAL_ACCESS_TOKEN="$(gh auth token 2>/dev/null)"' >> /home/app/.bashrc

echo "infisical-start: keyring seeded, gh authenticated" >&2
