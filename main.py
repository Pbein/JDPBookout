"""Entrypoint for JD Power PDF Downloader.

This script launches the orchestration flow to automate PDF downloads.
"""
from jdp_scraper.orchestration import run

if __name__ == "__main__":
    run()

