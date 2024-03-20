$(document).ready(function(){

    //Hide job steps until needed
      $('#perf-row').hide()

      $('#show-perf').click(function(){
      $('#perf-row').slideToggle(200)
      });

      $('#numbering-row').hide()

      $('#show-numbering').click(function(){
      $('#numbering-row').slideToggle(200)
      });

      $('#wrap-row').hide()

      $('#show-wraparound').click(function(){
      $('#wrap-row').slideToggle(200)
      });

      $('#mailmerge-row').hide()

      $('#show-mailmerge').click(function(){
      $('#mailmerge-row').slideToggle(200)
      });

      $('#padding-row').hide()

      $('#show-padding').click(function(){
      $('#padding-row').slideToggle(200)
      });

      $('#drill-row').hide()

      $('#show-drill').click(function(){
      $('#drill-row').slideToggle(200)
      });

      $('#staple-row').hide()

      $('#show-staple').click(function(){
      $('#staple-row').slideToggle(200)
      });

      $('#fold-row').hide()

      $('#show-fold').click(function(){
      $('#fold-row').slideToggle(200)
      });

      $('#tab-row').hide()

      $('#show-tab').click(function(){
      $('#tab-row').slideToggle(200)
      });

      $('#bulkmail-row').hide()

      $('#show-bulkmail').click(function(){
      $('#bulkmail-row').slideToggle(200)
      });

      $('#misc1-row').hide()

      $('#show-misc1').click(function(){
      $('#misc1-row').slideToggle(200)
      });

      $('#misc2-row').hide()

      $('#show-misc2').click(function(){
      $('#misc2-row').slideToggle(200)
      });

      $('#misc3-row').hide()

      $('#show-misc3').click(function(){
      $('#misc3-row').slideToggle(200)
      });

      $('#misc4-row').hide()

      $('#show-misc4').click(function(){
      $('#misc4-row').slideToggle(200)
      });


      /*$('#id_container').on("click change load",function(){

        var test1 = $('#test1').val();
        var test2 = $('#test2').val();
        var price = $('#id_price_per').val();

        //$('#first_test').val(test1);
        //$('#second_test').val(test1);

        document.getElementById("first_test").innerHTML = price;
        document.getElementById("second_test").innerHTML = test2;


        //$('#id_price_total').val(price);


      });*/

      $('#id_container').on("click change load",function(){

        var workorder_price = $('#id_step_workorder_price').val();
        var reclaim_artwork_price = $('#id_step_reclaim_artwork_price').val();
        var send_to_press_price = $('#id_step_send_to_press_price').val();
        var count_package_price = $('#id_step_count_package_price').val();
        var delivery_price = $('#id_step_delivery_price').val();
        var packing_slip_price = $('#id_step_packing_slip_price').val();
        send_to_press_price = Number(send_to_press_price);
        workorder_price = Number(workorder_price);
        reclaim_artwork_price = Number(reclaim_artwork_price);
        count_package_price = Number(count_package_price);
        delivery_price = Number(delivery_price);
        packing_slip_price = Number(packing_slip_price);
  
        var admin_cost = send_to_press_price + workorder_price + reclaim_artwork_price + count_package_price + delivery_price + packing_slip_price
  
  
        document.getElementById("admin_cost").innerHTML = admin_cost;

        var misc1_price = $('#id_misc1_price').val();
        var misc2_price = $('#id_misc2_price').val();
        var misc3_price = $('#id_misc3_price').val();
        var misc4_price = $('#id_misc4_price').val();

        misc1_price = Number(misc1_price);
        misc2_price = Number(misc2_price);
        misc3_price = Number(misc3_price);
        misc4_price = Number(misc4_price);

        var misc = misc1_price + misc2_price + misc3_price + misc4_price
  
  


        var mask_time = $('#id_masking_time').val();
        var kiss_time = $('#id_kiss_cut_time').val();
        var flex_time = $('#id_flex_cut_time').val();
        var weed_time = $('#id_weeding_time').val();
        kiss_time = Number(kiss_time);
        flex_time = Number(flex_time);
        mask_time = Number(mask_time);
        weed_time = Number(weed_time);
        
        var machine_rate = $('#id_machine_rate').val();
        var labor_rate = $('#id_labor_rate').val();
  
        var machine_cost = (kiss_time + flex_time) * machine_rate
        var labor_cost = (mask_time + weed_time) * labor_rate
  
  
        document.getElementById("machine_cost").innerHTML = machine_cost;
        document.getElementById("labor_cost").innerHTML = labor_cost;
  
  
      

        //Get width from selected inventory item. If no width, allow width to be entered
        if ($("#id_width").length){
          var width = $('#id_width').val();
          $('#id_media_width').val(width);
        } else {
        }

        var quantity = $('#id_quantity').val();
        quantity = Number(quantity);

        var media_width = $('#id_media_width').val();
        var usable_width = media_width - 1
        $('#id_usable_width').val(usable_width);

        var height = $('#id_print_height').val();
        height = Number(height);
        var width = $('#id_print_width').val();
        width = Number(width);
        var size = height * width
        size = Number(size);

        var w_marg = $('#id_print_w_margin').val();
        w_marg = Number(w_marg);
        var h_marg = $('#id_print_h_margin').val();
        h_marg = Number(h_marg);

        var print_width = width + w_marg + w_marg
        var print_height = height + h_marg + h_marg
        var ovarall_print = print_width * print_height

        var prints_per_row = usable_width / print_width
        prints_per_row = Math.floor(prints_per_row);
        $('#id_prints_per_row').val(prints_per_row);

        var number_of_rows = quantity / prints_per_row
        number_of_rows = Math.ceil(number_of_rows);
        $('#id_number_of_rows').val(number_of_rows);

        var media_length = number_of_rows * print_height
        $('#id_media_length').val(media_length);

        var total_sq_ft = media_length * media_width / 144
        $('#id_total_sq_ft').val(total_sq_ft);

        //$('#id_labor_rate').val(print_height);

        if ($("#id_price_per").length){
          var price = $('#id_price_per').val();
          var material_measurement = $('#material_measurement').val();
          if (material_measurement === 'SqFt') {
            var material_cost = price * total_sq_ft
            //var material_cost = 1
          } else if (material_measurement === 'Yd'){
            var material_cost = media_length / 36 * price
            //var material_cost = 2
          }
        } else {
          var material_cost = 0;
        }
        

        if ($("#id_mask_price_per").length){
          var mask_price = $('#id_mask_price_per').val();
          var mask_measurement = $('#mask_measurement').val();
          if (mask_measurement === 'SqFt') {
            var mask_cost = mask_price * total_sq_ft
            //var material_cost = 1
          } else if (mask_measurement === 'Yd'){
            var mask_cost = media_length / 36 * mask_price
            //var material_cost = 2
          }
        } else {
          var mask_cost = 0;
        }
        

        if ($("#id_laminate_price_per").length){
          var laminate_price = $('#id_laminate_price_per').val();
          var laminate_measurement = $('#laminate_measurement').val();
          if (laminate_measurement === 'SqFt') {
            var laminate_cost = laminate_price * total_sq_ft
            //var material_cost = 1
          } else if (laminate_measurement === 'Yd'){
            var laminate_cost = media_length / 36 * laminate_price
            //var material_cost = 2
          }
        } else {
          var laminate_cost = 0;
        }
        //$('#id_step_delivery_price').val(mask_cost);

        if ($("#id_substrate_price_per").length){
          var substrate_price = $('#id_substrate_price_per').val();
          var substrate_measurement = $('#substrate_measurement').val();
          if (substrate_measurement === 'SqFt') {
            var substrate_cost = substrate_price * total_sq_ft
            //var material_cost = 1
          } else if (substrate_measurement === 'Yd'){
            var substrate_cost = media_length / 36 * substrate_price
            //var material_cost = 2
          } else if (substrate_measurement === 'Ea'){
            substrate_price = Number(substrate_price);
            var substrate_cost = substrate_price * quantity
            substrate_cost = Number(substrate_cost);
          }
        } else {
          var substrate_cost = 0;
        }

        
        var ink_price = $('#id_inkcost_sq_ft').val();
        var ink_cost = ink_price * total_sq_ft

        
        if ($('#id_price_per').length){
        } else {
          material_cost = 0
        }
        if ($('#id_mask_price_per').length){
        } else {
          mask_cost = 0
        }
        if ($('#id_laminate_price_per').length){
        } else {
          laminate_cost = 0
        }
        if ($('#id_substrate_price_per').length){
        } else {
          substrate_cost = 0
        }
        if ($('#id_inkcost_sq_ft').length){
        } else {
          ink_cost = 0
        }
        var total_material_cost = material_cost + mask_cost + laminate_cost + substrate_cost + ink_cost

        //var total_material_cost = material_cost + mask_cost + laminate_cost

        total_material_cost = Number(total_material_cost)

        total_material_cost = total_material_cost.toFixed(2);

        total_material_cost = Number(total_material_cost)

        $('#id_material_cost').val(total_material_cost);

        var material_markup_percentage = $('#id_material_markup_percentage').val();

        var percent = material_markup_percentage / 100
        //var markup = price_per_m * percent
        var markup = total_material_cost * percent
        markup = Number(markup);

        markup = markup.toFixed(2);

        $('#id_material_markup').val(markup);

        admin_cost = Number(admin_cost);
        misc = Number(misc);
        machine_cost = Number(machine_cost);
        labor_cost = Number(labor_cost);
        markup = Number(markup);
        //var total_price = admin_cost + misc + machine_cost + labor_cost + total_material_cost + markup

        var total_price = admin_cost + misc + machine_cost + labor_cost + total_material_cost + markup

        total_price = total_price.toFixed(2);

        $('#id_price_total').val(total_price);

        var price_ea = total_price / quantity

        price_ea = price_ea.toFixed(2)

        $('#price_ea').val(price_ea);

        
        



        



        //Fill in pricing sheet on side
        document.getElementById("quantity").innerHTML = quantity;
        document.getElementById("width").innerHTML = width;
        document.getElementById("height").innerHTML = height;
        document.getElementById("print_width").innerHTML = print_width;
        document.getElementById("print_height").innerHTML = print_height;
        document.getElementById("media_width").innerHTML = media_width;
        document.getElementById("usable_width").innerHTML = usable_width;
        document.getElementById("prints_per_row").innerHTML = prints_per_row;
        document.getElementById("number_of_rows").innerHTML = number_of_rows;
        document.getElementById("media_length").innerHTML = media_length;

        material_cost = material_cost.toFixed(2);
        mask_cost = mask_cost.toFixed(2);
        laminate_cost = laminate_cost.toFixed(2);
        substrate_cost = substrate_cost.toFixed(2);
        ink_cost = ink_cost.toFixed(2);
        total_material_cost = total_material_cost.toFixed(2);
        document.getElementById("material_cost").innerHTML = material_cost;
        document.getElementById("mask_cost").innerHTML = mask_cost;
        document.getElementById("laminate_cost").innerHTML = laminate_cost;
        document.getElementById("substrate_cost").innerHTML = substrate_cost;
        document.getElementById("ink_cost").innerHTML = ink_cost;
        document.getElementById("total_material_cost").innerHTML = total_material_cost;


    });

    
    

});