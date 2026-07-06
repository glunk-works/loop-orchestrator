#!/bin/sh
# Sequences the devcontainer's postStart steps — devcontainer.json supports
# only one postStartCommand, so each concern gets its own script here rather
# than an unreadable inline &&-chain.
set -eu
sh /workspace/.devcontainer/gpg-forward.sh
sh /workspace/.devcontainer/infisical-start.sh
