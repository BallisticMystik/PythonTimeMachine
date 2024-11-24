# Library imports
from typing import Dict, Any
import json
from multiprocessing import Lock

# Project imports
from configg.backend import Backend


class JsonBackend(Backend):
    """ ini file backend for configg """

    def __init__(self, path: str):
        super().__init__(path)
        self.lock = Lock()

    def read(self) -> Dict[str, Any]:
        with open(self.path, "r") as fp:
            return json.load(fp)

    def write(self, data: Dict[str, Any]) -> None:
        self.lock.acquire(False)
        with open(self.path, "w+") as fp:
            json.dump(data, fp)
        self.lock.release()