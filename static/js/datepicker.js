(function () {
  function hasJquiDatepicker() {
    return !!(window.jQuery && window.jQuery.fn && typeof window.jQuery.fn.datepicker === "function");
  }

  function initDatepickers(root) {
    if (!hasJquiDatepicker()) return;

    const $ = window.jQuery;
    const $root = root ? $(root) : $(document);

    // ✅ support BOTH conventions site-wide
    const selector = "input.datepicker, input.dateinput, input[data-datepicker='1']";

    $root.find(selector).each(function () {
      const $el = $(this);

      // prevent double-init (jQuery UI adds this class)
      if ($el.hasClass("hasDatepicker")) return;

      $el.attr("autocomplete", "off");

      $el.datepicker({
        dateFormat: "mm/dd/yy",
        changeMonth: true,
        changeYear: true,
      });
    });
  }

  // expose globally (so you can call it from templates if needed)
  window.initDatepickers = initDatepickers;

  // DOM ready
  document.addEventListener("DOMContentLoaded", function () {
    initDatepickers(document);
  });

  // HTMX content swaps
  document.addEventListener("htmx:load", function (e) {
    initDatepickers(e.target);
  });

  // Bootstrap modal shown
  document.addEventListener("shown.bs.modal", function (e) {
    initDatepickers(e.target);
  });

  // ✅ Most reliable for HTMX swaps
  document.body.addEventListener("htmx:afterSwap", function (e) {
    initDatepickers(e.target);
  });

  // (Optional) also afterSettle for cases where the DOM finishes later
  document.body.addEventListener("htmx:afterSettle", function (e) {
    initDatepickers(e.target);
  });
})();