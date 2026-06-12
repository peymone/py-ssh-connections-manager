from ssh_manager.lib.client import AsyncSSHClient
from ssh_manager.lib.base import SSHClient


def init_client(backend: str, recon_attempts: int, recon_delay: int) -> SSHClient:
    """Initialize and return SSH client for specified backend (library)"""

    if backend == "asyncssh":
        return AsyncSSHClient(recon_attempts, recon_delay)

    if backend == "paramiko":
        pass
