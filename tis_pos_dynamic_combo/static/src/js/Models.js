odoo.define('tis_pos_dynamic_combo.Models', function (require) {
    'use strict';

    var models = require('point_of_sale.models');
    models.load_fields("product.product", "combo_pack");
    models.load_fields("product.product", "combo_sale_price");
    models.load_fields("product.template", "combo_pack");
    models.load_fields("product.template", "combo_sale_price");
    models.load_fields("product.product", "combo_line");
    models.load_fields("product.template", "combo_line");
    models.load_fields("product.product", "id_combo_products");
    models.load_fields("product.template", "id_combo_products");
    models.load_fields("pos.order.line", "combo_product_ids");
    models.load_fields("pos.order.line", "datas");


     models.load_models([
    {
      model: 'product.combo.line',
      condition: function(self) {
        return true;
      },
       fields: ['combo_product_id', 'quantity','uom', 'price', 'product_id'],
       loaded: function(self, result) {
        if (result.length) {
          self.product_combo = result;
          self.set('product_combo', result);
        }
      },
    }
  ], {
    'after': 'res.country.state'
  });


   models.load_models([
    {
      model: 'pos.order.line.combo.products',
      condition: function(self) {
        return true;
      },
      fields: ['pos_order_id','product_id', 'qty','product_uom_id','unit_price'],
      loaded: function(self, result) {
        if (result.length) {
          self.pos_order_lines = result;
          self.set('pos_order_line_combo_products', result);
        }
      },
    }
  ], {
    'after': 'res.country.state'
  });




});