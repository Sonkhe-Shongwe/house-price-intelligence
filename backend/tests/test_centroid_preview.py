import unittest
from backend.centroid_preview import relative_points
class CentroidProjectionTests(unittest.TestCase):
    def test_offsets_preserve_order_and_quantise(self):
        p,reason=relative_points([(0,2024,42.04,-87.68),(1,2023,42.042,-87.683)])
        self.assertIsNone(reason)
        self.assertEqual(p,[{"rank":0,"assessment_year":2024,"offset_x":0,"offset_y":0},
                            {"rank":1,"assessment_year":2023,"offset_x":-3,"offset_y":2}])
    def test_missing_overlap_and_extent_abstain(self):
        for lat,lon,reason in [(None,None,"missing_geometry"),(42.0401,-87.6801,"overlapping_centroids"),(42.08,-87.68,"outside_schematic_extent")]:
            with self.subTest(reason=reason):
                self.assertEqual(relative_points([(0,2024,42.04,-87.68),(1,2023,lat,lon)]),([],reason))
