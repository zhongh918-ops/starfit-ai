"""Rebuild youth trends from TrendRadar sqlite and score celebrity matches."""
from __future__ import annotations

import json
import math
import re
import sqlite3
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent
DATA = ROOT / "data"
TRENDRADAR_NEWS = Path.home() / "Tools/TrendRadar/output/news"

TAG_RULES = {
    "运动": r"运动|健身|跑步|马拉松|NBA|CBA|足球|篮球|奥运|世界杯|体坛|训练|瑜伽|骑行|网球|乒乓|运动员|皇马|国米|美网|郑钦文",
    "户外": r"户外|露营|徒步|登山|旅行|自驾|citywalk|海边|滑雪|冲浪|川西",
    "健康": r"健康|养生|减脂|减肥|睡眠|心理|防晒|成分|低糖|0糖|无糖|代糖|有机|轻食|蛋白|神药|司美格鲁肽",
    "科技": r"科技|AI|人工智能|芯片|华为|苹果|小米|机器人|智能|数码|手机|AR|VR|大模型|DeepSeek|折叠",
    "情绪价值": r"情绪|治愈|松弛|氛围|陪伴|真诚|松弛感|精神内耗|快乐|解压|燕麦系",
    "便利": r"便利|即饮|外卖|闪购|预制|懒人|通勤|速溶|即热|到家|即时零售",
    "时尚": r"时尚|穿搭|美妆|潮流|秀场|时装|造型",
    "体验": r"体验|沉浸|快闪|线下|展览|市集",
    "咖啡": r"咖啡|拿铁|冷萃|美式|咖啡因|茶姬",
    "活力": r"青春|活力|街舞|热血|燃",
}

NOTES = {
    "运动": "热榜持续出现赛事、健身、运动员形象；18–28 人群对运动生活方式接受度高。",
    "户外": "有旅行/露营正向内容，但徒步遇险等负面新闻会拉高风险，适合轻户外而非硬核探险。",
    "健康": "养生、成分党、神药打假同时在榜，年轻人要“健康感”但反伪科学。",
    "科技": "全平台最强信号（AI/折叠屏/智能硬件），科技感 TAG 有明确热度依据。",
    "情绪价值": "治愈、松弛讨论在知乎/抖音出现，即饮与耳机场景可打陪伴。",
    "便利": "外卖/预制菜/即时零售讨论多，即饮咖啡的便利是刚需。",
    "时尚": "造型、美妆热搜集中在明星红毯，适合时尚向代言人加分。",
    "体验": "沉浸式、市集、线下体验有内容热度，适合 campaign 落地形态。",
    "咖啡": "茶饮咖啡因争议曾上热搜，产品需避开高咖啡因焦虑。",
    "活力": "青春/燃向内容，适合运动与潮流人设。",
}


def _load_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def news_rows() -> list[dict]:
    rows = []
    if not TRENDRADAR_NEWS.exists():
        return rows
    for dbp in sorted(TRENDRADAR_NEWS.glob("*.db")):
        con = sqlite3.connect(dbp)
        for title, plat, rank in con.execute(
            "select title, platform_id, rank from news_items"
        ):
            rows.append(
                {
                    "date": dbp.stem,
                    "title": title,
                    "platform": plat,
                    "rank": rank or 99,
                }
            )
        con.close()
    return rows


def latest_db_mtime() -> str | None:
    files = list(TRENDRADAR_NEWS.glob("*.db")) if TRENDRADAR_NEWS.exists() else []
    if not files:
        return None
    ts = max(p.stat().st_mtime for p in files)
    return datetime.fromtimestamp(ts).astimezone().isoformat(timespec="seconds")


