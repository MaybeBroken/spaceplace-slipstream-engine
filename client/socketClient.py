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
            print(f"Connected to server at {uri}")
            while True:
                try:
                    for message in outbound:
                        print(f"Sending message: {message}")
                        await websocket.send(message)
                        print(f"Sent message: {message}")
                        outbound.remove(message)
                    response = await websocket.recv()
                    incoming.append(response)
                    print(f"Received message: {response}")
                except Exception as e:
                    print(f"Error processing data: {e}")
                    await asyncio.sleep(0.5)

    asyncio.run(connect())


def _check_server(uri):
    async def check():
        try:
            async with ws.connect(uri) as websocket:
                print(f"Server at {uri} is reachable")
                await websocket.close()
                return True
        except ws.ConnectionClosedError:
            print(f"Server at {uri} is not reachable")
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


def search_clients(port):
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
    print("Searching for clients...")
    clients = search_clients(7050)
    for cli in clients:
        print(f"Found client: {cli}")
    print("Done, found clients:", clients)
