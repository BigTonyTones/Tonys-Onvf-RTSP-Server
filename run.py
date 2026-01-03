#!/usr/bin/env python3
"""
Tonys Onvif-RTSP Server with Web UI
Entry Point
"""
import sys
import os

# Ensure the current directory is in sys.path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.utils import check_and_install_requirements, init_logger

if __name__ == "__main__":
    # Initialize log capturing as early as possible
    init_logger()
    
    # Check dependencies first
    check_and_install_requirements()
    
    # Check system dependencies (Linux only)
    from app.utils import check_and_install_system_dependencies
    check_and_install_system_dependencies()
    
    # Now import main app
    from app.main import main
    main()
