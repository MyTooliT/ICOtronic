"""Support for storing additional information about test results"""

# -- Imports ------------------------------------------------------------------

from enum import auto, Enum
from unittest import TextTestResult

# -- Class --------------------------------------------------------------------


class ExtendedTestResult(TextTestResult):
    """Store data about the result of a test"""

    class TestInformation:
        """Store additional data of a test result

        We use this class to store test information in a PDF report.

        """

        class Status(Enum):
            """Store the status of a test"""

            SUCCESS = auto()
            FAILURE = auto()
            ERROR = auto()
            SKIPPED = auto()

        def __init__(self):

            self.status = type(self).Status.SUCCESS
            self.message = ""

        def set_error(self, message):
            """Set the status of the test to error

            Args:

                message:
                    Specifies the error message

            """

            self.status = type(self).Status.ERROR
            self.message = message

        def set_failure(self, message):
            """Set the status of the test to failure

            Args:

                message:
                    Specifies the failure message

            """

            self.status = type(self).Status.FAILURE
            self.message = message

        def set_success(self):
            """Set the status of the test to success"""

            self.status = type(self).Status.SUCCESS
            self.message = ""

        def set_skipped(self):
            """Set the status of the test to skipped"""

            self.status = type(self).Status.SKIPPED

        def error(self):
            """Check if there was an error

            Returns:

                ``True`` if there was an error, ``False`` otherwise

            """

            return self.status == type(self).Status.ERROR

        def failure(self):
            """Check if there test failed

            Returns:

                ``True`` if the test failed, ``False`` otherwise

            """

            return self.status == type(self).Status.FAILURE

    def __init__(self, *arguments, **keyword_arguments):

        super().__init__(*arguments, **keyword_arguments)

        self.last_test = ExtendedTestResult.TestInformation()

    def addFailure(self, test, err):
        """Add information about the latest failure

        Args:

            test:
                The test case that produced the failure

            err:
                A tuple of the form returned by ``sys.exc_info()``:
                ``(type, value, traceback)``

        """

        super().addFailure(test, err)

        # Store message for latest failure
        failure_message = str(err[1])
        # Only store custom message added to assertion, since it should be more
        # readable for a person. If there was no custom message, then the
        # object stores the auto-generated message.
        custom_failure_message = failure_message.rsplit(" : ", maxsplit=1)[-1]

        self.last_test.set_failure(custom_failure_message)

    def addError(self, test, err):
        """Add information about the latest error

        This should usually not happen unless there are problems with the
        connection or the syntax of the current code base.

        Args:

            test:
                The test case that produced the error

            err:
                A tuple of the form returned by ``sys.exc_info()``:
                ``(type, value, traceback)``

        """

        super().addError(test, err)

        self.last_test.set_error(err[1])

    def addSuccess(self, test):
        """Add information about latest successful test

        Args:

            test:
                The successful test

        """

        super().addSuccess(test)

        self.last_test.set_success()

    def addSkip(self, test, reason):
        """Add information about latest skipped test

        Args:

            test:
                The skipped test

            reason:
                The reason why the test was skipped

        """

        super().addSkip(test, reason)

        self.last_test.set_skipped()
