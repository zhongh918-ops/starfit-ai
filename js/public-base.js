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
    if (/^https?:\/\//i.test(p) || p.charAt(0) === "#") return p;
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
  global.Match99Base = { root: root, href: href, withBase: withBase, isPublic: !!(gh || jsd) };
})(window);
