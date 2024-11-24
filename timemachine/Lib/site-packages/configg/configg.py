
# Library imports
from __future__ import annotations
from typing import TYPE_CHECKING, Optional, Dict, Any, List

# Type check imports
if TYPE_CHECKING:
    from configg.backend import Backend

# Project imports
from configg.exceptions import *
from configg.section_view import SectionView
from configg.ini_backend import IniBackend


class Configg:
    """
        Simple class that loads config data from a variety of formats (ini, json, xml etc), and presents them as a
        simple dictionary that can be read and written.

        Example:
            cfg = Configg("configg.ini")
            a = cfg.section_one["val_one"]
    """
    def __init__(self, path: str, data_backend: 'Backend' = None, autocommit: bool = False, readonly: bool = False,
                 defaults: Optional[dict[str, dict]] = None):
        """
        Configg constructor
        :param path: Path to config data file (it doesn't exist, will be created)
        :param data_backend: Backend data format (json, ini, xml etc) - defaults to ini
        :param autocommit: If true, writes to the dict will be written back to the config file
        :param readonly: Prevents modifying the dict if true
        :param defaults: Default values that will be used if a value isn't found
        """
        data_backend = data_backend or IniBackend
        self._backend = data_backend(path)
        self.readonly = readonly
        self.autocommit = autocommit
        self._sections = {}
        self._defaults = defaults if defaults else {}
        self.reload()
        # Make sure there is any empty section for default values if the section doesn't already exist
        for section, dict in self._defaults.items():
            if section not in self.sections:
                self.add_section(section, {})

    @property
    def sections(self) -> List[str]:
        """ :return: List of section names """
        return list(self._sections.keys())

    def iter_sections(self):
        """ : return: Generator of Sections """
        return (getattr(self, section) for section in self.sections)

    def commit(self) -> None:
        """ Commits current configg data to file """
        self._backend.write(self._sections)

    def reload(self) -> None:
        """ Reloads configg data from file """
        self._sections = self._backend.read()

    def add_section(self, name: str, data: Optional[Dict[str, Any]] = None) -> SectionView:
        """
        Adds new section to configg data.
        :param name: Name of section (will overwrite existing section)
        :param data: Dict of data to store in section (if omitted, will create empty section)
        """
        self._sections[name] = data or {}
        if self.autocommit:
            self.commit()
        return SectionView(self, self._sections[name], defaults=self._defaults)

    def remove_section(self, name: str) -> None:
        """
        Removes section from configg data
        :param name: Name of section
        """
        del self._sections[name]

    def __getattr__(self, item) -> SectionView:
        return SectionView(self, self._sections[item], self._defaults.get(item, {}))


