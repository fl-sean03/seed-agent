# Deploying Seed Agent on Oracle Cloud Free Tier

Oracle Cloud Always Free tier provides a perfect home for a seed agent:
- **ARM VM**: 4 OCPUs, 24 GB RAM (Ampere A1) — more than enough
- **Boot volume**: 200 GB
- **Always free**: No credit card charges

## Setup

### 1. Create an Oracle Cloud account

Sign up at [cloud.oracle.com](https://cloud.oracle.com). The Always Free tier
requires a credit card for verification but won't charge it.

### 2. Create a VM

- Shape: **VM.Standard.A1.Flex** (ARM)
- OCPUs: 1 (can use up to 4 for free)
- Memory: 6 GB (can use up to 24 for free)
- Image: **Ubuntu 24.04** (Canonical)
- SSH: Add your public key

### 3. SSH in and install prerequisites

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install inotify-tools
sudo apt install -y inotify-tools python3 python3-pip git

# Install Claude Code CLI
# Follow instructions at https://claude.ai/download

# Verify
claude --version
inotifywait --help
python3 --version
```

### 4. Clone and deploy

```bash
git clone https://github.com/sfhsdev/seed-agent.git
cd seed-agent
bash deploy/deploy.sh --seed-home ~/agent --context developer
```

### 5. Configure connectors

```bash
# Edit connectors.yml with your tokens
nano ~/agent/connectors.yml
```

### 6. Start the agent

```bash
# Manual start
cd ~/agent && SEED_HOME=~/agent bash seed/loop.sh

# Or use the seed CLI
./deploy/seed start

# Or install as systemd service
bash deploy/deploy.sh --seed-home ~/agent --systemd
sudo systemctl enable seed-agent
sudo systemctl start seed-agent
```

### 7. Verify

```bash
# Check status
./deploy/seed status

# View logs
./deploy/seed logs --follow

# Test with CLI connector
python3 -m connectors.cli.connector --seed-home ~/agent
```

## Cost

- **VM**: $0/month (Always Free)
- **Claude API**: ~$3-10/day depending on activity
- **Storage**: $0 (200 GB included)
- **Network**: 10 TB/month outbound (more than enough)

Total: **~$90-300/month** for the Claude API, everything else free.

## Tips

- Use `tmux` or `screen` to keep sessions alive
- Set up Slack + Email connectors for remote access
- The agent will self-modify and grow — check memory/ periodically
- Back up memory/ to git for version history
