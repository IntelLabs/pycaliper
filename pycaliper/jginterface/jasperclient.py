import socket
import sys
import argparse
import enum
import logging

logger = logging.getLogger(__name__)


DEFAULTHOST = "localhost"
DEFAULTPORT = 8080

_msgs_sent = 0
_jgsock = None


class SocketError(Exception):
    pass


class JasperError(Exception):
    pass


class ClientMode(enum.Enum):
    ONLINE = 0
    SIM = 1


MODE = ClientMode.ONLINE


def is_online():
    return MODE == ClientMode.ONLINE


def connect_tcp(host: str = DEFAULTHOST, port: int = DEFAULTPORT):
    # Create a TCP/IP socket
    global _jgsock
    _jgsock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    __connect(_jgsock, (host, port))


def close_tcp():
    global _jgsock
    __close(_jgsock)


def shutdown_tcp():
    global _jgsock
    __shutdown(_jgsock)


def eval(command: str):

    __send_command(_jgsock, command)

    result = __receive_message(_jgsock)
    if __check_error(result):
        return result["value"]
    else:
        raise JasperError(result["value"])


def __connect(sock: socket.socket, server_address):
    if is_online():
        try:
            sock.connect(server_address)
        except socket.error:
            raise SocketError(
                f"Unable to connect to Jasper console server at {str(server_address)}"
            )
    else:
        logger.info(f"Connecting to {server_address}, but in SIM mode. Not connecting.")


def __close(sock: socket.socket):
    if is_online():
        sock.sendall("CLOSE".encode("utf-8") + b"\n")
        sock.close()
    else:
        logger.info(f"Closing socket, but in SIM mode. Not closing.")


def __shutdown(sock: socket.socket):
    if is_online():
        sock.sendall("SHUTDOWN".encode("utf-8") + b"\n")
        sock.close()
    else:
        logger.info(f"Shutting down socket, but in SIM mode. Not shutting down.")


def __send_command(sock: socket.socket, cmd: str):
    global _msgs_sent
    if is_online():
        sock.sendall("EVAL".encode("utf-8") + b"\n")
        sock.sendall(cmd.encode("utf-8") + b"\n")
    else:
        logger.debug(f"Sending command: {cmd}, but in SIM mode. Not sending.")

    _msgs_sent += 1


def __receive_message(sock: socket.socket):

    if is_online():
        # Receive single character return code and 8 byte message length
        errorlenbuf = b""
        while len(errorlenbuf) < 9:
            errorlenbuf += sock.recv(9 - len(errorlenbuf))

        # Decode error code and message length
        errcode = errorlenbuf[0:1].decode("utf-8")
        msglen = int(errorlenbuf[1:].decode("utf-8"), 16)

        # Message length plus the 2 byte carriage return and newline
        bytes_left = msglen + 2
        chunks = []
        while bytes_left > 0:
            chunk = sock.recv(bytes_left)
            chunks.append(chunk)
            bytes_left -= len(chunk)
        msgrecv = (b"".join(chunks)[:-2]).decode("utf-8")

        return {"error": errcode, "length": msglen, "value": msgrecv}
    else:
        logger.debug(f"Receiving message, but in SIM mode. Not receiving.")
        return {"error": "0", "length": 0, "value": "SIM"}


def __check_error(result):
    # Hit an error code
    if result["error"] != "0":
        logger.error(f"Error {result['error']}: {result['value']}")
        return False
    return True


def main(args):

    argparser = argparse.ArgumentParser(description="Jasper Python Client")

    # Optional port and host arguments
    argparser.add_argument(
        "-p",
        "--port",
        type=int,
        help="Port number to connect to Jasper server",
        default=DEFAULTPORT,
    )
    argparser.add_argument(
        "-H",
        "--host",
        type=str,
        help="Host name to connect to Jasper server",
        default=DEFAULTHOST,
    )
    args = argparser.parse_args(args)

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        __connect(s, (args.host, args.port))
        data = input("jg_server (cmd|close|shutdown)> ")
        while True:
            if not data:
                pass
            elif data.lower() == "close":
                __close(s)
                break
            elif data.lower() == "shutdown":
                __shutdown(s)
                break
            else:
                __send_command(s, data)
                result = __receive_message(s)
                if __check_error(result):
                    print(f"{result['value']}")
            data = input("jg_server> ")


if __name__ == "__main__":
    main(sys.argv[1:])
