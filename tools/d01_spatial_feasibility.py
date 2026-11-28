"""Aggregate-only spatial feasibility on pinned, audited candidate snapshots."""
from collections import Counter, defaultdict
from math import isfinite
from tools import d01_extent_similarity as extent
from tools import d01_transaction_availability as tx

RADII = (2000, 1000)
CRS_NAMES = {"epsg:4326", "urn:ogc:def:crs:epsg::4326",
             "urn:ogc:def:crs:ogc:1.3:crs84", "ogc:crs84", "crs84",
             "http://www.opengis.net/def/crs/epsg/0/4326",
             "http://www.opengis.net/def/crs/ogc/1.3/crs84"}
# Permanent aggregate evidence only, in exact/alias/combined subject order,
# exact/combined pool order, 365/730 window order.
BINS = [
    [(1,2,2,261),(3,12,8,243),(10,31,29,196)],
    [(1,2,2,261),(3,9,8,246),(8,24,14,220)],
    [(0,1,2,263),(1,9,12,244),(8,24,28,206)],
    [(0,1,2,263),(1,6,12,247),(6,20,17,223)],
    [(2,0,0,72),(2,0,1,71),(2,1,6,65)],
    [(2,0,0,72),(2,0,1,71),(2,1,2,69)],
    [(1,1,0,72),(2,0,1,71),(2,1,1,70)],
    [(1,1,0,72),(2,0,1,71),(2,1,1,70)],
    [(3,2,2,333),(5,12,9,314),(12,32,35,261)],
    [(3,2,2,333),(5,9,9,317),(10,25,16,289)],
    [(1,2,2,335),(3,9,13,315),(10,25,29,276)],
    [(1,2,2,335),(3,6,13,318),(8,21,18,293)],
]


def observed_extent():
    strata = {}
    blocks = iter(BINS)
    for name, n in (("exact",266), ("alias_only",74), ("combined",340)):
        strata[name] = {}
        for pool_name, rows, parcels in (("earlier_exact_pool",266,260),
                                          ("earlier_combined_sensitivity_pool",340,330)):
            strata[name][pool_name] = {}
            for days in tx.WINDOWS:
                result = {}
                for filter_name, bins in zip(extent.FILTERS, next(blocks)):
                    q = extent.observed_coverage(n, rows, parcels, bins)[str(days)]
                    q.update(subjects_with_older_qualifying_event=0,
                             subject_candidate_pairs_with_older_qualifying_event=0)
                    result[filter_name] = q
                strata[name][pool_name][str(days)] = result
    return {"status":"REPORTED_EXTENT_SIMILARITY_FEASIBILITY_ONLY",
            "baseline_reproduced":True,"tolerance_percent":25,
            "primary_window_days":365,"sensitivity_window_days":730,
            "strata":strata,"verified_completed_sales":0,
            "historical_as_of_availability_verified":False,
            "limitations":"Reported dwelling and erf extents only; observation dates, units equivalence to living area, legal continuity, transfer and historical availability unverified. No spatial distance, price ranking, valuation or policy adoption. Older qualifying event counts are relative to latest earlier event among retained candidates."}


EXTENT_BASELINE = observed_extent()


def crs_status(raw):
    # Raw collection metadata, not the stripped processed collection.
    # No guessed axis swap, remote lookup or arbitrary CRS parsing.
    if any("crs" in f or "spatialReference" in f for f in raw["features"]):
        return "unsupported_or_conflicting"
    if "spatialReference" in raw:
        return "unsupported_or_conflicting"
    if "crs" not in raw:
        return "conditional_absent_geojson_declaration"
    crs = raw["crs"]
    if (isinstance(crs,dict) and set(crs)=={"type","properties"} and
            crs["type"]=="name" and isinstance(crs["properties"],dict) and
            set(crs["properties"])=={"name"} and
            isinstance(crs["properties"]["name"],str) and
            crs["properties"]["name"].casefold() in CRS_NAMES):
        return "explicit_supported_wgs84"
    return "unsupported_or_conflicting"


