/*
  Global HTMX modal helpers.

  IMPORTANT:
  - Must not throw if bootstrap/htmx aren't loaded (prevents breaking other JS).
  - Works with Bootstrap 5 Modal API (no jQuery dependency).
*/

(function () {
  function safeInit() {
    if (!window.htmx) return;

    function getModalInstance(modalId) {
      if (!window.bootstrap || !window.bootstrap.Modal) return null;
      const el = document.getElementById(modalId);
      if (!el) return null;
      return window.bootstrap.Modal.getOrCreateInstance(el);
    }

    function hardCleanupModalState() {
      // If anything gets “stuck”, clean it up.
      document.querySelectorAll(".modal-backdrop").forEach((b) => b.remove());
      document.body.classList.remove("modal-open");
      document.body.style.removeProperty("paddingRight");
    }

    // ✅ Open ONLY when a GET swaps content into a dialog target
    window.htmx.on("htmx:afterSwap", (e) => {
      const targetId = e.detail?.target?.id;
      const verb = (e.detail?.requestConfig?.verb || "").toLowerCase();

      if (verb !== "get") return;

      if (targetId === "dialog") getModalInstance("modal")?.show();
      if (targetId === "dialog2") getModalInstance("modal2")?.show();
    });

    // Hide when HTMX returns empty response to a dialog target (typical 204 close)
    window.htmx.on("htmx:beforeSwap", (e) => {
      const targetId = e.detail?.target?.id;

      if (targetId === "dialog" && !e.detail.xhr.response) {
        getModalInstance("modal")?.hide();
        e.detail.shouldSwap = false;
        setTimeout(hardCleanupModalState, 0);
      }

      if (targetId === "dialog2" && !e.detail.xhr.response) {
        getModalInstance("modal2")?.hide();
        e.detail.shouldSwap = false;
        setTimeout(hardCleanupModalState, 0);
      }
    });

    // ✅ Close whichever modal the request originated from ONLY on 204
    // (Prevents the "204 then 200" refresh from messing with the modal state)
    window.htmx.on("htmx:afterRequest", (e) => {
      const status = e.detail?.xhr?.status;
      if (status !== 204) return;

      const src = e.target;
      if (!src || !src.closest) return;

      const modalEl = src.closest(".modal");
      if (!modalEl) return;

      if (modalEl.id !== "modal" && modalEl.id !== "modal2") return;

      getModalInstance(modalEl.id)?.hide();
      setTimeout(hardCleanupModalState, 0);
    });

    // Clear dialogs on close
    document.addEventListener("hidden.bs.modal", (ev) => {
      if (ev.target?.id === "modal") {
        const d = document.getElementById("dialog");
        if (d) d.innerHTML = "";
        hardCleanupModalState();
      }
      if (ev.target?.id === "modal2") {
        const d = document.getElementById("dialog2");
        if (d) d.innerHTML = "";
        hardCleanupModalState();
      }
    });
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", safeInit);
  } else {
    safeInit();
  }
})();