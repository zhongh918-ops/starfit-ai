/* GitHub Pages lives at /starfit-ai/; jsDelivr at /gh/org/repo@version/; local app.py lives at /. */
(function (global) {
  var host = location.hostname || "";
  var path = location.pathname || "";
  var gh = /github\.io$/.test(host);
  var jsd = /jsdelivr\.net$/.test(host);
  var jsdMatch = path.match(/^\/gh\/([^/]+\/[^/@]+)@([^/]+)/);
  var root = gh ? "/starfit-ai" : (jsd && jsdMatch ? "/gh/" + jsdMatch[1] + "@" + jsdMatch[2] : "");
  var href = root ? root + "/" : "/";
  if (!document.querySelector("base")) {
    var el = document.createElement("base");
    el.href = href;
    document.head.insertBefore(el, document.head.firstChild);
  }
  function withBase(p) {
    if (!p || typeof p !== "string") return p;
    if (p.charAt(0) === "#") return p;
    if (root) {
      var twice = root + root;
      while (p.indexOf(twice) !== -1) p = p.split(twice).join(root);
    }
    if (/^https?:\/\//i.test(p)) return p;
    if (root && (p === root || p.indexOf(root + "/") === 0)) return p;
    if (p.charAt(0) === "/") return root + p;
    return p;
  }
  try {
    var pending = sessionStorage.getItem("match99-public-path");
    if (pending && /\/work/.test(location.pathname)) {
      sessionStorage.removeItem("match99-public-path");
      history.replaceState({ work: true }, "", root + pending + location.search + location.hash);
    }
  } catch (e) {}
  function fitApp() {
    try {
      var w = Math.max(window.innerWidth || 0, document.documentElement.clientWidth || 0);
      var h = Math.max(window.innerHeight || 0, document.documentElement.clientHeight || 0);
      if (window.visualViewport) {
        if (window.visualViewport.width) w = window.visualViewport.width;
        if (window.visualViewport.height) h = window.visualViewport.height;
      }
      var s = Math.min(1, (w - 16) / 1464, (h - 16) / 952);
      if (!(s > 0 && isFinite(s))) s = 1;
      document.documentElement.style.setProperty("--app-fit", String(s));
      var nodes = document.querySelectorAll(".app-window, .work-splash-window");
      for (var i = 0; i < nodes.length; i++) {
        nodes[i].style.zoom = String(s);
        nodes[i].style.transform = "none";
        nodes[i].style.margin = "0";
      }
    } catch (e) {}
  }
  fitApp();
  window.addEventListener("resize", fitApp);
  if (window.visualViewport) window.visualViewport.addEventListener("resize", fitApp);
  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", fitApp);
  global.Match99Base = { root: root, href: href, withBase: withBase, isPublic: !!(gh || jsd), fitApp: fitApp };
})(window);
