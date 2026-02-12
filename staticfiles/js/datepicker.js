/*
  Safe, idempotent datepicker wiring.
  - Avoids throwing if jQuery UI isn't loaded yet.
  - Only attaches to elements that exist.
*/

(function () {
  function initDatepickers() {
    if (!window.jQuery) return;
    const $ = window.jQuery;

    // jQuery UI datepicker not present? bail quietly.
    if (!$.fn || typeof $.fn.datepicker !== "function") return;

    // Add whatever selectors your project uses here.
    const selectors = [
      ".datepicker",
      'input[type="date"].use-datepicker',
      'input[data-datepicker="1"]',
    ];

    selectors.forEach((sel) => {
      $(sel).each(function () {
        const $el = $(this);

        // Prevent double-init
        if ($el.data("datepicker-initialized")) return;
        $el.data("datepicker-initialized", true);

        // Basic, safe defaults
        $el.datepicker({
          dateFormat: "mm/dd/yy",
          changeMonth: true,
          changeYear: true,
        });
      });
    });
  }

  // Run when DOM is ready (safe even if loaded late)
  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", initDatepickers);
  } else {
    initDatepickers();
  }
})();




/*$( function() {
    $( "#id_date_recieved" ).datepicker();
  } );

$( function() {
    $( "#id_discount_date_due" ).datepicker();
  } );

$( function() {
    $( "#id_date_paid" ).datepicker();
  } );

$( function() {
    $( "#id_date" ).datepicker();
  } );

$( function() {
  $( "#id_deadline" ).datepicker();
} );

$( function() {
  $( "#id_invoice_date" ).datepicker();
} );

$( function() {
  $( "#id_invoice_date" ).datepicker();
} );

$( function() {
  $( "#id_date_due" ).datepicker();
} );

$( function() {
  $( "#date_paid" ).datepicker();
} );

$( function() {
  $( "#id_start_date" ).datepicker();
} );

$( function() {
  $( "#id_end_date" ).datepicker();
} ); */