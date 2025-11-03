# Development

## Install

You can use the instructions below, if you want to work on the code of the ICOtronic package, i.e. add additional features or fix bugs.

1. Clone [the repository](https://github.com/MyTooliT/ICOtronic) to a directory of your choice. You can either use the [command line tool `git`](https://git-scm.com/downloads):

   ```sh
   git clone https://github.com/MyTooliT/ICOtronic.git
   ```

   or one of the many available [graphical user interfaces for Git](https://git-scm.com/downloads/guis) to do that.

2. Install ICOtronic with [uv](https://docs.astral.sh/uv)
   1. Change your working directory to the (root) directory of the cloned repository
   2. Install ICOtronic:

      ```sh
      uv venv --allow-existing
      uv sync --all-extras
      ```

      > **Notes:**
      >
      > - The command above will install the package in a virtual environment.
      > - You need to prefix commands, such as `icon` with the command `uv run` (e.g. `uv run icon`) to execute it in this virtual environment.
      > - Using `uv run` will only work in the root folder of the repository (that contains `pyproject.toml`).

3. Install other required tools (for tests)
   - `hdf5`: For the command line tool `h5dump` (Linux/macOS). You can install hdf5 via [Homebrew](https://brew.sh):

     ```sh
     brew install hdf5
     ```

## Style

Please use the guidelines from [PEP 8](https://www.python.org/dev/peps/pep-0008/). For code formatting we currently use [Black](https://github.com/psf/black), which should format code according to PEP 8 by default.

To format the whole code base you can use the following command in the root of the repository:

```sh
poetry black .
```

For development we recommend that you use a tool or plugin that reformats your code with Black every time you save. This way we can ensure that we use a consistent style for the whole code base.

## Tests

The following text describes some of the measures we should take to keep the software stable:

- Please only push your changes to the `main` branch, if you think there are no new bugs or regressions. The `main` branch **should always contain a working version of the software**.

- Please **always run** the **automatic test** (`make run`) for **every supported OS** (Linux, macOS, Windows) before you push to the `main` branch.

### Code Checks

#### Flake8

We check the code with [Flake8](https://flake8.pycqa.org). Please use the following command in the root of the repository to make sure you did not add any code that introduces warnings:

```sh
uv run flake8
```

#### mypy

To check the type hint in the code base we use the static code checker [mypy](https://mypy.readthedocs.io). Please use the following command in the root of the repository to check the code base for type problems:

```sh
uv run mypy icotronic
```

#### Pylint

We currently use [Pylint](https://github.com/PyCQA/pylint) to check the code:

```sh
uv run pylint .
```

### Automatic Tests

##### Usage

Please run the following command in the root of the repository:

```sh
uv run pytest -v
```

and make sure that it reports no test failures.

### Manual Tests

The text below specifies the manual test that should be executed before we [release a new version of the ICOtronic package](#development:section:release). Please note that the tests assume that you more or less use the [default configuration values](https://github.com/MyTooliT/ICOtronic/blob/main/icotronic/config/config.yaml).

##### Check the Performance of the Library

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
   uv run icon measure -t 300 -n Test-STH
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

## Release {#development:section:release}

1. Check that the [**CI jobs** for the `main` branch finished successfully](https://github.com/MyTooliT/ICOtronic/actions)
2. Check that the most recent [“Read the Docs” build of the documentation ran successfully](https://app.readthedocs.org/projects/icotronic/)
3. Check that the **checks and tests** run without any problems on **Linux**, **macOS** and **Windows**. To do that execute them command:

   ```sh
   make run
   ```

   in the root of the repository

4. Execute the **[manual tests](#manual-tests)** in Windows and check that everything works as expected.

5. Update the release notes:
   1. Open the [release notes](Releases) for the latest version
   2. Replace links with a permanent version:

      For example instead of
      - `../../something.txt` use
      - `https://github.com/MyTooliT/ICOtronic/blob/REVISION/something.txt`,

      where `REVISION` is the latest version of the main branch (e.g. `8568893f` for version `1.0.5`)

   3. Commit your changes

6. Change the version number and commit your changes (please replace `<VERSION>` with the version number e.g. `1.0.5`):

   ```sh
   uv version <VERSION>
   export icotronic_version="$(uv version --short)"
   git commit -a -m "Release: Release version $icotronic_version"
   git tag "$icotronic_version"
   git push && git push --tags
   ```

   **Note:** [GitHub Actions](https://github.com/MyTooliT/ICOtronic/actions) will publish a package based on the tagged commit and upload it to [PyPi](https://pypi.org/project/icotronic/).

7. Create a new release [here](https://github.com/MyTooliT/ICOtronic/releases/new)
   1. Insert the version number (e.g. `1.0.5`) into the tag field
   2. For the release title use “Version <VERSION>”, where `<VERSION>` specifies the version number (e.g. “Version 1.0.5”)
   3. Paste the release notes for the lastest release into the main text field
   4. Click on “Publish Release”

   **Note:** Alternatively you can also use the [`gh`](https://cli.github.com) command:

   ```sh
   gh release create
   ```

   to create the release notes.

8. Close the [milestone][] for the latest release number

[milestone]: https://github.com/MyTooliT/ICOtronic/milestones
