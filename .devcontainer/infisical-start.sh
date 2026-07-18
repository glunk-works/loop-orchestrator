#!/bin/sh
# Authenticates to Infisical via a Universal Auth machine identity and seeds
# this container's credentials from it: no persistent daemon, no secrets
# written to disk except the one file that must persist (see
# seed-secrets.sh). INFISICAL_CLIENT_ID/SECRET are forwarded from the host
# via devcontainer.json's containerEnv, the same ${localEnv:...} pattern
# gpg-forward.sh already relies on for GPG_HOST_DIR.
#
# The project itself is identified by /workspace/.infisical.json
# (workspaceId + defaultEnvironment) — that file contains no secret and is
# Infisical's own project-linking convention (created via `infisical init`).
# Unlike interactive/browser login, `infisical run` under universal-auth
# machine identity does NOT read workspaceId from .infisical.json on its
# own (it errors with "Project ID is required when using machine identity"),
# so it's passed explicitly via --projectId below.
set -eu

if [ -z "${INFISICAL_CLIENT_ID:-}" ] || [ -z "${INFISICAL_CLIENT_SECRET:-}" ]; then
    echo "infisical-start: INFISICAL_CLIENT_ID/SECRET not set, skipping Infisical provisioning" >&2
    exit 0
fi

INFISICAL_PROJECT_ID=$(python3 -c \
    "import json; print(json.load(open('/workspace/.infisical.json'))['workspaceId'])")

INFISICAL_TOKEN=$(infisical login --method=universal-auth \
    --client-id="${INFISICAL_CLIENT_ID}" \
    --client-secret="${INFISICAL_CLIENT_SECRET}" \
    --silent --plain)
export INFISICAL_TOKEN

# --env is passed explicitly (rather than relying solely on
# .infisical.json's defaultEnvironment) so this script always seeds from
# "dev" even if a developer changes that default locally for other reasons.
# --path points at where the secrets actually live in the Infisical project;
# the default path "/" holds none of them. NOTE: `/loop-engine` is the
# Infisical-side project path, deliberately NOT renamed with the sprint-42
# repo rename — it names storage in your Infisical project, not this repo.
# Rename it there first, then update this path, if you want them to match.
infisical run --projectId="${INFISICAL_PROJECT_ID}" --env=dev --path=/loop-engine \
    -- sh /workspace/.devcontainer/seed-secrets.sh

unset INFISICAL_TOKEN

# gh now owns the GitHub token in its own credential store. Future shells
# derive it fresh from there rather than persisting a second copy anywhere.
grep -qxF 'export GITHUB_PERSONAL_ACCESS_TOKEN="$(gh auth token 2>/dev/null)"' /home/app/.bashrc 2>/dev/null || \
    echo 'export GITHUB_PERSONAL_ACCESS_TOKEN="$(gh auth token 2>/dev/null)"' >> /home/app/.bashrc

echo "infisical-start: keyring seeded, gh authenticated" >&2
