"""
seed-agent connectors — Platform adapters for autonomous agents.

Each connector normalizes platform-specific communication into a standard
JSON message format, using the filesystem (inbox/outbox) as the interface.
The agent never imports connector code. The filesystem IS the interface.
"""

from connectors.base.connector import Connector
from connectors.base.message import Message, OutgoingMessage
from connectors.base.manager import ConnectorManager

__all__ = ["Connector", "Message", "OutgoingMessage", "ConnectorManager"]
