# 🚀 Pylemura Deployment & Publishing Guide

This guide outlines the standard workflow for versioning, building, and publishing `pylemura` to PyPI.

---

## 📋 Prerequisites

Ensure you have the necessary tools installed:

```bash
pip install --upgrade hatch build twine
```

---

## 🛠️ Step 1: Versioning

Update the version number in **both** of the following files (they must always match):

1. **`pyproject.toml`**:
    ```toml
    [project]
    version = "1.2.0"
    ```
2. **`src/pylemura/__init__.py`**:
    ```python
    __version__ = "1.2.0"
    ```

> ⚠️ **Important:** Keeping these two in sync is critical. A mismatch will not block the build,
> but it will cause `import pylemura; print(pylemura.__version__)` to report the wrong version
> after installation.

---

## 🧪 Step 2: Verification

### Install the package in editable mode (required for tests to find the package)

```bash
pip install -e ".[dev]"
```

> ℹ️ Without this step, pytest will fail with `ModuleNotFoundError: No module named 'pylemura'`
> even though the source is present, because the package is not on `sys.path`.

### Run the test suite

```bash
pytest
```

### Verify the version is consistent across the codebase

```bash
python3 -c "import pylemura; print(pylemura.__version__)"
```

---

## 📦 Step 3: Building the Package

Use `hatch` or `build` to generate the distribution files. This will create `.whl` and `.tar.gz`
files in the `dist/` directory.

Clean any previous build artifacts first:

```bash
rm -rf dist/
```

### Option A: Using Hatch (Recommended)
```bash
hatch build
```

### Option B: Using the `build` module
```bash
python3 -m build
```

Verify the build integrity:
```bash
python3 -m twine check dist/*
```

Both artifacts should report `PASSED`.

---

## 🏷️ Step 4: Git Versioning

Tag the new version in your repository to keep track of releases:

```bash
git add pyproject.toml src/pylemura/__init__.py
git commit -m "chore: release v1.2.0"
git tag v1.2.0
git push origin main --tags
```

---

## 📤 Step 5: Publishing to PyPI

> ⚠️ **Use `twine` to publish, not `hatch publish`.**
> `hatch publish` does not read `~/.pypirc` and will interactively prompt for credentials
> even when the file is configured. `twine` respects `~/.pypirc` out of the box.

### 🗝️ Best Practice: Set up `~/.pypirc` (Recommended)

Create `~/.pypirc` once and all future `twine` uploads will authenticate automatically:

```ini
[pypi]
  username = __token__
  password = pypi-YOUR_API_TOKEN_HERE
```

> ⚠️ **Token format:** the password must start with exactly `pypi-` (one prefix). A common
> mistake when copy-pasting from the PyPI UI is ending up with `pypi-pypi-…`, which will cause
> authentication to fail silently. Double-check the prefix before saving.

Generate a token at: https://pypi.org/manage/account/token/

### Upload with Twine

```bash
python3 -m twine upload dist/*
```

### Option B: Automated with Environment Variables (for CI/CD)

```bash
export TWINE_USERNAME="__token__"
export TWINE_PASSWORD="pypi-YOUR_API_TOKEN_HERE"
python3 -m twine upload dist/*
```

### Option C: Inline credentials (one-off)

```bash
python3 -m twine upload -u __token__ -p pypi-YOUR_API_TOKEN_HERE dist/*
```

---

## 📝 Documenting the Release

Don't forget to update:
- `CHANGELOG.md`: List the user-facing changes.
- `RELEASE_NOTES.md`: Highlight critical fixes or new features for the latest release.

---

## 🧹 Cleanup

After a successful build and publish, clean the `dist/` folder:
```bash
rm -rf dist/
```

---

## 🔎 Troubleshooting

| Symptom | Cause | Fix |
|---|---|---|
| `ModuleNotFoundError: No module named 'pylemura'` during tests | Package not installed in current env | Run `pip install -e ".[dev]"` first |
| `hatch publish` keeps prompting for username | `hatch` ignores `~/.pypirc` | Use `python3 -m twine upload dist/*` instead |
| `403 Forbidden` on upload | Token has double `pypi-pypi-` prefix | Edit `~/.pypirc` and remove the extra `pypi-` |
| `400 File already exists` | Version already published on PyPI | Bump the version number and rebuild |
| `twine check dist/*` fails | Malformed README or metadata | Fix the reported issue before uploading |
