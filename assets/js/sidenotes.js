/*
 * Turns standard Markdown footnotes into sidenotes.
 *
 * Works with kramdown footnotes ([^1] in Markdown) and with posts imported
 * from Substack (scripts/import_substack.py rewrites them to the same markup).
 * Each note is copied next to its first reference as <span class="sidenote">;
 * CSS floats it into the right margin on wide screens. On narrow screens the
 * reference number toggles the note open inline instead of jumping to the end.
 */
(function () {
  "use strict";

  var WIDE = window.matchMedia("(min-width: 1040px)");

  function noteContent(li) {
    var clone = li.cloneNode(true);
    clone.querySelectorAll(".reversefootnote, [role='doc-backlink']").forEach(function (el) {
      el.remove();
    });
    var frag = document.createDocumentFragment();
    Array.prototype.slice.call(clone.childNodes).forEach(function (node) {
      if (node.nodeType === 1 && node.tagName === "P") {
        var span = document.createElement("span");
        span.className = "sn-p";
        span.innerHTML = node.innerHTML.replace(/(&nbsp;|\s)+$/, "");
        frag.appendChild(span);
      } else if (node.nodeType === 1 || node.textContent.trim()) {
        frag.appendChild(node);
      }
    });
    return frag;
  }

  function build(body) {
    var refs = body.querySelectorAll("a.footnote[href^='#'], sup[role='doc-noteref'] > a[href^='#']");
    var seen = {};
    var count = 0;

    Array.prototype.forEach.call(refs, function (a) {
      var id = decodeURIComponent(a.getAttribute("href").slice(1));
      var li = document.getElementById(id);
      if (!li || seen[id]) return;
      seen[id] = true;

      var sup = a.closest("sup") || a;
      var note = document.createElement("span");
      note.className = "sidenote";
      note.id = "sn-" + id;
      note.setAttribute("role", "note");

      var num = document.createElement("span");
      num.className = "sn-num";
      num.textContent = a.textContent.trim();
      note.appendChild(num);
      note.appendChild(noteContent(li));

      // Floats can't escape tables/code blocks; put those notes just before the block.
      var blocker = sup.closest("table, pre, .katex-display");
      if (blocker) blocker.parentNode.insertBefore(note, blocker);
      else sup.parentNode.insertBefore(note, sup.nextSibling);

      a.setAttribute("aria-controls", note.id);
      a.addEventListener("click", function (e) {
        if (WIDE.matches) {
          e.preventDefault();          // note is already visible beside the text
          return;
        }
        e.preventDefault();
        var open = note.classList.toggle("is-open");
        a.setAttribute("aria-expanded", open ? "true" : "false");
      });
      count++;
    });

    if (count > 0) body.classList.add("has-sidenotes");
  }

  document.querySelectorAll(".post-body").forEach(build);
})();
