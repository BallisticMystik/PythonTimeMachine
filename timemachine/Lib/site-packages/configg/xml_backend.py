# Library imports
from typing import Dict, Any
import xml.etree.ElementTree as ET
from multiprocessing import Lock

# Project imports
from configg.backend import Backend


class XmlBackend(Backend):
    """ ini file backend for configg """

    def __init__(self, path: str):
        super().__init__(path)
        self.lock = Lock()

    def read(self) -> Dict[str, Any]:
        root = ET.parse(self.path).getroot()
        data = {}
        for child in root:
            data[child.tag] = {}
            for child2 in child:
                data[child.tag][child2.tag] = child2.text
        return data

    def write(self, data: Dict[str, Any]) -> None:
        sections = []
        for section, section_data in data.items():
            xml = "<{}>".format(section)
            for key, value in section_data.items():
                xml += "<{key}>{value}</{key}>".format(key=key, value=value)
            xml += "</{}>".format(section)
            sections.append(xml)
        xml_data = "<config>"
        for xml in sections:
            xml_data += xml
        xml_data += "</config>"
        self.lock.acquire(False)
        with open(self.path, "w+") as fp:
            fp.truncate()
            fp.seek(0)
            fp.write(xml_data)
        self.lock.release()

