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

    window.htmx.on("htmx:afterSwap", (e) => {
      const targetId = e.detail?.target?.id;
      if (targetId === "dialog") getModalInstance("modal")?.show();
      if (targetId === "dialog2") getModalInstance("modal2")?.show();
    });

    window.htmx.on("htmx:beforeSwap", (e) => {
      const targetId = e.detail?.target?.id;

      if (targetId === "dialog" && !e.detail.xhr.response) {
        getModalInstance("modal")?.hide();
        e.detail.shouldSwap = false;
      }

      if (targetId === "dialog2" && !e.detail.xhr.response) {
        getModalInstance("modal2")?.hide();
        e.detail.shouldSwap = false;
      }
    });

    // Clear dialogs on close
    document.addEventListener("hidden.bs.modal", (ev) => {
      if (ev.target?.id === "modal") {
        const d = document.getElementById("dialog");
        if (d) d.innerHTML = "";
      }
      if (ev.target?.id === "modal2") {
        const d = document.getElementById("dialog2");
        if (d) d.innerHTML = "";
      }
    });
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