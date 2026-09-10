/* Talent Library: render the ten-person fixture. Never invent people or scores. */
(function () {
  const MODE_KEY = "match99-data-mode";
  const CONSIDER_KEY = "match99-consider";
  const SHORT_KEY = "match99-library-shortlist";
  const OCC_ZH = {
    Actor: "演员", Actress: "演员", Performer: "艺人", Creator: "创作者",
    Athlete: "运动员", Host: "主持人", Dancer: "舞者", Choreographer: "编舞",
    Musician: "音乐人", Producer: "制作人",
    "Wellness Founder": "健康品牌创始人", "Endurance Athlete": "耐力运动员",
    "Documentary Creator": "纪录片创作者", "Fashion Model": "时装模特",
    "Creative Director": "创意总监", "Technology Creator": "科技创作者",
    "Gaming Host": "电竞主持"
  };
  const TAG_ZH = {
    sports: "运动", technology: "科技", energy: "活力", health: "健康",
    wellness: "健康", style: "时尚", "youth-culture": "青年文化",
    discipline: "自律", urban: "都市", outdoor: "户外", trust: "信任",
    music: "音乐", culture: "文化", design: "设计", gaming: "游戏", movement: "律动"
  };

  function t(key, vars) { return window.Match99I18n ? Match99I18n.t(key, vars) : key; }
  function isZh() { return !!(window.Match99I18n && Match99I18n.isZh()); }
  function roleLabel(occ) { return isZh() ? (OCC_ZH[occ] || occ) : occ; }
  function tagLabel(row) {
    if (isZh() && row && TAG_ZH[row.id]) return TAG_ZH[row.id];
    return (row && row.label) || "";
  }

  function mode() {
    try {
      const m = localStorage.getItem(MODE_KEY);
      if (m === "live" || m === "demo") return m;
    } catch (e) {}
    return "demo";
  }

  function setMode(next) {
    if (next === mode()) return;
    if (!confirm(t("mode.confirm"))) return;
    try { localStorage.setItem(MODE_KEY, next); } catch (e) {}
    try { sessionStorage.removeItem("match99-work"); } catch (e) {}
    location.reload();
  }

  function paintMode() {
    const el = document.getElementById("modeBadge");
    if (!el) return;
    const live = mode() === "live";
    el.textContent = live ? t("mode.liveBadge") : t("mode.demoBadge");
    el.classList.toggle("live", live);
  }

  function marketLabel(m) {
    if (!m) return "";
    if (isZh() && (m === "Mainland China" || m === "China")) return "中国大陆";
    return m;
  }

  function confLabel(level) {
    const lv = String(level || "medium").toLowerCase();
    const mapped = t("lvl." + (lv === "low-medium" ? "lowmed" : lv));
    const shown = mapped.indexOf("lvl.") === 0 ? lv : mapped;
    return t("lib.conf", { level: shown });
  }

  function readList(key) {
    try {
      const v = JSON.parse(sessionStorage.getItem(key) || "[]");
      return Array.isArray(v) ? v : [];
    } catch (e) { return []; }
  }

  function writeList(key, ids) {
    try { sessionStorage.setItem(key, JSON.stringify(ids)); } catch (e) {}
  }

  function feeLabel(c) {
    const r = c.commercial && c.commercial.feeRangeCny;
    if (!r || r.min == null) return t("common.unavailable");
    const a = (r.min / 1000000).toFixed(r.min % 1000000 ? 1 : 0);
    const b = (r.max / 1000000).toFixed(r.max % 1000000 ? 1 : 0);
    return t("lib.feeFmt", { a: a, b: b });
  }

  function riskKey(c) {
    const rp = (c.risk && c.risk.profile) || {};
    const conflict = String(rp.categoryConflict || "");
    if (conflict === "hold") return "high";
    if (conflict === "unverified") return "unverified";
    return String((c.risk && c.risk.level) || "medium");
  }

  function budgetMatch(c, band) {
    const r = c.commercial && c.commercial.feeRangeCny;
    if (!r) return false;
    const mid = (Number(r.min) + Number(r.max)) / 2;
    if (band === "under5") return mid < 5000000;
    if (band === "5to8") return mid >= 5000000 && mid < 8000000;
    if (band === "8to12") return mid >= 8000000 && mid <= 12000000;
    if (band === "over12") return mid > 12000000;
    return true;
  }

  function params() {
    return new URLSearchParams(location.search);
  }

  function writeParams(obj) {
    const u = new URL(location.href);
    ["q", "role", "audience", "market", "budget", "risk", "layout", "view"].forEach((k) => {
      if (obj[k]) u.searchParams.set(k, obj[k]);
      else u.searchParams.delete(k);
    });
    history.replaceState({ library: true }, "", u.pathname + u.search);
  }

  function withBase(path) {
    return window.Match99Base ? Match99Base.withBase(path) : path;
  }

  function portrait(c) {
    return withBase(c.portrait || ("/assets/portraits/" + (c.slug || "") + ".png"));
  }

  let all = [];
  let railView = "all";
  let roleOptions = [];
  let datasetKey = "candidate_fixture_cn_v1@1.1.0";

  function fillRoleSelect() {
    const roleSel = document.getElementById("fRole");
    if (!roleSel) return;
    const cur = roleSel.value;
    roleSel.innerHTML = '<option value="">' + t("lib.role") + "</option>"
      + roleOptions.map((r) => '<option value="' + r + '">' + roleLabel(r) + "</option>").join("");
    if (cur) roleSel.value = cur;
  }

  function paintMeta() {
    const status = document.getElementById("libStatus");
    const fixture = document.getElementById("libFixture");
    if (status) status.textContent = t("lib.status", { n: String(all.length) });
    if (fixture) fixture.textContent = t("lib.fixture", { id: datasetKey });
  }

  function filtered() {
    const q = (document.getElementById("libSearch").value || "").trim().toLowerCase();
    const role = document.getElementById("fRole").value;
    const audience = document.getElementById("fAudience").value;
    const market = document.getElementById("fMarket").value;
    const budget = document.getElementById("fBudget").value;
    const risk = document.getElementById("fRisk").value;
    const consider = new Set(readList(CONSIDER_KEY));
    const shorted = new Set(readList(SHORT_KEY));
    return all.filter((c) => {
      if (railView === "shortlist" && !shorted.has(c.id)) return false;
      if (railView === "added" && !consider.has(c.id)) return false;
      if (q) {
        const blob = [
          c.name,
          (c.occupations || []).map(roleLabel).join(" "),
          (c.occupations || []).join(" "),
          (c.personaTags || []).map(tagLabel).join(" "),
          marketLabel(c.market)
        ].join(" ").toLowerCase();
        if (!blob.includes(q)) return false;
      }
      if (role && !(c.occupations || []).includes(role)) return false;
      if (audience && c.ageBand !== audience) return false;
      if (market && c.market !== market) return false;
      if (budget && !budgetMatch(c, budget)) return false;
      if (risk && riskKey(c) !== risk) return false;
      return true;
    });
  }

  function render() {
    const layout = document.getElementById("viewList").classList.contains("on") ? "list" : "grid";
    const rows = filtered();
    const consider = new Set(readList(CONSIDER_KEY));
    const grid = document.getElementById("libCards");
    grid.classList.toggle("list", layout === "list");
    document.getElementById("libEmpty").hidden = rows.length > 0;
    document.getElementById("libCount").textContent = t("lib.count", { n: String(rows.length) });
    grid.innerHTML = rows.map((c) => {
      const tags = (c.personaTags || []).slice(0, 3);
      const added = consider.has(c.id);
      return '<article class="lib-card" data-id="' + c.id + '">'
        + '<div class="lib-photo"><img src="' + portrait(c) + '" alt="' + (c.name || "") + '"><span class="lib-demo-tag">' + t("lib.demoTag") + "</span></div>"
        + '<div class="lib-card-content"><div class="lib-name-row"><div><div class="lib-name">' + c.name + '</div>'
        + '<div class="lib-role">' + (c.occupations || []).map(roleLabel).join(" · ") + " · " + marketLabel(c.market) + " · " + (c.ageBand || "") + "</div></div>"
        + '<span class="lib-conf">' + confLabel(c.provenance && c.provenance.confidence) + "</span></div>"
        + '<div class="lib-tags">' + tags.map((row) => '<span class="lib-tag">' + tagLabel(row) + "</span>").join("") + "</div>"
        + '<div class="lib-meta"><span>' + t("lib.fee") + "</span><strong>" + feeLabel(c) + "</strong></div>"
        + '<div class="lib-actions">'
        + '<a class="lib-action" href="' + withBase("/work/candidates/" + encodeURIComponent(c.id) + "/overview") + '">' + t("lib.view") + "</a>"
        + '<button type="button" class="lib-action primary" data-add="' + c.id + '"' + (added ? " disabled" : "") + ">" + (added ? t("lib.addedBtn") : t("lib.add")) + "</button>"
        + "</div></div></article>";
    }).join("");
    writeParams({
      q: document.getElementById("libSearch").value || "",
      role: document.getElementById("fRole").value,
      audience: document.getElementById("fAudience").value,
      market: document.getElementById("fMarket").value,
      budget: document.getElementById("fBudget").value,
      risk: document.getElementById("fRisk").value,
      layout: layout,
      view: railView !== "all" ? railView : ""
    });
  }

  paintMode();

  document.getElementById("accountBtn").addEventListener("click", () => {
    const menu = document.getElementById("accountMenu");
    const open = menu.hidden;
    menu.hidden = !open;
    document.getElementById("accountBtn").setAttribute("aria-expanded", open ? "true" : "false");
  });
  document.addEventListener("click", (e) => {
    if (!e.target.closest(".account-wrap")) {
      document.getElementById("accountMenu").hidden = true;
      document.getElementById("accountBtn").setAttribute("aria-expanded", "false");
    }
  });
  document.getElementById("modeDemo").addEventListener("click", () => setMode("demo"));
  document.getElementById("modeLive").addEventListener("click", () => setMode("live"));

  document.querySelectorAll(".library-rail .nav-btn[data-view]").forEach((btn) => {
    btn.addEventListener("click", () => {
      if (btn.disabled) return;
      railView = btn.getAttribute("data-view");
      document.querySelectorAll(".library-rail .nav-btn[data-view]").forEach((b) => b.classList.toggle("on", b === btn));
      render();
    });
  });

  document.getElementById("viewGrid").addEventListener("click", () => {
    document.getElementById("viewGrid").classList.add("on");
    document.getElementById("viewList").classList.remove("on");
    render();
  });
  document.getElementById("viewList").addEventListener("click", () => {
    document.getElementById("viewList").classList.add("on");
    document.getElementById("viewGrid").classList.remove("on");
    render();
  });
  document.getElementById("libClear").addEventListener("click", () => {
    document.getElementById("libSearch").value = "";
    document.getElementById("fRole").value = "";
    document.getElementById("fAudience").value = "";
    document.getElementById("fMarket").value = "";
    document.getElementById("fBudget").value = "";
    document.getElementById("fRisk").value = "";
    railView = "all";
    document.querySelectorAll(".library-rail .nav-btn[data-view]").forEach((b) => b.classList.toggle("on", b.getAttribute("data-view") === "all"));
    render();
  });
  ["libSearch", "fRole", "fAudience", "fMarket", "fBudget", "fRisk"].forEach((id) => {
    document.getElementById(id).addEventListener("input", render);
    document.getElementById(id).addEventListener("change", render);
  });
  document.getElementById("libCards").addEventListener("click", (e) => {
    const add = e.target.closest("[data-add]");
    if (!add) return;
    const id = add.getAttribute("data-add");
    const ids = readList(CONSIDER_KEY);
    if (!ids.includes(id)) ids.push(id);
    writeList(CONSIDER_KEY, ids);
    render();
  });

  fetch("/api/state?mode=" + encodeURIComponent(mode()), { cache: "no-store" })
    .then((r) => {
      const ct = r.headers.get("content-type") || "";
      if (r.ok && ct.indexOf("json") >= 0) return r.json();
      throw new Error("static");
    })
    .catch(() => fetch("data/state.json?t=" + Date.now(), { cache: "no-store" }).then((r) => {
      if (!r.ok) throw new Error("load fail");
      return r.json();
    }))
    .then((data) => {
      all = data.celebrities || [];
      const roles = [...new Set(all.flatMap((c) => c.occupations || []))].sort();
      const audiences = [...new Set(all.map((c) => c.ageBand).filter(Boolean))].sort();
      const markets = [...new Set(all.map((c) => c.market).filter(Boolean))].sort();
      roleOptions = roles;
      fillRoleSelect();
      if (params().get("role")) document.getElementById("fRole").value = params().get("role");
      const aud = document.getElementById("fAudience");
      audiences.forEach((a) => {
        const o = document.createElement("option");
        o.value = a; o.textContent = a;
        aud.appendChild(o);
      });
      const mkt = document.getElementById("fMarket");
      markets.forEach((a) => {
        const o = document.createElement("option");
        o.value = a; o.textContent = marketLabel(a);
        mkt.appendChild(o);
      });
      const p = params();
      if (p.get("q")) document.getElementById("libSearch").value = p.get("q");
      if (p.get("audience")) document.getElementById("fAudience").value = p.get("audience");
      if (p.get("market")) document.getElementById("fMarket").value = p.get("market");
      if (p.get("budget")) document.getElementById("fBudget").value = p.get("budget");
      if (p.get("risk")) document.getElementById("fRisk").value = p.get("risk");
      if (p.get("layout") === "list") {
        document.getElementById("viewList").classList.add("on");
        document.getElementById("viewGrid").classList.remove("on");
      }
      if (p.get("view")) {
        railView = p.get("view");
        document.querySelectorAll(".library-rail .nav-btn[data-view]").forEach((b) => b.classList.toggle("on", b.getAttribute("data-view") === railView));
      }
      const demo = data.demo || {};
      datasetKey = demo.datasetKey || datasetKey;
      paintMeta();
      if (window.Match99I18n) Match99I18n.applyDom();
      render();
    })
    .catch((err) => {
      document.getElementById("libEmpty").hidden = false;
      document.getElementById("libEmpty").textContent = t("lib.loadFail") + " " + err;
    });

  if (window.Match99I18n) {
    Match99I18n.onChange(function () {
      paintMode();
      fillRoleSelect();
      const mkt = document.getElementById("fMarket");
      if (mkt) {
        [...mkt.options].forEach((o) => {
          if (o.value) o.textContent = marketLabel(o.value);
        });
      }
      if (window.Match99I18n) Match99I18n.applyDom();
      paintMeta();
      render();
    });
  }
})();
