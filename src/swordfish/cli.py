"""
Module that contains the command line app.
"""
import sys
import argparse
import logging
import signal
from pathlib import Path
import pkg_resources  # part of setuptools

from rich.logging import RichHandler

from swordfish.monitor import monitor
from swordfish.utils import get_device, print_args
DEFAULT_FREQ = 60

version = pkg_resources.require("swordfish")[0].version
parser = argparse.ArgumentParser(description="swordfish app")

subparsers = parser.add_subparsers(dest='subparser_name', title='subcommands', help='additional help')

parser_breakpoints = subparsers.add_parser("breakpoints", help="Connect to minoTour,"
                                                               " use adaptive sampling to try to narrow down"
                                                               " putative CNVs.")
parser_breakpoints.set_defaults(func=monitor)
parser_balance = subparsers.add_parser("balance", help="Connect to minoTour and configure a balancing experiment.")
parser_balance.set_defaults(func=monitor)
parser.add_argument(
    "--mt-key", default=None, help="Access token for MinoTour", required=True
)
parser.add_argument(
    "--mk-host", default="localhost", help="Address for connecting to MinKNOW",
)
parser.add_argument(
    "--mk-port", default=9501, help="Port for connecting to MinKNOW",
)
parser.add_argument(
    "--use_tls", action="store_true", help="Use TLS for connecting to MinKNOW",
)
parser.add_argument(
    "-f",
    "--freq",
    default=DEFAULT_FREQ,
    type=int,
    help=f"Frequency, in seconds, to poll MinoTour, default: {DEFAULT_FREQ}. Cannot be less than {DEFAULT_FREQ}",
)
parser.add_argument(
    "--mt-host",
    default="localhost",
    help="Address for connecting to minoTour. Default - localhost",
)
parser.add_argument(
    "--mt-port",
    default="8100",
    type=int,
    help="Port for connecting to minotour. Default - 8100.",
)
parser.add_argument("--device", type=str, required=True, help="MinION device or GridION position")
parser.add_argument("--toml", type=Path, required=True, help="Path to TOML file that will be updated")
parser.add_argument(
    "--no-minknow",
    default=False,
    help="For testing - skips minknow validation. Not recommended."
    " Will be deprecated in favour of a mock minknow server for testing.",
    action="store_true",
)
parser_balance.add_argument(
    "--threshold",
    default=50,
    type=int,
    help="Threshold X coverage to start unblocking amplicons on a barcode. Default 50. Cannot be less than 20.",
)
parser_breakpoints.add_argument(
    "--min-diff",
    default=4,
    type=int,
    help="Ruptures parameter, for calculating potential breakpoints"
)
parser_breakpoints.add_argument(
    "--exp-ploidy",
    default=2,
    type=int,
    help="Expected ploidy of the species being sequenced. Default 100."
)
parser_breakpoints.add_argument(
    "--reads-bin",
    default=100,
    type=int,
    help="Expected estimated number of reads to be in a bin. Default 100."
)
parser_breakpoints.add_argument(
    "--behave-toml",
    required=True,
    default=Path("chunkalicious.toml"),
    type=Path,
    dest="b_toml",
    help="Path to toml file containing desired behaviour for barcodes on mapping matches, "
         "and min and max allowed chunk sizes. An example can be found in chunkalicious.toml "
)


def signal_handler(signal, frame):
    print("Caught Ctrl+C, exiting.", file=sys.stderr)
    sys.exit(0)


signal.signal(signal.SIGINT, signal_handler)


def main(args=None):
    args = parser.parse_args(args=args)
    print(args)
    formatter = logging.Formatter(
        "[%(asctime)s] %(levelname)s - %(message)s", "%Y-%m-%d %H:%M:%S"
    )
    handler = RichHandler()
    handler.setFormatter(formatter)

    logger = logging.getLogger(__name__)
    logger.setLevel(logging.INFO)
    logger.addHandler(handler)
    logger.info(f"Welcome to Swordfish version {version}. How may we help you today?")
    print_args(args, logger=logger, exclude={"mt_key"})
    # Check TOML file
    # Call monitor module
    if args.subparser_name:
        args.func(args, version)
    else:
        parser.parse_args("--help")
