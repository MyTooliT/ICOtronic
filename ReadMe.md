[![GitHub Workflow Documentation](https://img.shields.io/github/actions/workflow/status/mytoolit/ICOtronic/documentation.yaml?branch=main&label=Documentation)](https://mytoolit.github.io/ICOtronic/) [![API Documentation](https://img.shields.io/readthedocs/icotronic?label=API%20Documentation)](https://icotronic.readthedocs.io/en/stable/) [![GitHub Workflow Tests](https://img.shields.io/github/actions/workflow/status/mytoolit/ICOtronic/tests.yaml?branch=main&label=Tests)](https://github.com/MyTooliT/ICOtronic/actions/workflows/tests.yaml)

# ICOtronic

This repository contains data collection and test software for the [ICOtronic system](https://www.mytoolit.com/ICOtronic/). For more information, please take a look [at the online documentation](https://mytoolit.github.io/ICOtronic/).

## Documentation

While you should be able to read the [various Markdown files of the documentation](Documentation) separately, we recommend you read the [bookdown](https://bookdown.org) manual instead. We provide a prebuilt version of the documentation [**here**](https://mytoolit.github.io/ICOtronic/).

You can also download the documentation [under the GitHub Actions tab](https://github.com/MyTooliT/ICOtronic/actions/workflows/documentation.yaml) (just select the latest run and click on the link “ICOtronic Manual”).

### Build

If you want to build the documentation yourself, you need the following software:

- [R](https://www.r-project.org),
- [bookdown](https://bookdown.org),
- [make](<https://en.wikipedia.org/wiki/Make_(software)>), and
- (optionally for the PDF version of the manual) the [TinyTeX R package](https://yihui.org/tinytex/).

After you installed the required software you can build the

- HTML (`make html`),
- EPUB (`make epub`), and
- PDF (`make pdf`)

version of the documentation. The output will be stored in the folder `Bookdown` in the root of the repository. If you want to build all versions of the documentation, just use the command

```sh
make doc
```

in the repo root.
