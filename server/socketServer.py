import direct.stdpy.threading as threading
from time import sleep
import websockets as ws
import asyncio

inbound = []
outbound = []
clients = set()


def broadcast(message):
    for client in clients:
        asyncio.create_task(client.send(message))


def iter_messages():
    val = inbound.copy()
    inbound.clear()
    return iter(val)


def register_client(client):
    clients.add(client)
    print(f"Client registered: {client.remote_address}")


def unregister_client(client):
    clients.discard(client)
    print(f"Client unregistered: {client.remote_address}")


async def handle_client(websocket):
    register_client(websocket)
    while True:
        try:
            message = await websocket.recv()
            inbound.append(message)
        except ws.ConnectionClosed:
            pass
        except Exception as e:
            print(f"Error handling client {websocket.remote_address}: {e}")
        finally:
            unregister_client(websocket)
            break


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
