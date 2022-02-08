import logging
import sys
import time

from rich.logging import RichHandler
from rich.console import Console

from swordfish.endpoints import EndPoint
from swordfish.minotour_api import MinotourAPI
from swordfish.utils import validate_mt_connection, write_toml_file, get_original_toml_settings, get_device, get_run_id, \
    update_extant_targets, _get_preset_behaviours

from grpc import RpcError
DEFAULT_FREQ = 60

formatter = logging.Formatter(
        "[%(asctime)s] %(levelname)s - %(message)s", "%Y-%m-%d %H:%M:%S"
    )
handler = RichHandler()
handler.setFormatter(formatter)

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
logger.addHandler(handler)
console = Console()


def monitor(args, sf_version):
    """
    Monitor the ARTIC task amplicons in minoTour
    Parameters
    ----------
    toml_file: pathlib.Path
        Path to the toml file
    position: minknow_api.manager.FlowCellPosition
        The position that the swordfish run is being performed on
    mt_key: str
        The uuid API token provided on the minoTour profile details page
    frequency: int
        The frequency that we check for updates in minotour at, in seconds
    mt_host: str
        Address minotour is hosted at
    mt_port: int
        The port that minoTour is accesible on the host at
    threshold: int
        The coverage threshold to unblock an amplicon at
    no_minknow: bool
        Whether we are using minknow or not. We should be, this is only really for testing
    sf_version: str
        The version of swordfish package

    Returns
    -------
    None
    """
    if args.subparser_name == "breakpoints":
        logger.warning("Breakpoints is experimental, use at your own risk!")
    toml_file = args.toml
    mt_key = args.mt_key
    frequency = args.freq
    mt_host = args.mt_host
    no_minknow = args.no_minknow
    mt_port = args.mt_port
    artic = True
    if args.subparser_name == "balance":
        threshold = args.threshold
    else:
        artic = False
        reads_per_bin = args.reads_bin
        exp_ploidy = args.exp_ploidy
        min_diff = args.min_diff
    if not args.toml.is_file():
        sys.exit(f"TOML file not found at {args.toml}")

    # Check MinoTour key is provided
    if args.mt_key is None and not args.simple:
        sys.exit("No MinoTour access token provided")

    # Check MinoTour polling frequency
    # todo, move checks into utils
    if args.freq < DEFAULT_FREQ:
        sys.exit(f"-f/--freq cannot be lower than {DEFAULT_FREQ}")
    if artic:
        if args.threshold > 1000:
            sys.exit("-t/--threshold cannot be more than 1000")

    mt_api = MinotourAPI(host_address=mt_host, port_number=mt_port, api_key=mt_key)
    validate_mt_connection(mt_api, version=sf_version)
    # Get run id from minknow
    run_id = get_run_id(args)
    while True:
        # Polling loop
        # Poll for update

        og_settings_dict, _ = get_original_toml_settings(toml_file)
        # Check run is present in minoTour
        run_json, status = mt_api.get_json(EndPoint.VALIDATE_TASK, run_id=run_id, second_slug="run", third_slug=args.subparser_name)
        if status == 404:
            logger.warning(f"Run with id {run_id} not found. Trying again in {frequency} seconds.")
            time.sleep(frequency)
            continue

        job_json, status = mt_api.get_json(EndPoint.VALIDATE_TASK, run_id=run_id, second_slug="task", third_slug=args.subparser_name)
        if status == 404:
            # Todo attempt to start a task ourselves
            task = "Artic" if artic else "Minimap2+CNV"
            logger.warning(f"{task} task not found for run {run_json['name']}.\n"
                           f"Please start one in the minoTour interface. Checking again in {frequency} seconds.")
            time.sleep(frequency)
            continue
        # Todo at this point post the original toml
        if artic:
            logger.info("Run information and Artic task found in minoTour. Fetching TOML information...")
            data, status = mt_api.get_json(EndPoint.GET_COORDS, run_id=run_id, threshold=threshold)
        else:
            # check for behaviours provided, and if there are none, use as provided by minoTour
            logger.info(f"{args.b_toml} provided for behaviour.")
            behaviours = _get_preset_behaviours(args.b_toml)
            logger.info("Run information and Minimap + CNV task found in minoTour. Fetching task information...")
            job_master_data, status = mt_api.get_json(EndPoint.TASK_INFO, swordify=False, flowcell_pk=run_json["flowcell"])
            logger.info("Run information and Minimap + CNV task information retrieved. Fetching TOML information...")
            data, status = mt_api.get_json(EndPoint.BREAKPOINTS, swordify=False, job_master_pk=job_master_data["id"], reads_per_bin=reads_per_bin, exp_ploidy=exp_ploidy, min_diff=min_diff)
            data = update_extant_targets(data, args.toml, behaviours)
        if status == 200:
            og_settings_dict["conditions"].update(data)
            write_toml_file(og_settings_dict, toml_file)
        elif status == 204:
            logger.warning(f"No barcode found in minoTour for this ARTIC task. Trying again in {frequency} seconds.")

        time.sleep(frequency)
