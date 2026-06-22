import socket
import threading
from datetime import datetime


class Frame:
    def __init__(self, frame_bytes: bytes):
        self.length = frame_bytes[0]
        self.reader_address = frame_bytes[1]
        self.command = frame_bytes[2]
        self.status = frame_bytes[3]
        self.data = frame_bytes[4:-2]
        self.checksum = frame_bytes[-2:]

    def __str__(self) -> str:
        return (
            f"RESPONSE       >> {hex_readable(self.length)} {hex_readable(self.reader_address)} "
            f"{hex_readable(self.command)} {hex_readable(self.status)} {hex_readable(self.data)} "
            f"{hex_readable(self.checksum)}\n"
            f"READER ADDRESS >> {hex_readable(self.reader_address)}\n"
            f"COMMAND        >> {hex_readable(self.command)}\n"
            f"STATUS         >> {hex_readable(self.status)}\n"
            f"DATA           >> {hex_readable(self.data)}\n"
            f"CHECKSUM       >> {hex_readable(self.checksum)}\n"
        )


class Response:
    def __init__(self, response_bytes: bytes):
        self.frames = self._parse_frames(response_bytes)

    def _parse_frames(self, response_bytes: bytes):
        frames = []
        index = 0
        while index < len(response_bytes):
            length = response_bytes[index]
            frame_end = index + length + 1  # +1 to include the length byte itself
            frame_bytes = response_bytes[index:frame_end]
            if len(frame_bytes) < length + 1:
                raise ValueError("Incomplete frame data")
            frames.append(Frame(frame_bytes))
            index = frame_end
        return frames

    def __str__(self) -> str:
        now = datetime.now()
        return_value = f">>> {now} - START RESPONSE ================================\n"
        for index, frame in enumerate(self.frames):
            return_value += f">>> FRAME [{index}] ===\n"
            return_value += str(frame)
        return_value = (
            return_value + f"\n>>> {now} - END RESPONSE   ================================\n\n"
        )
        return return_value.strip()


def hex_readable(data: bytes | int, bytes_separator: str = " ") -> str:
    if isinstance(data, int):
        return f"{data:02X}"
    return bytes_separator.join(f"{x:02X}" for x in data)


def handle_client(client_socket: socket.socket, addr):
    print(f"Connection from {addr}")
    # client_socket.settimeout(5.0)
    try:
        raw_response: bytes = client_socket.recv(1024)
        while raw_response:
            response: Response = Response(raw_response)
            # print(response)

            for frame in response.frames:
                print(
                    f"Reader: {hex_readable(frame.reader_address)} -> Tag: {hex_readable(frame.data, '')}"
                )  # Tag
                # send the data to database or any other sink

            raw_response = client_socket.recv(1024)
    except Exception as e:
        print(f"Error: {e}")
    finally:
        client_socket.close()
        print(f"Connection closed for {addr}")


def start_server(host: str, port: int) -> None:
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind((host, port))
    server_socket.listen(5)  # Set max 5 connections
    print(f"Server listening on {host}:{port}")

    try:
        while True:
            client_socket, addr = server_socket.accept()
            client_thread = threading.Thread(
                target=handle_client, args=(client_socket, addr), daemon=True
            )
            client_thread.start()

    except KeyboardInterrupt:
        print("Shutting down the server...")
    finally:
        server_socket.close()


if __name__ == "__main__":
    start_server(host="0.0.0.0", port=2077)
