$(document).load(function () {
    $("#id_customer").select2();
    $('#id_customer').on('select2:select', (e) => {
      htmx.trigger("#id_customer", "change")
    });
  })