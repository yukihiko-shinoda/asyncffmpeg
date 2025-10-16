"""The socket to comunicate processes of different group each other."""

import socket
from contextlib import closing

from tests.testlibraries.keyboardinterrupter import SECOND_SLEEP_FOR_TEST_KEYBOARD_INTERRUPT_CTRL_C_POPEN_MIDDLE


class LocalSocket:
    """The socket to comunicate processes of different group each other."""

    ENCODING = "utf-8"
    HOST = "127.0.0.1"
    # Almost ports are blocked on GitHub Windows runner.
    # Although the port 8080 seems to be able to use.
    # see: https://github.community/t/what-is-the-default-firewall-for-github-actions-runners/17732
    PORT = 8080
    TIME_TO_ALLOW_ACCESS = 1
    TIMEOUT = SECOND_SLEEP_FOR_TEST_KEYBOARD_INTERRUPT_CTRL_C_POPEN_MIDDLE
    MAX_BUFFER_SIZE = 1024
    SOCKET_REUSE_ADDRESS_ENABLE = 1

    @staticmethod
    def send(message: str) -> None:
        with closing(socket.socket(socket.AF_INET, socket.SOCK_STREAM)) as socket_from:
            socket_from.connect((LocalSocket.HOST, LocalSocket.PORT))
            socket_from.send(bytes(message, LocalSocket.ENCODING))

    @staticmethod
    def receive() -> str:
        """Receives message."""
        with closing(socket.socket(socket.AF_INET, socket.SOCK_STREAM)) as socket_to:
            socket_to.settimeout(LocalSocket.TIMEOUT)
            # see:
            #   - https://docs.python.org/ja/3/library/socket.html#example
            #   - Answer: Python server “Only one usage of each socket address is normally permitted”
            #     https://stackoverflow.com/a/12362623/12721873
            socket_to.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, LocalSocket.SOCKET_REUSE_ADDRESS_ENABLE)
            socket_to.bind((LocalSocket.HOST, LocalSocket.PORT))
            socket_to.listen(LocalSocket.TIME_TO_ALLOW_ACCESS)
            connection, _ = socket_to.accept()
            try:
                return str(connection.recv(LocalSocket.MAX_BUFFER_SIZE), LocalSocket.ENCODING)
            finally:
                connection.close()
