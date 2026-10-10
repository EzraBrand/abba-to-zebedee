// Filter, sort, footnote pop-ups and table-of-contents highlight. No dependencies.
(function () {
  "use strict";
  const NIKUD = /[֑-ׇ]/g;
  const norm = (s) => s.normalize("NFC").replace(NIKUD, "").replace(/[״"׳']/g, "").toLowerCase();

  // ---- open external links in a new tab
  document.querySelectorAll('main a[href^="http"]').forEach((a) => {
    a.target = "_blank";
    a.rel = "noopener";
  });

  // ---- filter all name-list rows
  const input = document.getElementById("name-filter");
  const count = document.getElementById("filter-count");
  const rows = Array.from(document.querySelectorAll(".name-list .nl-row:not(.nl-head)"));
  rows.forEach((r) => { r._text = norm(r.textContent); });
  let timer;
  function applyFilter() {
    const q = norm(input.value.trim());
    let shown = 0;
    rows.forEach((r) => {
      const hit = !q || r._text.includes(q);
      r.classList.toggle("hidden", !hit);
      if (hit) shown++;
    });
    document.querySelectorAll(".name-list").forEach((list) => {
      const any = list.querySelector(".nl-row:not(.nl-head):not(.hidden)");
      list.classList.toggle("hidden", !!q && !any);
    });
    count.textContent = q ? `${shown} of ${rows.length}` : "";
    const params = new URLSearchParams(location.search);
    q ? params.set("q", input.value.trim()) : params.delete("q");
    history.replaceState(null, "", `${location.pathname}${params.toString() ? "?" + params : ""}${location.hash}`);
  }
  if (input) {
    input.addEventListener("input", () => { clearTimeout(timer); timer = setTimeout(applyFilter, 120); });
    const q0 = new URLSearchParams(location.search).get("q");
    if (q0) { input.value = q0; applyFilter(); }
  }

  // ---- sort a name list by clicking a column title (third click restores the order)
  const collator = new Intl.Collator(["he", "en"], { sensitivity: "base", numeric: true });
  document.querySelectorAll(".name-list").forEach((list) => {
    const head = list.querySelector(".nl-head");
    if (!head) return;
    const body = Array.from(list.querySelectorAll(".nl-row:not(.nl-head)"));
    body.forEach((r, i) => { r._order = i; });
    Array.from(head.children).forEach((col, ci) => {
      col.setAttribute("role", "button");
      col.tabIndex = 0;
      const sort = () => {
        const state = col.getAttribute("aria-sort");
        const next = state === "ascending" ? "descending" : state === "descending" ? null : "ascending";
        Array.from(head.children).forEach((c) => c.removeAttribute("aria-sort"));
        const sorted = body.slice().sort((a, b) => {
          if (!next) return a._order - b._order;
          const r = collator.compare(norm(a.children[ci].textContent.trim()), norm(b.children[ci].textContent.trim()));
          return next === "ascending" ? r : -r;
        });
        if (next) col.setAttribute("aria-sort", next);
        sorted.forEach((r) => list.appendChild(r));
      };
      col.addEventListener("click", sort);
      col.addEventListener("keydown", (e) => { if (e.key === "Enter" || e.key === " ") { e.preventDefault(); sort(); } });
    });
  });

  // ---- sort data tables by column
  document.querySelectorAll(".data-table table").forEach((table) => {
    const tbody = table.tBodies[0];
    const orig = Array.from(tbody.rows);
    Array.from(table.tHead.rows[0].cells).forEach((th, ci) => {
      th.addEventListener("click", () => {
        const dir = th.dataset.dir === "asc" ? "desc" : th.dataset.dir === "desc" ? "" : "asc";
        Array.from(table.tHead.rows[0].cells).forEach((c) => delete c.dataset.dir);
        if (dir) th.dataset.dir = dir;
        const val = (r) => r.cells[ci].textContent.trim();
        const rowsSorted = !dir ? orig : orig.slice().sort((a, b) => {
          const x = val(a), y = val(b), nx = parseFloat(x), ny = parseFloat(y);
          const r = !isNaN(nx) && !isNaN(ny) ? nx - ny : collator.compare(x, y);
          return dir === "asc" ? r : -r;
        });
        rowsSorted.forEach((r) => tbody.appendChild(r));
      });
    });
  });

  // ---- footnote pop-ups
  let pop;
  function hidePop() { if (pop) { pop.remove(); pop = null; } }
  document.querySelectorAll("a.footnote-ref").forEach((a) => {
    const id = decodeURIComponent(a.getAttribute("href").slice(1));
    const note = document.getElementById(id);
    if (!note) return;
    const show = () => {
      hidePop();
      pop = document.createElement("div");
      pop.className = "fn-pop";
      pop.innerHTML = note.innerHTML.replace(/<a [^>]*class="footnote-back"[^>]*>.*?<\/a>/g, "");
      document.body.appendChild(pop);
      const r = a.getBoundingClientRect();
      const left = Math.min(window.scrollX + r.left, window.scrollX + document.documentElement.clientWidth - pop.offsetWidth - 12);
      pop.style.left = Math.max(8, left) + "px";
      pop.style.top = window.scrollY + r.bottom + 6 + "px";
      pop.addEventListener("mouseleave", hidePop);
    };
    a.addEventListener("mouseenter", show);
    a.addEventListener("focus", show);
  });
  document.addEventListener("click", (e) => { if (pop && !pop.contains(e.target)) hidePop(); });
  document.addEventListener("keydown", (e) => { if (e.key === "Escape") hidePop(); });

  // ---- highlight the current section in the table of contents
  const toc = document.getElementById("toc");
  if (toc && "IntersectionObserver" in window) {
    const links = new Map(Array.from(toc.querySelectorAll("a")).map((a) => [decodeURIComponent(a.hash.slice(1)), a]));
    const heads = Array.from(document.querySelectorAll("main h1[id], main h2[id], main h3[id]")).filter((h) => links.has(h.id));
    const obs = new IntersectionObserver((entries) => {
      entries.forEach((en) => {
        if (en.isIntersecting) {
          links.forEach((a) => a.classList.remove("active"));
          toc.querySelectorAll("li.active-parent").forEach((li) => li.classList.remove("active-parent"));
          const a = links.get(en.target.id);
          a.classList.add("active");
          for (let li = a.parentElement.parentElement.closest("li"); li; li = li.parentElement.closest("li")) {
            li.classList.add("active-parent");
          }
          a.scrollIntoView({ block: "nearest" });
        }
      });
    }, { rootMargin: "-10% 0px -80% 0px" });
    heads.forEach((h) => obs.observe(h));
  }
})();