def rebuild_trends(rows: list[dict] | None = None) -> dict:
    rows = rows if rows is not None else news_rows()
    today = datetime.now().strftime("%Y-%m-%d")
    tag_hits: dict[str, list] = defaultdict(list)
    today_hits: dict[str, int] = defaultdict(int)
    for r in rows:
        for tag, pat in TAG_RULES.items():
            if re.search(pat, r["title"], re.I):
                tag_hits[tag].append(r)
                if r["date"] == today:
                    today_hits[tag] += 1

    max_all = max((len(v) for v in tag_hits.values()), default=1) or 1
    max_today = max(today_hits.values(), default=1) or 1

    trends = {}
    for tag in TAG_RULES:
        hits = tag_hits.get(tag, [])
        all_n = len(hits)
        tod_n = today_hits.get(tag, 0)
        heat = round(0.35 * (all_n / max_all) + 0.65 * (tod_n / max_today), 3) if rows else 0
        if tag == "户外" and any("徒步" in h["title"] and "去世" in h["title"] for h in hits):
            verdict = "caution"
        elif tag in ("健康", "便利", "体验", "情绪价值"):
            verdict = "add"
        elif tag in ("时尚", "活力", "咖啡"):
            verdict = "optional"
        else:
            verdict = "keep"
        ev = []
        seen = set()
        for h in sorted(hits, key=lambda x: (0 if x["date"] == today else 1, x["rank"])):
            if h["title"] in seen:
                continue
            seen.add(h["title"])
            ev.append(h)
            if len(ev) >= 5:
                break
        trends[tag] = {
            "tag": tag,
            "mention_count": all_n,
            "today_count": tod_n,
            "heat": heat,
            "verdict": verdict,
            "note": NOTES.get(tag, ""),
            "evidence": ev,
            "sources": ["TrendRadar 11 平台热榜"],
        }
    payload = {
        "generated_at": datetime.now().astimezone().isoformat(timespec="seconds"),
        "source_mtime": latest_db_mtime(),
        "today": today,
        "total_items": len(rows),
        "today_items": sum(1 for r in rows if r["date"] == today),
        "tags": trends,
    }
    DATA.mkdir(parents=True, exist_ok=True)
    (DATA / "youth_trends.json").write_text(
        json.dumps(payload["tags"], ensure_ascii=False, indent=2), encoding="utf-8"
    )
    (DATA / "meta.json").write_text(
        json.dumps(
            {k: payload[k] for k in ("generated_at", "source_mtime", "today", "total_items", "today_items")},
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )
    return payload


def recount_celebrity_heat(celebrities: list[dict], rows: list[dict] | None = None) -> list[dict]:
    rows = rows if rows is not None else news_rows()
    today = datetime.now().strftime("%Y-%m-%d")
    out = []
    for c in celebrities:
        name = c["name"]
        all_hits = [r for r in rows if name in r["title"]]
        today_hits = [r for r in all_hits if r["date"] == today]
        c = dict(c)
        c["heat_mentions"] = len(all_hits)
        c["today_mentions"] = len(today_hits)
        if all_hits:
            c["evidence"] = [
                {
                    "source": f"TrendRadar/{h['platform']}",
                    "date": h["date"],
                    "title": h["title"],
                }
                for h in sorted(all_hits, key=lambda x: (0 if x["date"] == today else 1, x["rank"]))[:3]
            ]
        out.append(c)
    return out


def optimize_tags(seed_tags: list[str], trends: dict) -> list[dict]:
    result, seen = [], set()

    def push(tag: str, origin: str, weight: float):
        if tag in seen:
            return
        seen.add(tag)
        tr = trends.get(tag) or {
            "heat": 0.4,
            "verdict": "keep",
            "note": "趋势库暂无独立热度，按人设 TAG 参与匹配。",
            "evidence": [],
            "mention_count": 0,
            "today_count": 0,
        }
        result.append(
            {
                "tag": tag,
                "origin": origin,
                "weight": weight,
                "heat": tr.get("heat", 0.4),
                "verdict": tr.get("verdict", "keep"),
                "note": tr.get("note", ""),
                "mention_count": tr.get("mention_count", 0),
                "today_count": tr.get("today_count", 0),
            }
        )

    for tag in seed_tags:
        v = (trends.get(tag) or {}).get("verdict")
        push(tag, "seed", 0.55 if v == "caution" else 1.15)
    for tag in ("健康", "便利", "体验", "情绪价值"):
        push(tag, "trend-add", 0.62)
    return sorted(result, key=lambda t: t["weight"] * (0.5 + 0.5 * t["heat"]), reverse=True)


def match_product(product: dict, trends: dict, celebrities: list[dict]) -> dict:
    opt = optimize_tags(product["seed_tags"], trends)
    ranked = []
    for celeb in celebrities:
        num = den = 0.0
        hits = []
        for t in opt:
            cv = float(celeb["tags"].get(t["tag"], 0))
            w = t["weight"] * (0.5 + 0.5 * t["heat"])
            num += w * cv
            den += w
            if cv >= 0.55:
                hits.append({"tag": t["tag"], "celeb": cv})
        tag_score = num / den if den else 0
        split = celeb["fan_profile"]["age_split"]
        age_score = split.get("18-24", 0) + split.get("25-28", 0)
        heat_score = min(1.0, 0.25 + 0.75 * math.log(1 + celeb.get("heat_mentions", 0)) / math.log(17))
        risk_score = 1 - celeb["risk"]["score"]
        final = 0.50 * tag_score + 0.22 * age_score + 0.08 * heat_score + 0.20 * risk_score
        ranked.append(
            {
                "celeb": celeb,
                "tagScore": tag_score,
                "ageScore": age_score,
                "heatScore": heat_score,
                "riskScore": risk_score,
                "final": final,
                "hits": sorted(hits, key=lambda x: x["celeb"], reverse=True)[:4],
            }
        )
    ranked.sort(key=lambda x: x["final"], reverse=True)
    return {"product": product, "tags": opt, "ranked": ranked}


def campaign_for(product: dict, top_name: str) -> dict:
    maps = {
        "cold-brew": {
            "direction": f"把冷萃做成{top_name}的「随身冷静」：训练前后、city walk、通勤都可以开盖。避开高咖啡因焦虑，强调低负担。",
            "slogans": [f"{top_name}同款冷静 · 冷萃即走", "热的是生活，冷的是你", "打开罐，比打开社交更轻"],
        },
        "shoes": {
            "direction": f"用{top_name}的运动真实感带训练场景，科技缓震做产品证据。",
            "slogans": ["这一步，被看见", "轻，是为了再跑一公里", f"{top_name} · 训练日从落地开始"],
        },
        "headphones": {
            "direction": f"把降噪做成情绪边界。{top_name}负责「我需要自己的声音」。",
            "slogans": ["世界先静一下", "你的节奏，入耳生效", f"{top_name} · 把噪音留在舱外"],
        },
    }
    return maps.get(product["id"], {"direction": f"{top_name} × {product['name']}", "slogans": [f"{top_name} × {product['name']}"]})


def load_state() -> dict:
    celeb_doc = _load_json(DATA / "celebrities.json")
    products = _load_json(DATA / "products.json")["products"]
    rows = news_rows()
    payload = rebuild_trends(rows)
    celebs = recount_celebrity_heat(celeb_doc["celebrities"], rows)
    meta_path = DATA / "meta.json"
    meta = _load_json(meta_path) if meta_path.exists() else {}
    state = {
        "trends": payload["tags"],
        "celebrities": celebs,
        "products": products,
        "meta": {
            **meta,
            "server_time": datetime.now().astimezone().isoformat(timespec="seconds"),
            "live": True,
        },
    }
    public = {
        "trends": state["trends"],
        "celebrities": state["celebrities"],
        "products": state["products"],
        "meta": {**state["meta"], "live": False, "public": True},
    }
    (DATA / "state.json").write_text(json.dumps(public, ensure_ascii=False, indent=2), encoding="utf-8")
    return state
