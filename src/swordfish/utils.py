"""
Utilities for speaking with MinoTour
"""
import toml
from minknow_api.manager import Manager
import logging
import sys

from swordfish.endpoints import EndPoint

formatter = logging.Formatter(
        "[%(asctime)s] %(levelname)s - %(message)s", "%Y-%m-%d %H:%M:%S"
    )
handler = logging.StreamHandler()
handler.setFormatter(formatter)

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
        sys.exit(f"Swordfish version {version} incompatibile with minoTour version {resp.headers['x-mt-version']}")


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
    target_conditions = {k: v for k, v in dicty["conditions"].items() if isinstance(v, dict) and k in keys}
    toml_dict["conditions"] = generic_conditions
    toml_dict["conditions"].update(target_conditions)
    return toml_dict

