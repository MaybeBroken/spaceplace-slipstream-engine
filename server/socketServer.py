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
        else:
            print(f"SERVER: Target client not found: {target_client}")
    else:
        for wsock, q in clients.items():
            q.put(message)


def iter_messages():
    val = inbound.copy()
    inbound.clear()
    if not val:
        return []
    # Return (websocket, message) tuples for serverApp to know the sender
    return [(wsock, json.loads(msg)) for wsock, msg in val]


def register_client(client):
    clients[client] = queue.Queue()
    print(f"SERVER: Client registered: {client.remote_address}")


def unregister_client(client):
    if client in clients:
        clients.pop(client, None)
        if disconnect_callback:
            disconnect_callback()
        print(f"SERVER: Client unregistered: {client.remote_address}")


disconnect_callback = lambda: None


def register_disconnect_callback(callback):
    """
    Register a callback function to be called when the client disconnects.
    The callback should accept no arguments.
    """

    def disconnect_handler():
        print("WS override => Connection closed")
        callback()

    # Override the default connection closed handler
    global disconnect_callback
    disconnect_callback = disconnect_handler


async def handle_client(websocket):

    async def read_incoming():
        while True:
            try:
                message = await websocket.recv()
                if message == "WS_CLIENT_REGISTER":
                    register_client(websocket)
                elif message:
                    inbound.append((websocket, message))
            except ws.ConnectionClosed:
                print(f"SERVER: Connection closed by client {websocket.remote_address}")
                unregister_client(websocket)
                break
            except Exception as e:
                print(f"SERVER: Error handling client {websocket.remote_address}: {e}")
                unregister_client(websocket)
                break

    async def send_outbound():
        while True:
            if websocket not in clients:
                await asyncio.sleep(1 / 30)
                continue
            q = clients[websocket]
            try:
                if not q.empty():
                    message = q.get()
                    await websocket.send(message)
                else:
                    await asyncio.sleep(1 / 60)
            except ws.ConnectionClosed:
                print(
                    f"SERVER: Connection closed while sending to {websocket.remote_address}"
                )
                unregister_client(websocket)
                break
            except Exception as e:
                print(
                    f"SERVER: Error sending message to {websocket.remote_address}: {e}"
                )
                unregister_client(websocket)
                break

    asyncio.create_task(read_incoming())
    asyncio.create_task(send_outbound())
    print("SERVER: Connection established, waiting for messages...")
    await asyncio.Future()  # Keep the connection open


async def main(ip, port):
    server = await ws.serve(handle_client, ip, port)
    print(f"SERVER: WebSocket server started on ws://{ip}:{port}")
    try:
        await asyncio.Future()  # Run forever
        print("SERVER: Server shutting down...")
    except KeyboardInterrupt:
        print("SERVER: Server shutting down...")
        server.close()
        await server.wait_closed()


def launch_server(ip, port):
    threading.Thread(target=lambda: asyncio.run(main(ip, port)), daemon=True).start()


if __name__ == "__main__":
    launch_server("localhost", 7050)
    while True:
        sleep(1)
