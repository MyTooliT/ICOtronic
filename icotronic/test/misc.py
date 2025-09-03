"""Misc functions related to testing"""

# -- Imports ------------------------------------------------------------------

from pytest import MarkDecorator

# -- Functions ----------------------------------------------------------------

# pylint: disable=import-outside-toplevel


def skip_hardware_tests_ci() -> MarkDecorator | None:
    """Skip hardware dependent test on CI sytem

    Returns:

        - ``None`` if pytest is not installed or
        - a decorator that skips tests if the environment variable ``CI`` is
          defined

    """

    try:
        from pytest import mark
        from os import environ

        return mark.skipif(
            "CI" in environ, reason="requires ICOtronic hardware"
        )
    except ModuleNotFoundError:
        return None


# pylint: enable=import-outside-toplevel
