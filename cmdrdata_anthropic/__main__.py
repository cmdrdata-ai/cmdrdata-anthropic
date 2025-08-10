#!/usr/bin/env python3
"""
Main entry point for cmdrdata-anthropic CLI commands
"""
import sys

from .cli_setup import main as setup_main


def main():
    """Main CLI entry point"""
    if len(sys.argv) > 1 and sys.argv[1] == "setup":
        return setup_main()
    else:
        print("CmdrData Anthropic SDK")
        print("\nAvailable commands:")
        print("  python -m cmdrdata_anthropic setup    - Interactive setup wizard")
        print("\nFor more info: https://docs.cmdrdata.ai")
        return 0


if __name__ == "__main__":
    sys.exit(main())
