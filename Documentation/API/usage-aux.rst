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
