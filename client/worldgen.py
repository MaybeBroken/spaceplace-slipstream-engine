from time import time
import opensimplex as opsx


class WorldGen:
    def __init__(
        self, threshold, chunk_size=16, voxel_scale=1, noise_scale=1, seed=None
    ):
        self.threshold = threshold
        self.GENERATED_CHUNKS: dict[tuple[int, int], list[tuple[int, int, float]]] = {}
        self.CHUNK_SIZE = chunk_size * voxel_scale
        self.VOX_SC = voxel_scale
        self.NOISE_SCALE = noise_scale / self.VOX_SC
        self.seed = seed if seed is not None else int(time() * 1000)

    def set_seed(self, seed):
        self.seed = seed
        opsx.seed(seed=seed)

    def get_noise_point(self, x, y, z, seed):
        opsx.seed(seed=seed)
        scalar = 6 * self.NOISE_SCALE
        return (
            opsx.noise4(x=x / scalar, y=y / scalar, z=0, w=z / scalar)
            + opsx.noise4(x=x / scalar * 2, y=y / scalar * 2, z=1, w=z / scalar * 2)
        ) / 2

    def generate_chunk(self, x, y, threshold):
        chunk = []
        for i in range(0, self.CHUNK_SIZE, self.VOX_SC):
            for j in range(0, self.CHUNK_SIZE, self.VOX_SC):
                noise = self.get_noise_point(
                    (x * self.CHUNK_SIZE) + i, (y * self.CHUNK_SIZE) + j, 0, self.seed
                )
                if noise > threshold:
                    chunk.append((i, j, noise))
        return chunk


class WorldManager:
    def __init__(
        self, WorldGen: WorldGen, renderObject, renderDistance=2, scale_multiplier=1
    ):
        self.WorldGen = WorldGen
        self.voxelScale = WorldGen.VOX_SC
        self.renderObject = renderObject
        self.renderDistance: int = renderDistance * self.voxelScale
        self.activeChunks = set()
        self.lastActiveChunks = set()
        self.newChunks = set()
        self.lastNewChunks = set()
        self.generatedChunk = False
        self.scale_multiplier = scale_multiplier

    def update(self):
        self.generatedChunk = False
        activeChunk = (
            self.renderObject.getPos()
            // self.WorldGen.CHUNK_SIZE
            // self.scale_multiplier
        )
        activeChunk = [int(activeChunk[0]), int(activeChunk[1])]
        for x in range(
            activeChunk[0] - self.renderDistance,
            activeChunk[0] + self.renderDistance + 1,
        ):
            for y in range(
                activeChunk[1] - self.renderDistance,
                activeChunk[1] + self.renderDistance + 1,
            ):
                x, y = int(x / self.voxelScale), int(y / self.voxelScale)
                if not self.generatedChunk:
                    if (x, y) in self.WorldGen.GENERATED_CHUNKS:
                        self.activeChunks.add((x, y))
                    else:
                        self.WorldGen.GENERATED_CHUNKS[(x, y)] = (
                            self.WorldGen.generate_chunk(x, y, self.WorldGen.threshold)
                        )
                        self.newChunks.add((x, y))
                        self.generatedChunk = True

        for x, y in self.activeChunks.copy():
            if (
                x < activeChunk[0] - self.renderDistance
                or x > activeChunk[0] + self.renderDistance
                or y < activeChunk[1] - self.renderDistance
                or y > activeChunk[1] + self.renderDistance
            ):
                self.activeChunks.remove((x, y))
