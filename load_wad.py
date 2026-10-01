from os import wait
import struct
from dataclasses import dataclass
import duckdb

con = duckdb.connect("doom.duckdb")

#Logging tags
LUMP_TAG              = "[LUMP_READER]"
MAP_TAG               = "[MAP_READER]"
#Function logging 
LOAD_LINEDEF_LUMP_TAG = "[f_load_linedef_lump]"
LOAD_SIDEDEF_LUMP_TAG = "[f_load_sidedef_lump]"
LOAD_VERTEX_LUMP_TAG  = "[f_load_vertex_lump]"

# Struct reading shortcuts
# LE = little endian, S = signed, U = unsinged
# Number represents num bits
LE_32_U = "<I"
LE_16_S = "<h"
LE_64_S = "<8s"


MAP_NAMES = []
LUMPS     = []
MAPS      = []



# Sizes
LINEDEF_SIZE_BYTES = 14
SIDEDEF_SIZE_BYTES = 30
VERTEX_SIZE_BYZES  = 4


@dataclass
class Lump:
    name:   str
    offset: int
    size:   int
    index:  int

#https://doom.fandom.com/wiki/Linedef
@dataclass 
class Linedef:
    map_id:        int
    index:         int
    start_vertex:  int
    end_vertex:    int
    flags:         int
    special_type:  int
    sector_tag:    int
    right_sidedef: int
    left_sidedef:  int

# https://doom.fandom.com/wiki/Sidedef
@dataclass 
class Sidedef:
    map_id:              int
    index:               int
    x_offset:            int
    y_offset:            int
    name_upper_texture:  str
    name_lower_texture:  str 
    name_middle_texture: str
    faces_sector:        int

# https://doom.fandom.com/wiki/Vertex
@dataclass 
class Vertex:
    map_id: int
    index:  int
    x_pos:  int
    y_pos:  int

@dataclass 
class Map:
    id:       int
    linedefs: list[Linedef]
    sidedefs: list[Sidedef]
    vertices: list[Vertex]



# Map name format ExMy
# x can take on values from 1 to 4 
# y can take on values from 1 to 9
def compute_map_names():
    for i in range(1,5):
        for j in range(1,10):
            name = f"E{i}M{j}"
            MAP_NAMES.append(name)

def lump_is_map(lump_name):
    return lump_name in MAP_NAMES

#Not relevant yet
def load_things_lump(lump):
    pass

def load_linedef_lump(lump, wad, map_id):
    assert lump.size % LINEDEF_SIZE_BYTES == 0 # Check for malformed data
    linedefs = []
    wad.seek(lump.offset)
    num_members = lump.size // LINEDEF_SIZE_BYTES
    print(f"{LOAD_LINEDEF_LUMP_TAG} loading {lump.name}")
    print(f"{LOAD_LINEDEF_LUMP_TAG} num_linedefs: {num_members}")

    for i in range(num_members):
        linedef = Linedef(
                map_id= map_id,
                index= i, 
                start_vertex=struct.unpack(LE_16_S, wad.read(2))[0],
                end_vertex=struct.unpack(LE_16_S, wad.read(2))[0],
                flags=struct.unpack(LE_16_S, wad.read(2))[0],
                special_type=struct.unpack(LE_16_S, wad.read(2))[0],
                sector_tag=struct.unpack(LE_16_S, wad.read(2))[0],
                right_sidedef=struct.unpack(LE_16_S, wad.read(2))[0],
                left_sidedef=struct.unpack(LE_16_S, wad.read(2))[0]
                )
        linedefs.append(linedef)

    return linedefs


def load_sidedef_lump(lump,wad,map_id):
    assert lump.size % SIDEDEF_SIZE_BYTES == 0 # Check for malformed data 
    sidedefs = []

    wad.seek(lump.offset) 
    num_members = lump.size // SIDEDEF_SIZE_BYTES

    print(f"{LOAD_SIDEDEF_LUMP_TAG} num_sidedefs : {num_members}")

    for i in range(num_members):
        sidedef = Sidedef(
                map_id=map_id,
                index= i,
                x_offset= struct.unpack(LE_16_S, wad.read(2))[0],
                y_offset= struct.unpack(LE_16_S, wad.read(2))[0],
                name_upper_texture= struct.unpack(LE_64_S, wad.read(8))[0].rstrip(b"\x00").decode("ascii"),
                name_lower_texture= struct.unpack(LE_64_S, wad.read(8))[0].rstrip(b"\x00").decode("ascii"),
                name_middle_texture= struct.unpack(LE_64_S, wad.read(8))[0].rstrip(b"\x00").decode("ascii"),
                faces_sector= struct.unpack(LE_16_S, wad.read(2))[0]
                )
        sidedefs.append(sidedef)
    return sidedefs


def load_vertex_lump(lump,wad,map_id):
    assert lump.size % VERTEX_SIZE_BYZES == 0 # Check for malformed data 
    vertices = [] 

    wad.seek(lump.offset)
    num_members = lump.size // VERTEX_SIZE_BYZES
    print(f"{LOAD_VERTEX_LUMP_TAG} num vertices {num_members}")

    for i in range(num_members):
        vertex = Vertex(
                map_id=map_id,
                index = i,
                x_pos= struct.unpack(LE_16_S, wad.read(2))[0],
                y_pos= struct.unpack(LE_16_S, wad.read(2))[0]
                )
        vertices.append(vertex)



    return vertices






