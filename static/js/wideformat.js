$(document).ready(function () {
  // ----------------------------
  // Helpers
  // ----------------------------

  const getNum = (id) => Number($(id).val() || 0);

  const setText = (id, val) => {
    $(id).text(val);
  };

  const setVal = (id, val) => {
    $(id).val(val);
  };

  const calcCost = (priceId, measurementId, totalSqFt, mediaLength, qty = 1) => {
    if (!$(priceId).length) return 0;

    let price = getNum(priceId);
    let measure = $(measurementId).val();

    switch (measure) {
      case "SqFt":
        return price * totalSqFt;
      case "Yd":
        return (mediaLength / 36) * price;
      case "Ea":
        return price * qty;
      default:
        return 0;
    }
  };

  const getSidesMultiplier = () => {
  const el = $("input[name='single_double_sided']:checked");
  if (!el.length) return 1;
  const v = String(el.val()).trim().toLowerCase();

  // numeric values like "1" / "2"
  const n = Number(v);
  if (!Number.isNaN(n)) return n >= 2 ? 2 : 1;

  // text values like "single", "double", "double sided", "two-sided"
  if (/(double|two|2)/.test(v)) return 2;
  return 1;
  };

  // ----------------------------
  // Toggle misc rows
  // ----------------------------

  function initToggleRows() {
    $(".toggle-row").each(function () {
      const trigger = $(this);
      const target = $($(this).data("target"));
      const priceInput = target.find("input[id$='_price']");
      const descInput = target.find("input[id$='_description']");

      const hasPrice = priceInput.length && parseFloat(priceInput.val()) > 0.01;
      const hasDesc = descInput.length && $.trim(descInput.val()).length > 0;

      if (hasPrice || hasDesc) {
        target.show();
        trigger.prop("checked", true);
      } else {
        target.hide();
        trigger.prop("checked", false);
      }

      trigger.on("click", () => target.slideToggle(200));
    });
  }

  // ----------------------------
  // Main calculation function
  // ----------------------------

  function recalc() {
    // --- Admin costs ---
    const admin_cost =
      getNum("#id_step_workorder_price") +
      getNum("#id_step_reclaim_artwork_price") +
      getNum("#id_step_send_to_press_price") +
      getNum("#id_step_count_package_price") +
      getNum("#id_step_delivery_price") +
      getNum("#id_step_packing_slip_price");

    setText("#admin_cost", admin_cost);

    // --- Misc ---
    const misc =
      getNum("#id_misc1_price") +
      getNum("#id_misc2_price") +
      getNum("#id_misc3_price") +
      getNum("#id_misc4_price");

    // --- Machine/Labor costs ---
    const machine_cost =
      (getNum("#id_kiss_cut_time") + getNum("#id_flex_cut_time")) *
      getNum("#id_machine_rate");

    const labor_cost =
      (getNum("#id_masking_time") + getNum("#id_weeding_time")) *
      getNum("#id_labor_rate");

    setText("#machine_cost", machine_cost);
    setText("#labor_cost", labor_cost);

    // --- Media calculations ---
    let quantity = getNum("#id_quantity");
    let media_width = getNum("#id_media_width") || getNum("#id_width");
    let usable_width = media_width - 1;
    setVal("#id_usable_width", usable_width);

    let height = getNum("#id_print_height");
    let width = getNum("#id_print_width");

    // Rotate if needed
    if (height < usable_width && height > width) {
      [height, width] = [width, height];
    }

    const w_marg = getNum("#id_print_w_margin");
    const h_marg = getNum("#id_print_h_margin");

    const print_width = width + w_marg * 2;
    const print_height = height + h_marg * 2;

    const prints_per_row = Math.floor(usable_width / print_width) || 1;
    const number_of_rows = Math.ceil(quantity / prints_per_row);

    const media_length = number_of_rows * print_height;
    const total_sq_ft = (media_length * media_width) / 144;

    setVal("#id_prints_per_row", prints_per_row);
    setVal("#id_number_of_rows", number_of_rows);
    setVal("#id_media_length", media_length);
    setVal("#id_total_sq_ft", total_sq_ft);

    // --- Material costs ---
    let material_cost = calcCost(
      "#id_price_per",
      "#material_measurement",
      total_sq_ft,
      media_length
    );

    let mask_cost = calcCost(
      "#id_mask_price_per",
      "#mask_measurement",
      total_sq_ft,
      media_length
    );

    let laminate_cost = calcCost(
      "#id_laminate_price_per",
      "#laminate_measurement",
      total_sq_ft,
      media_length
    );

    let substrate_cost = calcCost(
      "#id_substrate_price_per",
      "#substrate_measurement",
      total_sq_ft,
      media_length,
      quantity
    );

    let ink_cost = getNum("#id_inkcost_sq_ft") * total_sq_ft;

    // --- Double-sided multiplier ---
    const sideMult = getSidesMultiplier();
      material_cost *= sideMult;
      mask_cost     *= sideMult;
      laminate_cost *= sideMult;
      ink_cost      *= sideMult;



    let total_material_cost =
      material_cost + mask_cost + laminate_cost + substrate_cost + ink_cost;

    total_material_cost = Number(total_material_cost.toFixed(2));
    setVal("#id_material_cost", total_material_cost);

    // --- Markup ---
    const material_markup_percentage = getNum("#id_material_markup_percentage");
    const markup = Number(
      (total_material_cost * (material_markup_percentage / 100)).toFixed(2)
    );
    setVal("#id_material_markup", markup);

    // --- Totals ---
    let total_price =
      admin_cost + misc + machine_cost + labor_cost + total_material_cost + markup;
    total_price = Number(total_price.toFixed(2));

    setVal("#id_price_total", total_price);

    let price_ea = quantity > 0 ? (total_price / quantity).toFixed(2) : 0;
    setVal("#price_ea", price_ea);

    // --- Fill side sheet ---
    [
      ["#quantity", quantity],
      ["#width", width],
      ["#height", height],
      ["#print_width", print_width],
      ["#print_height", print_height],
      ["#media_width", media_width],
      ["#usable_width", usable_width],
      ["#prints_per_row", prints_per_row],
      ["#number_of_rows", number_of_rows],
      ["#media_length", media_length],
      ["#material_cost", material_cost.toFixed(2)],
      ["#mask_cost", mask_cost.toFixed(2)],
      ["#laminate_cost", laminate_cost.toFixed(2)],
      ["#substrate_cost", substrate_cost.toFixed(2)],
      ["#ink_cost", ink_cost.toFixed(2)],
      ["#total_material_cost", total_material_cost.toFixed(2)],
    ].forEach(([id, val]) => setText(id, val));
  }

  // ----------------------------
  // Init
  // ----------------------------

  initToggleRows();       // setup misc row toggles
  $(document).ready(recalc); // initial calculation

  // Recalc whenever any input/select changes inside container
  $("#id_container").on("input change", "input, select", recalc);

  // Recalc when single/double sided radios change
  $("input[name='single_double_sided']").on("change", recalc);

  $(document).on("change", "input[name='single_double_sided']", recalc);

  console.log("sides:", $("input[name='single_double_sided']:checked").val(),
            "mult:", getSidesMultiplier());
});
