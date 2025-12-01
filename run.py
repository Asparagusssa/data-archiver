#!/usr/bin/env python3
"""
Скрипт для запуска архиватора
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.main import main

if __name__ == "__main__":
    main()