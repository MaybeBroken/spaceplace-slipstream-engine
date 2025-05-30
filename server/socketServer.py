import direct.stdpy.threading as threading
from time import sleep
import websockets as ws
import asyncio
import json
import queue

inbound = []
clients = {}  # websocket -> outbound queue


def send_message(message, target_client=None):
    try:
        message = json.dumps(message)
    except Exception as e:
        raise ValueError("Message must be a JSON encodable object") from e
    if target_client:
        if target_client in clients:
            clients[target_client].put(message)
            print(
                f"Added message to outbound queue for {target_client.remote_address}: {message}"
            )
        else:
            print(f"Target client not found: {target_client}")
    else:
        for wsock, q in clients.items():
            q.put(message)
            print(f"Added message to outbound queue for {wsock.remote_address}: {message}")


def iter_messages():
    val = inbound.copy()
    inbound.clear()
    if not val:
        return []
    # Return (websocket, message) tuples for serverApp to know the sender
    return [(wsock, json.loads(msg)) for wsock, msg in val]


def register_client(client):
    clients[client] = queue.Queue()
    print(f"Client registered: {client.remote_address}")


def unregister_client(client):
    clients.pop(client, None)
    print(f"Client unregistered: {client.remote_address}")


async def handle_client(websocket):
    register_client(websocket)

    async def read_incoming():
        while True:
            try:
                message = await websocket.recv()
                if message:
                    inbound.append((websocket, message))
                    print(
                        f"Received message from {websocket.remote_address}: {message}"
                    )
            except ws.ConnectionClosed:
                print(f"Connection closed by client {websocket.remote_address}")
                unregister_client(websocket)
                break
            except Exception as e:
                print(f"Error handling client {websocket.remote_address}: {e}")
                unregister_client(websocket)
                break

    async def send_outbound():
        q = clients[websocket]
        while True:
            try:
                if not q.empty():
                    message = q.get()
                    await websocket.send(message)
                    print(f"Sent message to {websocket.remote_address}: {message}")
                else:
                    await asyncio.sleep(0.1)
            except ws.ConnectionClosed:
                print(f"Connection closed while sending to {websocket.remote_address}")
                unregister_client(websocket)
                break
            except Exception as e:
                print(f"Error sending message to {websocket.remote_address}: {e}")
                unregister_client(websocket)
                break

    asyncio.create_task(read_incoming())
    asyncio.create_task(send_outbound())
    print("Connection established, waiting for messages...")
    await asyncio.Future()  # Keep the connection open


async def main(ip, port):
    server = await ws.serve(handle_client, ip, port)
    print(f"WebSocket server started on ws://{ip}:{port}")
    try:
        await asyncio.Future()  # Run forever
        print("Server shutting down...")
    except KeyboardInterrupt:
        print("Server shutting down...")
        server.close()
        await server.wait_closed()


def launch_server(ip, port):
    threading.Thread(target=lambda: asyncio.run(main(ip, port)), daemon=True).start()


if __name__ == "__main__":
    launch_server("localhost", 7050)
    while True:
        sleep(1)