###############################################################################

compute_map_names()
# https://doom.fandom.com/wiki/WAD
with open("DOOM1.WAD","rb") as wad:
    # Extract header, byter order little endian
    identification = wad.read(4).decode("ascii")
    num_lumps = struct.unpack(LE_32_U, wad.read(4))[0]
    table_offsets = struct.unpack(LE_32_U, wad.read(4))[0]

    print(f"{LUMP_TAG} Loading {identification}\nnum_lumps:{num_lumps}")

    wad.seek(table_offsets)

    # WAD lump directory entry (16 bytes total):
    # 0x00-0x03: file position of lump data
    # 0x04-0x07: lump size in bytes
    # 0x08-0x0F: 8-byte ASCII lump name, null-padded on the right
    for i in range(num_lumps):
        file_pos = struct.unpack(LE_32_U, wad.read(4))[0]
        lump_size = struct.unpack(LE_32_U, wad.read(4))[0]
        # Remove null padding
        lump_name = wad.read(8).rstrip(b"\x00").decode("ascii", errors="replace")

        LUMPS.append(Lump(name= lump_name,offset=file_pos,size=lump_size, index = i))

    map_lumps = [i for i in LUMPS if i.name in MAP_NAMES]


    # Once a Map Lump is encountered the order of the following lumps is well
    # defined.
    # 1. THINGS (https://doom.fandom.com/wiki/Thing)
    # 2. LINEDEFS (https://doom.fandom.com/wiki/Linedef)
    # 3. SIDEDEFS (https://doom.fandom.com/wiki/Sidedef)
    # 4. VERTEXES (https://doom.fandom.com/wiki/Vertex)
    # 5. SEGS     (https://doom.fandom.com/wiki/Seg)
    # 6. SSECTORS (https://doom.fandom.com/wiki/Subsector)
    # 7. NODES    (https://doom.fandom.com/wiki/Node)
    # 8. SECTORS  (https://doom.fandom.com/wiki/Sector)
    # 9. REJECT   (https://doom.fandom.com/wiki/Reject)
    # 10. BLOCKMAP (https://doom.fandom.com/wiki/Blockmap)
    # 11. BEHAVIOR  (https://doom.fandom.com/wiki/Behavior)
    for map_id, lump in enumerate(map_lumps):
        print(f"{MAP_TAG} loading map {lump.name}")
        things_lump = LUMPS[lump.index + 1]
        load_things_lump(things_lump)

        linedef_lump = LUMPS[lump.index + 2]
        linedefs = load_linedef_lump(linedef_lump,wad, map_id)

        sidedef_lump = LUMPS[lump.index + 3]
        sidedefs = load_sidedef_lump(sidedef_lump, wad, map_id)

        vertex_lump = LUMPS[lump.index + 4]
        vertices = load_vertex_lump(vertex_lump, wad, map_id)

        MAPS.append(Map(id= map_id, linedefs=linedefs,sidedefs=sidedefs,
                        vertices=vertices))


con.execute("DROP TABLE IF EXISTS linedefs")
con.execute("DROP TABLE IF EXISTS sidedefs")
con.execute("DROP TABLE IF EXISTS vertices")

con.execute("""
CREATE TABLE IF NOT EXISTS vertices (
    map_id INTEGER,
    id INTEGER,
    x INTEGER,
    y INTEGER,
    PRIMARY KEY (map_id, id)
);

CREATE TABLE IF NOT EXISTS linedefs (
    map_id INTEGER,
    id INTEGER,
    v1_id INTEGER,
    v2_id INTEGER,
    flags INTEGER,
    special INTEGER,
    tag INTEGER,
    right_sidedef INTEGER,
    left_sidedef INTEGER,
    PRIMARY KEY (map_id, id)
);

CREATE TABLE IF NOT EXISTS sidedefs (
    map_id INTEGER,
    id INTEGER,
    x_offset INTEGER,
    y_offset INTEGER,
    upper_texture VARCHAR,
    lower_texture VARCHAR,
    middle_texture VARCHAR,
    sector_id INTEGER,
    PRIMARY KEY (map_id, id)
);
""")

con.execute("BEGIN")

for m in MAPS:
    con.executemany(
        "INSERT INTO vertices VALUES (?, ?, ?, ?)",
        [
            (
                v.map_id,
                v.index,
                v.x_pos,
                v.y_pos
            )
            for v in m.vertices
        ]
    )

    con.executemany(
        "INSERT INTO linedefs VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
        [
            (
                l.map_id,
                l.index,
                l.start_vertex,
                l.end_vertex,
                l.flags,
                l.special_type,
                l.sector_tag,
                l.right_sidedef,
                l.left_sidedef
            )
            for l in m.linedefs
        ]
    )

    con.executemany(
        "INSERT INTO sidedefs VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
        [
            (
                s.map_id,
                s.index,
                s.x_offset,
                s.y_offset,
                s.name_upper_texture,
                s.name_lower_texture,
                s.name_middle_texture,
                s.faces_sector
            )
            for s in m.sidedefs
        ]
    )

con.execute("COMMIT")


with open("wads.sql", "r") as f:
    query = f.read()

for map_id, lump in enumerate(map_lumps):
    print(f"\n{MAP_TAG} drawing map {lump.name}")

    result = con.execute(query, [map_id]).fetchall()

    for row in result:
        print(row[0])

