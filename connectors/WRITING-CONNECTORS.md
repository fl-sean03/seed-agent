# Writing Custom Connectors

Build a connector for any communication platform in under 200 lines.

## The Contract

Your connector must:
1. **Receive** events from the platform
2. **Normalize** them to the standard Message format
3. **Write** JSON files to `messages/inbox/`
4. **Poll** `messages/outbox/<your-name>/` for outgoing messages
5. **Send** outgoing messages back to the platform

That's it. The agent handles everything else.

## Step-by-Step

### 1. Create the connector directory

```
connectors/
└── myplatform/
    ├── __init__.py          # Empty
    ├── connector.py         # Your connector class
    └── README.md            # Setup instructions
```

### 2. Subclass Connector

```python
from connectors.base.connector import Connector
from connectors.base.message import (
    ConnectorInfo, Content, Conversation, Message, OutgoingMessage, Sender,
)

class MyPlatformConnector(Connector):
    connector_type = "myplatform"  # Must be set

    def connect(self) -> None:
        """Authenticate with the platform."""
        self._token = self.get_config("token", env_key="MYPLATFORM_TOKEN")
        # Set up your client, authenticate, etc.

    def disconnect(self) -> None:
        """Clean up on shutdown."""
        pass

    def send_message(self, msg: OutgoingMessage) -> bool:
        """Send a message to the platform. Return True on success."""
        # msg.conversation_id = where to send
        # msg.text = what to send
        # msg.thread_id = reply to (optional)
        return True

    def run_loop(self) -> None:
        """Main event loop. Must block. Check self._running for shutdown."""
        import threading, time

        # Start outbox poller in background
        def poll():
            while self._running:
                self.process_outbox()
                time.sleep(2)
        threading.Thread(target=poll, daemon=True).start()

        # Your platform-specific event loop
        while self._running:
            event = self._client.wait_for_event()  # Your platform SDK

            msg = Message(
                connector=ConnectorInfo(type="myplatform", instance=self.name),
                sender=Sender(id="...", username="...", display_name="..."),
                content=Content(text=event.text),
                conversation=Conversation(id="...", type="channel", name="..."),
            )
            self.write_to_inbox(msg)  # Base class handles the rest
```

### 3. Register it (optional)

Add to `connectors/base/manager.py` CONNECTOR_REGISTRY:

```python
CONNECTOR_REGISTRY = {
    ...
    "myplatform": "connectors.myplatform.connector",
}
```

Or use the fully qualified module path in connectors.yml:

```yaml
connectors:
  - name: my-instance
    type: connectors.myplatform.connector
    token: ${MYPLATFORM_TOKEN}
```

### 4. Add a __main__ block

```python
if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--seed-home", default=".")
    parser.add_argument("--name", default="myplatform-main")
    args = parser.parse_args()

    connector = MyPlatformConnector(name=args.name, seed_home=args.seed_home)
    connector.run()
```

## Helper Methods

The base class provides:

| Method | What it does |
|--------|-------------|
| `self.write_to_inbox(msg)` | Write a Message to the inbox directory |
| `self.poll_outbox()` | Read and delete outgoing messages |
| `self.process_outbox()` | Poll + send all pending messages |
| `self.get_config(key, default, env_key)` | Read config with env var expansion |
| `self.logger` | Pre-configured logger |
| `self._running` | Set to False on SIGTERM/SIGINT |

## Tips

- Keep your connector under 250 lines
- Handle reconnection in your `run_loop`
- Use `self._running` to check for shutdown signals
- Log at INFO level for message flow, DEBUG for everything else
- Move failed outbox messages to `messages/failed/` instead of retrying forever
- Start the outbox poller as a daemon thread in `run_loop`
- Test with the CLI connector first to verify your message format

## Testing

```python
# Test message normalization without connecting to the platform
from connectors.base.message import Message, ConnectorInfo, Sender, Content, Conversation

msg = Message(
    connector=ConnectorInfo(type="myplatform", instance="test"),
    sender=Sender(id="u1", username="test"),
    content=Content(text="hello"),
    conversation=Conversation(id="c1", type="dm"),
)
print(msg.to_json())  # Verify the output
```
