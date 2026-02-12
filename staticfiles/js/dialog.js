/*
  Global HTMX modal helpers.

  IMPORTANT:
  - Must not throw if bootstrap/htmx aren't loaded (prevents breaking other JS).
  - Works with Bootstrap 5 Modal API (no jQuery dependency).
*/

(function () {
  function safeInit() {
    if (!window.htmx) return;

    function ensureModal(id) {
      if (!window.bootstrap || !window.bootstrap.Modal) return null;
      const el = document.getElementById(id);
      if (!el) return null;
      return window.bootstrap.Modal.getOrCreateInstance(el);
    }

    const modal = ensureModal("modal");
    const modal2 = ensureModal("modal2");

    // If bootstrap isn't loaded yet, just don't wire modal behavior.
    if (!modal && !modal2) return;

    window.htmx.on("htmx:afterSwap", (e) => {
      const targetId = e.detail && e.detail.target && e.detail.target.id;
      if (targetId === "dialog" && modal) modal.show();
      if (targetId === "dialog2" && modal2) modal2.show();
    });

    window.htmx.on("htmx:beforeSwap", (e) => {
      const targetId = e.detail && e.detail.target && e.detail.target.id;

      if (targetId === "dialog" && modal && !e.detail.xhr.response) {
        modal.hide();
        e.detail.shouldSwap = false;
      }

      if (targetId === "dialog2" && modal2 && !e.detail.xhr.response) {
        modal2.hide();
        e.detail.shouldSwap = false;
      }
    });

    // Clear dialogs on close
    const m1 = document.getElementById("modal");
    if (m1) {
      m1.addEventListener("hidden.bs.modal", () => {
        const d = document.getElementById("dialog");
        if (d) d.innerHTML = "";
      });
    }

    const m2 = document.getElementById("modal2");
    if (m2) {
      m2.addEventListener("hidden.bs.modal", () => {
        const d = document.getElementById("dialog2");
        if (d) d.innerHTML = "";
      });
    }
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", safeInit);
  } else {
    safeInit();
  }
})();



/*;(function () {

  const modal = new bootstrap.Modal(document.getElementById("NewCustomerModal"))

    htmx.on("htmx:afterSwap", (e) => {
      // Response targeting #dialog => show the modal
      if (e.detail.target.id == "newcustomerdialog") {
        $("#NewCustomerModal").modal("show")
      }
    })
  
    htmx.on("htmx:beforeSwap", (e) => {
      console.log("htmx:beforeSwap", e)
      // Empty response targeting #dialog => hide the modal
      if (e.detail.target.id == "dialog" && !e.detail.xhr.response) {
        $("#modal").modal("hide")
        e.detail.shouldSwap = false
      }
    })
  
    // Remove dialog content after hiding
    $("#modal").on("hidden.bs.modal", () => {
      $("#dialog").empty()
    })
  })()*/