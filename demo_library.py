"""Stable demo fixtures for the ten-person fictional library.

Identities live only in data/fixtures/profiles.json. Match scores are never
written back onto those records.
"""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent
FIXTURES = ROOT / "data" / "fixtures"

DATASET_ID = "candidate_fixture_cn_v1"
FIXTURE_VERSION = "1.1.0"
DATASET_KEY = f"{DATASET_ID}@{FIXTURE_VERSION}"
TREND_SNAPSHOT_ID = "trend_demo_2026_09_10"
PRODUCT_AEROSTRIDE = "product_aerostride_v1"
SCORING_BALANCED = "scoring_balanced_v1"
MATCH_MODEL = "demo-weighted-fit-v1"

TAG_FROM_SIGNAL = {
    "signal_sports": "运动",
    "signal_technology": "科技",
    "signal_energy": "活力",
    "signal_health": "健康",
    "signal_outdoor": "户外",
}

PERSONA_TO_TAG = {
    "sports": "运动",
    "technology": "科技",
    "energy": "活力",
    "health": "健康",
    "wellness": "健康",
    "style": "时尚",
    "youth-culture": "活力",
    "discipline": "运动",
    "urban": "体验",
    "outdoor": "户外",
    "trust": "情绪价值",
    "music": "体验",
    "culture": "时尚",
    "design": "时尚",
    "gaming": "科技",
    "movement": "运动",
}

RISK_SCORE = {
    "low": 0.16,
    "medium": 0.32,
    "high": 0.58,
    "unverified": 0.4,
    "clear": 0.18,
    "hold": 0.62,
}

LISTING_CROPS = {
    "kai-ren": "/assets/candidates/listing-kai-ren.png",
    "mina-zhou": "/assets/candidates/listing-mina-zhou.png",
    "evan-lu": "/assets/candidates/listing-evan-lu.png",
}

CASE_IMAGES = {
    "case_001_a": "/assets/evidence/evidence-motionlab-run.png",
    "case_001_b": "/assets/evidence/evidence-nova-audio.png",
}


def _load(name: str):
    return json.loads((FIXTURES / name).read_text(encoding="utf-8"))


def load_profiles_doc() -> dict:
    return _load("profiles.json")


def load_analysis_doc() -> dict:
    return _load("demo-analysis-aerostride.json")


def load_trend_doc() -> dict:
    return _load("trend-snapshot.json")


def load_scoring_doc() -> dict:
    return _load("scoring-presets.json")


def load_archetype_doc() -> dict:
    return _load("archetype-signals.json")


def demo_trends() -> dict:
    snap = load_trend_doc()
    out = {}
    for sig in snap.get("signals") or []:
        tag = TAG_FROM_SIGNAL.get(sig.get("id"))
        if not tag:
            continue
        direction = sig.get("direction") or "stable"
        verdict = "keep"
        if direction == "rising":
            verdict = "keep"
        heat = round(float(sig.get("relativeAttention") or 0) / 100, 3)
        evidence = []
        for ev in (snap.get("evidence") or [])[:3]:
            ev_id = ev.get("id") or ""
            thumb = {
                "trend_evidence_001": "/assets/trends/evidence-01-running.png",
                "trend_evidence_002": "/assets/trends/evidence-02-training.png",
                "trend_evidence_003": "/assets/trends/evidence-03-footwear.png",
            }.get(ev_id)
            evidence.append(
                {
                    "source": f"Demo/{ev.get('platform')}",
                    "platform": ev.get("platform"),
                    "date": ev.get("date"),
                    "title": ev.get("headline"),
                    "status": ev.get("status") or "simulated",
                    "image": thumb,
                }
            )
        out[tag] = {
            "tag": tag,
            "mention_count": int(sig.get("observedTitleCount") or 0),
            "today_count": int(round((sig.get("dailyIndex") or [0])[-1])),
            "heat": heat,
            "verdict": verdict,
            "note": f"Demo snapshot {snap.get('snapshotId')}. Simulated relative attention, not live market share.",
            "evidence": evidence,
            "sources": ["Demo fixture trend_demo_2026_09_10"],
            "relativeAttention": sig.get("relativeAttention"),
            "changePct": sig.get("changePct"),
            "direction": direction,
            "platformCount": sig.get("platformCount"),
            "bestRank": sig.get("bestRank"),
            "dailyIndex": sig.get("dailyIndex") or [],
            "provenance": "demo_snapshot",
        }
    for tag in ("情绪价值", "便利", "时尚", "体验", "咖啡"):
        if tag not in out:
            out[tag] = {
                "tag": tag,
                "mention_count": 0,
                "today_count": 0,
                "heat": 0.22,
                "verdict": "optional",
                "note": "Not a primary signal in the demo trend snapshot.",
                "evidence": [],
                "sources": ["Demo fixture trend_demo_2026_09_10"],
                "relativeAttention": 22,
                "changePct": 0,
                "direction": "stable",
                "platformCount": 0,
                "bestRank": None,
                "dailyIndex": [20, 21, 21, 22, 22, 22, 22],
                "provenance": "demo_snapshot",
            }
    return out


