# Troubleshooting

## Import Errors

If [`icon`](#icon-cli-tool) fails with an error message that looks similar to the following text on Windows:

```
Traceback (most recent call last):
…
    from numexpr.interpreter import MAX_THREADS, use_vml, __BLOCK_SIZE1__
ImportError: DLL load failed while importing interpreter: The specified module could not be found.

DLL load failed while importing interpreter: The specified module could not be found.
```

then you probably need to install the [“Microsoft Visual C++ Redistributable package” ](https://docs.microsoft.com/en-us/cpp/windows/latest-supported-vc-redist). You can download the latest version

- for the `x64` architecture, i.e. for AMD and Intel CPUs, [here](https://aka.ms/vs/17/release/vc_redist.x64.exe) and
- for the `ARM64` architecture [here](https://aka.ms/vs/17/release/vc_redist.arm64.exe).

## Insufficient Rights

**If you do not have sufficient rights** to install the package you can also try to install the package in the user package folder:

```sh
pip install --user icotronic
```

## Unable to Locate HDF5 {#introduction:section:unable-to-locate-hdf5}

The installation of the ICOtronic package might fail with an error message that looks like this:

```
… implicit declaration of function 'H5close'
```

If you uses [Homebrew][] on an Apple Silicon based Mac you can use the [following commands to fix this problem](https://stackoverflow.com/questions/73029883/could-not-find-hdf5-installation-for-pytables-on-m1-mac):

[Homebrew]: https://brew.sh

```sh
pip uninstall -y tables
brew install hdf5 c-blosc2 lzo bzip2
export BLOSC_DIR=/opt/homebrew/opt/c-blosc
export BZIP2_DIR=/opt/homebrew/opt/bzip2
export LZO_DIR=/opt/homebrew/opt/lzo
export HDF5_DIR=/opt/homebrew/opt/hdf5
pip install --no-cache-dir tables
```

## HDF5 Library Not Loaded

If [`icon`](#icon-cli-tool) fails with an error message that looks like this on macOS:

> `Library not loaded: /opt/homebrew/opt/hdf5/lib/libhdf5.….dylib`

In that case you might have installed an outdated cached version of [PyTables](https://www.pytables.org). You should be able to fix this issue using the same steps as described [above ](#introduction:section:unable-to-locate-hdf5).

## Unable to open OpenBLAS library

If [`icon`](#icon-cli-tool) fails with the error message:

> ImportError: libopenblas.so.0: cannot open shared object file: No such file or directory

on [Raspbian](http://www.raspbian.org) (or some other GNU/Linux version based on Debian) then you probably need to install the [OpenBLAS](http://www.openblas.net) library:

```sh
sudo apt-get install libopenblas-dev
```

## Unknown Command

If `pip install` prints **warnings about the path** that look like this:

> The script … is installed in `'…\Scripts'` which is not on PATH.

then please add the text between the single quotes (without the quotes) to your [PATH environment variable](<https://en.wikipedia.org/wiki/PATH_(variable)>). Here `…\Scripts` is just a placeholder. Please use the value that `pip install` prints on your machine. If

- you used the [installer from the Python website](https://www.python.org/downloads) (and checked “Add Python to PATH”) or
- you used [winget](https://docs.microsoft.com/en-us/windows/package-manager/winget/)

to install Python, then the warning above should not appear. On the other hand, the **Python version from the [Microsoft Store](https://www.microsoft.com/en-us/store/apps/windows) might not add the `Scripts` directory** to your path.
