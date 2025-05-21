.. currentmodule:: icotronic.can

*****************
Device Connection
*****************

Connecting to STU
=================

To communicate with the ICOtronic system use the :class:`Connection` class. We recommend you use the async context manager to open and close the connection (to the STU):

.. doctest::

   >>> from asyncio import run
   >>> from icotronic.can import Connection

   >>> async def create_and_shutdown_connection():
   ...     async with Connection() as stu:
   ...         pass # ← Your code goes here

   >>> run(create_and_shutdown_connection())

Connecting to Sensor Device
===========================

.. currentmodule:: icotronic.can.node.stu

To connect to a sensor device (e.g. SHA, SMH, STH) use the async context manager of the coroutine :meth:`stu.connect_sensor_device`. To connect to a device you need to know one of the `identifiers of the device`_. In the example below we connect to a device with the name `Test-STH`:

.. doctest::

   >>> from asyncio import run
   >>> from netaddr import EUI
   >>> from icotronic.can import Connection

   >>> async def connect_to_sensor_device(identifier):
   ...     async with Connection() as stu:
   ...         async with stu.connect_sensor_device(identifier) as sensor_device:
   ...             return await sensor_device.get_mac_address()

   >>> mac_address = run(connect_to_sensor_device("Test-STH"))
   >>> isinstance(mac_address, EUI)
   True

By default :meth:`stu.connect_sensor_device` assumes that you want to connect to a generic sensor device (e.g. a sensory milling head (SMH)). To connect to an STH (a sensor device with additional functionality), use :class:`STH` for the `sensor_node_class` parameter:

.. doctest::

   >>> from asyncio import run
   >>> from icotronic.can import Connection, STH

   >>> async def get_sensor_range(identifier):
   ...     async with Connection() as stu:
   ...         async with stu.connect_sensor_device(identifier, STH) as sth:
   ...             return await sth.get_acceleration_sensor_range_in_g()

   >>> sensor_range = run(get_sensor_range("Test-STH"))
   >>> 0 <= sensor_range <= 200
   True

.. _identifiers of the device: https://mytoolit.github.io/ICOtronic/#sensor-device-identifiers

***********************
Auxiliary Functionality
***********************

Reading Names
=============

After your are connected to the a device you can read its (advertisement) name using the coroutine :meth:`SensorNode.get_name`:

.. doctest::

   >>> from asyncio import run
   >>> from icotronic.can import Connection

   >>> async def read_sensor_name(name):
   ...     async with Connection() as stu:
   ...         async with stu.connect_sensor_device(name) as sensor_device:
   ...             sensor_name = await sensor_device.get_name()
   ...             return sensor_name

   >>> sensor_name = "Test-STH"
   >>> run(read_sensor_name(sensor_name))
   'Test-STH'

*********
Streaming
*********

Reading Data
============

After you connected to the sensor device use the coroutine :meth:`SensorNode.open_data_stream` to open the data stream and an ``async for`` statement to iterate over the received streaming data. The following code:

.. doctest::

   >>> from icotronic.can import StreamingConfiguration

   >>> async def read_streaming_data():
   ...     async with Connection() as stu:
   ...         async with stu.connect_sensor_device("Test-STH") as sensor_device:
   ...             channels = StreamingConfiguration(first=True)
   ...             async with sensor_device.open_data_stream(channels) as stream:
   ...                 async for data, lost_messages in stream:
   ...                     print(data)
   ...                     break

   # Example Output: [32579, 32637, 32575]@1724251001.976368
   >>> run(read_streaming_data()) # doctest:+ELLIPSIS
   [...]@... #...

- connects to a device called ``Test-STH``,
- opens a data stream for the first measurement channel,
- receives a single streaming message and
  prints its representation.

.. currentmodule:: icotronic.can.streaming

The data returned by the ``async for`` (``stream``) is an object of the class :class:`StreamingData` with the following attributes:

- :attr:`StreamingData.values`: a list containing either two or three values,
- :attr:`StreamingData.timestamp`: the timestamp when the data was collected (actually `when it was received by the CAN controller <https://docs.peak-system.com/API/PCAN-Basic.Net/html/4f55937b-3d8f-de9e-62a9-be1b8a150f05.htm>`_)
- :attr:`StreamingData.counter`: a cyclic message counter (0 – 255) that can be used to detect data loss

.. note::
   The amount of data stored in :attr:`StreamingData.values` depends on the enabled streaming channels. For the `recommended amount of one or three enabled channels`_ the list contains three values. For

   - one enabled channel all three values belong to the same channel, while
   - for the three enabled channels

     - the first value belongs to the first channel,
     - the second value to the second channel,
     - and the third value to the third channel.

.. |recommended amount of one or three enabled channels| replace:: **recommended amount** of one or three enabled channels
.. _recommended amount of one or three enabled channels: https://mytoolit.github.io/ICOtronic/#channel-selection

By default :attr:`StreamingData.values` contains 16-bit ADC values. To convert the data into multiples of g (`the standard gravity <https://en.wikipedia.org/wiki/Standard_gravity>`_) you can

- use the coroutine :meth:`STH.get_acceleration_conversion_function` to retrieve a function that converts 16-bit ADC values values into multiples of g and then
- use this function to convert streaming data with the method :meth:`StreamingData.apply`.

