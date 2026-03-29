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

Update the version number in the following files:

1.  **`pyproject.toml`**:
    ```toml
    [project]
    version = "1.1.0"
    ```
2.  **`src/pylemura/__init__.py`**:
    ```python
    __version__ = "1.1.0"
    ```

---

## 🧪 Step 2: Verification

Before building, always run the tests to ensure stability:

```bash
pytest
```

Verify that the version matches across the codebase:

```bash
python3.11 -c "import pylemura; print(pylemura.__version__)"
```

---

## 📦 Step 3: Building the Package

Use `hatch` or `build` to generate the distribution files. This will create `.whl` and `.tar.gz` files in the `dist/` directory.

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

---

## 🏷️ Step 4: Git Versioning

Tag the new version in your repository to keep track of releases:

```bash
git add pyproject.toml src/pylemura/__init__.py
git commit -m "chore: release v1.1.0"
git tag v1.1.0
git push origin main --tags
```

---

## 📤 Step 5: Publishing to PyPI

### Option A: Interactive Publish (Requires Token)
Run the following command. It will prompt you for your username (use `__token__`) and your API token as the password.

```bash
hatch publish
```

### Option B: Automated with Environment Variables (Recommended)
You can set these variables in your shell before running the publish command. This is common in CI/CD environments and for avoiding interactive password prompts.

```bash
export HATCH_INDEX_USER="__token__"
export HATCH_INDEX_AUTH="pypi-YOUR_API_TOKEN_HERE"
hatch publish
```

### Option C: Providing Token directly in command
If you have your API token, you can provide it directly:

```bash
hatch publish -u __token__ -p pypi-YOUR_API_TOKEN_HERE
```

### 🗝️ Best Practice: Setup `.pypirc` (Optional)
To avoid entering your token every time, create a `~/.pypirc` file:

```ini
[pypi]
  username = __token__
  password = pypi-YOUR_API_TOKEN_HERE
```

---

## 📝 Documenting the Release

Don't forget to update:
- `CHANGELOG.md`: List the user-facing changes.
- `RELEASE_NOTES.md`: Highlight critical fixes or new features for the latest version.

---

## 🧹 Cleanup
After a successful build and publish, you can clean the `dist/` folder:
```bash
rm -rf dist/
```
