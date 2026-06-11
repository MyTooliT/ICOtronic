"""Support code for acceleration measurements"""

# -- Imports ------------------------------------------------------------------

from collections.abc import Iterable
from math import log, sqrt
from statistics import pvariance

from icotronic.measurement.constants import ADC_MAX_VALUE

# -- Functions ----------------------------------------------------------------


def ratio_noise_max(values: Iterable[int]) -> float:
    """Calculate the ratio noise to max ADC amplitude in dB

    Args:

        values:
            An iterable object that stores a series of measured 16 bit raw ADC
            (acceleration) values

    Returns:

        The ratio of the average noise to the highest possible measured value

    """

    max_value = ADC_MAX_VALUE / 2
    standard_deviation = sqrt(pvariance(values))
    return 20 * log(standard_deviation / max_value, 10)


# -- Main ---------------------------------------------------------------------

if __name__ == "__main__":
    from doctest import testmod

    testmod()
