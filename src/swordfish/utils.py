"""
Utilities for speaking with MinoTour
"""
import time
from pathlib import Path
from pprint import pformat

import toml
from grpc import RpcError
from minknow_api.manager import Manager
import logging
import sys

from rich.logging import RichHandler
from swordfish.endpoints import EndPoint

handler = RichHandler()
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
logger.addHandler(handler)


def print_args(args, logger=None, exclude=None):
    """Print and format all arguments from the command line"""
    if exclude is None:
        exclude = []
    dirs = dir(args)
    for attr in dirs:
        if attr[0] != "_" and attr not in exclude and attr.lower() == attr:
            record = "{a}={b}".format(a=attr, b=getattr(args, attr))
            if logger is not None:
                logger.info(record)
            else:
                print(record)


def get_device(device, **kws):
    """Get gRPC device"""
    manager = Manager(**kws)
    for position in manager.flow_cell_positions():
        if position.name == device:
            return position
    raise RuntimeError(f"Could not find device {device}")


def validate_mt_connection(mt_api, version):
    """
    Validate swordfishes connection to minoTour
    Parameters
    ----------
    mt_api: swordfish.minotour_api.MinotourAPI
        Convience class for querying minoTour
    version: str
        The version of the swordfish client being used.
    Returns
    -------
    None

    """
    logger.info("Testing connection to minoTour.")
    resp = mt_api._head(EndPoint.TEST)
    if resp.status_code == 200:
        logger.info(f"Successfully connected to minoTour.")
    else:
        sys.exit(f"Unsuccessful connection to minoTour at {resp.url}\nstatus: {resp.status_code}\nreason: {resp.text}")

    logger.info(f"Compatible versions {resp.headers['x-sf-version']}")
    if version in resp.headers['x-sf-version']:
        logger.info("We have compatibility!")
    else:
        logger.error(f"Swordfish version {version} incompatible with minoTour version {resp.headers['x-mt-version']}")
        sys.exit(f"BAD! Dead ☠️")


def write_toml_file(data, toml_file_path):
    """

    Parameters
    ----------
    data: dict
        the returned toml data from minoTour
    toml_file_path: pathlib.Path
        The file path to the Toml file to overwrite

    Returns
    -------
    None
    """
    if not str(toml_file_path).endswith("_live"):
        toml_file_path = f"{toml_file_path}_live"
    with open(toml_file_path, "w") as fh:
        toml.dump(data, fh)
    logger.info(f"Successfully updated toml file at {toml_file_path}")


def get_original_toml_settings(toml_file_path):
    """
    Get the original settings from the toml file. Conditions, Caller settings, conditions.classified and conditions.unclassified
    Parameters
    ----------
    toml_file_path: pathlib.Path
        Path to the toml file that will be updated
    Returns
    -------
    dict
        Dict of the settings we will keep between iterations
    """
    with open(toml_file_path, "r") as fh:
        dicty = toml.load(fh)
    keys = {"classified", "unclassified"}
    toml_dict = {"caller_settings": dicty["caller_settings"]}
    # nested dictionary conditions faff
    generic_conditions = {k: v for k, v in dicty["conditions"].items() if not isinstance(v, dict)}
    base_conditions = {k: v for k, v in dicty["conditions"].items() if isinstance(v, dict) and k in keys}
    other_conditions = {k: v for k, v in dicty["conditions"].items() if isinstance(v, dict) and k not in keys}
    toml_dict["conditions"] = generic_conditions
    toml_dict["conditions"].update(base_conditions)
    return toml_dict, other_conditions


def get_run_id(args):
    """
    Get the run_id from minknow API
    Parameters
    ----------
    args: argparse.Namespace
        The argument parser options

    Returns
    -------
    str
        Run id UUid
    """
    device = None

    # Check device
    if not args.no_minknow:
        try:
            position = get_device(
                args.device, host=args.mk_host, port=args.mk_port, use_tls=args.use_tls,
            )
        except (RuntimeError, Exception) as e:
            msg = e.message if hasattr(e, "message") else str(e)
            sys.exit(msg)
        mk_api = position.connect()
        mk_run_information = None
        try:
            mk_run_information = mk_api.acquisition.get_current_acquisition_run()
            # we need this information
            while not mk_run_information:
                logger.warning("Could not gather current acquistion info. Trying again in 5 seconds....")
                mk_run_information = mk_api.acquisition.get_current_acquisition_run()
                time.sleep(5)
        except RpcError as e:
            logger.error(repr(e))
        run_id = mk_run_information.run_id
    else:
        run_id = "638c4dea5cd1434a9a5c2ab9edee1e49"
    return run_id


def update_extant_targets(new_data: dict, toml_file_path: Path, behaviours: dict) -> dict:
    """
    Update any barcode we already have in the target TOML file by adding targets in place,
     so we accrue targets rather than overwrite them.
    Parameters
    ----------
    new_data: dict
        Data that has been fetched from minoTour this iteration
    toml_file_path: Path
        Path to the toml file that will be read
    behaviours: dict
        dict containing behaviours as provided
    Returns
    -------
    dict
        Data to be written to the toml file
    """
    _, existing_barcodes = get_original_toml_settings(toml_file_path)
    for barcode, conditions in new_data.items():
        if barcode in existing_barcodes:
            targets = set(existing_barcodes[barcode].get("targets", []))
            new_targets = set(conditions.get("targets", []))
            targets.update(new_targets)
            new_data[barcode]["targets"] = sorted(list(targets))
        new_data[barcode].update(behaviours["chunk_settings"])
        new_data[barcode].update(behaviours["unblock_behaviour"])
    return new_data


def _check_behaviour_toml(behaviour_toml: Path) -> Path:
    """
    Check the behaviour toml provided exists.
    Parameters
    ----------
    behaviour_toml: Path
        Path to behaviour toml
    Returns
    -------
    Path
        Absolute Path to the toml file.
    """
    if behaviour_toml.exists():
        return behaviour_toml.resolve()
    raise FileNotFoundError(behaviour_toml)


def _get_preset_behaviours(behaviour_toml: Path) -> dict:
    """
    Read the preset behaviours in the behaviour toml to Dict

    Parameters
    ----------
    behaviour_toml: Path
        Path to the behaviour TOML
    Returns
    -------
    dict
        The behaviour unblocks
    """
    toml_path = _check_behaviour_toml(behaviour_toml)
    behaviours = toml.load(toml_path)
    logger.info(pformat(behaviours))
    return behaviours


def get_live_toml_file(toml_file: Path) -> Path:
    """
    Check to see if the TOML file path exists already
    Parameters
    ----------
    toml_file: Path
        Pathlib Path holding the user provided path to the toml file.

    Returns
    -------
    Path
        path to the live toml file if it exists, else the normal TOML file path
    """
    live_file = Path(str(toml_file) + "_live")
    if live_file.exists():
        return live_file
    return toml_file
