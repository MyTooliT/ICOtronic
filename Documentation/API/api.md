```{eval-rst}
.. currentmodule:: icotronic.can
```

# API

## Connection

```{eval-rst}
.. autoclass:: Connection
   :members: __aenter__
```

## Nodes

```{eval-rst}
.. autoclass:: STU
   :members:
```

```{eval-rst}
.. autoclass:: SensorNode
   :members:
```

```{eval-rst}
.. autoclass:: STH
   :members:
```

## Streaming

```{eval-rst}
.. currentmodule:: icotronic.can.streaming
```

```{eval-rst}
.. autoclass:: AsyncStreamBuffer
   :members: dataloss, reset_stats
```

```{eval-rst}
.. autoclass:: StreamingConfiguration
   :members:
```

```{eval-rst}
.. autoclass:: StreamingData
   :members:
```

## Measurement

```{eval-rst}
.. currentmodule:: icotronic.measurement
```

### Data

```{eval-rst}
.. autoclass:: DataPoint
   :members:
```

```{eval-rst}
.. autoclass:: ChannelData
   :members:
   :special-members: __add__
```

```{eval-rst}
.. autoclass:: MeasurementData
   :members:
```

```{eval-rst}
.. autoclass:: Conversion
   :members:
```

### Storage

```{eval-rst}
.. currentmodule:: icotronic.measurement.storage
```

```{eval-rst}
.. autoclass:: Storage
   :members:
```

```{eval-rst}
.. autoclass:: StorageData
   :members:
```

## ADC

```{eval-rst}
.. currentmodule:: icotronic.can.adc
```

```{eval-rst}
.. autoclass:: ADCConfiguration
   :members:
```

## Sensor Configuration

```{eval-rst}
.. currentmodule:: icotronic.can
```

```{eval-rst}
.. autoclass:: SensorConfiguration
   :members:
```
