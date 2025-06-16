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
            asyncio.run(self.async_connect(GRAPHQL_URL))
        except KeyboardInterrupt:
            print("Connection interrupted by user.")
            sys.exit(0)

    async def async_connect(self, GRAPHQL_URL):
        await ping_url(GRAPHQL_URL)
        transport = AIOHTTPTransport(url=GRAPHQL_URL)
        self.session = Client(
            transport=transport,
            fetch_schema_from_transport=True,
        )

        registerClient = gql(
            """
                mutation RegisterClient {
    clientConnect(client: "Slipstream Engine", mobile: true, cards: ["Slipstream Core"])
    }
            """
        )

        result = await self.session.execute_async(registerClient)

        getSimulatorId = gql(
            """query SimulatorId {
    clients(clientId:"Slipstream Engine") {
        simulator {
        id
        }
    }
}"""
        )

        result = await self.session.execute_async(getSimulatorId)
        self.simulatorId = result["clients"][0]["simulator"]["id"]
        print(f"Simulator ID: {self.simulatorId}")

        getThrustersId = gql(
            f"""query GetThrusterId {{
    thrusters(simulatorId:"{self.simulatorId}") {{
        id
    }}
}}"""
        )

        result = await self.session.execute_async(getThrustersId)
        self.thrusterIds = [thruster["id"] for thruster in result["thrusters"]]
        print(f"Thruster IDs: {self.thrusterIds}")

    async def async_set_thruster_rotation(self, pitch, roll, yaw):
        rotation_fields = []
        if pitch != None:
            rotation_fields.append(f"pitch: {pitch}")
        if roll != None:
            rotation_fields.append(f"roll: {roll}")
        if yaw != None:
            rotation_fields.append(f"yaw: {yaw}")
        rotation_str = ", ".join(rotation_fields)
        setThrusterDirection = gql(
            f"""mutation setThrusterDirection {{
        rotationSet(id:"{self.thrusterIds[0]}", rotation: {{
        {rotation_str}
        }})
    }}"""
        )
        result = await self.session.execute_async(setThrusterDirection)

    async def async_set_thruster_direction(self, x, y, z):
        setThrusterDirection = gql(
            f"""mutation setThrustersPos {{
    directionUpdate(
      id: "{self.thrusterIds[0]}",
        direction: {{
          x:{x}
          y:{y}
          z:{z}
        }}
    )
            }}"""
        )
        result = await self.session.execute_async(setThrusterDirection)
        return result

    async def async_get_thruster_loc_rot(self):
        getThrusterLocRot = gql(
            f"""query getThrusters {{
    thrusters(simulatorId: "{self.simulatorId}") {{
      direction{{
        x
        y
        z
    }}
      rotation {{
        roll
        pitch
        yaw
      }}
  }}
}}"""
        )
        result = await self.session.execute_async(getThrusterLocRot)
        return result["thrusters"][0]["direction"], result["thrusters"][0]["rotation"]

    async def async_get_thruster_info(self):
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

        result = await self.session.execute_async(getThrusterInfo)
        return result["thruster"]

    def get_thruster_info(self):
        return asyncio.run(self.async_get_thruster_info())

    def get_thruster_loc_rot(self):
        return asyncio.run(self.async_get_thruster_loc_rot())

    def set_thruster_rotation(self, pitch=None, roll=None, yaw=None):
        asyncio.run(self.async_set_thruster_rotation(pitch, roll, yaw))

    def set_thruster_direction(self, x, y, z):
        asyncio.run(self.async_set_thruster_direction(x, y, z))

    def get_thruster_ids(self):
        return self.thrusterIds

    def get_simulator_id(self):
        return self.simulatorId

    def get_session(self):
        return self.session


if __name__ == "__main__":
    conn = Connection()
    rot = (0, 0, 0)
    while True:
        sleep(1 / 60)
        rot = tuple(map(lambda x: x + 1, rot))
        asyncio.run(conn.async_set_thruster_rotation(*rot))