In the example below we convert the first retrieved streaming data object and return it:

.. doctest::

   >>> async def read_streaming_data_g():
   ...     async with Connection() as stu:
   ...         async with stu.connect_sensor_device("Test-STH", STH) as sth:
   ...             conversion_to_g = (await
   ...                 sth.get_acceleration_conversion_function())
   ...             channels = StreamingConfiguration(first=True)
   ...             async with sth.open_data_stream(channels) as stream:
   ...                 async for data, lost_messages in stream:
   ...                     data.apply(conversion_to_g)
   ...                     return data

   >>> streaming_data = run(read_streaming_data_g())
   >>> len(streaming_data.values)
   3
   >>> all([-100 <= value <= 100 for value in streaming_data.values])
   True

Storing Data
============

.. currentmodule:: icotronic.measurement.storage

If you want to store streaming data for later use you can use the :class:`Storage` class to open a context manager that lets you store data as `HDF5 <https://en.wikipedia.org/wiki/Hierarchical_Data_Format>`_ file via the method :func:`add_streaming_data` of the class :class:`StorageData`:

.. automethod:: StorageData.add_streaming_data

For a more complete example, please take a look at the :ref:`HDF5 example code<Examples>`.

Determining Data Loss
=====================

.. currentmodule:: icotronic.can.streaming

Sometimes the

- **connection** to your sensor device might be **bad** or
- code might run **too slow to retrieve/process streaming data**.

In both cases there will be some form of data loss. The ICOtronic library currently takes multiple measures to detect data loss.

Bad Connection
--------------

The iterator for streaming data :class:`AsyncStreamBuffer` will raise a :class:`StreamingTimeoutError`, if there is **no streaming data for a certain amount of time** (default: 5 seconds):

.. autoexception:: StreamingTimeoutError

:class:`AsyncStreamBuffer` also provides access to statistics that can be used to determine the amount of lost data. For example, if you iterate through the streaming messages with ``async for``, then in addition to the streaming data the iterator will also return the **amount of lost messages since the last successfully received message** (``lost_messages`` in the example below):

.. code-block::
   :emphasize-lines: 2

   async with sensor_device.open_data_stream(channels) as stream:
       async for data, lost_messages in stream:
           if lost_messages > 0:
               print(f"Lost {lost_messages} messages!")

To access the overall data quality, since the start of streaming you can use the method :meth:`AsyncStreamBuffer.dataloss`:

.. automethod:: AsyncStreamBuffer.dataloss

The example code below shows how to use this method:

.. doctest::

   >>> from asyncio import run
   >>> from time import monotonic
   >>> from icotronic.can import Connection

   >>> async def determine_data_loss(identifier):
   ...     async with Connection() as stu:
   ...         async with stu.connect_sensor_device(identifier) as sensor_device:
   ...              end = monotonic() + 1 # Read data for roughly one second
   ...              channels = StreamingConfiguration(first=True)
   ...              async with sensor_device.open_data_stream(channels) as stream:
   ...                  async for data, lost_messages in stream:
   ...                      if monotonic() > end:
   ...                          break
   ...
   ...                  return stream.dataloss()

   >>> data_loss = run(determine_data_loss(identifier="Test-STH"))
   >>> data_loss < 0.1 # We assume that the data loss was less than 10 %
   True

If you want to calculate the amount of data loss for a specific time-span you can use the method :meth:`AsyncStreamBuffer.reset` to reset the message statistics at the start of the time-span. In the following example we stream data for (roughly) 2.1 seconds and return a list with the amount of data loss over periods of 0.5 seconds:

.. doctest::

   >>> from asyncio import run
   >>> from time import monotonic
   >>> from icotronic.can import Connection

   >>> async def determine_data_loss(identifier):
   ...       async with Connection() as stu:
   ...           async with stu.connect_sensor_device(identifier) as sensor_device:
   ...               start = monotonic()
   ...               end = start + 2.1
   ...               last_reset = start
   ...               data_lost = []
   ...               channels = StreamingConfiguration(first=True)
   ...               async with sensor_device.open_data_stream(channels) as stream:
   ...                   async for data, lost_messages in stream:
   ...                       current = monotonic()
   ...                       if current >= last_reset + 0.5:
   ...                          data_lost.append(stream.dataloss())
   ...                          stream.reset_stats()
   ...                          last_reset = current
   ...                       if current > end:
   ...                           break
   ...
   ...                   return data_lost

   >>> data_lost = run(determine_data_loss(identifier="Test-STH"))
   >>> len(data_lost)
   4
   >>> all(map(lambda loss: loss < 0.1, data_lost))
   True

.. note:: We used a overall runtime of 2.1 seconds, since in a timing interval of 2 seconds there is always the possibility that the code above either returns three or four data loss values depending on the specific timing.

Slow Processing of Data
-----------------------

The buffer of the CAN controller is only able to store a certain amount of streaming messages before it has to drop them to make room for new ones. For this reason the ICOtronic library will raise a :class:`StreamingBufferError`, if the buffer for streaming messages exceeds a certain threshold (default: 10 000 messages):

.. autoexception:: StreamingBufferError
