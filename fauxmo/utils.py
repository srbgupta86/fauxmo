"""utils.py

Utility functions for Fauxmo.
"""

import importlib.util
import pathlib
import socket
import struct
import uuid
from types import ModuleType

from . import logger


def get_local_ip(ip_address: str=None) -> str:
    """Attempt to get the local network-connected IP address."""

    if ip_address is None or ip_address.lower() == "auto":
        logger.debug("Attempting to get IP address automatically")

        hostname = socket.gethostname()
        ip_address = socket.gethostbyname(hostname)

        # Workaround for Linux returning localhost
        # See: SO question #166506 by @UnkwnTech
        if ip_address in ['127.0.1.1', '127.0.0.1', 'localhost']:
            tempsock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            tempsock.connect(('8.8.8.8', 0))
            ip_address = tempsock.getsockname()[0]
            tempsock.close()

    logger.debug(f"Using IP address: {ip_address}")
    return ip_address


def make_serial(name: str) -> str:
    """Create a persistent UUID from the device name.

    Returns a suitable UUID derived from `name`. Should remain static for a
    given name.

    Args:
        name (str): Friendly device name (e.g. "living room light")
    """

    return str(uuid.uuid3(uuid.NAMESPACE_X500, name))


def module_from_file(modname: str, path_str: str) -> ModuleType:
    """Load a module into `modname` from a file path.

    Args:
        modname: The desired module name
        path_str: Path to the file
    """

    path = pathlib.Path(path_str).expanduser()
    spec = importlib.util.spec_from_file_location(modname, str(path))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def make_udp_sock() -> socket.socket:
    """Make a suitable udp socket to listen for device discovery requests."""

    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind(('', 1900))
    group = socket.inet_aton('239.255.255.250')
    mreq = struct.pack('4sL', group, socket.INADDR_ANY)
    sock.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, mreq)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

    reuseport = getattr(socket, "SO_REUSEPORT", None)
    if reuseport:
        sock.setsockopt(socket.SOL_SOCKET, reuseport, 1)

    return sock