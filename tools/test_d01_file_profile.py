"""Invented-only offline sales profiling tests."""
import csv
import io
import json
import unittest
from unittest.mock import patch
from tools import d01_file_profile as p


def fixture():
    return [
        ["INVENTED-1","Invented PINELANDS","123 PINELANDS","500","150","2024/01/01","R 1,000,000"],
        ["INVENTED-1","Invented PINELANDS","123 PINELANDS","500","150","2025/01/01","R 1200000"],
        ["INVENTED-2","Invented PINELANDS","SS123/2000-1","20","","2025/01/01","R 0"],
        ["INVENTED-3","Invented OTHER","Other","bad","-1","2027/01/01","bad"]
    ]


def csv_bytes(rows,headers=p.HEADERS):
    out=io.StringIO(newline="")
    csv.writer(out).writerows([headers,*rows])
    return out.getvalue().encode("utf-8-sig")


class SaleTests(unittest.TestCase):
    def test_profile_quality(self):
        with patch.object(p,"EXPECTED",4):
            q=p.profile(csv_bytes(fixture()))
        self.assertEqual(q["rows"],4)
        self.assertEqual(q["price_quality"],{"positive":2,"zero":1,"invalid":1})
        self.assertEqual(q["references_with_multiple_valid_sale_dates"],1)
        self.assertEqual(q["exact_duplicate_rows"]["groups"],0)
        self.assertEqual(q["description_patterns"]["sectional_style"],1)
        self.assertEqual(q["sale_date_quality"]["future"],1)
        self.assertEqual(q["preliminary_erf_sale_rows_before_duplicate_review"],2)
        self.assertEqual(q["preliminary_erf_sale_rows_with_positive_both_extents"],2)
        self.assertNotIn("INVENTED-1",json.dumps(q))

    def test_duplicate_not_same_as_repeat_sale(self):
        rows=fixture()
        rows.append(rows[0][:])
        conflict=rows[0][:]
        conflict[-1]="R 1300000"
        rows.append(conflict)
        with patch.object(p,"EXPECTED",6):
            q=p.profile(csv_bytes(rows))
        self.assertEqual(q["exact_duplicate_rows"],{"groups":1,"rows":2})
        self.assertEqual(q["reference_date_conflicting_prices"],1)
        self.assertEqual(q["repeated_reference_date_price"]["groups"],1)

    def test_structure_and_privacy(self):
        with patch.object(p,"EXPECTED",4):
            with self.assertRaisesRegex(p.ProfileStop,"HEADER"):
                p.profile(csv_bytes(fixture(),["bad"]*7))
            with self.assertRaisesRegex(p.ProfileStop,"ROW_COUNT"):
                p.profile(csv_bytes(fixture()[:2]))
            with self.assertRaisesRegex(p.ProfileStop,"ROW_STRUCTURE"):
                p.profile(csv_bytes(fixture()+[fixture()[0]]))
            rows=fixture()
            rows[0][1]="private@example.org"
            with self.assertRaisesRegex(p.ProfileStop,"UNEXPECTED_TEXT"):
                p.profile(csv_bytes(rows))

    def test_currency(self):
        for s,expected in [("R 0","zero"),("R -1","negative"),("R 1,23","invalid"),
                           ("R 1.001","invalid"),("R 1 000.00","positive"),("","missing")]:
            self.assertEqual(p.number(s,True)[0],expected)


if __name__=="__main__":
    unittest.main()
