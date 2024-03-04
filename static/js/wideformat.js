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

      $('#id_container').on("click change",function(){

        if ($("#id_width").length){
          var width = $('#id_width').val();
          $('#id_media_width').val(width);
        } else {
        }

        

        

        var quantity = $('#id_quantity').val();

        var media_width = $('#id_media_width').val();
        var usable_width = media_width - 2
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

        $('#id_labor_rate').val(print_height);


        var pc = price_per_m / 1000
        var pc = Number(pc);
        var cost = pc * sheets
        var cost = Number(cost);
        var paper_cost = cost + misc
        var paper_cost = Number(paper_cost);






















          
        var price_per_m = $('#id_price_per_m').val();
        var sheets = $('#id_parent_sheets_required').val();

        //This needs to be replaced with a dynamic number from database
        var misc = 5
        var misc = Number(misc);

        //var testprice = price_per_m
        //var testprice = Number(testprice)
        //testprice = testprice.toFixed(2);
        
        var pc = price_per_m / 1000
        var pc = Number(pc);
        var cost = pc * sheets
        var cost = Number(cost);
        var paper_cost = cost + misc
        var paper_cost = Number(paper_cost);

        paper_cost = paper_cost.toFixed(2);

        $('#id_material_cost').val(paper_cost);




        document.getElementById("id_paper_price").innerHTML = price_per_m;
        document.getElementById("id_material_costs").innerHTML = paper_cost;

    });

});