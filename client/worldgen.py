from time import time
import random
import math
import hashlib


def fade(t):
    # Perlin's fade function for smoothing
    return t * t * t * (t * (t * 6 - 15) + 10)


def lerp(a, b, t):
    # Linear interpolation
    return a + t * (b - a)


def grad(hash, x, y):
    # Simple gradient function for 2D
    h = hash & 3
    u = x if h & 1 == 0 else -x
    v = y if h & 2 == 0 else -y
    return u + v


def hash_corner(a, b, seed):
    # Use a hash function with seed for more randomness
    s = f"{a}_{b}_{seed}".encode()
    h = hashlib.sha256(s).digest()
    return int.from_bytes(h[:4], "little")


def pseudo_perlin_noise2(x, y, seed=0):
    # Find unit square that contains point
    X = int(math.floor(x)) & 255
    Y = int(math.floor(y)) & 255

    # Find relative x, y of point in square
    xf = x - math.floor(x)
    yf = y - math.floor(y)

    # Compute fade curves for each coordinate
    u = fade(xf)
    v = fade(yf)

    # Hash coordinates of the 4 square corners
    corners = []
    for dx in [0, 1]:
        for dy in [0, 1]:
            hash_val = hash_corner(X + dx, Y + dy, seed)
            corners.append(grad(hash_val, xf - dx, yf - dy))

    # Interpolate along y
    l0 = lerp(corners[0], corners[1], v)
    l1 = lerp(corners[2], corners[3], v)
    value = lerp(l0, l1, u)
    # Normalize to [-1, 1]
    return value / 2.0


class opsx:
    _seed = 0

    @staticmethod
    def seed(seed=None):
        # Set a global seed for hashing
        if seed is not None:
            opsx._seed = seed
            random.seed(seed)
        else:
            opsx._seed = int(time() * 1000)
            random.seed(opsx._seed)

    @staticmethod
    def noise4(x, y, z=0, w=0):
        # Only use x and y for 2D noise, pass seed for randomness
        return pseudo_perlin_noise2(x, y, seed=opsx._seed)


class WorldGen:
    def __init__(
        self, threshold, chunk_size=16, voxel_scale=1, noise_scale=1, seed=None
    ):
        self.threshold = threshold
        self.GENERATED_CHUNKS: dict[tuple[int, int], list[tuple[int, int, float]]] = {}
        self.CHUNK_SIZE = chunk_size  # Remove scaling by voxel_scale
        self.VOX_SC = voxel_scale
        self.NOISE_SCALE = noise_scale
        self.seed = seed if seed is not None else int(time() * 1000)

    def set_seed(self, seed):
        self.seed = seed
        opsx.seed(seed=seed)

    def get_noise_point(self, x, y, seed):
        opsx.seed(seed=seed)
        scalar = 3 * self.NOISE_SCALE
        return opsx.noise4(x=x / scalar, y=y / scalar)

    def generate_chunk(self, x, y, threshold):
        chunk = []
        # Use voxel_scale only for step size, not for scaling chunk size
        for i in range(0, self.CHUNK_SIZE, self.VOX_SC):
            for j in range(0, self.CHUNK_SIZE, self.VOX_SC):
                noise = self.get_noise_point(
                    (x * self.CHUNK_SIZE) + i, (y * self.CHUNK_SIZE) + j, self.seed
                )
                if noise > threshold:
                    chunk.append((i, j, noise))
        return chunk


class WorldManager:
    def __init__(self, WorldGen: WorldGen, renderObject, renderDistance=2):
        self.WorldGen = WorldGen
        self.voxelScale = WorldGen.VOX_SC
        self.renderObject = renderObject
        self.renderDistance: int = renderDistance
        self.activeChunks = set()
        self.lastActiveChunks = set()
        self.newChunks = set()
        self.lastNewChunks = set()
        self.generatedChunks = 0

    def update(self):
        self.generatedChunks = 0
        pos = (
            self.renderObject.getPos()
            / self.voxelScale
            / self.WorldGen.CHUNK_SIZE
            / self.WorldGen.VOX_SC
        )
        activeChunk = [
            int(pos[0] / self.WorldGen.CHUNK_SIZE),
            int(pos[1] / self.WorldGen.CHUNK_SIZE),
        ]
        for x in range(
            activeChunk[0] - self.renderDistance,
            activeChunk[0] + self.renderDistance + 1,
        ):
            for y in range(
                activeChunk[1] - self.renderDistance,
                activeChunk[1] + self.renderDistance + 1,
            ):
                # Use x, y directly as chunk coordinates
                if self.generatedChunks < 3:
                    if (x, y) in self.WorldGen.GENERATED_CHUNKS:
                        self.activeChunks.add((x, y))
                    else:
                        self.WorldGen.GENERATED_CHUNKS[(x, y)] = (
                            self.WorldGen.generate_chunk(x, y, self.WorldGen.threshold)
                        )
                        self.newChunks.add((x, y))
                        self.generatedChunks += 1
                else:
                    pass
        for x, y in self.activeChunks.copy():
            if (
                x < activeChunk[0] - self.renderDistance
                or x > activeChunk[0] + self.renderDistance
                or y < activeChunk[1] - self.renderDistance
                or y > activeChunk[1] + self.renderDistance
            ):
                self.activeChunks.remove((x, y))
