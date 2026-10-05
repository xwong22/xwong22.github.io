(function () {
  "use strict";

  // Light / dark toggle (remembers the choice; otherwise follows the OS setting).
  var root = document.documentElement;
  var toggle = document.querySelector(".theme-toggle");
  if (toggle) {
    toggle.addEventListener("click", function () {
      var current = root.getAttribute("data-theme") ||
        (window.matchMedia("(prefers-color-scheme: dark)").matches ? "dark" : "light");
      var next = current === "dark" ? "light" : "dark";
      root.setAttribute("data-theme", next);
      try { localStorage.setItem("theme", next); } catch (e) {}
    });
  }

  // Abstract / BibTeX toggles on publication entries.
  document.querySelectorAll(".pub-toggle").forEach(function (btn) {
    btn.addEventListener("click", function () {
      var target = document.getElementById(btn.getAttribute("aria-controls"));
      if (!target) return;
      var open = btn.getAttribute("aria-expanded") !== "true";
      btn.setAttribute("aria-expanded", open ? "true" : "false");
      target.hidden = !open;
    });
  });

  // Margin notes: tap the ⊕ to open on small screens.
  document.querySelectorAll(".marginnote-toggle").forEach(function (btn) {
    btn.addEventListener("click", function () {
      var note = btn.nextElementSibling;
      if (note) note.classList.toggle("is-open");
    });
  });
})();
