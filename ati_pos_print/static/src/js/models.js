odoo.define('ati_pos_print.models', function (require) {
    var models = require('point_of_sale.models');

    var order_super = models.Order.prototype;
    models.Order = models.Order.extend({
        export_for_printing: function () {
            var json = order_super.export_for_printing.apply(this, arguments);

            return _.extend(json, {
                'client': this.get_client() ? this.get_client().name : false,
                'client_phone': this.get_client() ? this.get_client().phone : false,
                'client_mobile': this.get_client() ? this.get_client().mobile : false,
                'apoteker': this.pos.config.employee_id ? this.pos.config.employee_id[1] : false
            });
        },
        add_product: function (product, options) {
            order_super.add_product.apply(this,arguments);
            if(options.combo_products_ordered){
                this.get_last_orderline().set_product_combo(options.combo_products_ordered)
            }
        }
    });

    var _super_orderline = models.Orderline.prototype;
    models.Orderline = models.Orderline.extend({
        initialize: function(attr, options) {
            _super_orderline.initialize.call(this, attr, options);
            this.product_combo = this.product_combo || [];
        },
        set_product_combo: function(combo_products_ordered){
            this.product_combo = combo_products_ordered;
            this.trigger('change', this);
        },
        get_product_combo: function() {
            return this.product_combo;
        },
        export_as_JSON: function () {
            var json = _super_orderline.export_as_JSON.call(this);

            return _.extend(json, {
                'product_combo': this.get_product_combo(),
                'product_id': this.get_product().id,
                'product_tmpl_id': this.get_product().product_tmpl_id
            });
        },
        init_from_JSON: function(json) {
            _super_orderline.init_from_JSON.apply(this,arguments);
            this.product_combo = json.product_combo;
        },
        export_for_printing: function () {
            var json = _super_orderline.export_for_printing.apply(this, arguments);

            return _.extend(json, {
                'product_combo': this.get_product_combo(),
                'product_id': this.get_product().id,
                'product_tmpl_id': this.get_product().product_tmpl_id
            });
        },
    });

});