def representative(g):
    from shapely.geometry import shape
    if not isinstance(g,dict) or g.get("type") not in ("Polygon","MultiPolygon"):
        return "unsupported_geometry", None
    try:
        polys = [g["coordinates"]] if g["type"]=="Polygon" else g["coordinates"]
        if not isinstance(polys,list) or not polys:
            return "invalid_geometry", None
        for poly in polys:
            if not isinstance(poly,list) or not poly:
                return "invalid_geometry", None
            for ring in poly:
                if not isinstance(ring,list) or len(ring)<4 or ring[0]!=ring[-1]:
                    return "invalid_geometry", None
                for pos in ring:
                    if not isinstance(pos,list) or len(pos)!=2:
                        return "unsupported_geometry", None
                    if any(type(v) not in (int,float) or not isfinite(v) for v in pos):
                        return "invalid_geometry", None
                    if not (18<=pos[0]<=19.5 and -35<=pos[1]<=-33):
                        return "outside_envelope", None
        p = shape(g)
        if p.is_empty or not p.is_valid or not isfinite(p.area) or p.area<=0:
            return "invalid_geometry", None
        point = p.representative_point()
        if point.is_empty or not p.contains(point) or not all(isfinite(v) for v in (point.x,point.y)):
            return "invalid_geometry", None
        return "valid", (point.x,point.y)
    except (ValueError,TypeError,KeyError,OverflowError):
        return "invalid_geometry", None
    except Exception:
        return "invalid_geometry", None


def qualify(raw, projection, oids):
    crs = crs_status(raw)
    reasons = {}
    points = {}
    by_point = defaultdict(set)
    for f in projection["features"]:
        p = f["properties"]
        oid = p["OBJECTID"]
        if oid not in oids:
            continue
        if crs=="unsupported_or_conflicting":
            reason, point = "crs_abstention", None
        elif not p["quality_flags"]["spatial_candidate"]:
            reason, point = "prior_spatial_flag_excluded", None
        else:
            reason, point = representative(f["geometry"])
        reasons[oid] = reason
        if point is not None:
            points[oid] = point
            by_point[point].add(oid)
    if set(reasons)!=oids:
        raise ValueError("SPATIAL_PARCEL_ACCOUNTING")
    duplicate_groups = [ids for ids in by_point.values() if len(ids)>1]
    for ids in duplicate_groups:
        for oid in ids:
            reasons[oid] = "coincident_point"
            del points[oid]
    counts = Counter(dict.fromkeys(("valid","crs_abstention","prior_spatial_flag_excluded",
                                    "unsupported_geometry","invalid_geometry","outside_envelope",
                                    "coincident_point"),0))
    counts.update(reasons.values())
    return points, {"crs_status":crs,"candidate_parcels":len(oids),
                    "parcel_outcomes":dict(counts),
                    "coincident_point_groups":len(duplicate_groups),
                    "coincident_point_parcels":counts["coincident_point"],
                    "usable_candidate_parcels":len(points)}


def distance_lookup(points):
    from pyproj import Geod
    geod = Geod(ellps="WGS84")
    cache = {}
    def distance(a,b):
        if a==b or a not in points or b not in points:
            return None
        key = frozenset((a,b))
        if key not in cache:
            _,_,d = geod.inv(*points[a],*points[b])
            cache[key] = d if isfinite(d) and d>0 else None
        return cache[key]
    return distance


def within(distance, radius):
    return distance is not None and isfinite(distance) and 0 < distance <= radius


