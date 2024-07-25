$(document).ready(function(){

    //Hide job steps until needed
      //$('#perf-row').hide()
      if ($("#id_step_perf_price").val() > .01){
        $('#perf-row').show()
      } else {
        $('#perf-row').hide()
      }

      $('#show-perf').click(function(){
      $('#perf-row').slideToggle(200)
      });

      //$('#numbering-row').hide()
      if ($("#id_step_number_price").val() > .01){
        $('#numbering-row').show()
      } else {
        $('#numbering-row').hide()
      }

      $('#show-numbering').click(function(){
      $('#numbering-row').slideToggle(200)
      });

      //$('#wrap-row').hide()
      if ($("#id_step_insert_frontback_cover_price").val() > .01 || $("#id_step_insert_wrap_around_price").val() > .01 || $("#id_step_insert_chip_divider_price").val() > .01){
        $('#wrap-row').show()
      } else {
        $('#wrap-row').hide()
      }

      $('#show-wraparound').click(function(){
      $('#wrap-row').slideToggle(200)
      });

      //$('#mailmerge-row').hide()
      if ($("#id_step_print_mailmerge_price").val() > .01){
        $('#mailmerge-row').show()
      } else {
        $('#mailmerge-row').hide()
      }

      $('#show-mailmerge').click(function(){
      $('#mailmerge-row').slideToggle(200)
      });

      //$('#padding-row').hide()
      if ($("#id_step_NCR_compound_price").val() > .01 || $("#id_step_white_compound_price").val() > .01){
        $('#padding-row').show()
      } else {
        $('#padding-row').hide()
      }

      $('#show-padding').click(function(){
      $('#padding-row').slideToggle(200)
      });

      //$('#drill-row').hide()
      if ($("#id_step_set_to_drill_price").val() > .01 || $("#id_step_drill_price").val() > .01){
        $('#drill-row').show()
      } else {
        $('#drill-row').hide()
      }

      $('#show-drill').click(function(){
      $('#drill-row').slideToggle(200)
      });

      $('#staple-row').hide()
      if ($("#id_step_staple_price").val() > .01){
        $('#staple-row').show()
      } else {
        $('#staple-row').hide()
      }

      $('#show-staple').click(function(){
      $('#staple-row').slideToggle(200)
      });

      //$('#fold-row').hide()
      if ($("#id_step_fold_price").val() > .01){
        $('#fold-row').show()
      } else {
        $('#fold-row').hide()
      }

      $('#show-fold').click(function(){
      $('#fold-row').slideToggle(200)
      });

      //$('#tab-row').hide()
      if ($("#id_step_tab_price").val() > .01){
        $('#tab-row').show()
      } else {
        $('#tab-row').hide()
      }

      $('#show-tab').click(function(){
      $('#tab-row').slideToggle(200)
      });

      //$('#bulkmail-row').hide()
      if ($("#id_step_bulk_mail_tray_sort_paperwork_price").val() > .01){
        $('#bulkmail-row').show()
      } else {
        $('#bulkmail-row').hide()
      }

      $('#show-bulkmail').click(function(){
      $('#bulkmail-row').slideToggle(200)
      });

      if (($("#id_step_duplo_price").val() > .01) || ($("#id_step_duplo_price").val()))  {
        $('#duplo-row').show()
      //if ($("#id_misc1_description").val()){
        //$('#misc1-row').show()
      } else {
        $('#duplo-row').hide()
        //alert( "Handler for `keyup` called." );
      }

      $('#show-duplo').click(function(){
        $('#duplo-row').slideToggle(200)
        });


      if (($("#id_misc1_price").val() > .01) || ($("#id_misc1_description").val()))  {
        $('#misc1-row').show()
      //if ($("#id_misc1_description").val()){
        //$('#misc1-row').show()
      } else {
        $('#misc1-row').hide()
        //alert( "Handler for `keyup` called." );
      }

      if ($("#id_misc2_price").val() > .01 || ($("#id_misc2_description").val())){
        $('#misc2-row').show()
      } else {
        $('#misc2-row').hide()
      }

      //$('#misc1-row').hide()

      $('#show-misc1').click(function(){
      $('#misc1-row').slideToggle(200)
      });

      //$('#misc2-row').hide()

      $('#show-misc2').click(function(){
      $('#misc2-row').slideToggle(200)
      });

      //$('#misc3-row').hide()
      if ($("#id_misc3_price").val() > .01 || ($("#id_misc3_description").val())){
        $('#misc3-row').show()
      } else {
        $('#misc3-row').hide()
      }

      $('#show-misc3').click(function(){
      $('#misc3-row').slideToggle(200)
      });

      //$('#misc4-row').hide()
      if ($("#id_misc4_price").val() > .01 || ($("#id_misc4_description").val())){
        $('#misc4-row').show()
      } else {
        $('#misc4-row').hide()
      }

      $('#show-misc4').click(function(){
      $('#misc4-row').slideToggle(200)
      });



    //Autofill qtys on newjob form
      $('#id_container').on("click change",function(){
        //alert( "Handler for `keyup` called." );

        if ($("#id_pages_per_book").length){
          var pages_per_book = $('#id_pages_per_book').val();
        } else {
          var pages_per_book = 1;
        }

        var qty = $('#id_qty').val();
        //var pages_per_book = $('#id_pages_per_book').val();
        var overage = $('#id_overage').val();
    
        var press_sheet_per_parent = $('#id_press_sheet_per_parent').val();
        var gangup = $('#id_gangup').val();


        
        var qty = Number(qty);
        var pages_per_book = Number(pages_per_book);
        var overage = Number(overage);
        var press_sheet_per_parent = Number(press_sheet_per_parent);
        var gangup = Number(gangup);
        
        
        var sheet_qty = qty * pages_per_book;
        
        var output = press_sheet_per_parent * gangup;
        
        var c = sheet_qty + overage;
        var parent = c / output;
        var parent = Math.ceil(parent);
    
        var click1 = press_sheet_per_parent * parent
        var click2 = press_sheet_per_parent * parent


        
    
        $('#id_qty_of_sheets').val(sheet_qty);
        document.getElementById("id_sheets").innerHTML = sheet_qty;
    
        $('#id_output_per_sheet').val(output);
        
        $('#id_parent_sheets_required').val(parent);
    
        $('#id_side_1_clicks').val(click1);
        $('#id_side_2_clicks').val(click2);

        

        //Calculate printing cost. Number of clicks * price / click rounded to two decimals
        var printcost1 = $('#id_step_print_cost_side_1').val();
        var printcost2 = $('#id_step_print_cost_side_2').val();

        var printcost1 = Number(printcost1);
        var printcost2 = Number(printcost2);
        
        var clickcost1 = click1 * printcost1
        var clickcost2 = click2 * printcost2

        clickcost1 = clickcost1.toFixed(2);
        clickcost2 = clickcost2.toFixed(2);

        $('#id_step_print_cost_side_1_price').val(clickcost1);
        $('#id_step_print_cost_side_2_price').val(clickcost2);

        //$('#id_mailmerge_qty').val(sheet_qty)
        //$('#id_perf_number_of_pieces').val(sheet_qty)
        //$('#id_fold_number_to_fold').val(sheet_qty)
        //$('#id_number_number_of_pieces').val(sheet_qty)
        //Insert number to drill after it gets added to form
        //$('#id_staple_number_of_pieces').val(qty)
        //$('#id_tabs_number_of_pieces').val(qty)
        

        //Fill in pricing sheet on side
        document.getElementById("id_price_qty").innerHTML = qty;
        document.getElementById("id_pages_qty").innerHTML = pages_per_book;
        document.getElementById("id_press_per_parent").innerHTML = press_sheet_per_parent;
        document.getElementById("id_gangup_cnt").innerHTML = gangup;
        document.getElementById("id_overage_cnt").innerHTML = overage;
        document.getElementById("id_parent_output").innerHTML = output;
        document.getElementById("id_parent_required").innerHTML = parent;
        document.getElementById("id_clicks_one").innerHTML = click1;
        document.getElementById("id_clicks_two").innerHTML = click2;
        document.getElementById("id_side_one_charge").innerHTML = clickcost1;
        document.getElementById("id_side_two_charge").innerHTML = clickcost2;


    
      });
  
    
    //Calculate number of parent sheets needed
    $('#id_container').on("click change",function(){
        //alert( "Handler for `keyup` called." );
        var press_sheet_per_parent = $('#id_press_sheet_per_parent').val();
        var gangup = $('#id_gangup').val();
        var output = press_sheet_per_parent * gangup
    
        $('#id_output_per_sheet').val(output);
    
    
      });

    
  
    //Add material cost after htmx call.... Need to find a better handler for this
    $('#id_container').on("click change",function(){
          
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

    //Material Markup. Needs to use same handler as material cost when that is discovered
    $('#id_container').on("click change",function(){
      //alert( "Handler for `keyup` called." );
      var price_per_m = $('#id_price_per_m').val();
      var material_cost = $('#id_material_cost').val();
      var material_markup_percentage = $('#id_material_markup_percentage').val();
      var sheets = $('#id_parent_sheets_required').val();
      
      //This needs to be replaced with a dynamic number from database
      var misc = 5
      
      
      var material_markup_percentage = Number(material_markup_percentage);
      document.getElementById("id_markup_percent").innerHTML = material_markup_percentage;

      var price_per_m = Number(price_per_m);
      var sheets = Number(sheets);

      //calculate price per sheet
      var paper_cost = price_per_m / 1000
      var cost = paper_cost * sheets

      var paper_cost = cost + misc
      
      var percent = material_markup_percentage / 100
      //var markup = price_per_m * percent
      var markup = paper_cost * percent

      var markup = Number(markup)
      var material_cost = Number(material_cost)
      
      var total = markup + material_cost

      markup = markup.toFixed(2);

      $('#id_material_markup').val(markup);

      
    });


    $('#id_container').on("click change",function(){
      //alert( "Handler for `keyup` called." );
      var mailmerge = $('#id_mailmerge_qty').val();
      var price = $('#id_mailmerge_price_per_piece').val();

      //var mailmerge = Number(mailmerge);
      //var price = Number(price);

      var mailmerge_price = mailmerge * price
      mailmerge_price = mailmerge_price.toFixed(2);

      $('#id_step_print_mailmerge_price').val(mailmerge_price);
  
  
    });

    $('#id_container').on("click change",function(){
      //alert( "Handler for `keyup` called." );
      var setup = $('#id_step_set_to_perf_price').val();
      var price = $('#id_perf_price_per_piece').val();
      var qty = $('#id_perf_number_of_pieces').val();

      var pcs = qty * price
      pcs = pcs.toFixed(2);
      pcs = Number(pcs)

      setup = Number(setup)

      total = pcs + setup
      total = total.toFixed(2);

      $('#id_step_perf_price').val(total);
  
  
    });

    $('#id_container').on("click change",function(){
      var setup = $('#id_step_set_to_number_price').val();

      //alert( "Handler for `keyup` called." );
      var price = $('#id_number_price_to_number').val();
      var qty = $('#id_number_number_of_pieces').val();

      var pcs = qty * price
      pcs = pcs.toFixed(2);
      pcs = Number(pcs)

      setup = Number(setup)

      total = pcs + setup
      total = total.toFixed(2)


      $('#id_step_number_price').val(total);
  
  
    });

    $('#id_container').on("click change",function(){
      //alert( "Handler for `keyup` called." );
      var setup = $('#id_step_set_folder_price').val();
      var price = $('#id_fold_price_per_fold').val();
      var qty = $('#id_fold_number_to_fold').val();

      var pcs = qty * price
      pcs = pcs.toFixed(2);
      pcs = Number(pcs)

      setup = Number(setup)

      total = pcs + setup
      total = total.toFixed(2);

      $('#id_step_fold_price').val(total);
  
  
  
    });

    $('#id_container').on("click change",function(){
      //alert( "Handler for `keyup` called." );
      var set_to_staple = $('#id_step_set_to_staple_price').val();
      var price = $('#id_staple_price_per_staple').val();
      var qty = $('#id_staple_staples_per_piece').val();
      var pieces = $('#id_staple_number_of_pieces').val();

      var total = qty * price * pieces
      total = total.toFixed(2);

      total = Number(total)
      set_to_staple = Number(set_to_staple)

      price = total + set_to_staple

      price = price.toFixed(2);

      $('#id_step_staple_price').val(price);
  
  
    });

    /*$('#id_fold_price_per_fold, #id_fold_number_to_fold').keyup(function(){
      //alert( "Handler for `keyup` called." );
      var price = $('#id_fold_price_per_fold').val();
      var qty = $('#id_fold_number_to_fold').val();

      var total = qty * price
      total = total.toFixed(2);

      $('#id_step_fold_price').val(total);
  
  
    });*/

    $('#id_container').on("click change",function(){
      //alert( "Handler for `keyup` called." );
      var price = $('#id_tabs_price_per_tab').val();
      var qty = $('#id_tabs_per_piece').val();
      var pieces = $('#id_tabs_number_of_pieces').val();

      var total = qty * price * pieces
      total = total.toFixed(2);

      $('#id_step_tab_price').val(total);
  
  
    });
//############################################################### Begining of total form
    $('#id_container').on("click change",function(){
      var qty = $('#id_qty').val();

      if ($("#id_step_workorder_price").length){
        var workorder = $('#id_step_workorder_price').val();
      } else {
        var workorder = 0;
      }
      
      if ($("#id_step_reclaim_artwork_price").length){
        var reclaim = $('#id_step_reclaim_artwork_price').val();
      } else {
        var reclaim = 0;
      }
      
      if ($("#id_step_send_to_press_price").length){
        var send_to_press = $('#id_step_send_to_press_price').val();
      } else {
        var send_to_press = 0;
      }
      
      if ($("#id_material_cost").length){
        var material_cost = $('#id_material_cost').val();
      } else {
        var material_cost = 0;
      }
      
      if ($("#id_material_markup").length){
        var markup = $('#id_material_markup').val();
      } else {
        var markup = 0;
      }
      
      if ($("#id_step_print_cost_side_1_price").length){
        var side1 = $('#id_step_print_cost_side_1_price').val();
      } else {
        var side1 = 0;
      }
      
      if ($("#id_step_print_cost_side_2_price").length){
        var side2 = $('#id_step_print_cost_side_2_price').val();
      } else {
        var side2 = 0;
      }
      
      if ($("#id_step_trim_to_size_price").length){
        var trim = $('#id_step_trim_to_size_price').val();
      } else {
        var trim = 0;
      }
      
      if ($("#id_step_wear_and_tear_price").length){
        var wear = $('#id_step_wear_and_tear_price').val();
      } else {
        var wear = 0;
      }

      if ($("#id_step_send_mailmerge_to_press_price").length){
        var mailmerge = $('#id_step_send_mailmerge_to_press_price').val();
      } else {
        var mailmerge = 0;
      }
      
      if ($("#id_step_print_mailmerge_price").length){
        var print_mailmerge = $('#id_step_print_mailmerge_price').val();
      } else {
        var print_mailmerge = 0;
      }
      
      if ($("#id_step_NCR_compound_price").length){
        var ncr = $('#id_step_NCR_compound_price').val();
      } else {
        var ncr = 0;
      }
      
      if ($("#id_step_white_compound_price").length){
        var white = $('#id_step_white_compound_price').val();
      } else {
        var white = 0;
      }
      
      if ($("#id_step_perf_price").length){
        var perf = $('#id_step_perf_price').val();
      } else {
        var perf = 0;
      }
      
      if ($("#id_step_number_price").length){
        var number = $('#id_step_number_price').val();
      } else {
        var number = 0;
      }

      if ($("#id_step_insert_frontback_cover_price").length){
        var insert_cover = $('#id_step_insert_frontback_cover_price').val();
      } else {
        var insert_cover = 0;
      }

      if ($("#id_step_insert_wrap_around_price").length){
        var insert = $('#id_step_insert_wrap_around_price').val();
      } else {
        var insert = 0;
      }

      if ($("#id_step_insert_chip_divider_price").length){
        var insert_chip = $('#id_step_insert_chip_divider_price').val();
      } else {
        var insert_chip = 0;
      }

      if ($("#id_step_set_to_drill_price").length){
        var set_drill = $('#id_step_set_to_drill_price').val();
      } else {
        var set_drill = 0;
      }

      if ($("#id_step_drill_price").length){
        var drill = $('#id_step_drill_price').val();
      } else {
        var drill = 0;
      }

      if ($("#id_step_staple_price").length){
        var staple = $('#id_step_staple_price').val();
      } else {
        var staple = 0;
      }

      if ($("#id_step_fold_price").length){
        var fold = $('#id_step_fold_price').val();
      } else {
        var fold = 0;
      }

      if ($("#id_step_tab_price").length){
        var tab = $('#id_step_tab_price').val();
      } else {
        var tab = 0;
      }

      if ($("#id_step_bulk_mail_tray_sort_paperwork_price").length){
        var tray = $('#id_step_bulk_mail_tray_sort_paperwork_price').val();
      } else {
        var tray = 0;
      }

      if ($("#id_misc1_price").length){
        var misc1 = $('#id_misc1_price').val();
      } else {
        var misc1 = 0;
      }

      if ($("#id_misc2_price").length){
        var misc2 = $('#id_misc2_price').val();
      } else {
        var misc2 = 0;
      }

      if ($("#id_misc3_price").length){
        var misc3 = $('#id_misc3_price').val();
      } else {
        var misc3 = 0;
      }

      if ($("#id_misc4_price").length){
        var misc4 = $('#id_misc4_price').val();
      } else {
        var misc4 = 0;
      }

      if ($("#id_step_id_count_price").length){
        var count = $('#id_step_id_count_price').val();
      } else {
        var count = 0;
      }

      if ($("#id_step_count_package_price").length){
        var package = $('#id_step_count_package_price').val();
      } else {
        var package = 0;
      }

      if ($("#id_step_delivery_price").length){
        var deliver = $('#id_step_delivery_price').val();
      } else {
        var deliver = 0;
      }

      if ($("#id_step_packing_slip_price").length){
        var packing_slip = $('#id_step_packing_slip_price').val();
      } else {
        var packing_slip = 0;
      }
 
       
      
      /*var workorder = $('#id_step_workorder_price').val();
      var reclaim = $('#id_step_reclaim_artwork_price').val();
      var send_to_press = $('#id_step_send_to_press_price').val();
      var mailmerge = $('#id_step_send_mailmerge_to_press_price').val();
      var material_cost = $('#id_material_cost').val();
      var markup = $('#id_material_markup').val();
      var side1 = $('#id_step_print_cost_side_1_price').val();
      var side2 = $('#id_step_print_cost_side_2_price').val();
      var trim = $('#id_step_trim_to_size_price').val();
      var wear = $('#id_step_wear_and_tear_price').val();
      var print_mailmerge = $('#id_step_print_mailmerge_price').val();
      var ncr = $('#id_step_NCR_compound_price').val();
      var white = $('#id_step_white_compound_price').val();
      var perf = $('#id_step_perf_price').val();
      var number = $('#id_step_number_price').val();
      var insert_cover = $('#id_step_insert_frontback_cover_price').val();
      var insert = $('#id_step_insert_wrap_around_price').val();
      var insert_chip = $('#id_step_insert_chip_divider_price').val();
      var set_drill = $('#id_step_set_to_drill_price').val();
      var drill = $('#id_step_drill_price').val();
      var staple = $('#id_step_staple_price').val();
      var fold = $('#id_step_fold_price').val();
      var tab = $('#id_step_tab_price').val();
      var tray = $('#id_step_bulk_mail_tray_sort_paperwork_price').val();
      var misc1 = $('#id_misc1_price').val();
      var misc2 = $('#id_misc2_price').val();
      var misc3 = $('#id_misc3_price').val();
      var misc4 = $('#id_misc4_price').val();
      var count = $('#id_step_id_count_price').val();
      var package = $('#id_step_count_package_price').val();
      var deliver = $('#id_step_delivery_price').val();
      var packing_slip = $('#id_step_packing_slip_price').val();*/

      /*qty = Number(qty)
      paper_cost = Number(paper_cost)
      parent_sheets = Number(parent_sheets)

      paper_cost = paper_cost / parent_sheets * qty
      m = total / qty * 1000*/

      workorder = Number(workorder)
      reclaim = Number(reclaim)
      send_to_press = Number(send_to_press)
      mailmerge = Number(mailmerge)
      material_cost = Number(material_cost)
      markup = Number(markup)
      side1 = Number(side1)
      side2 = Number(side2)
      trim = Number(trim)
      wear = Number(wear)
      print_mailmerge = Number(print_mailmerge)
      ncr = Number(ncr)
      white = Number(white)
      perf = Number(perf)
      number = Number(number)
      insert_cover = Number(insert_cover)
      insert = Number(insert)
      insert_chip = Number(insert_chip)
      set_drill = Number(set_drill)
      drill = Number(drill)
      staple = Number(staple)
      fold = Number(fold)
      tab = Number(tab)
      tray = Number(tray)
      misc1 = Number(misc1)
      misc2 = Number(misc2)
      misc3 = Number(misc3)
      misc4 = Number(misc4)
      count = Number(count)
      package = Number(package)
      deliver = Number(deliver)
      packing_slip = Number(packing_slip)


      var total = workorder + reclaim + send_to_press + mailmerge+ material_cost + markup + side1 + side2 + trim + wear + print_mailmerge + ncr + white + perf + number + insert_cover + insert + insert_chip + set_drill + 
      drill + staple + fold + tab + tray + misc1 + misc2 + misc3 + misc4 + count + package + deliver + packing_slip

      //var total = workorder + reclaim + send_to_press + mailmerge + material_cost + markup + side1 + side2 + trim
      total = total.toFixed(2);

      m = total / qty * 1000

      m = m.toFixed(2);

      price_ea = total / qty
      price_ea = price_ea.toFixed(4)

      $('#id_price_total').val(total);

      $('#id_price_total_per_m').val(m);

      $('#price_ea').val(price_ea);
      document.getElementById("id_price_ea").innerHTML = price_ea;

      


      document.getElementById("id_price_ea").innerHTML = price_ea;
      document.getElementById("id_count_x").innerHTML = count;
      document.getElementById("id_delivery").innerHTML = deliver;
      document.getElementById("id_packing_slip").innerHTML = packing_slip;
      document.getElementById("id_total").innerHTML = total;





  
  
    });

    /*$('#id_container').on("click change",function(){
      //alert( "Handler for `keyup` called." );
      var workorder = $('#id_step_workorder_price').val();
      var reclaim = $('#id_step_reclaim_artwork_price').val();

      workorder=Number(workorder)
      reclaim = Number(reclaim)

      var total = workorder + reclaim
      total = total.toFixed(2);

      $('#id_price_total').val(total);
  
  
    });*/
  

  
  
  
  });