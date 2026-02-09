# Publishing to PyPI

This document explains how to publish the `yuichan` package to PyPI.

## Prerequisites

1. Install required tools:
```bash
pip install build twine
```

2. Create a PyPI account at https://pypi.org/account/register/

3. Create an API token at https://pypi.org/manage/account/token/

## Building the Package

Build both wheel and source distributions:

```bash
python -m build
```

This creates files in the `dist/` directory:
- `yuichan-X.Y.Z-py3-none-any.whl` (wheel distribution)
- `yuichan-X.Y.Z.tar.gz` (source distribution)

## Uploading to PyPI

### Test PyPI (recommended for first upload)

```bash
python -m twine upload --repository testpypi dist/*
```

### Production PyPI

```bash
python -m twine upload dist/*
```

You'll be prompted for your API token (use `__token__` as the username and your token as the password).

## Note about Metadata Format

The package uses Metadata-Version 2.4 with modern license expression (`license = "MIT"`).
Some older versions of `twine check` may show warnings about "unrecognized or malformed field 'license-expression'".
This is a known compatibility issue and can be safely ignored - PyPI accepts these packages without issues.

## Version Management

To release a new version:

1. Update the version in `pyproject.toml`
2. Update the version in `yuichan/__init__.py`
3. Build and upload following the steps above

## Verification

After publishing, verify the package is installable:

```bash
pip install yuichan
python -c "import yuichan; print(yuichan.__version__)"
```
