/* GitHub Pages lives at /starfit-ai/; local app.py lives at /. */
(function (global) {
  var gh = /github\.io$/.test(location.hostname);
  var root = gh ? "/starfit-ai" : "";
  var href = gh ? "/starfit-ai/" : "/";
  if (!document.querySelector("base")) {
    var el = document.createElement("base");
    el.href = href;
    document.head.insertBefore(el, document.head.firstChild);
  }
  function withBase(path) {
    if (!path) return path;
    if (/^https?:\/\//i.test(path) || path.charAt(0) === "#") return path;
    if (path.charAt(0) === "/") return root + path;
    return path;
  }
  try {
    var pending = sessionStorage.getItem("match99-public-path");
    if (pending && /\/work/.test(location.pathname)) {
      sessionStorage.removeItem("match99-public-path");
      history.replaceState({ work: true }, "", root + pending + location.search + location.hash);
    }
  } catch (e) {}
  global.Match99Base = { root: root, href: href, withBase: withBase, isPublic: gh };
})(window);
