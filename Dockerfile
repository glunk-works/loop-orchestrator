# syntax=docker/dockerfile:1

FROM python:3.12-slim AS base

RUN groupadd --gid 1000 app \
    && useradd --uid 1000 --gid app --create-home --shell /bin/bash app

WORKDIR /workspace

COPY pyproject.toml README.md ./
COPY src/ src/

RUN pip install --no-cache-dir . cryptography==49.0.0

# Custom encrypted-file keyring backend (containers/keyring_backend/) — lives
# outside src/loop_engine/ deliberately, wired in purely via keyring's own
# backend-discovery config below, never imported by loop_engine's own code.
COPY containers/keyring_backend/cryptfile_backend.py /opt/loop-engine-keyring-backend/cryptfile_backend.py

RUN mkdir -p /home/app/.config/python_keyring \
    && printf '[backend]\ndefault-keyring=cryptfile_backend.EncryptedFileKeyring\nkeyring-path=/opt/loop-engine-keyring-backend\n' \
        > /home/app/.config/python_keyring/keyringrc.cfg \
    && chown -R app:app /home/app/.config

# --- dev: full contributor toolchain, source stays a bind mount ---
FROM base AS dev

RUN apt-get update \
    && apt-get install --no-install-recommends -y git curl gnupg openssh-client socat procps \
    && curl -fsSL https://cli.github.com/packages/githubcli-archive-keyring.gpg \
        -o /usr/share/keyrings/githubcli-archive-keyring.gpg \
    && echo "deb [signed-by=/usr/share/keyrings/githubcli-archive-keyring.gpg] \
        https://cli.github.com/packages stable main" > /etc/apt/sources.list.d/github-cli.list \
    && apt-get update \
    && apt-get install --no-install-recommends -y gh \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

RUN pip install --no-cache-dir hatch

USER app

# --- prod: minimal runtime, no dev tooling ---
FROM base AS prod

USER app

ENTRYPOINT ["loop-engine"]
