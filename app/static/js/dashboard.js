/**
 * Manosamvada — Dashboard Interaction Layer
 * Handles session search and CSV export triggering.
 */

(function () {
  "use strict";

  const searchInput = document.getElementById("dashboard-search");
  const resultsEl = document.getElementById("search-results");
  let debounceTimer = null;

  if (searchInput) {
    searchInput.addEventListener("input", () => {
      clearTimeout(debounceTimer);
      const query = searchInput.value.trim();

      if (!query) {
        resultsEl.innerHTML = "";
        return;
      }

      debounceTimer = setTimeout(async () => {
        try {
          const res = await fetch(`/dashboard/search?q=${encodeURIComponent(query)}`);
          const data = await res.json();

          if (!data.results.length) {
            resultsEl.innerHTML = '<div class="empty-state">No conversations match your search.</div>';
            return;
          }

          resultsEl.innerHTML = data.results
            .map(
              (r) => `
              <a href="/chat/?session=${r.id}" class="session-item" style="display:block; padding:12px; border-bottom:1px solid var(--border-soft);">
                ${r.title}
              </a>`
            )
            .join("");
        } catch (err) {
          console.error("Search error:", err);
        }
      }, 300);
    });
  }
})();
