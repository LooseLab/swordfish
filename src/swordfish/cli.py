"""
Module that contains the command line app.
"""
import sys
import argparse
import logging
import signal
from pathlib import Path
import pkg_resources  # part of setuptools

version = pkg_resources.require("swordfish")[0].version

from swordfish.utils import get_device, print_args
from swordfish.monitor import monitor


DEFAULT_FREQ = 60

parser = argparse.ArgumentParser(description="swordfish app")
parser.add_argument("device", type=str, help="MinION device or GridION position")
parser.add_argument("toml", type=Path, help="Path to TOML file that will be updated")
parser.add_argument(
    "--mt-key", default=None, help="Access token for MinoTour",
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
    help="Port for connecting to minotour. Default - 8100.",
)
parser.add_argument(
    "--no-minknow",
    default=False,
    help="For testing - skips minknow validation. Not recommended."
    " Will be deprecated in favour of a mock minknow server for testing.",
    action="store_true",
)
parser.add_argument(
    "-t",
    "--threshold",
    default=50,
    type=int,
    help="Threshold X coverage to start unblocking amplicons on a barcode. Default 50. Cannot be less than 20.",
)


def signal_handler(signal, frame):
    print(" Caught Ctrl+C, exiting.", file=sys.stderr)
    sys.exit(0)


signal.signal(signal.SIGINT, signal_handler)


def main(args=None):
    args = parser.parse_args(args=args)

    formatter = logging.Formatter(
        "[%(asctime)s] %(levelname)s - %(message)s", "%Y-%m-%d %H:%M:%S"
    )
    handler = logging.StreamHandler()
    handler.setFormatter(formatter)

    logger = logging.getLogger(__name__)
    logger.setLevel(logging.INFO)
    logger.addHandler(handler)

    logger.info(f"Welcome to Swordfish version {version}. How may we help you today?")
    print_args(args, logger=logger, exclude={"mt_key"})
    # Check TOML file
    if not args.toml.is_file():
        sys.exit(f"TOML file not found at {args.toml}")

    # Check MinoTour key is provided
    if args.mt_key is None:
        sys.exit("No MinoTour access token provided")

    # Check MinoTour polling frequency
    if args.freq < DEFAULT_FREQ:
        sys.exit(f"-f/--freq cannot be lower than {DEFAULT_FREQ}")

    if args.threshold > 1000:
        sys.exit("-t/--threshold cannot be more than 1000")

    device = None
    # Check device
    if not args.no_minknow:
        try:
            device = get_device(
                args.device, host=args.mk_host, port=args.mk_port, use_tls=args.use_tls,
            )
        except (RuntimeError, Exception) as e:
            msg = e.message if hasattr(e, "message") else str(e)
            sys.exit(msg)

    # Call monitor module
    monitor(
        args.toml,
        device,
        args.mt_key,
        args.freq,
        args.mt_host,
        args.mt_port,
        args.threshold,
        args.no_minknow,
        sf_version=version,
    )
