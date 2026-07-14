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
    && curl -1sLf https://artifacts-cli.infisical.com/infisical.gpg \
        | gpg --dearmor -o /usr/share/keyrings/infisical-archive-keyring.gpg \
    && echo "deb [signed-by=/usr/share/keyrings/infisical-archive-keyring.gpg] \
        https://artifacts-cli.infisical.com/deb stable main" > /etc/apt/sources.list.d/infisical.list \
    && apt-get update \
    && apt-get install --no-install-recommends -y gh infisical=0.43.100 \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# gitleaks ships only as a GitHub release binary (no apt repo): pinned
# version + sha256 verification, matching the repo's supply-chain bar. Keep
# the version in sync with what gitleaks-action resolves in CI.
ARG GITLEAKS_VERSION=8.30.1
ARG GITLEAKS_SHA256=551f6fc83ea457d62a0d98237cbad105af8d557003051f41f3e7ca7b3f2470eb
RUN curl -fsSL "https://github.com/gitleaks/gitleaks/releases/download/v${GITLEAKS_VERSION}/gitleaks_${GITLEAKS_VERSION}_linux_x64.tar.gz" \
        -o /tmp/gitleaks.tar.gz \
    && echo "${GITLEAKS_SHA256}  /tmp/gitleaks.tar.gz" | sha256sum -c - \
    && tar -xzf /tmp/gitleaks.tar.gz -C /usr/local/bin gitleaks \
    && rm /tmp/gitleaks.tar.gz

# ruff is a hatch dev-env dependency (pyproject [tool.hatch.envs.default]), so
# the base stage's `pip install .` (runtime deps only) does not put it on the
# container's system Python. The sandboxed Coder's `run_lint` tool shells
# `sys.executable -m ruff`, which resolves to that system Python — so ruff must
# be installed here for `run_lint` to work inside the sandbox. Pin matches
# pyproject.
RUN pip install --no-cache-dir hatch ruff==0.15.20

USER app

# --- prod: minimal runtime, no dev tooling ---
FROM base AS prod

USER app

ENTRYPOINT ["loop-engine"]
