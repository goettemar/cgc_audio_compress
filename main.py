#!/usr/bin/env python3
"""CGC Audio Compress — Neural Audio Compression mit EnCodec."""

import sys


def main():
    # Import backends to trigger auto-registration
    import src.backends  # noqa: F401
    from src.gui.app import run_gui

    sys.exit(run_gui())


if __name__ == "__main__":
    main()
