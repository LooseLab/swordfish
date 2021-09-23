from enum import Enum


class EndPoint(Enum):
    SWORDFISH_BASE = "/readfish/swordfish"
    RUNS = "/reads/runs/{}/"
    VALIDATE_TASK = "/{}/validate/{}"
    TEST = "/test-connect/"
    GET_COORDS = "/{}/chopchop/{}"

    def swordify_url(self, **kwargs):
        """
        Swordfishify urls, formatting the provided run id into them
        Returns
        -------
        run_id: str
            The run id UUID
        """
        # todo switch to list kwargs.values for formatting
        format_list = [x for x in kwargs]
        return f"{self.__class__.SWORDFISH_BASE}{self.value.format(format_list)}"

    def __str__(self):
        return f"{self.value}"