def _age_split(dist: dict) -> dict:
    a18 = float(dist.get("18-24") or 0)
    a25 = float(dist.get("25-34") or 0)
    older = float(dist.get("35-44") or 0) + float(dist.get("45+") or 0)
    total = a18 + a25 + older or 1
    return {
        "18-24": round(a18 / total, 3),
        "25-28": round(a25 * 0.55 / total, 3),
        "29-35": round((a25 * 0.45 + older * 0.4) / total, 3),
    }


def _risk(profile: dict) -> dict:
    rp = profile.get("riskProfile") or {}
    vol = str(rp.get("reputationVolatility") or "medium")
    conflict = str(rp.get("categoryConflict") or "unverified")
    score = max(RISK_SCORE.get(vol, 0.32), RISK_SCORE.get(conflict, 0.32))
    if conflict == "hold":
        level = "high"
    elif score >= 0.45:
        level = "high"
    elif score >= 0.28:
        level = "medium"
    else:
        level = "low"
    notes = list(rp.get("unverified") or [])
    return {"score": score, "level": level, "notes": notes, "profile": rp}


def profile_to_celebrity(profile: dict) -> dict:
    """Adapter for the existing matcher. Does not copy analysis scores."""
    tags = {}
    for row in profile.get("personaTags") or []:
        zh = PERSONA_TO_TAG.get(row.get("id"))
        if not zh:
            continue
        tags[zh] = max(tags.get(zh, 0), float(row.get("score") or 0) / 100)
    aud = profile.get("audience") or {}
    dist = aud.get("ageDistribution") or {}
    slug = profile.get("slug") or profile["id"]
    cases = []
    for case in profile.get("endorsementCases") or []:
        item = dict(case)
        if not item.get("imageAsset"):
            item["imageAsset"] = CASE_IMAGES.get(item.get("id"))
        cases.append(item)
    return {
        "id": profile["id"],
        "slug": slug,
        "name": profile["name"],
        "name_en": profile["name"],
        "gender": profile.get("gender"),
        "age": profile.get("age"),
        "birth_year": None,
        "occupations": list(profile.get("roles") or []),
        "tags": tags,
        "personaTags": profile.get("personaTags") or [],
        "fan_profile": {
            "core_age": [18, 28],
            "age_split": _age_split(dist),
            "ageDistribution": dist,
            "genderDistribution": aud.get("genderDistribution") or {},
            "interests": aud.get("interests") or [],
            "engagement": "Simulated demo engagement",
            "platforms": [p.get("platform") for p in (aud.get("platforms") or [])],
            "platformDetail": aud.get("platforms") or [],
            "topRegions": aud.get("topRegions") or [],
        },
        "risk": _risk(profile),
        "heat_mentions": int((profile.get("trendProfile") or {}).get("momentum30d") or 0),
        "today_mentions": 0,
        "evidence": [],
        "why_for_coffee": profile.get("whyCandidate") or "",
        "public_image": profile.get("bio") or "",
        "main_audience": (profile.get("ageBand") or "") + " · " + (profile.get("market") or ""),
        "works": [],
        "portrait": f"/assets/portraits/{slug}.png",
        "listingImage": LISTING_CROPS.get(slug, f"/assets/portraits/{slug}.png"),
        "profilePortrait": "/assets/candidates/profile-kai-ren.png" if slug == "kai-ren" else f"/assets/portraits/{slug}.png",
        "bio": profile.get("bio") or "",
        "whyCandidate": profile.get("whyCandidate") or "",
        "tradeoff": profile.get("tradeoff") or "",
        "market": profile.get("market"),
        "ageBand": profile.get("ageBand"),
        "languages": profile.get("languages") or [],
        "commercial": profile.get("commercial") or {},
        "creativeProfile": profile.get("creativeProfile") or {},
        "trendProfile": profile.get("trendProfile") or {},
        "culturalArchetype": profile.get("culturalArchetype") or {},
        "endorsementCases": cases,
        "provenance": profile.get("provenance") or {"mode": "demo", "simulated": True},
        "assets": profile.get("assets") or {},
        "demo": True,
    }


def demo_celebrities() -> list[dict]:
    doc = load_profiles_doc()
    return [profile_to_celebrity(p) for p in (doc.get("candidates") or [])]


def fixture_bundle() -> dict:
    profiles = load_profiles_doc()
    analysis = load_analysis_doc()
    snap = load_trend_doc()
    scoring = load_scoring_doc()
    return {
        "datasetId": DATASET_ID,
        "fixtureVersion": FIXTURE_VERSION,
        "datasetKey": DATASET_KEY,
        "productBriefVersionId": PRODUCT_AEROSTRIDE,
        "scoringStrategyVersionId": SCORING_BALANCED,
        "trendSnapshotId": TREND_SNAPSHOT_ID,
        "matchModelVersion": MATCH_MODEL,
        "disclaimer": profiles.get("disclaimer"),
        "profiles": profiles.get("candidates") or [],
        "analysis": analysis,
        "trendSnapshot": snap,
        "scoringPresets": scoring,
        "archetypes": load_archetype_doc(),
    }
