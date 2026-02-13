"""
Stub for worlds/__init__.py when running from bundled .apworld

This version doesn't scan for world folders since we're running from inside a ZIP file.
It only provides the necessary imports and classes needed by CommonClient.
"""
from __future__ import annotations

import typing
import logging

# Essential imports from worlds module
class AutoWorldRegister(type):
    """Registry for world classes"""
    world_types: typing.Dict[str, typing.Any] = {}
    
    def __new__(mcs, name, bases, dct):
        cls = super().__new__(mcs, name, bases, dct)
        if "game" in dct:
            AutoWorldRegister.world_types[dct["game"]] = cls
        return cls

# Network data package - minimal entry for SSHD
network_data_package: typing.Dict[str, typing.Any] = {
    "version": 1,
    "games": {
        "Skyward Sword HD": {
            "item_name_to_id": {},
            "location_name_to_id": {},
            "version": 0,
            "checksum": "SSHD_BUNDLED",
        }
    }
}

# Required for CommonClient compatibility
__all__ = [
    "AutoWorldRegister",
    "network_data_package",
]
