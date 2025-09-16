Auxiliary Functionality
#######################

Reading Names
*************

After your are connected to the a node you can read its (advertisement) name using the coroutine :meth:`SensorNode.get_name`:

.. doctest::

   >>> from asyncio import run
   >>> from icotronic.can import Connection

   >>> async def read_sensor_name(name):
   ...     async with Connection() as stu:
   ...         async with stu.connect_sensor_node(name) as sensor_node:
   ...             sensor_name = await sensor_node.get_name()
   ...             return sensor_name

   >>> sensor_name = "Test-STH"
   >>> run(read_sensor_name(sensor_name))
   'Test-STH'

Changing ADC Configuration
**************************

To change

- the sample rate/frequency (via prescaler, acquisition time and oversampling rate) or
- the reference voltage

of the analog digital converter (ADC) of your sensor node you can use the coroutine :meth:`SensorNode.set_adc_configuration`. Since all of the parameters of this coroutine use default values, you can also just call it without changing any parameters to apply the default ADC configuration.

.. note:: Some sensor nodes use a different reference voltage (**not 3.3V**), in this case applying the default configuration might not be what you want.

To retrieve the current ADC configuration use the coroutine :meth:`SensorNode.get_adc_configuration`, which will return an :class:`ADCConfiguration` object. This object provides the method :meth:`ADCConfiguration.sample_rate` to calculate the sampling rate/frequency based on the current value of prescaler, acquisition time and oversampling rate.

In the example below we

- apply the default ADC configuration on the sensor node,
- retrieve the configuration via the coroutine :meth:`SensorNode.get_adc_configuration`, and then
- print the sampling rate/frequency based on the retrieved ADC configuration values.

.. doctest::

   >>> from asyncio import run
   >>> from icotronic.can import Connection
   >>> from icotronic.can.adc import ADCConfiguration

   >>> async def write_read_adc_config(name):
   ...     async with Connection() as stu:
   ...         async with stu.connect_sensor_node(name) as sensor_node:
   ...             # Set default configuration
   ...             await sensor_node.set_adc_configuration()
   ...             # Retrieve ADC configuration
   ...             adc_configuration = await sensor_node.get_adc_configuration()
   ...             print("Sample Rate: "
   ...                   f"{adc_configuration.sample_rate():0.2f} Hz")

   >>> run(write_read_adc_config("Test-STH"))
   Sample Rate: 9523.81 Hz

One option to decrease the sample rate from the default value of about 9524 Hz is to change the

- prescaler,
- acquisition time or
- oversampling rate.

For a

- formula on how to calculate the sample rate based on the values above and
- a list of suggested sample rates

please take a look at the section `“Sampling Rate”`_ of the general ICOtronic system documentation. The example code below shows you how to change the sample rate to about 4762 Hz.

.. doctest::

   >>> from asyncio import run
   >>> from icotronic.can import Connection
   >>> from icotronic.can.adc import ADCConfiguration

   >>> async def change_sample_rate(name):
   ...     async with Connection() as stu:
   ...         async with stu.connect_sensor_node(name) as sensor_node:
   ...             # Retrieve current reference voltage
   ...             adc_configuration = await sensor_node.get_adc_configuration()
   ...             reference_voltage = adc_configuration.reference_voltage
   ...             # Change sample rate
   ...             configuration = ADCConfiguration(
   ...                                 prescaler=2,
   ...                                 acquisition_time=8,
   ...                                 oversampling_rate=128,
   ...                                 reference_voltage=reference_voltage)
   ...             print("Set sample rate to "
   ...                   f"{configuration.sample_rate():0.2f} Hz")
   ...             await sensor_node.set_adc_configuration(**configuration)

   >>> run(change_sample_rate("Test-STH"))
   Set sample rate to 4761.90 Hz

.. _“Sampling Rate”: https://mytoolit.github.io/Documentation/#sampling-rate

Changing Channel Configuration
******************************

Some ICOtronic sensor nodes support changing the mapping from the three available measurement channels to different sensor channels. To get the current mapping you can use the coroutine :meth:`SensorNode.get_sensor_configuration`. The following code:

.. code-block::

   from asyncio import run
   from icotronic.can import Connection
   from icotronic.can.error import UnsupportedFeatureException

   async def read_sensor_configuration(identifier):
      async with Connection() as stu:
           async with stu.connect_sensor_node(identifier) as sensor_node:
               try:
                   print(await sensor_node.get_sensor_configuration())
               except UnsupportedFeatureException as error:
                   print(error)

   run(read_sensor_configuration("Test-STH"))

will either

- print the current sensor configuration e.g.::

    M1: S1, M2: S2, M3: S3

- or print an error message::

    Reading sensor configuration not supported

  if the sensor node does not support getting (or setting) the sensor configuration.

To set the sensor configuration you can use the coroutine :meth:`SensorNode.set_sensor_configuration`.

.. currentmodule:: icotronic.measurement.sensor

The method expects a :class:`SensorConfiguration` object as parameter. The following code:

.. code-block::

   from asyncio import run
   from icotronic.can import Connection, SensorConfiguration
   from icotronic.can.error import UnsupportedFeatureException

   async def set_sensor_configuration(identifier):
       async with Connection() as stu:
           async with stu.connect_sensor_node(identifier) as sensor_node:
               try:
                   config = await sensor_node.get_sensor_configuration()
                   print(f"Sensor configuration: {config}")
                   await sensor_node.set_sensor_configuration(
                       SensorConfiguration(first=2, second=4, third=1)
                   )
                   config = await sensor_node.get_sensor_configuration()
                   print(f"Updated sensor configuration: {config}")
               except UnsupportedFeatureException:
                   print("Sensor configuration not supported by device")

   run(set_sensor_configuration("Test-STH"))


will set the sensor configuration for

- the first measurement channel to the sensor channel `2`,
- the second measurement channel to the sensor channel `4`, and
- the third measurement channel to the sensor channel `1`.

For hardware that supports channel configuration the code should print the following text::

  Sensor configuration: M1: S1, M2: S2, M3: S3
  Updated sensor configuration: M1: S2, M2: S4, M3: S1
