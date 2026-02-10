# Email Connector

IMAP/SMTP email connector using Python stdlib. No external dependencies.

## Setup

For Gmail, use an [App Password](https://myaccount.google.com/apppasswords)
(not your regular password). Enable IMAP in Gmail settings.

## Configuration

```yaml
# connectors.yml
connectors:
  - name: email-main
    type: email
    imap_host: imap.gmail.com
    imap_port: 993
    smtp_host: smtp.gmail.com
    smtp_port: 587
    username: ${EMAIL_USERNAME}
    password: ${EMAIL_PASSWORD}
    poll_interval: 60        # Seconds between IMAP checks
    folders: ["INBOX"]
    allowed_senders: []      # Email addresses to filter (empty = all)
```

## Environment Variables

| Variable | Description |
|----------|-------------|
| `EMAIL_USERNAME` | Email address |
| `EMAIL_PASSWORD` | App password (not regular password) |

## Dependencies

None. Uses Python stdlib (imaplib, smtplib).

## Standalone Usage

```bash
python -m connectors.email.connector --seed-home ~/agent
```
