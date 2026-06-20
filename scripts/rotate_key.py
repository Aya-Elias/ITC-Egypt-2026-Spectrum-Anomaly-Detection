"""Rotate a local development key."""

from __future__ import annotations

import argparse

from src.security.key_rotation import rotate_key


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("path", help="Key path to rotate")
    args = parser.parse_args()
    print(rotate_key(args.path))


if __name__ == "__main__":
    main()
