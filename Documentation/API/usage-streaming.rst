Streaming
#########

Reading Data
************

After you connected to the sensor node use the coroutine :meth:`SensorNode.open_data_stream` to open the data stream and an ``async for`` statement to iterate over the received streaming data. The following code:

.. doctest::

   >>> from asyncio import run
   >>> from icotronic.can import Connection
   >>> from icotronic.can import StreamingConfiguration

   >>> async def read_streaming_data():
   ...     async with Connection() as stu:
   ...         async with stu.connect_sensor_node("Test-STH") as sensor_node:
   ...             channels = StreamingConfiguration(first=True)
   ...             async with sensor_node.open_data_stream(channels) as stream:
   ...                 async for data, lost_messages in stream:
   ...                     return data

   >>> data = run(read_streaming_data())

   >>> # Example Output: [32579, 32637, 32575]@1724251001.976368 #123
   >>> data # doctest:+ELLIPSIS
   [..., ..., ...]@... #...

   >>> len(data.values)
   3
   >>> isinstance(data.timestamp, float)
   True
   >>> all(0 <= value <= 2**16-1 for value in data.values)
   True
   >>> 0 <= data.counter <= 255
   True

- connects to a node called ``Test-STH``,
- opens a data stream for the first measurement channel,
- receives a single streaming data object,
- prints its representation and
- shows some of the properties of the streaming data object.

The data returned by the ``async for`` (``stream``) is an object of the class :class:`StreamingData` with the following attributes:

- :attr:`StreamingData.values`: a list containing either two or three values,
- :attr:`StreamingData.timestamp`: the timestamp when the data was collected
- :attr:`StreamingData.counter`: a cyclic message counter (0 – 255) that can be used to detect data loss

.. note::
   The amount of data stored in :attr:`StreamingData.values` depends on the enabled streaming channels. For the `recommended amount of one or three enabled channels`_ the list contains three values. For

   - one enabled channel all three values belong to the same channel, while
   - for the three enabled channels

     - the first value belongs to the first channel,
     - the second value belongs to the second channel,
     - and the third value belongs to the third channel.

.. |recommended amount of one or three enabled channels| replace:: **recommended amount** of one or three enabled channels
.. _recommended amount of one or three enabled channels: https://mytoolit.github.io/ICOtronic/#channel-selection

By default :attr:`StreamingData.values` contains 16-bit ADC values. To convert the data into multiples of g (`the standard gravity <https://en.wikipedia.org/wiki/Standard_gravity>`_) you can

- use the coroutine :meth:`STH.get_acceleration_conversion_function` to retrieve a function that converts 16-bit ADC values values into multiples of g and then
- use this function to convert streaming data with the method :meth:`StreamingData.apply`.

In the example below we convert the first retrieved streaming data object and return it:

.. doctest::

   >>> from asyncio import run
   >>> from icotronic.can import Connection
   >>> from icotronic.can import STH, StreamingConfiguration

   >>> async def read_streaming_data_g():
   ...     async with Connection() as stu:
   ...         async with stu.connect_sensor_node("Test-STH", STH) as sth:
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

Collecting Multiple Values
**************************

While working directly with the class :class:`StreamingData` might make sense for small projects often you:

- want to collect a bunch of data values,
- work on data for a specific measurement channel, or
- convert data values.

For that case you can use the class :class:`MeasurementData`. The example code below

- collects data for all three measurement channels,
- applies a conversion into multiples of g for the first channel (only), and
- checks that the values for the first channel are all between -2 g and 2 g.

.. doctest::

   >>> from asyncio import run
   >>> from time import monotonic
   >>> from icotronic.can import Connection, STH, StreamingConfiguration
   >>> from icotronic.measurement import Conversion, MeasurementData

   >>> async def collect_streaming_data(identifier):
   ...    async with Connection() as stu:
   ...        async with stu.connect_sensor_node(identifier, STH) as sth:
   ...            conversion_to_g = (await
   ...                sth.get_acceleration_conversion_function())
   ...            all_channels = StreamingConfiguration(
   ...                first=True, second=True, third=True
   ...            )
   ...            measurement_data = MeasurementData(all_channels)
   ...            async with sth.open_data_stream(all_channels) as stream:
   ...                messages = 10
   ...                async for data, _ in stream:
   ...                    measurement_data.append(data)
   ...                    messages -= 1
   ...                    if messages <= 0:
   ...                        break
   ...            measurement_data.apply(Conversion(first=conversion_to_g))
   ...            return measurement_data

   >>> data = run(collect_streaming_data(identifier="Test-STH"))
   >>> first_channel_in_g = data.first()
   >>> all(-2 <= data.value <= 2 for data in first_channel_in_g)
   True

Storing Data
************

