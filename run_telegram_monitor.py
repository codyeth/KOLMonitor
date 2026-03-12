"""
Telegram Monitor — Standalone Runner
Chạy: python run_telegram_monitor.py

Script này độc lập với X monitor runner.
"""
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from monitors.telegram_monitor import main

if __name__ == "__main__":
    main()
