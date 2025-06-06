import asyncio
from time import sleep
from gql import Client, gql
from gql.transport.aiohttp import AIOHTTPTransport
import sys
import aiohttp
import json


async def ping_url(url):
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as resp:
                if resp.status != 200:
                    print(f"Error: Unable to reach {url}, status code {resp.status}")
                    sys.exit(1)
                else:
                    print(f"Success: {url} is reachable, status code {resp.status}")
    except Exception as e:
        print(f"Error: Unable to reach {url} ({e})")
        sys.exit(1)


class Connection:
    def __init__(self, GRAPHQL_URL="http://localhost:4444/graphql"):
        try:
            asyncio.run(self.connect(GRAPHQL_URL))
        except KeyboardInterrupt:
            print("Connection interrupted by user.")
            sys.exit(0)

    async def connect(self, GRAPHQL_URL):
        await ping_url(GRAPHQL_URL)
        transport = AIOHTTPTransport(url=GRAPHQL_URL)
        async with Client(
            transport=transport,
            fetch_schema_from_transport=True,
        ) as self.session:

            registerClient = gql(
                """
                mutation RegisterClient {
    clientConnect(client: "Slipstream Engine", mobile: true, cards: ["Slipstream Core"])
    }
            """
            )

            result = await self.session.execute(registerClient)

            getSimulatorId = gql(
                """query SimulatorId {
    clients(clientId:"Slipstream Engine") {
        simulator {
        id
        }
    }
}"""
            )

            result = await self.session.execute(getSimulatorId)
            self.simulatorId = result["clients"][0]["simulator"]["id"]
            print(f"Simulator ID: {self.simulatorId}")

            getThrustersId = gql(
                f"""query GetThrusterId {{
    thrusters(simulatorId:"{self.simulatorId}") {{
        id
    }}
}}"""
            )

            result = await self.session.execute(getThrustersId)
            self.thrusterIds = [thruster["id"] for thruster in result["thrusters"]]
            print(f"Thruster IDs: {self.thrusterIds}")

    async def set_thruster_direction(self, pitch, roll, yaw):
        setThrusterDirection = gql(
            f"""mutation setThrusterDirection {{
    rotationSet(id:"{self.thrusterIds[0]}", rotation: {{
        pitch: {pitch},
        roll: {roll},
        yaw: {yaw}
    }})
}}"""
        )

        await self.session.execute(
            setThrusterDirection,
        )

    async def get_thruster_info(self):
        getThrusterInfo = gql(
            f"""query GetThrusterInfo {{
  thruster(id: "{self.thrusterIds[0]}") {{
    id
    type
    direction {{
      x
      y
      z
    }}
    rotation {{
      yaw
      pitch
      roll
    }}
    rotationDelta {{
      yaw
      pitch
      roll
    }}
    rotationRequired {{
      yaw
      pitch
      roll
    }}
    manualThrusters
    power {{
      power
      powerLevels
      defaultLevel
    }}
    rotationSpeed
    movementSpeed
  }}
}}
            """
        )

        result = await self.session.execute(getThrusterInfo)
        return result["thruster"]


if __name__ == "__main__":
    Connection()
