# My modules
from ssh_manager.config import SSHConfig, TunnelConfig
from ssh_manager.lib.base import SSHClient
import ssh_manager.errors as er

# Built-In modules
from asyncio import sleep as asleep
from dataclasses import dataclass
from asyncio import Lock
import asyncssh as assh


@dataclass
class SSHConnection:
    """Client specific SSH connection and tunnels"""

    conn: assh.SSHClientConnection
    tuns: dict[str, assh.SSHListener]


class AsyncSSHClient(SSHClient):
    def __init__(self, recon_attempts: int, recon_delay: int):
        """Client for AsyncSSH library

        Args:
            recon_attempts (int): maximum number of reconnection attempts to SSH server
            recon_delay (int): timeout in seconds between reconnection attempts
        """

        self._connections: dict[str, SSHConnection] = {}
        self._recon_attemps = recon_attempts
        self._recon_delay = recon_delay
        self._alock = Lock()

    def is_connected(self, connection_id: str) -> bool:
        """Ensure SSH connection exists and connected to server"""

        connection = self._connections.get(connection_id)
        return connection and not connection.conn.is_closed()

    async def open_ssh(self, cfg: SSHConfig) -> None:
        """Establish and save TCP connection with SSH server (limited attempts)"""

        connection_id = cfg.get_connection_id()
        asyncssh_cfg = cfg.get_asyncssh_cfg()
        last_error = None

        async with self._alock:  # Connect SSH server
            for attempt in range(self._recon_attemps):

                try:  # Establish and save SSH connection
                    connection = SSHConnection(await assh.connect(**asyncssh_cfg), {})
                    self._connections[connection_id] = connection
                    return

                except Exception as error:
                    last_error = error

                    # Pass delay on last attempt
                    if attempt < self._recon_attemps - 1:
                        await asleep(self._recon_delay)

        try:  # Errors check
            if last_error:
                raise last_error

        # Connection errors
        except (ConnectionRefusedError, TimeoutError, OSError) as e:
            raise er.SSHConnError(cfg.username, cfg.host, cfg.port) from e

        # Authentication errors
        except (
            assh.HostKeyNotVerifiable,
            assh.PermissionDenied,
            assh.ConfigParseError,
            assh.KeyImportError,
            assh.ProtocolError,
        ) as e:
            raise er.SSHAuthError(cfg.username, cfg.host, cfg.port) from e

        # Other SSH errors
        except assh.Error as e:
            raise er.SSHError(cfg.username, cfg.host, cfg.port) from e

    async def close_ssh(self, connection_id: str) -> None:
        """Close TCP connection to SSH server and all underlying tunnels (errors ommited)"""

        async with self._alock:

            connection = self._connections.pop(connection_id)

            # Close all associated tunnels
            for tunnel in connection.tuns.values():
                try:
                    tunnel.close()
                    await tunnel.wait_closed()

                except Exception:
                    continue

            connection.tuns.clear()

            try:  # Close SSH
                connection.conn.close()
                await connection.conn.wait_closed()

            except Exception:
                pass

            finally:
                connection.conn = None
                del connection

    async def open_tunnel(self, connection_id: str, cfg: TunnelConfig) -> None:
        """Open tunnel from local host:port to remote and return it's id"""

        connection = self._connections.get(connection_id)
        tun_cfg = cfg.get_asyncssh_cfg()
        tun_id = cfg.get_tunnel_id()

        async with self._alock:

            # Check tunnel existence
            tun = connection.tuns.get(tun_id)
            if tun:
                return

            try:  # Create and save tunnel
                tun = await connection.conn.forward_local_port(**tun_cfg)
                connection.tuns[tun_id] = tun
                return

            except OSError as e:  # Busy ports error
                raise er.SSHTunPortError(*tun_cfg.values()) from e

            except assh.PermissionDenied as e:  # No permissions error
                raise er.SSHTunPersmissionError(*tun_cfg.values()) from e

            except assh.Error as e:  # Other tunnel errors
                raise er.SSHTunError(*tun_cfg.values()) from e

    async def close_tunnel(self, connection_id: str, tunnel_id: str) -> None:
        """Close tunnel from local host:port to remote (errors ommited)"""

        async with self._alock:

            connection = self._connections.get(connection_id)
            tunnel = connection.tuns.pop(tunnel_id, None)

            if not tunnel:  # Check tunnel existence
                return

            try:  # Close tunnel
                tunnel.close()
                await tunnel.wait_closed()

            except Exception:
                pass

    async def exec_command(self, connection_id: str, command: str) -> str:
        """Execute command on remote host and return result string"""

        connection = self._connections.get(connection_id)

        try:
            result = await connection.conn.run(command, check=True)
            return result.stdout

        except assh.ProcessError as e:
            raise er.SSHCommandFailedError(command) from e

        except assh.Error as e:
            raise er.SSHCommandExecuteError(command) from e
