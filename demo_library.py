"""Stable demo fixtures for the ten-person fictional library.

Identities live only in data/fixtures/profiles.json. Match scores are never
written back onto those records.
"""
from __future__ import annotations

import hashlib
import json
import math
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

CASE_IMAGE_BY_CATEGORY = (
    ("footwear", "/assets/evidence/evidence-motionlab-run.png"),
    ("run", "/assets/evidence/evidence-motionlab-run.png"),
    ("fitness", "/assets/evidence/evidence-motionlab-run.png"),
    ("sport", "/assets/evidence/evidence-motionlab-run.png"),
    ("hydrat", "/assets/evidence/evidence-motionlab-run.png"),
    ("outdoor", "/assets/evidence/evidence-motionlab-run.png"),
    ("tech", "/assets/evidence/evidence-nova-audio.png"),
    ("audio", "/assets/evidence/evidence-nova-audio.png"),
    ("mobile", "/assets/evidence/evidence-nova-audio.png"),
    ("gaming", "/assets/evidence/evidence-nova-audio.png"),
    ("wearable", "/assets/evidence/evidence-nova-audio.png"),
    ("wellness", "/assets/evidence/evidence-wellness.png"),
    ("health", "/assets/evidence/evidence-wellness.png"),
    ("apparel", "/assets/evidence/evidence-lifestyle.png"),
    ("fashion", "/assets/evidence/evidence-lifestyle.png"),
    ("lifestyle", "/assets/evidence/evidence-lifestyle.png"),
    ("fragrance", "/assets/evidence/evidence-lifestyle.png"),
    ("music", "/assets/evidence/evidence-lifestyle.png"),
)


def _case_image(case: dict) -> str | None:
    if case.get("imageAsset"):
        return case.get("imageAsset")
    known = CASE_IMAGES.get(case.get("id"))
    if known:
        return known
    cat = str(case.get("category") or "").lower()
    for key, src in CASE_IMAGE_BY_CATEGORY:
        if key in cat:
            return src
    return "/assets/evidence/evidence-lifestyle.png"


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


def load_credits_doc() -> dict:
    path = FIXTURES / "credits.json"
    if not path.exists():
        return {}
    return _load("credits.json")


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


def _unit(seed: str) -> float:
    digest = hashlib.md5(seed.encode("utf-8")).hexdigest()
    return int(digest[:8], 16) / 0xFFFFFFFF


def _series30d(profile: dict) -> list[float]:
    """Stable demo mention-index path from recorded momentum / change / volatility."""
    tp = profile.get("trendProfile") or {}
    if isinstance(tp.get("series30d"), list) and len(tp["series30d"]) >= 2:
        return [round(float(v), 1) for v in tp["series30d"]]
    end = float(tp.get("momentum30d") or 50)
    change = float(tp.get("change30dPct") or 0)
    vol = str(tp.get("volatility") or "medium")
    amp = {"low": 2.2, "medium": 6.5, "medium-high": 11.0, "high": 14.0}.get(vol, 6.5)
    start = end / (1.0 + change / 100.0) if change > -99 else end
    slug = str(profile.get("slug") or profile.get("id") or "demo")
    n = 30
    out = []
    for i in range(n):
        t = i / (n - 1)
        base = start + (end - start) * (t ** 0.85)
        u1 = _unit(f"{slug}:a:{i}")
        u2 = _unit(f"{slug}:b:{i}")
        wobble = amp * math.sin((i + 1) * 0.55 + u1 * 6.28) * (0.35 + 0.65 * u2)
        if vol in ("medium-high", "high") and u1 > 0.82:
            wobble += amp * (u2 - 0.3)
        out.append(round(max(8.0, min(100.0, base + wobble)), 1))
    out[-1] = round(max(8.0, min(100.0, end)), 1)
    return out


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
            item["imageAsset"] = _case_image(item)
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
        "evidence": list(profile.get("mentions") or profile.get("evidence") or []),
        "why_for_coffee": profile.get("whyCandidate") or "",
        "public_image": profile.get("bio") or "",
        "main_audience": (profile.get("ageBand") or "") + " · " + (profile.get("market") or ""),
        "works": list(profile.get("works") or []),
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
        "trendProfile": {**(profile.get("trendProfile") or {}), "series30d": _series30d(profile)},
        "culturalArchetype": profile.get("culturalArchetype") or {},
        "endorsementCases": cases,
        "provenance": profile.get("provenance") or {"mode": "demo", "simulated": True},
        "assets": profile.get("assets") or {},
        "demo": True,
    }


def demo_celebrities() -> list[dict]:
    doc = load_profiles_doc()
    credits = (load_credits_doc() or {}).get("candidates") or {}
    out = []
    for profile in doc.get("candidates") or []:
        celeb = profile_to_celebrity(profile)
        extra = credits.get(profile["id"]) or credits.get(profile.get("slug") or "") or {}
        if extra.get("works"):
            celeb["works"] = list(extra["works"])
        if extra.get("mentions"):
            celeb["evidence"] = list(extra["mentions"])
        out.append(celeb)
    return out


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
