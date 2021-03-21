import sys
import grpc
sys.path.append("Evocraft-py")
import minecraft_pb2_grpc
from minecraft_pb2 import *
import random
import time

channel = grpc.insecure_channel('localhost:5001')
client = minecraft_pb2_grpc.MinecraftServiceStub(channel)

class Vector3:
    def __init__(self, x, y, z):
        self.x = x
        self.y = y
        self.z = z
    def to_point(self):
        return Point(x = self.x, y = self.y, z = self.z)

    def surrounding(self):
        result = []
        for x in range(-1, 2):
            for y in range(-1, 2):
                for z in range(-1, 2):
                    (nx, ny, nz) = (self.x + x, self.y + y, self.z + z)
                    if(x == 0 and y == 0 and z == 0): continue
                    if(nx > Space.MAX_POSITION.x or ny > Space.MAX_POSITION.y or nz > Space.MAX_POSITION.z): continue
                    if(nx < Space.MIN_POSITION.x or ny < Space.MIN_POSITION.y or nz < Space.MIN_POSITION.z): continue
                    result.append(Vector3(nx, ny, nz))
        return result
    def __str__(self):
        return "%s,%s,%s" % (self.x, self.y, self.z)
        
class Space:
    MAX_POSITION = Vector3(40, 44, 40)
    MIN_POSITION = Vector3(0, 4, 0)
    @classmethod
    def random(cls, min = MIN_POSITION, max = MAX_POSITION):
        return Vector3(
            random.randrange(cls.MIN_POSITION.x, cls.MAX_POSITION.x),
            random.randrange(cls.MIN_POSITION.y, cls.MAX_POSITION.y),
            random.randrange(cls.MIN_POSITION.z, cls.MAX_POSITION.z)
        )

class UnitThreshold:
    BORN = range(6, 8)
    SURVIVE = range(6, 10)
    OVERCROWDING = range(10, 27)
    UNDERCROWDING = range(0, 6)

class Unit:
    def __init__(self, position, block_type = ICE, is_death = False):
        self.position = position
        self.block_type = block_type
        self.is_death = is_death
    
def write(units):
    blocks = [
        Block(position=u.position.to_point(), type=u.block_type, orientation=NORTH) 
        if not u.is_death else Block(position=u.position.to_point(), type=AIR, orientation=NORTH) 
        for u in units.values()
    ]
    client.spawnBlocks(Blocks(blocks=blocks))

def clear():
    client.fillCube(FillCubeRequest(
        cube=Cube(
            min=Space.MIN_POSITION.to_point(),
            max=Space.MAX_POSITION.to_point()
        ),
        type=AIR
    ))

def next_units(units):
    nexts = {}
    for u in units.values():
        if(u.is_death): continue
        living = 0
        related_units_surrouding = set()
        for surrouding_pos in u.position.surrounding():
            if str(surrouding_pos) in units.keys() and not units[str(surrouding_pos)].is_death:
                sr = units[str(surrouding_pos)].position.surrounding()
                if(len(related_units_surrouding) == 0):
                    related_units_surrouding = set(sr)
                else:
                    related_units_surrouding &= set(sr)
                living += 1
        if(living in UnitThreshold.BORN):
            for b in related_units_surrouding:
                nexts[str(b)] = Unit(position=b)
        if(living in UnitThreshold.SURVIVE):
            nexts[str(u.position)] = u
        if(living in UnitThreshold.OVERCROWDING or living in UnitThreshold.UNDERCROWDING ):
            u.is_death = True
            nexts[str(u.position)] = u
    return nexts

def main():
    init_units = [ Unit(Space.random()) for _ in range(0, 5000)]
    units = {str(u.position): u for u in init_units}
    for i in range(100):
        if(i < 15): time.sleep(2.0)
        print("episode: {}", i)
        write(units)
        units = next_units(units)

if __name__ == "__main__":
    if(len(sys.argv) > 1 and sys.argv[1] == "clear"):
        clear()
    else:
        main()