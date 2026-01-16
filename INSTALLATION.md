# Installation Guide

Complete setup instructions for running the JD Power PDF Downloader on a fresh machine.

## Prerequisites

- **Python 3.10 or higher** - [Download from python.org](https://www.python.org/downloads/)
- **Windows, macOS, or Linux**
- **~2GB disk space** (for Playwright browsers)
- **Internet connection**

## Step-by-Step Installation

### 1. Verify Python Installation

Open a terminal/command prompt and verify Python is installed:

```bash
python --version
# or
python3 --version
```

You should see `Python 3.10.x` or higher.

### 2. Clone or Download the Repository

```bash
git clone https://github.com/Pbein/JDPBookout.git
cd JDPBookout
```

Or download and extract the ZIP file from GitHub.

### 3. Create a Virtual Environment (Recommended)

**Windows:**
```bash
python -m venv .venv
.venv\Scripts\activate
```

**macOS/Linux:**
```bash
python3 -m venv .venv
source .venv/bin/activate
```

You'll see `(.venv)` in your terminal prompt when the virtual environment is active.

### 4. Install Python Dependencies

```bash
pip install -r requirements.txt
```

This installs:
- `playwright` - Browser automation
- `python-dotenv` - Environment variable management
- `requests` - HTTP library
- `PyPDF2` - PDF validation
- `keyring` - Secure credential storage
- `cryptography` - Encryption utilities

### 5. Install Playwright Browsers

Playwright needs to download the Chromium browser (~300MB):

```bash
python -m playwright install chromium
```

This downloads and installs the browser binaries. Only needs to be done once.

### 6. Configure Credentials (Optional for CLI Mode)

For command-line usage, create a `.env` file in the project root:

```bash
# .env file
JD_USER=your_username
JD_PASS=your_password
HEADLESS=false
BLOCK_RESOURCES=false
MAX_DOWNLOADS=10
CONCURRENT_CONTEXTS=5
```

**Note:** The GUI application has its own credential entry, so this is optional if you only use the GUI.

## Running the Application

### Desktop GUI (Easiest)

```bash
python main_gui.py
```

Enter your credentials in the GUI window and click Start.

### Command Line (Advanced)

```bash
python main_async.py
```

Requires `.env` file with credentials.

## Troubleshooting

### "python: command not found"

Try `python3` instead of `python`:
```bash
python3 --version
python3 -m venv .venv
```

### "playwright install failed"

Ensure you have sufficient disk space (~2GB) and internet connectivity. Try:
```bash
python -m playwright install --force chromium
```

### "Module not found" errors

Make sure your virtual environment is activated:
- You should see `(.venv)` in your terminal prompt
- Re-run: `pip install -r requirements.txt`

### GUI doesn't open

- Verify Python version is 3.10+
- Check that tkinter is installed (usually comes with Python)
- On Linux, you may need: `sudo apt-get install python3-tk`

### Permission errors on Windows

Run your terminal/command prompt as Administrator.

## Next Steps

1. Read `README.md` for feature overview
2. Read `PRODUCTION_GUIDE.md` for production run instructions
3. Read `docs/GUI_README.md` for GUI documentation
4. Run the application and start downloading PDFs!

## System Requirements

- **CPU:** Multi-core recommended for parallel processing
- **RAM:** 4GB minimum, 8GB+ recommended
- **Disk:** 2GB for browsers, additional space for PDFs
- **OS:** Windows 10+, macOS 10.15+, or modern Linux

## Support

For issues or questions:
1. Check the troubleshooting section above
2. Review documentation in the `docs/` folder
3. Check GitHub issues
