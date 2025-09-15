###########################
ICOtronic API Documentation
###########################

*******
Purpose
*******

The ICOtronic package contains

- a set of command line tools (`icon`_, `test-sth`_, …) and
- a `Python library`_

.. |icon| replace:: ``icon``
.. _icon: https://mytoolit.github.io/ICOtronic/#icon-cli-tool
.. |test-sth| replace:: ``test-sth``
.. _test-sth: https://mytoolit.github.io/ICOtronic/#tutorials:section:production-tests
.. _Python library: https://pypi.org/project/icotronic/

to

- control the `ICOtronic system`_,
- acquire data, and
- test ICOtronic hardware (e.g. stationary transceiver units and sensory tool holders).

This documentation **describes the Python library API** (i.e. how to create programs that use the `ICOtronic system`_). If you want more general information on the command line tools and the `ICOtronic system`_ itself we recommend that you check out the `general ICOtronic documentation`_.

.. _ICOtronic system: https://www.mytoolit.com/icotronic/

.. _general ICOtronic documentation: https://mytoolit.github.io/ICOtronic/

.. toctree::
   :maxdepth: 2
   :caption: Contents:

   usage-connection
   usage-streaming
   usage-aux
   api
   examples
