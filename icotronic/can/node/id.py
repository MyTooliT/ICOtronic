"""Support for a node (single CAN communication unit) in the ICOtronic system

See: https://mytoolit.github.io/Documentation/#mytoolit-communication-protocol
"""

# -- Imports ------------------------------------------------------------------

from __future__ import annotations

from re import fullmatch

# -- Classes ------------------------------------------------------------------


class NodeId:
    """This class represents a CAN node of the ICOtronic system

    A node represents a communication participant, such as a specific STH
    or a specific STU in the ICOtronic system.

    Args:

        node:
            The number that identifies this node

    Examples:

        Create node with default value

        >>> NodeId().value
        0

        Create nodes with string values

        >>> NodeId('STH 1')
        STH 1

        >>> NodeId('STU1')
        STU 1

        >>> NodeId('SPU 1').value
        15

        Using incorrect numbers to initialize a node will fail

        >>> NodeId('STU 15')
        Traceback (most recent call last):
           ...
        ValueError: Unknown node identifier “STU 15”

        You can create a copy of an already existing node

        >>> NodeId(NodeId('STH 2'))
        STH 2

    """

    def __init__(self, node: int | str | NodeId = 0) -> None:

        if isinstance(node, str):
            # Check for broadcast pseudo nodes
            broadcast_match = fullmatch(
                "Broadcast With(?P<no_acknowledgment>out)? Acknowledgment",
                node,
            )
            if broadcast_match:
                self.value = 0 if broadcast_match["no_acknowledgment"] else 31
                return

            # Check normal nodes
            node_match = fullmatch(
                r"(?P<name>S(?:PU|TH|TU)) ?(?P<number>\d{1,2})", node
            )

            if node_match is not None:
                node_name = node_match["name"]
                node_number = int(node_match["number"])

                if node_name == "STH" and 1 <= node_number <= 14:
                    self.value = node_number
                    return

                if node_name == "SPU" and 1 <= node_number <= 2:
                    self.value = node_number + 14
                    return

                if node_name == "STU" and 1 <= node_number <= 14:
                    self.value = node_number + 16
                    return

            raise ValueError(f"Unknown node identifier “{node}”")

        if isinstance(node, NodeId):
            self.value = node.value
            return

        self.value = node

    def __repr__(self) -> str:
        """Return the string representation of the current node

        Returns:

            A string that describes the node

        Examples:

            Get the string representation of some example node ids

            >>> NodeId(0)
            Broadcast With Acknowledgment

            >>> NodeId(31)
            Broadcast Without Acknowledgment

            >>> NodeId(10)
            STH 10

            >>> NodeId(15)
            SPU 1

            >>> NodeId(18)
            STU 2

        """

        if self.value in (0, 31):
            return (
                "Broadcast "
                f"With{'' if self.value == 0 else 'out'} Acknowledgment"
            )
        if self.is_sth():
            return f"STH {self.value}"

        if 15 <= self.value <= 16:
            return f"SPU {self.value - 14}"

        return f"STU {self.value - 16}"

    def is_sth(self) -> bool:
        """Check if this node is an STH or not

        Returns:

            ``True`` if this node is an STH or ``False`` otherwise

        Examples:

            Check for some example node ids if they represent an STH or not

            >>> NodeId('STH 1').is_sth()
            True

            >>> NodeId('STU 12').is_sth()
            False

            >>> NodeId('STH 12').is_sth()
            True

        """

        return 1 <= self.value <= 14

    def is_stu(self) -> bool:
        """Check if this node is an STU or not

        Returns:

            ``True`` if this node is an STU or ``False`` otherwise

        Examples:

            Check for some example node ids if they represent an STU or not

            >>> NodeId('STH 7').is_stu()
            False

            >>> NodeId('STU 14').is_stu()
            True

            >>> NodeId('SPU 1').is_stu()
            False

        """

        return 17 <= self.value <= 30


# -- Main ---------------------------------------------------------------------

if __name__ == "__main__":
    from doctest import testmod

    testmod()
