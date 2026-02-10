# Webhook Connector

Generic HTTP endpoint using Flask. Accepts POST requests with JSON payloads.
Enables integration with any platform that can send HTTP webhooks.

## Install

```bash
pip install seed-agent[webhook]
```

## Configuration

```yaml
# connectors.yml
connectors:
  - name: webhook-main
    type: webhook
    host: 0.0.0.0
    port: 8080
    secret: ${WEBHOOK_SECRET}  # Optional
    path: /webhook
```

## Endpoints

| Method | Path | Description |
|--------|------|-------------|
| POST | `/webhook` | Send a message to the agent |
| GET | `/webhook/health` | Health check |
| GET | `/webhook/response/<id>` | Poll for a response |

## Send a Message

```bash
curl -X POST http://localhost:8080/webhook \
  -H "Content-Type: application/json" \
  -H "X-Webhook-Secret: your-secret" \
  -d '{"sender": "user", "text": "Hello agent", "channel": "webhook"}'
```

## Environment Variables

| Variable | Description |
|----------|-------------|
| `WEBHOOK_SECRET` | Optional secret for request verification |

## Standalone Usage

```bash
python -m connectors.webhook.connector --seed-home ~/agent --port 8080
```
