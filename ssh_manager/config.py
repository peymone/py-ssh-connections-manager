from dataclasses import dataclass


@dataclass
class SSHConfig:
    """SSH connection config"""

    host: str = None
    port: int = None
    pKey: str = None
    username: str = None
    password: str = None
    passphrase: str = None
    known_hosts: str = None
    open_ssh_config: str = None

    def get_asyncssh_cfg(self) -> dict:
        """Parse SSH config to asyncssh format"""

        config = {
            "host": self.host,
            "port": self.port,
            "username": self.username,
            "password": self.password,
            "passphrase": self.passphrase,
            "known_hosts": self.known_hosts,
            "client_keys": [self.pKey] if self.pKey else None,
            "config": [self.open_ssh_config] if self.open_ssh_config else None,
        }

        return {k: v for k, v in config.items() if v is not None}

    def get_connection_id(self) -> str:
        """Generate SSH connection id from config: user@remotehost:22"""

        return f"{self.username}@{self.host}:{self.port}"


@dataclass
class TunnelConfig:
    """SSH tunnel config"""

    local_host: str
    local_port: int
    dest_host: str
    dest_port: int

    def get_tunnel_id(self) -> str:
        """Generate tunnel id from config: localhost:80-remotehost:80"""

        return "{}:{}-{}:{}".format(
            self.local_host, self.local_port, self.dest_host, self.dest_port
        )

    def get_asyncssh_cfg(self) -> dict:
        """Parse tunnel config to asyncssh format"""

        return {
            "listen_host": self.local_host,
            "listen_port": self.local_port,
            "dest_host": self.dest_host,
            "dest_port": self.dest_port,
        }
