import logging
import time

from swordfish.endpoints import EndPoint
from swordfish.minotour_api import MinotourAPI
from swordfish.utils import validate_mt_connection, write_toml_file, get_original_toml_settings

from grpc import RpcError


formatter = logging.Formatter(
        "[%(asctime)s] %(levelname)s - %(message)s", "%Y-%m-%d %H:%M:%S"
    )
handler = logging.StreamHandler()
handler.setFormatter(formatter)

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
logger.addHandler(handler)


def monitor(toml_file, position, mt_key, frequency, mt_host, mt_port, no_minknow, sf_version):
    # Upload initial TOML file
    if not no_minknow:
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
        run_id = "61fe42b9257b07b2c4e3e046aa94a6c827f6befd"

    mt_api = MinotourAPI(host_address=mt_host, port_number=mt_port, api_key=mt_key)
    validate_mt_connection(mt_api, version=sf_version)
    while True:
        # Polling loop
        # Poll for update
        # If sha256sum is different update TOML_live file

        og_settings_dict = get_original_toml_settings(toml_file)
        # Check run is present in minoTour
        run_json, status = mt_api.get_json(EndPoint.VALIDATE_TASK, run_id=run_id, second_slug="run")
        if status == 404:
            logger.warning(f"Run with id {run_id} not found. Trying again in {frequency} seconds.")
            time.sleep(frequency)
            continue

        job_json, status = mt_api.get_json(EndPoint.VALIDATE_TASK, run_id=run_id, second_slug="task")
        if status == 404:
            # Todo attempt to start a task ourselves
            logger.warning(f"Artic task not found for run {run_json['name']}.\n"
                           f"Please start one in the minoTour interface. Checking again in {frequency} seconds.")
            time.sleep(frequency)
            continue
        # Todo at this point post the original toml
        logger.info("Run information and Artic task found in minoTour. Fetching toml information...")
        data, status = mt_api.get_json(EndPoint.GET_COORDS, run_id=run_id)
        og_settings_dict["conditions"].update(data)
        write_toml_file(og_settings_dict, toml_file)

        time.sleep(frequency)
