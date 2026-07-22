# Development sandbox — all software work happens inside this container.
# Add tools here (never install on the host), then run: sandbox/sandbox.sh rebuild
FROM ubuntu:24.04

ENV DEBIAN_FRONTEND=noninteractive

# Base toolchain: build essentials, git, networking utils, tmux
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    ca-certificates \
    curl \
    git \
    jq \
    pkg-config \
    tmux \
    unzip \
    wget \
    && rm -rf /var/lib/apt/lists/*

# Node.js 22 LTS — drop this block if the project has no package.json
RUN curl -fsSL https://deb.nodesource.com/setup_22.x | bash - \
    && apt-get install -y --no-install-recommends nodejs \
    && rm -rf /var/lib/apt/lists/* \
    && npm install -g pnpm

# Python 3 + venv + pip — drop this block if the project has no Python
RUN apt-get update && apt-get install -y --no-install-recommends \
    python3 \
    python3-pip \
    python3-venv \
    && rm -rf /var/lib/apt/lists/*

# Non-root dev user (uid 1000 matches the host user, keeps bind-mount perms clean)
RUN userdel -r ubuntu 2>/dev/null || true \
    && useradd -m -u 1000 -s /bin/bash dev
USER dev
WORKDIR /workspace

# tmux defaults (mouse, vi copy-mode, OSC52 clipboard) for the dev user
COPY --chown=dev:dev tmux.conf /home/dev/.tmux.conf

CMD ["sleep", "infinity"]
