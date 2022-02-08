from enum import Enum


class EndPoint(Enum):
    SWORDFISH_BASE = "/readfish/swordfish"
    RUNS = "/reads/runs/{}/"
    VALIDATE_TASK = "/{}/validate/{}/{}"
    TEST = "/test-connect/"
    GET_COORDS = "/{}/chopchop/{}"
    BREAKPOINTS = "/alignment/breakpoints/{}/{}/{}/{}"
    TASK_INFO = "/alignment/get_task/{}"

    def swordify_url(self, **kwargs):
        """
        Swordfishify urls, formatting the provided run id into them
        Returns
        -------
        run_id: str
            The run id UUID
        """
        # todo switch some form of validation for number of format params vs number of required params
        swordify = kwargs.pop("swordify") if "swordify" in kwargs else True
        format_list = [x for x in kwargs.values()]
        if swordify:
            return f"{self.__class__.SWORDFISH_BASE}{self.value.format(*format_list)}"
        return f"{self.value.format(*format_list)}"

    def __str__(self):
        return f"{self.value}"
