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
    
    # Run main application
    try:
        exit_code = main()
        # If main() returns 5, we restart. Otherwise, we exit.
        if exit_code != 5:
            sys.exit(exit_code if exit_code is not None else 0)
        
        print("\n" + "="*60)
        print("RESTARTING SERVER (Applying Updates)...")
        print("="*60 + "\n")
        
        import time
        time.sleep(1) # Allow sockets a brief moment to close
        
        # Use os.execv to completely replace the Python process.
        # This ensures fresh module imports from disk and utterly destroys 
        # any lingering daemon threads from the previous run.
        os.execv(sys.executable, [sys.executable] + sys.argv)
        
    except KeyboardInterrupt:
        print("\nManual shutdown requested. Goodbye!")
        sys.exit(0)
    except Exception as e:
        print(f"\nFatal error: {e}")
        sys.exit(1)