def coverage(subjects,pool,sizes,points,distance,days,prior):
    bins = {r:Counter(dict.fromkeys(("zero","one_to_two","three_to_four","five_or_more"),0)) for r in RADII}
    # Denominator includes coordinate abstentions; distinguish these from zero
    # qualifying candidates with usable subject coordinates.
    abstain = 0
    eligible_pairs_missing = 0
    invalid_distance_pairs = 0
    baseline_bins = Counter(dict.fromkeys(("zero","one_to_two","three_to_four","five_or_more"),0))
    def category(n):
        return "zero" if n==0 else "one_to_two" if n<3 else "three_to_four" if n<5 else "five_or_more"
    for subject in subjects:
        oid = subject[0]
        # Distance depends only on candidate parcel, so latest qualifying
        # event after both extent filters remains latest after distance filter.
        selected = extent.latest_maps(subject,pool,sizes,days)[2]
        baseline_bins[category(len(selected))]+=1
        if oid not in points:
            abstain+=1
            continue
        counts = dict.fromkeys(RADII,0)
        for other in selected:
            if other not in points:
                eligible_pairs_missing+=1
                continue
            d=distance(oid,other)
            if d is None:
                invalid_distance_pairs+=1
            for r in RADII:
                counts[r]+=within(d,r)
        if not 0<=counts[1000]<=counts[2000]<=len(selected):
            raise ValueError("SPATIAL_NESTING")
        for r,n in counts.items():
            bins[r][category(n)]+=1
    if dict(baseline_bins)!=prior["exclusive_counts"] or len(subjects)!=prior["subject_rows"]:
        raise ValueError("SPATIAL_EXTENT_COVERAGE_MISMATCH")
    result={}
    for r,b in bins.items():
        if sum(b.values())+abstain!=len(subjects):
            raise ValueError("SPATIAL_ACCOUNTING")
        result[str(r)]={"subject_rows":len(subjects),"pool_rows":len(pool),
                       "pool_distinct_candidate_parcels":len({e[0] for e in pool}),
                       "pool_rows_with_usable_point":sum(e[0] in points for e in pool),
                       "pool_distinct_parcels_with_usable_point":len({e[0] for e in pool if e[0] in points}),
                       "subject_coordinate_abstentions":abstain,
                       "assessed_subject_rows":len(subjects)-abstain,
                       "exclusive_counts":dict(b),
                       "at_least_one":len(subjects)-abstain-b["zero"],
                       "at_least_three":b["three_to_four"]+b["five_or_more"],
                       "at_least_five":b["five_or_more"],
                       "insufficient_for_three_including_abstentions":abstain+b["zero"]+b["one_to_two"],
                       "insufficient_for_five_including_abstentions":len(subjects)-b["five_or_more"]}
    return {"dual_extent_baseline":prior,"extent_eligible_subject_candidate_pairs_missing_pool_point":eligible_pairs_missing,
            "extent_eligible_subject_candidate_pairs_invalid_distance":invalid_distance_pairs,"radius_metres":result}


def assess_spatial(events,strict_events,extents,raw,projection,prior):
    if prior!=EXTENT_BASELINE:
        raise ValueError("SPATIAL_EXTENT_BASELINE_MISMATCH")
    counts=Counter(strict_events)
    eligible=[e for e in events if counts[e[:2]]==1]
    sizes={e:tuple(extent.positive_extent(v) for v in extents[e]) for e in eligible}
    points,quality=qualify(raw,projection,{e[0] for e in eligible})
    distance=distance_lookup(points)
    exact=[e for e in eligible if e[2]=="exact"]
    alias=[e for e in eligible if e[2]=="alias_only"]
    strata={}
    for name,subjects in (("exact",exact),("alias_only",alias),("combined",eligible)):
        strata[name]={}
        for pool_name,pool in (("earlier_exact_pool",exact),("earlier_combined_sensitivity_pool",eligible)):
            strata[name][pool_name]={str(days):coverage(subjects,pool,sizes,points,distance,days,
                 prior["strata"][name][pool_name][str(days)]["dwelling_and_erf_25pct"]) for days in tx.WINDOWS}
    return {"status":"CONDITIONAL_SPATIAL_FEASIBILITY_ONLY","baseline_reproduced":True,
            "geometry":quality,"tolerance_percent":25,"primary_window_days":365,
            "sensitivity_window_days":730,"strata":strata,"verified_completed_sales":0,
            "historical_as_of_availability_verified":False,"policy_adopted":False,
            "limitations":"Pinned GeoJSON export provenance and conditional CRS only, no independent geodetic accuracy. Current parcel interior representative points, WGS84 geodesic metres, not building or historical locations. Coordinate abstentions excluded from assessed bins but included in insufficiency. No valuation, ranking or legal identity promotion."}
