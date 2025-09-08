
# SED Project — v2 (First-run Setup GUI + config.json)

- On first run, a Setup window collects DB host/port/user/password/database.
- It tests connection, creates the DB if allowed, and writes `config.json`.
- App auto-initializes schema & default users (admin/admin123, alif/alif123).
- GUI includes CRUD scaffolds, search, CSV/PDF export, and logging.

Dev run:
    pip install -r requirements.txt
    python -m gui.start

Build .exe:
    run setup_windows.bat
