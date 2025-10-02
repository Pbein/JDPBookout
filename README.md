## JD Power Automated PDF Downloader (Playwright + Python)

This project will automate downloading vehicle PDFs from JD Power Values Online using a CSV of Reference Numbers. It is scaffolded only; logic will be implemented later.

### Overview
- CSV-driven automation:
  - Login, accept license if prompted
  - Go to inventory, clear filters, export CSV
  - Read Reference Numbers from CSV
  - For each number: filter grid, open vehicle (book icon), print/email to capture PDF
  - Save as `<ReferenceNumber>.pdf` in today's folder, mark as done, resume safely

### Setup
1. Install Python 3.10+ and create a virtual environment.
   - Windows (cmd):
     ```bash
     py -3.10 -m venv .venv && .venv\Scripts\activate
     ```
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Install Playwright browsers (Chromium):
   ```bash
   python -m playwright install chromium
   ```
4. Create a `.env` from `.env.example` and set credentials:
   ```
   JD_USER=your_username
   JD_PASS=your_password
   HEADLESS=false
   ```

### Config
- Defined in `jdp_scraper/config.py` (placeholders now):
  - Base URLs (login, inventory, vehicle)
  - Timeouts and retry counts
  - `HEADLESS` flag from env
  - Download directory naming (e.g., `YYYY-MM-DD`)

### Selectors
- Defined in `jdp_scraper/selectors.py` (placeholders):
  - Login: username, password, submit
  - License: accept button
  - Inventory: grid table, reference input, book icon in row, export CSV, clear filters
  - Vehicle: print/email button, indicator when ready

### Modules (scaffold only)
- `auth.py`: login flow placeholder
- `license_page.py`: license acceptance placeholder
- `inventory.py`: inventory navigation, export, filtering placeholders
- `vehicle.py`: vehicle page, print/download placeholders
- `downloads.py`: folder management and done-list cache placeholders
- `orchestration.py`: high-level flow placeholder
- `waits.py`, `logging_utils.py`, `config.py`, `selectors.py`: support scaffolding

### Running
- Not implemented yet. `main.py` is a stub that will later call orchestration.

