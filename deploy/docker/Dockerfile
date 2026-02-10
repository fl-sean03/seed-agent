FROM ubuntu:24.04

# System dependencies
RUN apt-get update && apt-get install -y \
    python3 python3-pip python3-venv \
    inotify-tools \
    curl \
    git \
    && rm -rf /var/lib/apt/lists/*

# Install Claude Code CLI
# Note: Replace with actual install command when available for your platform
# RUN curl -fsSL https://claude.ai/install.sh | sh

# Create agent user
RUN useradd -m -s /bin/bash seed
USER seed
WORKDIR /home/seed

# Copy seed-agent framework
COPY --chown=seed:seed . /home/seed/seed-agent-framework/

# Install Python dependencies
RUN python3 -m pip install --user -e /home/seed/seed-agent-framework/

# Default seed home
ENV SEED_HOME=/home/seed/agent
RUN mkdir -p $SEED_HOME

# Deploy the seed
RUN bash /home/seed/seed-agent-framework/deploy/deploy.sh \
    --seed-home $SEED_HOME

VOLUME ["/home/seed/agent/seed/memory", "/home/seed/agent/logs"]

CMD ["bash", "/home/seed/agent/seed/loop.sh"]
