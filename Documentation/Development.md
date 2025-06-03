# Development

## Install

You can use the instructions below, if you want to work on the code of the ICOtronic package, i.e. add additional features or fix bugs.

1. Clone [the repository](https://github.com/MyTooliT/ICOtronic) to a directory of your choice. You can either use the [command line tool `git`](https://git-scm.com/downloads):

   ```sh
   git clone https://github.com/MyTooliT/ICOtronic.git
   ```

   or one of the many available [graphical user interfaces for Git](https://git-scm.com/downloads/guis) to do that.

2. Install ICOtronic in “developer mode”

   1. Change your working directory to the (root) directory of the cloned repository
   2. Install ICOtronic:

      ```sh
      pip install -e .[dev,test]
      ```

      > **Notes:**
      >
      > - The command above will install the repository in “editable mode” (`-e`), meaning that a command such as `icon` will use the current code inside the repository.
      > - The command also installs
      >   - development (`dev`) and
      >   - test (`test`) dependencies

3. Install other required tools (for tests)

   - `hdf5`: For the command line tool `h5dump` (Linux/macOS). You can install hdf5 via [Homebrew](https://brew.sh):

     ```sh
     brew install hdf5
     ```

## Style

Please use the guidelines from [PEP 8](https://www.python.org/dev/peps/pep-0008/). For code formatting we currently use [Black](https://github.com/psf/black), which should format code according to PEP 8 by default.

To format the whole code base you can use the following command in the root of the repository:

```sh
black .
```

For development we recommend that you use a tool or plugin that reformats your code with Black every time you save. This way we can ensure that we use a consistent style for the whole code base.

## Tests

The following text describes some of the measures we should take to keep the software stable.

Please only push your changes to the `main` branch, if you think there are no new bugs or regressions. The `main` branch **should always contain a working version of the software**. Please **always run**

- the **automatic test** (`make run`) for **every supported OS** (Linux, macOS, Windows) and
- the **manual tests** on Windows

before you push to the `main` branch.

### Code Checks

#### Flake8

We check the code with [flake8](https://flake8.pycqa.org):

```sh
pip install flake8
```

Please use the following command in the root of the repository to make sure you did not add any code that introduces warnings:

```sh
flake8
```

#### mypy

To check the type hint in the code base we use the static code checker [mypy](https://mypy.readthedocs.io):

```sh
pip install mypy
```

Please use the following command in the root of the repository to check the code base for type problems:

```sh
mypy icotronic
```

#### Pylint

We currently use [Pylint](https://github.com/PyCQA/pylint) to check the code:

```sh
pylint .
```

### Automatic Tests

#### Requirements

Please install the [pytest testing module](https://docs.pytest.org):

```sh
pip install pytest
```

##### Usage

Please run the following command in the root of the repository:

```sh
pytest -v
```

and make sure that it reports no test failures.

### Manual Tests

#### STH Test

1. Call the command `test-sth` for a working STH
2. Wait for the command execution
3. Check that the command shows no error messages
4. Open the PDF report (`STH Test.pdf`) in the repository root and make sure that it includes the correct test data

#### STU Test {#development:section:stu-test}

1. Call the command `test-stu` (or `test-stu -k eeprom -k connection` when you want to skip the flash test) for a working STU
2. Wait for the command execution
3. Check that the command shows no error messages
4. Open the PDF report (`STU Test.pdf`) in the repository root and make sure that it includes the correct test data

##### Extended Tests {#development:section:extended-tests}

The text below specifies extended manual test that should be executed before we [release a new version of the ICOtronic package](#development:section:release). Please note that the tests assume that you more or less use the [default configuration values](https://github.com/MyTooliT/ICOtronic/blob/main/icotronic/config/config.yaml).

###### Check the Performance of the Library

1. Open your favorite terminal application and change your working directory to the root of the repository

2. Remove HDF5 files from the repository:

   ```sh
   rm *.hdf5
   ```

   > **Note:** You can ignore errors about “no matches for wildcard” on Linux and macOS. This message just tells you that there is no file with the extension `hdf5` in the current directory.

3. Check that no HDF5 files exist in the repository. The following command should not produce any output:

   ```sh
   ls *.hdf5
   ```

4. Give your test STH the [name](#tutorials:section:sth-renaming) “Test-STH”

5. Run the following command

   ```sh
   icon measure -t 300 -n Test-STH
   ```

   - The command should not print any **no error messages**.
   - The **data loss must be below 1 %**.

6. Check that the repo now contains a HDF5 (`*.hdf5`) file

   ```sh
   ls *.hdf5
   ```

7. Open the file in [HDFView](#measurement-data)

8. Check that the timestamp of the last value in the `acceleration` table has **approximately the value `30 000 000`** (all values above `29 900 000` should be fine).

### Combined Checks & Tests

While you need to execute some test for the ICOtronic package manually, other tests and checks can be automated.

> **Note:** For the text below we assume that you installed [`make`](<https://en.wikipedia.org/wiki/Make_(software)#Makefile>) on your machine.

To run all checks, the STH test and the STU test use the following `make` command:

```sh
make run
```

Afterwards make sure there were no (unexpected) errors in the output of the STH and STU test.

## Release {#development:section:release}

1.  Check that the [**CI jobs** for the `main` branch finished successfully](https://github.com/MyTooliT/ICOtronic/actions)
2.  Check that the most recent [“Read the Docs” build of the documentation ran successfully](https://app.readthedocs.org/projects/icotronic/)
3.  Check that the **checks and tests** run without any problems on **Linux**, **macOS** and **Windows**

    1. Set the value of `sth` → `status` in the [configuration](#changing-configuration-values) to `Epoxied`
    2. Execute the command:

       ```sh
       make run
       ```

       in the root of the repository

4.  Check that the **firmware flash** works in Windows

    - Execute `test-sth`

      1. once with `sth` → `status` set to `Epoxied`, and
      2. once set to `Bare PCB`

      in the [configuration](#changing-configuration-values). To make sure, that the STU flash test also works, please use both STU test commands described in the section [“STU Test”](#development:section:stu-test).

      If you follow the steps above you make sure that the **flash tests work** for both STU and STH, and there are **no unintentional consequences of (not) flashing the chip** before you run the other parts of the test suite.

5.  Execute the **[extended manual tests](#development:section:extended-tests)** in Windows and check that everything works as expected

6.  Create a new release [here](https://github.com/MyTooliT/ICOtronic/releases/new)

    1. Open the [release notes](Releases) for the latest version
    2. Replace links with a permanent version:

       For example instead of

       - `../../something.txt` use
       - `https://github.com/MyTooliT/ICOtronic/blob/REVISION/something.txt`,

       where `REVISION` is the latest version of the main branch (e.g. `8568893f` for version `1.0.5`)

    3. Commit your changes
    4. Copy the release notes
    5. Paste them into the main text of the release web page
    6. Decrease the header level of each section by two
    7. Remove the very first header
    8. Check that all links work correctly

7.  Change the [`__version__`](../icotronic/__init__.py) number inside the [`icotronic`](../icotronic) package
8.  Add a tag with the version number to the latest commit

    ```sh
    export icotronic_version="$(python -c '
    from icotronic import __version__
    print(__version__)')"
    git tag "$icotronic_version"
    ```

    **Note:** GitHub CI will publish a package based on this commit and upload it to [PyPi](https://pypi.org/project/icotronic/)

9.  Push the latest updates
10. Insert the version number (e.g. `1.0.5`) into the tag field
11. For the release title use “Version VERSION”, where `VERSION` specifies the version number (e.g. “Version 1.0.5”)
12. Click on “Publish Release”
13. Close the [milestone][] for the latest release number
14. Create a new [milestone][] for the next release
15. Go to [Read The Docs](https://readthedocs.org/projects/icotronic/) and enable the documentation for the latest release
    1. Click on “Versions”
    2. Click on the button “Activate” next to the version number of the latest release

[milestone]: https://github.com/MyTooliT/ICOtronic/milestones
