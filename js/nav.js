(function () {
  const page = document.body.getAttribute("data-page") || "";
  const current = page === "opening" ? "work" : page;
  document.querySelectorAll(".mnav a[data-nav]").forEach((a) => {
    if (a.getAttribute("data-nav") === current) a.setAttribute("aria-current", "page");
    else a.removeAttribute("aria-current");
  });
  if (window.Match99I18n) Match99I18n.applyDom();
})();