If you want to store streaming data for later use you can use the :class:`Storage` class to open a context manager that lets you store data as `HDF5`_ file via the method :func:`add_streaming_data` of the class :class:`StorageData`. The code below shows how to store one second of measurement data in a file called ``measurement.hdf5``.

.. _HDF5: https://en.wikipedia.org/wiki/Hierarchical_Data_Format

.. doctest:: store

   >>> from asyncio import run
   >>> from pathlib import Path
   >>> from time import monotonic
   >>> from icotronic.can import Connection, STH, StreamingConfiguration
   >>> from icotronic.measurement import Storage

   >>> async def store_streaming_data(identifier, storage):
   ...     async with Connection() as stu:
   ...         async with stu.connect_sensor_node(identifier, STH) as sth:
   ...             conversion_to_g = (await
   ...                 sth.get_acceleration_conversion_function())
   ...
   ...             # Store acceleration range as metadata
   ...             storage.write_sensor_range(
   ...                 await sth.get_acceleration_sensor_range_in_g()
   ...             )
   ...             # Store sampling rate (and ADC configuration as metadata)
   ...             storage.write_sample_rate(await sth.get_adc_configuration())
   ...
   ...             async with sth.open_data_stream(
   ...                 storage.streaming_configuration
   ...             ) as stream:
   ...                 # Read data for about one seconds
   ...                 end = monotonic() + 1
   ...                 async for data, _ in stream:
   ...                     # Convert from ADC bit value into multiples of g
   ...                     storage.add_streaming_data(
   ...                         data.apply(conversion_to_g))
   ...                     if monotonic() > end:
   ...                         break

   >>> filepath = Path("measurement.hdf5") # Store data in HDF5 file
   >>> with Storage(filepath, StreamingConfiguration(first=True)) as storage:
   ...     run(store_streaming_data("Test-STH", storage))

.. testcleanup:: store

   >>> filepath.unlink() # Remove data after you are done working with it

Since `HDF5`_ is a standard file format you can use general purpose tools such as `HDFView`_ to view the stored data. To specifically analyze the data produced by the ICOtronic package you can also use one of the scripts of the `ICOlyzer package`_.

For more information about the measurement format, please take a look at the section `“Measurement Data”`_ of the general ICOtronic package documentation.

.. _ICOlyzer package: https://github.com/MyTooliT/ICOlyzer
.. _HDFView: https://www.hdfgroup.org/download-hdfview
.. _“Measurement Data”: https://mytoolit.github.io/ICOtronic/#measurement-data

Determining Data Loss
*********************

.. currentmodule:: icotronic.can.streaming

Sometimes the

- **connection** to your sensor node might be **bad** or
- code might run **too slow to retrieve/process streaming data**.

In both cases there will be some form of data loss. The ICOtronic library currently takes multiple measures to detect data loss.

Bad Connection
==============

The iterator for streaming data :class:`AsyncStreamBuffer` will raise a :class:`StreamingTimeoutError`, if there is **no streaming data for a certain amount of time** (default: 5 seconds). The class :class:`AsyncStreamBuffer` also provides access to statistics that can be used to determine the amount of lost data. For example, if you iterate through the streaming messages with ``async for``, then in addition to the streaming data, the iterator will also return the **amount of lost messages since the last successfully received message** (``lost_messages`` in the example below):

.. code-block::
   :emphasize-lines: 2

   async with sensor_node.open_data_stream(channels) as stream:
       async for data, lost_messages in stream:
           if lost_messages > 0:
               print(f"Lost {lost_messages} messages!")

To access the overall data quality, since the start of streaming you can use the method :meth:`AsyncStreamBuffer.dataloss`. The example code below shows how to use this method:

.. doctest::

   >>> from asyncio import run
   >>> from time import monotonic
   >>> from icotronic.can import Connection, StreamingConfiguration

   >>> async def determine_data_loss(identifier):
   ...     async with Connection() as stu:
   ...         async with stu.connect_sensor_node(identifier) as sensor_node:
   ...              end = monotonic() + 1 # Read data for roughly one second
   ...              channels = StreamingConfiguration(first=True)
   ...              async with sensor_node.open_data_stream(channels) as stream:
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
   >>> from icotronic.can import Connection, StreamingConfiguration

   >>> async def determine_data_loss(identifier):
   ...       async with Connection() as stu:
   ...           async with stu.connect_sensor_node(identifier) as sensor_node:
   ...               start = monotonic()
   ...               end = start + 2.1
   ...               last_reset = start
   ...               data_lost = []
   ...               channels = StreamingConfiguration(first=True)
   ...               async with sensor_node.open_data_stream(channels) as stream:
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

The buffer of the CAN controller is only able to store a certain amount of streaming messages before it has to drop them to make room for new ones. For this reason the ICOtronic library will raise a :class:`StreamingBufferError`, if the buffer for streaming messages exceeds a certain threshold (default: 10 000 messages).
