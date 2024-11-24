
# Library imports
from __future__ import annotations
from typing import Dict, Any, TYPE_CHECKING, List, Tuple

# Type check imports
if TYPE_CHECKING:
    from configg.configg import Configg

# Project imports
from configg.exceptions import *


class SectionView:

    def __init__(self, parent: Configg, data: dict, defaults: dict):
        for key, value in data.items():
            if type(key) is not str:
                raise Exception
            if type(key) not in [str, int]:
                raise Exception
        self._parent = parent
        self._data = data
        self._defaults = defaults

    def __getitem__(self, key) -> Any:
        """
        dict operator, provides dict-like access to data
        :param key: key
        :return: Value stored (or subsequent dict)
        :raises: KeyError if key not present in data or defaults
        """
        if key in self._data:
            return self._data[key]
        elif key in self._defaults:
            return self._defaults[key]
        else:
            raise KeyError("'{key}' not found in {parent}.{obj}".format(key=key, parent=self._parent, obj=self))

    def __setitem__(self, key, value) -> None:
        """
        dict operator, provides dict-like access to write data
        :param key: key
        :param value:
        :return:
        """
        if self._parent.readonly:
            raise ReadOnlyError
        self._data[key] = value
        if self._parent.autocommit:
            self.commit()

    def __contains__(self, key) -> bool:
        """
        dict operator, returns true if key is present
        :param key: Key to check
        :return: key present?
        """
        return key in self._data

    def keys(self) -> List[str]:
        """ :return: List of dictionary keys """
        return list(self._data.keys())

    def items(self) -> List[Tuple[str, Any]]:
        """:return: List of (key, item) tuples """
        return list(self._data.items())

    def values(self) -> List[Any]:
        """:return: List of values"""
        return list(self._data.values())

    def commit(self) -> None:
        """ Commits current configg data to file """
        self._parent.commit()

    def reload(self) -> None:
        """ Reloads configg data from file """
        self._parent.reload()

    def configg(self) -> Configg:
        """ :return: Return parent Configg instance """
        return self._parent

    def as_dict(self) -> dict:
        """ :return: Return data as pure python dictionary """
        return self._data.copy()

    def defaults(self) -> dict:
        """ :return: Return default values as a pure python dictionary """
        return self._defaults.copy()

