"""Tiny generated PMTiles v3/MVT test fixture, no external data.

Writer only for one z0 tile with invented polygon/line geometry. Not a
general-purpose PMTiles parser/extractor or representation of any real place.
Spec: https://github.com/protomaps/PMTiles/blob/main/spec/v3/spec.md
"""
import json
import struct

ATLAS_FIXTURE_PATH = "/context/atlas-fixture-v1.pmtiles"


def _varint(n):
    out = bytearray()
    while n >= 128:
        out.append((n & 127) | 128)
        n >>= 7
    out.append(n)
    return bytes(out)


def _field(n, value):
    if isinstance(value, int):
        return _varint(n << 3) + _varint(value)
    return _varint(n << 3 | 2) + _varint(len(value)) + value


def _geometry(points, polygon):
    def zig(n):
        return n*2 if n >= 0 else -n*2-1
    out = [9, zig(points[0][0]), zig(points[0][1]),
           ((len(points)-1) << 3) | 2]
    for (x0,y0),(x,y) in zip(points, points[1:]):
        out += [zig(x-x0),zig(y-y0)]
    if polygon:
        out.append(15)
    return b"".join(_varint(n) for n in out)


def _layer(name, points, polygon):
    feature = _field(1, 1) + _field(3, 3 if polygon else 2) + _field(4, _geometry(points, polygon))
    layer = _field(1, name.encode()) + _field(2, feature) + _field(5, 4096) + _field(15, 2)
    return _field(3, layer)


def generated_atlas_archive():
    tile = (
        _layer("water", [(1800,1500),(2100,1500),(2180,2450),(1900,2500)], True)
        + _layer("landuse", [(2200,1800),(2600,1800),(2600,2220),(2200,2220)], True)
        + _layer("roads", [(1400,2000),(1850,2040),(2250,2080),(2800,2200)], False)
    )
    # One sorted tile entry: count, delta tile ID (z0=0), run length,
    # tile byte length, first tile data offset plus one.
    root = b"\x01\x00\x01" + _varint(len(tile)) + b"\x01"
    metadata = json.dumps({"name":"Invented Atlas vector fixture","description":"No real geography",
        "vector_layers":[{"id":name,"fields":{},"minzoom":0,"maxzoom":0}
                         for name in ("water","landuse","roads")]},
        separators=(",",":")).encode()
    header = bytearray(127)
    header[:8] = b"PMTiles\x03"
    # Standard fixed header and first 16 KiB root-read window; no leaf
    # directories, uncompressed internal metadata and MVT payload.
    struct.pack_into("<11Q",header,8,127,len(root),127+len(root),len(metadata),
                     16384,0,16384,len(tile),1,1,1)
    header[96:102] = bytes([1,1,1,1,0,0])
    struct.pack_into("<4i",header,102,-1800000000,-850000000,1800000000,850000000)
    header[118] = 0
    struct.pack_into("<2i",header,119,0,0)
    prefix = bytes(header)+root+metadata
    return prefix.ljust(16384,b"\x00")+tile
