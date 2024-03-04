$(document).ready(function(){

    $('#modal-body').on("click change load",function(){
        //alert( "Handler for `keyup` called." );
        var price = $('#set_price').val();
        var setqty = $('#set_qty').val();
        var qty = $('#id_quantity').val();

        var override = $('#id_override_price').val();

        var totalpieces = setqty * qty
        totalpieces = Number(totalpieces)

        var totalprice = qty * price
        totalprice = Number(totalprice)

        var override = $("#id_override_price").val();
        override = Number(override)

        if (override >= .01 ){
            var totalprice = $('#id_override_price').val();
          } else {
            
          }

        var unitprice = totalprice / totalpieces
        unitprice = unitprice.toFixed(4)

        totalprice = totalprice.toFixed(2)

        unitprice = Number(unitprice)
        totalprice = Number(totalprice)
        

        $('#id_unit_price').val(unitprice);
        
        
        $('#id_total_price').val(totalprice);
        
        //$('#id_total_pieces').val(totalpieces);
        $('#id_total_pieces').val(totalpieces);





        /*
        
        $('#price_ea').val(price_ea);
        
        
        
        
        
        

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
        document.getElementById("id_price_ea").innerHTML = price_ea;*/

    });
});