.. currentmodule:: icotronic.can

Connection
##########

Connecting to STU
*****************

To communicate with the ICOtronic system use the the async context manager of the :class:`Connection` class to open and close the connection to the STU:

.. doctest::

   >>> from asyncio import run
   >>> from icotronic.can import Connection

   >>> async def create_and_shutdown_connection():
   ...     async with Connection() as stu:
   ...         pass # ← Your code goes here

   >>> run(create_and_shutdown_connection())

Connecting to Sensor Node
*************************

To connect to a sensor node (e.g. SHA, SMH, STH) use the async context manager of the coroutine :meth:`stu.connect_sensor_node`. To connect to a node you need to know one of the `identifiers of the node`_. In the example below we connect to a node with the name `Test-STH`:

.. doctest::

   >>> from asyncio import run
   >>> from netaddr import EUI
   >>> from icotronic.can import Connection

   >>> async def connect_to_sensor_node(identifier):
   ...     async with Connection() as stu:
   ...         async with stu.connect_sensor_node(identifier) as sensor_node:
   ...             return await sensor_node.get_mac_address()

   >>> mac_address = run(connect_to_sensor_node("Test-STH"))
   >>> isinstance(mac_address, EUI)
   True

By default :meth:`stu.connect_sensor_node` assumes that you want to connect to a generic sensor node (e.g. a sensory milling head (SMH)). To connect to an STH (a sensor node with additional functionality), use :class:`STH` for the ``sensor_node_class`` parameter:

.. doctest::

   >>> from asyncio import run
   >>> from icotronic.can import Connection, STH

   >>> async def get_sensor_range(identifier):
   ...     async with Connection() as stu:
   ...         async with stu.connect_sensor_node(identifier, STH) as sth:
   ...             return await sth.get_acceleration_sensor_range_in_g()

   >>> sensor_range = run(get_sensor_range("Test-STH"))
   >>> 0 <= sensor_range <= 200
   True

.. _identifiers of the node: https://mytoolit.github.io/ICOtronic/#sensor-node-identifiers
