"""Main entry point"""

__autodoc__ = False

import argparse
import logging as log

from docmd import GenMd


def parse_args():
    """Parse command line arguments."""

    parser = argparse.ArgumentParser(
        description="Generate markdown from a python module"
    )
    parser.add_argument(
        "module",
        help="Python import path for a module that contains code to document.",
    )
    parser.add_argument(
        "--debug", help="Debug output", action="store_true", default=False
    )
    parser.add_argument(
        "--out", "-o", help="Output folder", action="store", default=None
    )
    parser.add_argument(
        "--src",
        "-u",
        help="Source url, for generating source links",
        action="store",
        default=None,
    )
    return parser.parse_args()


def main():
    """Cli entry point."""
    log.basicConfig()
    args = parse_args()
    if args.debug:
        log.getLogger().setLevel(log.DEBUG)
    docmd = GenMd(output_dir=args.out, source_url=args.src)
    mod = docmd.import_module(args.module)
    docmd.module_gen(mod)


if __name__ == "__main__":
    main()
