# My modules
from ssh_manager.config import SSHConfig, TunnelConfig
from ssh_manager.lib import init_client
import ssh_manager.errors as er

# Built-In modules
from dataclasses import dataclass
from typing import Literal


@dataclass
class SSHConnection:
    """Opened SSH connection and tunnels"""

    config: SSHConfig
    tunnels: dict[str, TunnelConfig]


class SSHConnectionManager:
    def __init__(
        self,
        recon_attempts: int,
        recon_delay: int,
        client: Literal["asyncssh", "paramiko"],
    ):
        """Connection manager for SSH

        Args:
            recon_attempts (int): maximum number of reconnection attempts to SSH server
            recon_delay (int): timeout in seconds between reconnection attempts
            client (str): underlying client for controlling SSH connections

        Usage example:
            manager = SSHConnectionManager(5, 1, "asyncssh") # Create SSH client
            conn_id = await manager.open_ssh(ssh_cfg) # Establish SSH connection
            tunn_id = await manager.open_tunnel(conn_id, tun_cfg) # Open tunnel
            await manager.close_ssh(conn_id) # Close SSH connection
        """

        self._client = init_client(client, recon_attempts, recon_delay)
        self._connections: dict[str, SSHConnection] = dict()

    def _get_connection(self, connection_id: str) -> SSHConnection:
        """Get connection by id or rise error"""

        connection = self._connections.get(connection_id)

        if not connection:
            raise er.SSHConnectionNotFoundError(connection_id)

        return connection

    async def open_ssh(self, config: SSHConfig) -> str:
        """Establish SSH connection with remote server and return it's id"""

        connection_id = config.get_connection_id()
        connection = self._connections.get(connection_id)

        # Check if connection already established
        if connection and self._client.is_connected(connection_id):
            return connection_id

        # Connect SSH and save it
        await self._client.open_ssh(config)
        self._connections[connection_id] = SSHConnection(config, {})

        return connection_id

    async def close_ssh(self, connection_id: str) -> None:
        """Close TCP connection to SSH server and all underlying tunnels"""

        connection = self._connections.pop(connection_id, None)

        if connection:  # Close connection
            await self._client.close_ssh(connection_id)

            # Delete connection object
            connection.tunnels.clear()
            del connection

    async def close_all(self) -> None:
        """Close all established TCP connections to SSH servers and all underlying tunnels"""

        for connection_id in self._connections:
            await self._client.close_ssh(connection_id)

        self._connections.clear()

    async def open_tunnel(self, connection_id: str, config: TunnelConfig) -> str:
        """Open tunnel from local host:port to remote and return it's id"""

        connection = self._get_connection(connection_id)
        tunnel_id = config.get_tunnel_id()

        # Check if connection established
        if not self._client.is_connected(connection_id):
            await self.reopen_ssh_tunnels(connection_id)

        # Check tunnel existense
        if tunnel_id is connection.tunnels:
            return tunnel_id

        # Open and save tunnel
        await self._client.open_tunnel(connection_id, config)
        connection.tunnels[tunnel_id] = config

        return tunnel_id

    async def close_tunnel(self, connection_id: str, tunnel_id: str) -> None:
        """Close specific tunnel from local host:port to remote"""

        connection = self._get_connection(connection_id)
        tunnel_config = connection.tunnels.pop(tunnel_id, None)

        if not tunnel_config:  # Check tunnel esistense
            raise er.SSHTunnelNotFoundError(connection_id, tunnel_id)

        # Check if connection established
        if not self._client.is_connected(connection_id):
            await self.reopen_ssh_tunnels(connection_id)
            return

        # Close tunnel
        await self._client.close_tunnel(connection_id, tunnel_id)

    async def close_tunnels(self, connection_id: str) -> None:
        """Close all tunnels for SSH connection"""

        connection = self._get_connection(connection_id)

        # Check if connection established
        if not self._client.is_connected(connection_id):
            await self.reopen_ssh_tunnels(connection_id, connection.tunnels.keys())
            return

        # Close tunnels
        for tunnel_id in connection.tunnels:
            await self._client.close_tunnel(connection_id, tunnel_id)

        connection.tunnels.clear()

    async def exec_command(self, connection_id: str, command: str) -> str:
        """Execute command on remote host and return result"""

        _ = self._get_connection(connection_id)

        if not self._client.is_connected(connection_id):
            await self.reopen_ssh_tunnels(connection_id)

        return await self._client.exec_command(connection_id, command)

    async def reopen_ssh_tunnels(
        self, connection_id: str, skip_tuns_id: list[str]
    ) -> None:
        """Close SSH connection and tunnels and open it again"""

        connection = self._get_connection(connection_id)

        # Close SSH connection and tunnels, reopen SSH
        await self._client.close_ssh(connection_id)
        await self._client.open_ssh(connection.config)

        # Reopen tunnels
        for tun_id, tun_cfg in connection.tunnels.items():
            if tun_id in skip_tuns_id:
                continue

            await self._client.open_tunnel(connection_id, tun_cfg)
