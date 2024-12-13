odoo.define('tis_pos_dynamic_combo.order', function (require) {
"use strict";

    var utils = require('web.utils');
    var round_pr = utils.round_precision;
    var models = require('point_of_sale.models');
    var core = require('web.core');
    var qweb = core.qweb;
    var _t = core._t;
    var round_di = utils.round_decimals;
    var round_pr = utils.round_precision;


    var _super_Orderline = models.Orderline.prototype;
    models.Orderline = models.Orderline.extend({
        initialize: function (attributes, options) {
            var res = _super_Orderline.initialize.apply(this, arguments);
                this.ser = options.combo_products_ordered;
                this.opt = options.total_charge_list
            return res;
        },
        get_combo_prd: function(){
            return this.ser;
        },
         get_combo_price: function(){
            return this.opt;
        },


        get_unit_price: function(){
            var digits = this.pos.dp['Product Price'];
            // round and truncate to mimic _symbol_set behavior
            if(this.ser){
                var combo_price = this.get_combo_price();
                 var price_combo = combo_price[0].total_charge
                return parseFloat(round_di(price_combo || 0, digits).toFixed(digits));
            }
            else{
                 return parseFloat(round_di(this.price || 0, digits).toFixed(digits));
            }
        },



        export_as_JSON: function () {
            var json = _super_Orderline.export_as_JSON.call(this);
            var combo_prd_data = this.get_combo_prd()
            if(combo_prd_data){
                  json['datas'] = combo_prd_data;
                  json['combo_product_ids'] = [];
                 var  combo_dict = {}
                 var  combo_list = []
                 for (var j =0; j< combo_prd_data.length; j++){
                        combo_dict ={'product_id':combo_prd_data[j].product_id,'qty':combo_prd_data[j].quantity,'unit_price':combo_prd_data[j].price,'product_uom_id':combo_prd_data[j].uom};
                        combo_list.push(combo_dict);
                        json.combo_product_ids.push([0, false, combo_dict ]);

              }

            }
            return json;
        },

    });


    var _super_Order = models.Order.prototype;
    models.Order = models.Order.extend({

        init_from_JSON: function (json) {
            var res = _super_Order.init_from_JSON.apply(this, arguments);
            return res;
        },
        add_product: function(product, options){
            if(this._printed){
                this.destroy();
                return this.pos.get_order().add_product(product, options);
            }
            this.assert_editable();
            options = options || {};
            var attr = JSON.parse(JSON.stringify(product));
            attr.pos = this.pos;
            attr.order = this;

            if(options.combo_products_ordered){
                    var line = new models.Orderline({}, {pos: this.pos, order: this, product: product, combo_products_ordered:options.combo_products_ordered,total_charge_list:options.total_charge_list});

                line.set_unit_price(options.total_charge_list[0].total_charge);
            }
            else{
                var line = new models.Orderline({}, {pos: this.pos, order: this, product: product});
            }
            if(options.qty){
                line.set_quantity(options.qty);
            }
            if(options.quantity !== undefined){
                line.set_quantity(options.quantity);
            }

            if(options.price !== undefined){
                line.set_unit_price(options.price);
            }

            //To substract from the unit price the included taxes mapped by the fiscal position
            this.fix_tax_included_price(line);

            if(options.discount !== undefined){
                line.set_discount(options.discount);
            }

            if(options.extras !== undefined){
                for (var prop in options.extras) {
                    line[prop] = options.extras[prop];
                }
            }

             var to_merge_orderline;
             for (var i = 0; i < this.orderlines.length; i++) {
                  if(this.orderlines.at(i).can_be_merged_with(line) && options.merge !== false){
                   to_merge_orderline = this.orderlines.at(i);
               }
             }
            if (to_merge_orderline){
              to_merge_orderline.merge(line);
              this.select_orderline(to_merge_orderline);
               }
            else {
              this.orderlines.add(line);
               this.select_orderline(this.get_last_orderline());
              }
            this.select_orderline(this.get_last_orderline());

            console.log("Ini line.has_product_lot : ", line.has_product_lot)
            console.log("Ini options : ", options)
            console.log("Ini options.draftPackLotLines : ", options.draftPackLotLines)
            /*if(line.has_product_lot){
                this.display_lot_popup();
            }*/

        },



    });
});