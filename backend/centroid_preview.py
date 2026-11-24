"""Source-shaped fictional centroid rehearsal, distinct from virtual map.
Never serves raw coordinates, PINs, real historical records or distance claims.
"""
from math import isfinite
from backend.buyer_evidence_preview import project_buyer_evidence,require
from backend.curated_ingestion_candidate import _plan,_verify_build
from backend.synthetic_investigation_store import SyntheticInvestigationStore,CuratedReadQueries

def relative_points(members):
    """Subject-relative, quantised schematic offsets in millidegrees.
    Not a geographic coordinate reference system. Never jitter overlapping points.
    """
    if not members or any(type(lat) not in (int,float) or type(lon) not in (int,float)
                          or not isfinite(lat) or not isfinite(lon)
                          or not 40<=lat<=43 or not -89<=lon<=-86
                          for _,_,lat,lon in members):
        return [],"missing_geometry"
    _,_,origin_lat,origin_lon=members[0]
    points=[{"rank":rank,"assessment_year":year,"offset_x":round((lon-origin_lon)*1000),
             "offset_y":round((lat-origin_lat)*1000)} for rank,year,lat,lon in members]
    if any(abs(p["offset_x"])>20 or abs(p["offset_y"])>20 for p in points):
        return [],"outside_schematic_extent"
    if len({(p["offset_x"],p["offset_y"]) for p in points})!=len(points):
        return [],"overlapping_centroids"
    return points,None

def centroid_preview(store, iid):
    require(isinstance(store,SyntheticInvestigationStore))
    record=store.reopen(iid)
    preview=project_buyer_evidence(record)
    build=preview["provenance"]["build_id"]
    result={"contract_version":"centroid-preview-v1","investigation_id":iid,"build_id":build,
            "source_kind":"synthetic_fixture","geometry_kind":"fictional_parcel_centroid_schematic",
            "building_identity_verified":False,"real_geography_verified":False,
            "public_display_approved":False,"historical_asof_verified":False,"distance_supported":False,
            "source_snapshot_id":None,"available":False,"reason":"unsupported_fixture_revision","points":[]}
    revision=next((v for v in ("v5","v6") if _plan(v)[2]==build),None)
    if revision is None:return result
    # Check the exact reviewed source rows for the investigation's frozen build,
    # not whichever revision is currently active.
    require(_verify_build(store.connection,revision)==build)
    sid=_plan(revision)[1]["geography"]["snapshot_id"]
    require(sid in record["data_build"]["source_snapshot_ids"])
    result["source_snapshot_id"]=sid
    if not preview["sales"] or not record["subject"]["pin"]:
        result["reason"]="insufficient_evidence"
        return result
    queries=CuratedReadQueries(store.connection,build)
    members=[(0,record["subject"]["pin"],int(record["analysis_date"][:4])-1)]
    members.extend((rank,row["pin"],row["characteristics_year"]) for rank,row in enumerate(record["comparables"],1))
    points=[]
    for rank,pin,year in members:
        geo=queries._geography(pin,year)
        points.append((rank,year,geo[1] if geo else None,geo[2] if geo else None))
    result["points"],result["reason"]=relative_points(points)
    result["available"]=result["reason"] is None
    return result
