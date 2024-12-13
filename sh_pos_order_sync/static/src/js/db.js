odoo.define("sh_pos_order_sync.db", function (require) {
    "use strict";

    var DB = require("point_of_sale.DB");
    DB.include({
        init: function (options) {
            this._super(options);
            this.all_order = [];
            this.all_config = [];
            this.config_by_id = {};
            this.order_by_id = {};
            this.order_line_by_id = {};
        },
        all_configs: function (all_config) {
            for (var i = 0, len = all_config.length; i < len; i++) {
                var each_config = all_config[i];
                this.all_config.push(each_config);
                this.config_by_id[each_config.id] = each_config;
            }
        },
        all_orders: function (all_order) {
            var new_write_date = "";
            for (var i = 0, len = all_order.length; i < len; i++) {
                var each_order = all_order[i];
                this.all_order.push(each_order);
                this.order_by_id[each_order.id] = each_order;
                this.order_by_uid[each_order.sh_uid] = each_order;
            }
        },
        all_orders_line: function (all_order_line) {
            var new_write_date = "";
            for (var i = 0, len = all_order_line.length; i < len; i++) {
                var each_order_line = all_order_line[i];
                this.order_line_by_id[each_order_line.id] = each_order_line;
                this.order_line_by_uid[each_order_line.sh_line_id] = each_order_line;
            }
        },
    });
});
