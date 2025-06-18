import opensimplex as opsx


class WorldGen:
    def __init__(
        self, threshold, P3D_CAMERA, chunk_size=16, voxel_scale=1, noise_scale=1
    ):
        self.threshold = threshold
        self.GENERATED_CHUNKS: dict[tuple[int, int], list[tuple[int, int, float]]] = {}
        self.CHUNK_SIZE = chunk_size
        self.P3D_CAMERA = P3D_CAMERA
        self.VOX_SC = voxel_scale
        self.NOISE_SCALE = noise_scale / voxel_scale

    def get_noise_point(self, x, y, z, seed):
        opsx.seed(seed=seed)
        scalar = 6 * self.NOISE_SCALE
        return opsx.noise4(x=x / scalar, y=y / scalar, z=0, w=z / scalar)

    def generate_chunk(self, x, y, threshold):
        chunk = []
        for i in range(0, self.CHUNK_SIZE, self.VOX_SC):
            for j in range(0, self.CHUNK_SIZE, self.VOX_SC):
                noise = self.get_noise_point(
                    (x * self.CHUNK_SIZE) + i, (y * self.CHUNK_SIZE) + j, 0, 0
                )
                if noise > threshold:
                    chunk.append((i, j, noise))
        return chunk


class WorldManager:
    def __init__(self, WorldGen: WorldGen, P3D_CAMERA, renderDistance=2):
        self.WorldGen = WorldGen
        self.P3D_CAMERA = P3D_CAMERA
        self.renderDistance: int = renderDistance
        self.activeChunks = set()
        self.lastActiveChunks = set()
        self.newChunks = set()
        self.lastNewChunks = set()

    def update(self):
        activeChunk = self.P3D_CAMERA.getPos() // self.WorldGen.CHUNK_SIZE
        activeChunk = [int(activeChunk[0]), int(activeChunk[1])]
        for x in range(
            activeChunk[0] - self.renderDistance,
            activeChunk[0] + self.renderDistance + 1,
        ):
            for y in range(
                activeChunk[1] - self.renderDistance,
                activeChunk[1] + self.renderDistance + 1,
            ):
                if (x, y) in self.WorldGen.GENERATED_CHUNKS:
                    self.activeChunks.add((x, y))
                else:
                    self.WorldGen.GENERATED_CHUNKS[(x, y)] = (
                        self.WorldGen.generate_chunk(x, y, self.WorldGen.threshold)
                    )
                    self.newChunks.add((x, y))

        for x, y in self.activeChunks.copy():
            if (
                x < activeChunk[0] - self.renderDistance
                or x > activeChunk[0] + self.renderDistance
                or y < activeChunk[1] - self.renderDistance
                or y > activeChunk[1] + self.renderDistance
            ):
                self.activeChunks.remove((x, y))
