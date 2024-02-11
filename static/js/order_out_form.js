$(document).ready(function(){

    $('#modal-body').on("click change",function(){
        //alert( "Handler for `keyup` called." );
        var price = $('#id_purchase_price').val();
        var percent_markup = $('#id_percent_markup').val();
        var qty = $('#id_quantity').val();

        var markup = (percent_markup / 100) + 1

        markup = Number(markup)
        
  
        var total = price * markup
        total = total.toFixed(2);
        total = Number(total)
  
        var override = $("#id_override_price").val();
        override = Number(override)

        if (override >= .01 ){
            var total = $('#id_override_price').val();
          } else {
            $('#id_total_price').val(total);
          }

          

        price_ea = total / qty
        price_ea = price_ea.toFixed(4)

        $('#price_ea').val(price_ea);
        document.getElementById("id_price_ea").innerHTML = price_ea;

    });
});