import json
import struct
import unittest
from backend.context_archive_fixture import generated_atlas_archive, ATLAS_FIXTURE_PATH

class GeneratedAtlasArchiveTests(unittest.TestCase):
    def test_fixture_header_offsets_and_metadata(self):
        data=generated_atlas_archive()
        self.assertEqual(data,generated_atlas_archive())
        self.assertEqual(data[:8],b"PMTiles\x03")
        root,rootlen,meta,metalen,leaf,leaflen,tile,tilelen,addresses,entries,contents=struct.unpack_from("<11Q",data,8)
        self.assertEqual((root,leaf,leaflen,tile,addresses,entries,contents),(127,16384,0,16384,1,1,1))
        self.assertEqual(root+rootlen,meta)
        self.assertEqual(tile+tilelen,len(data))
        self.assertEqual(data[96:102],bytes([1,1,1,1,0,0]))
        self.assertEqual([layer["id"] for layer in json.loads(data[meta:meta+metalen])["vector_layers"]],["water","landuse","roads"])
        self.assertTrue(ATLAS_FIXTURE_PATH.endswith(".pmtiles"))
