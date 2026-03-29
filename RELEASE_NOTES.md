# Release Notes - v1.1.0

## Python 3.11 Docker Compatibility Update

`pylemura` v1.1.0 is a focused stability release that fixes a Python 3.11 import-time crash affecting Docker deployments. Environments were correctly passing `LEMURA_API_KEY`, `LEMURA_BASE_URL`, and `LEMURA_MODEL`, but the package could still fail before startup completed because of a logger formatting bug.

---

### What Changed

- Fixed Python 3.11 compatibility in the default logger by removing f-string expressions that embedded backslash-based ANSI escape sequences.
- Preserved the existing logger output format while making imports safe across supported Python versions.
- Added a regression test to keep this startup path covered in CI.

---

### Why This Release Matters

- Dockerized applications using Python 3.11 can now import `pylemura` successfully.
- Backend startup failures caused by the logger no longer surface as misleading downstream 503s.
- The package behavior now matches the `requires-python = ">=3.11"` support claim in the project metadata.

---

### Upgrade

```bash
pip install --upgrade pylemura==1.1.0
```

If you were previously pinning `1.0.0` in a Docker image, rebuild after upgrading so the fixed package is installed into the container.

---

### Verification

This release was verified with:

- `pytest -q`
- `PYTHONPATH=src python3.11 -c "import pylemura; print(pylemura.__version__)"`

---

*Thank you to everyone who reported and helped narrow down the Docker startup issue.*
