
# Library imports
from typing import Dict, Any
import configparser
from multiprocessing import Lock

# Project imports
from configg.backend import Backend


class IniBackend(Backend):
    """ ini file backend for configg """

    def __init__(self, path: str):
        super().__init__(path)
        self.lock = Lock()

    def read(self) -> Dict[str, Any]:
        parser = configparser.ConfigParser()
        parser.read(self.path)
        data = {}
        for section_name, section_dict in parser._sections.items():
            data[section_name] = section_dict
        return self._strip_quotes(data)

    def write(self, data: Dict[str, Any]) -> None:
        self.lock.acquire(False)
        with open(self.path, "w+") as fp:
            parser = configparser.ConfigParser()
            parser.read_dict(data)
            parser.write(fp)
        self.lock.release()