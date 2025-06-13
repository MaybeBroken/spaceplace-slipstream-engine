import websockets as ws
import asyncio
import socket
import subprocess
import re
import direct.stdpy.threading as threading
import json

outbound = []
incoming = []


def send_message(message):
    try:
        message = json.dumps(message)
    except Exception as e:
        raise ValueError("Message must be a JSON encodable object") from e
    outbound.append(message)


def iter_messages():
    val = incoming.copy()
    incoming.clear()
    if not val:
        return []
    return [json.loads(id) for id in val]


def _connect_to_server(uri):
    async def connect():
        async with ws.connect(uri) as websocket:
            print(f"CLIENT: Connected to server at {uri}")

            async def read_incoming():
                while True:
                    try:
                        message = await websocket.recv()
                        if message:
                            incoming.append(message)
                            print(f"CLIENT: Received message: {message}")
                    except ws.ConnectionClosed:
                        print("CLIENT: Connection closed")
                        break
                    except Exception as e:
                        print(f"CLIENT: Error receiving message: {e}")
                        break

            async def send_outbound():
                while True:
                    try:
                        if outbound:
                            message = outbound.pop(0)
                            await websocket.send(message)
                            print(f"CLIENT: Sent message: {message}")
                        else:
                            await asyncio.sleep(0.1)  # <-- Add this line
                    except ws.ConnectionClosed:
                        print("CLIENT: Connection closed while sending")
                        break
                    except Exception as e:
                        print(f"CLIENT: Error sending message: {e}")
                        break

            print("CLIENT: Starting read Thread")
            asyncio.create_task(read_incoming())
            print("CLIENT: Starting send Thread")
            asyncio.create_task(send_outbound())
            print("CLIENT: Connection established, waiting for messages...")
            await asyncio.Future()  # Keep the connection open

    asyncio.run(connect())


def _check_server(uri):
    async def check():
        try:
            async with ws.connect(uri) as websocket:
                print(f"CLIENT: Server at {uri} is reachable")
                await websocket.close()
                return True
        except ws.ConnectionClosedError:
            print(f"CLIENT: Server at {uri} is not reachable")
            return False
        except Exception as e:
            return False

    return asyncio.run(check())


def start_client(uri):
    if not uri.startswith("ws://") and not uri.startswith("wss://"):
        raise ValueError("URI must start with 'ws://' or 'wss://'")
    if _check_server(uri):
        _connect_to_server(uri)


def get_arp_ips():
    arp_ips = set()
    arp_ips.add(socket.gethostbyname(socket.gethostname()))  # Add local IP
    arp_ips.add("localhost")  # Add localhost for good measure
    try:
        output = subprocess.check_output("arp -a", shell=True, encoding="utf-8")
        # Regex for IPv4 addresses
        ip_pattern = re.compile(r"(\d{1,3}(?:\.\d{1,3}){3})")
        for line in output.splitlines():
            match = ip_pattern.search(line)
            if match:
                arp_ips.add(match.group(1))
    except Exception as e:
        print(f"Error reading ARP table: {e}")
    return list(arp_ips)


def search_servers(port):
    found = []
    ips = get_arp_ips()
    threads = []
    lock = threading.Lock()

    def check_ip(ip):
        uri = f"ws://{ip}:{port}"
        try:
            if _check_server(uri):
                with lock:
                    found.append(uri)
        except Exception as e:
            pass

    for ip in ips:
        t = threading.Thread(target=check_ip, args=(ip,))
        t.start()
        threads.append(t)

    for t in threads:
        t.join()

    return found


if __name__ == "__main__":
    print("Searching for servers...")
    servers = search_servers(7050)
    for srv in servers:
        print(f"Found server: {srv}")
    print("Done, found servers:", servers)
