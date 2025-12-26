#!/usr/bin/env python3
"""
Tonys Onvif-RTSP Server with Web UI
Entry Point

This script provides the main entry point for the ONVIF-RTSP server.
It handles command line arguments, dependency checking, and server startup.

Usage:
    python run.py [OPTIONS]

Options:
    --port PORT         Web UI port (default: 5552, env: ONVIF_WEB_PORT)
    --rtsp-port PORT    RTSP server port (default: 8554, env: ONVIF_RTSP_PORT)
    --no-browser        Don't open browser automatically (env: ONVIF_NO_BROWSER)
    --config FILE       Path to custom config file (env: ONVIF_CONFIG_FILE)
    --debug             Enable debug mode (env: ONVIF_DEBUG)
    --help, -h          Show help message

Environment Variables:
    ONVIF_WEB_PORT      Web UI port (default: 5552)
    ONVIF_RTSP_PORT     RTSP server port (default: 8554)
    ONVIF_CONFIG_FILE   Path to camera configuration file
    ONVIF_DEBUG         Enable debug mode (true/false)
    ONVIF_NO_BROWSER    Disable auto-opening browser (true/false)
"""

import sys
import os
import argparse

# Ensure the current directory is in sys.path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Import logging configuration first
from app.logging_config import get_logger, setup_logging

logger = get_logger(__name__)


def parse_arguments():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        prog="run.py",
        description="Tonys Onvif-RTSP Server - Virtual ONVIF camera server with web UI",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python run.py                         # Start with defaults
  python run.py --port 8080             # Use custom web UI port
  python run.py --no-browser            # Don't open browser
  python run.py --debug                 # Enable debug mode
  python run.py --config my_config.json # Use custom config file

For more information, visit the project repository.
        """
    )

    parser.add_argument(
        "--port",
        type=int,
        default=None,
        metavar="PORT",
        help="Web UI port (default: 5552)"
    )

    parser.add_argument(
        "--rtsp-port",
        type=int,
        default=None,
        metavar="PORT",
        help="RTSP server port (default: 8554)"
    )

    parser.add_argument(
        "--no-browser",
        action="store_true",
        help="Don't open browser automatically on startup"
    )

    parser.add_argument(
        "--config",
        type=str,
        default=None,
        metavar="FILE",
        help="Path to custom camera configuration file"
    )

    parser.add_argument(
        "--debug",
        action="store_true",
        help="Enable debug mode with verbose output"
    )

    parser.add_argument(
        "--version",
        action="version",
        version="Tonys Onvif-RTSP Server v4.0"
    )

    return parser.parse_args()


def validate_arguments(args):
    """Validate command line arguments."""
    errors = []

    # Validate port numbers
    if args.port is not None:
        if args.port < 1 or args.port > 65535:
            errors.append(f"Invalid web UI port: {args.port} (must be 1-65535)")
        if args.port < 1024:
            logger.warning("Port %d is a privileged port and may require elevated permissions", args.port)

    if args.rtsp_port is not None:
        if args.rtsp_port < 1 or args.rtsp_port > 65535:
            errors.append(f"Invalid RTSP port: {args.rtsp_port} (must be 1-65535)")
        if args.rtsp_port < 1024:
            logger.warning("RTSP port %d is a privileged port and may require elevated permissions", args.rtsp_port)

    # Validate config file
    if args.config is not None:
        if not os.path.exists(args.config):
            errors.append(f"Config file not found: {args.config}")
        elif not os.path.isfile(args.config):
            errors.append(f"Config path is not a file: {args.config}")

    # Check for port conflicts
    if args.port is not None and args.rtsp_port is not None:
        if args.port == args.rtsp_port:
            errors.append("Web UI port and RTSP port cannot be the same")

    if errors:
        logger.error("Configuration Errors:")
        for error in errors:
            logger.error("  - %s", error)
        logger.info("Use --help for usage information")
        sys.exit(1)


def setup_debug_mode():
    """Configure debug mode settings."""
    os.environ['LOG_LEVEL'] = 'DEBUG'
    setup_logging()  # Re-setup with new level
    logger.debug("Debug mode enabled - verbose logging active")


def main():
    """Main entry point."""
    # Import config values (these read from env vars with defaults)
    from app.config import (
        WEB_UI_PORT, MEDIAMTX_PORT, CONFIG_FILE,
        DEBUG_MODE, NO_BROWSER
    )

    # Parse command line arguments
    args = parse_arguments()

    # Validate arguments
    validate_arguments(args)

    # Enable debug mode if requested (CLI or env var)
    if args.debug or DEBUG_MODE:
        setup_debug_mode()

    # Check dependencies first
    from app.utils import check_and_install_requirements
    check_and_install_requirements()

    # Check system dependencies (Linux only)
    from app.utils import check_and_install_system_dependencies
    check_and_install_system_dependencies()

    # Now import and run the main app with arguments
    from app.main import run_server

    # Build options dictionary
    # Priority: CLI args > env vars > defaults
    options = {
        'port': args.port if args.port is not None else WEB_UI_PORT,
        'rtsp_port': args.rtsp_port if args.rtsp_port is not None else MEDIAMTX_PORT,
        'open_browser': not (args.no_browser or NO_BROWSER),
        'config_file': args.config if args.config is not None else CONFIG_FILE,
        'debug': args.debug or DEBUG_MODE
    }

    # Start the server
    run_server(options)


if __name__ == "__main__":
    main()
