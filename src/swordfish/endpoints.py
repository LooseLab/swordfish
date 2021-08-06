from enum import Enum


class EndPoint(Enum):
    SWORDFISH_BASE = "/readfish/swordfish"
    RUNS = "/reads/runs/{}/"
    VALIDATE_TASK = "/{}/"
    TEST = "/minknow/test-connect/"

    def swordify_url(self, run_id):
        """
        Swordfishify urls, formatting the provided run id into them
        Returns
        -------
        run_id: str
            The run id UUID
        """
        return f"{self.__class__.SWORDFISH_BASE}{self.value.format(run_id)}"

    def __str__(self):
        return "{self.value}"