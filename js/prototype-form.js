(function () {
  const form = document.querySelector("[data-prototype-form]");
  if (!form) return;
  const success = form.querySelector(".form-success");
  const error = form.querySelector(".form-error");

  form.addEventListener("submit", (e) => {
    e.preventDefault();
    if (success) success.classList.remove("show");
    if (error) error.classList.remove("show");

    const required = [...form.querySelectorAll("[data-required]")];
    const missing = required.filter((el) => {
      if (el.type === "checkbox") return !el.checked;
      if (el.type === "radio") {
        const name = el.name;
        return !form.querySelector(`input[name="${name}"]:checked`);
      }
      return !String(el.value || "").trim();
    });

    const email = form.querySelector('input[type="email"]');
    const emailOk = email && /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email.value.trim());

    if (missing.length || (email && !emailOk)) {
      if (error) {
        error.textContent = (window.Match99I18n && Match99I18n.t("form.required")) || "Please complete the required fields. Nothing was sent.";
        error.classList.add("show");
      }
      return;
    }

    form.reset();
    if (success) {
      success.textContent = (window.Match99I18n && Match99I18n.t("form.prototypeOnly")) || "Prototype only — no data was submitted.";
      success.classList.add("show");
    }
  });
})();
