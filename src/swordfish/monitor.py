import logging
from swordfish.endpoints import EndPoint
from swordfish.minotour_api import MinotourAPI

from grpc import RpcError



formatter = logging.Formatter(
        "[%(asctime)s] %(levelname)s - %(message)s", "%Y-%m-%d %H:%M:%S"
    )
handler = logging.StreamHandler()
handler.setFormatter(formatter)

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
logger.addHandler(handler)

def monitor(toml_file, position, mt_key, frequency, mt_host, mt_port):
    # Upload initial TOML file
    mk_api = position.connect()
    mk_run_information = None
    try:
        mk_run_information = mk_api.get_current_acquisition_run()
        # we need this information
        while not mk_run_information:
            logger.warning("Could not gather current acquistion info. Trying again in 5 seconds....")
            mk_run_information = self.get_current_acquisition_run()
            time.sleep(5)
    except RpcError:
        logger.error()

    mt_api = MinotourAPI(host_address=mt_host, port_number=mt_port, api_key=mt_key)
    mt_api.get(EndPoint.TEST.swordify_url())
    while True:
        # Polling loop
        # Poll for update
        # If sha256sum is different update TOML_live file
        pass
