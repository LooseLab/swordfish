import json as json_library
import logging
from pprint import pformat
from typing import Tuple

import requests

from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry

retry_strategy = Retry(
    total=6,
    status_forcelist=[429, 502, 503, 504, 500],
    method_whitelist=["HEAD", "GET", "OPTIONS", "POST"],
    backoff_factor=1,
)
adapter = HTTPAdapter(max_retries=retry_strategy)
http = requests.Session()
http.mount("https://", adapter)
http.mount("http://", adapter)

log = logging.getLogger(__name__)
log.setLevel(logging.INFO)


class MinotourAPI:
    def __init__(self, host_address, port_number, api_key):
        self.port_number = port_number
        self.request_headers = {
            "Authorization": f"Token {api_key}",
            "Content-Type": "application/json",
            "Content-Encoding": "gzip",
        }
        self.host_address = host_address
        self.format_base_url()

    def format_base_url(self):
        # TODO add in check for if the user types http or https
        self.host_address = (
            f"https://{self.host_address}/api/v1/"
            if self.port_number == 443
            else f"http://{self.host_address}:{self.port_number}/api/v1"
        )

    def _get(self, endpoint, params=None, **kwargs):
        """
        Get the response to a request to the minoTour server
        Parameters
        ----------
        endpoint:  <enum 'EndPoint'>
            The Enum for the endpoint we wish to get from
        params: dict
            The get request params to include
        base_id: str
            The base id for the url ex. /minion/*1*/
        run_id: str
            The run id to append to the url

        Returns
        -------
        requests.models.Response
            The requests object from the request

        """

        url = f"{self.host_address}{endpoint.swordify_url(**kwargs)}"
        resp = http.get(url, headers=self.request_headers, params=params)
        return resp

    def get(self, *args, **kwargs):
        """
        Perform get AJAX requests to minoTour server
        Parameters
        ----------
        args
            Expanded function arguments
        kwargs
            Expanded keyword arguments
        Returns
        -------
        tuple[int, str]
            The response status code and the text

        """

        resp = self._get(*args, **kwargs)
        if resp.status_code not in {200, 201, 204, 404}:
            return log.error(pformat(resp.text))
        else:
            return resp.status_code, resp.text

    def get_json(self, *args, **kwargs):
        """
        Get Json from minoTour
        Parameters
        ----------
        args
            Expanded function arguments
        kwargs
            Expanded keyword arguments
        Returns
        -------
        Tuple[dict, list]
            Json parsed data string

        """
        # TODO careful as this may not tells us we have errors
        status, text = self.get(*args, **kwargs)
        try:
            return json_library.loads(text), status
        except json_library.JSONDecodeError as e:
            log.error(repr(e))
            return status, text

    def _head(self, endpoint, *args, **kwargs):
        """
        Perform a head request to minotour
        Parameters
        ----------
        args
        kwargs

        Returns
        -------
        The response object of the request
        """
        url = f"{self.host_address}{endpoint.swordify_url(**kwargs)}"
        resp = http.head(url, headers=self.request_headers)
        return resp