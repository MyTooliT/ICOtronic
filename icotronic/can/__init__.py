"""Support for the MyTooliT CAN protocol

See: https://mytoolit.github.io/Documentation/#mytoolit-communication-protocol

for more information
"""

# -- Exports ------------------------------------------------------------------

from .error import ErrorResponseError, CANConnectionError, NoResponseError
from .connection import Connection
from .streaming import StreamingConfiguration
from .node.sth import STH
