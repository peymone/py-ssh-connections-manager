from abc import ABC, abstractmethod

from ssh_manager.config import SSHConfig, TunnelConfig


class SSHClient(ABC):
    @abstractmethod
    def is_connected(self, connection_id: str) -> bool:
        """Ensure SSH connection exists and connected to server"""

        pass

    @abstractmethod
    def open_ssh(self, config: SSHConfig) -> None:
        """Establish and save TCP connection with SSH server (limited attempts)"""

        pass

    @abstractmethod
    def close_ssh(self, connection_id: str) -> None:
        """Close TCP connection to SSH server and all underlying tunnels"""

        pass

    @abstractmethod
    def open_tunnel(self, connection_id: str, config: TunnelConfig) -> None:
        """Open tunnel from local host:port to remote"""

        pass

    @abstractmethod
    def close_tunnel(self, connection_id: str, tunnel_id: str) -> None:
        """Close tunnel from local host:port to remote (errors ommited)"""

        pass

    @abstractmethod
    def exec_command(self, connection_id: str, command: str) -> str:
        """Execute command on remote host and return result string"""

        pass
