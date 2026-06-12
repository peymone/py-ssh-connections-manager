SSHErrorMsg = "[SSH_ERROR] Unknown SSH error occured"
SSHConnErrorMsg = "[SSH_ERROR] SSH connection failed (network problems) for {}@{}:{}"
SSHAuthErrorMsg = "[SSH_ERROR] SSH auth failed (Invalid PKey/Credentials) for {}@{}:{}"
SSHTunErrorMsg = "[SSH ERROR] Unable to create a tunnel for {}:{}-{}:{}"
SSHTunPortErrorMsg = "[SSH_ERROR] Ports on local or remote host are busy {}:{}-{}:{}"
SSHTunPersmissionErrorMsg = "[SSH ERROR] No tun forwarding permissions for {}:{}-{}:{}"
SSHCommandFailedErrorMsg = "[SSH ERROR] Executed command returned a error code: '{}'"
SSHCommandExecuteErrorMsg = "[SSH ERROR] Connection loss while executing command: '{}'"
SSHConnectionNotFoundErrorMsg = "[SSH_ERROR] SSH connection with id='{}' not found"
SSHTunnelNotFoundErrorMsg = "[SSH_ERROR] Tunnel with id='{}' not found for '{}'"


class SSHError(Exception):
    """Basic exception for SSH related errors"""

    pass


class SSHConnError(SSHError):
    """Network error during establishing SSH connection with server"""

    def __init__(self, user: str, host: str, port: int):
        message = SSHConnErrorMsg.format(user, host, port)
        super().__init__(message)


class SSHAuthError(SSHError):
    """Unavle to authenticate with provided credentials to SSH"""

    def __init__(self, user: str, host: str, port: int):
        message = SSHAuthErrorMsg.format(user, host, port)
        super().__init__(message)


class SSHTunError(SSHError):
    """Unable to create tunnel from local host:port to remote - unknown error"""

    def __init__(
        self, local_host: str, local_port: int, remote_host: str, remote_port: int
    ):
        message = SSHTunErrorMsg.format(
            local_host, local_port, remote_host, remote_port
        )
        super().__init__(message)


class SSHTunPortError(SSHError):
    """Unable to create tunnel from local host:port to remote - busy ports"""

    def __init__(
        self, local_host: str, local_port: int, remote_host: str, remote_port: int
    ):
        message = SSHTunPortErrorMsg.format(
            local_host, local_port, remote_host, remote_port
        )
        super().__init__(message)


class SSHTunPersmissionError(SSHError):
    """Unable to create tunnel from local host:port to remote - no permissions"""

    def __init__(
        self, local_host: str, local_port: int, remote_host: str, remote_port: int
    ):
        message = SSHTunPersmissionErrorMsg.format(
            local_host, local_port, remote_host, remote_port
        )
        super().__init__(message)


class SSHCommandFailedError(SSHError):
    """Executed command returned a error code"""

    def __init__(self, command):
        message = SSHCommandFailedErrorMsg.format(command)
        super().__init__(message)


class SSHCommandExecuteError(SSHError):
    """Unable to execute command on remote host"""

    def __init__(self, command):
        message = SSHCommandExecuteErrorMsg.format(command)
        super().__init__(message)


class SSHConnectionNotFoundError(SSHError):
    """SSH client not created"""

    def __init__(self, ssh_connection_id: str):
        message = SSHConnectionNotFoundErrorMsg.format(ssh_connection_id)
        super().__init__(message)


class SSHTunnelNotFoundError(SSHConnError):
    def __init__(self, ssh_connection_id: str, tunnel_id: str):
        message = SSHTunnelNotFoundErrorMsg.format(ssh_connection_id, tunnel_id)
        super().__init__(message)
