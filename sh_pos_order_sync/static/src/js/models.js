odoo.define("sh_pos_order_sync.models", function (require) {
    "use strict";

    var models = require("point_of_sale.models");
    var core = require("web.core");
    var orderlist_screens = require("sh_pos_order_list.screen");
    var _t = core._t;
    models.load_models({
        model: "pos.order",
        label: "load_orders",
        domain: function (self) {
            return ["|", ["assigned_config", "=", self.config.id], ["user_id", "=", self.user.id]];
        },
        loaded: function (self, all_order) {
            self.db.all_orders(all_order);
            self.env.pos.order_length = all_order.length;
            self.env.pos.db.all_display_order =  all_order;
        },
    });
    models.load_models({
        model: "pos.order.line",
        label: "load_orders_line",
        loaded: function (self, all_order_line) {
            self.db.all_orders_line(all_order_line);
        },
    });

    models.load_models({
        model: "pos.config",
        label: "load_config",
        loaded: function (self, all_config) {
            self.db.all_configs(all_config);
        },
    });

    var _super_order = models.Order.prototype;
    models.Order = models.Order.extend({
        initialize: function () {
            var self = this;
            self.is_edit = false;
            self.is_order_send = false
            self.is_reprint = false;
            _super_order.initialize.apply(this, arguments);
        },
        set_assigned_config: function (assigned_config) {
            this.assigned_config = assigned_config;
        },
        get_assigned_config: function () {
            return this.assigned_config;
        },
        export_as_JSON: function () {
            var json = _super_order.export_as_JSON.apply(this, arguments);
            json.assigned_config = this.get_assigned_config() || null;
            json.sh_is_order_send = this.is_order_send || false;
            return json;
        },
        export_for_printing: function () {
            var self = this;
            var orders = _super_order.export_for_printing.call(this);
            var new_val = {
                assigned_config: this.get_assigned_config() || false,
            };
            if (self.is_reprint && self.payment_data) {
                new_val["paymentlines"] = [];
                new_val["change"] = self.amount_return;
                _.each(self.payment_data, function (each_payment_data) {
                    if (each_payment_data.amount && Math.abs(each_payment_data.amount) != self.amount_return) {
                        var payment_data = { amount: each_payment_data.amount, name: each_payment_data.payment_method_id[1] };
                        new_val["paymentlines"].push(payment_data);
                    }
                });
            }
            $.extend(orders, new_val);
            return orders;
        },
    });

    var PosModelSuper = models.PosModel;
    models.PosModel = models.PosModel.extend({
        initialize: function () {
            var self = this;
            PosModelSuper.prototype.initialize.apply(this, arguments);
            this.save = false;
            this.is_new = false
        },
        add_new_order: function(options){
            if(!this.is_new){
                return PosModelSuper.prototype.add_new_order.apply(this, arguments);
            }else{
                return false
            }
        },
        notification: function (type, message) {
            var self = this;
            var types = ["success", "warning", "info", "danger"];
            if ($.inArray(type.toLowerCase(), types) != -1) {
                var newMessage = "";
                message = _t(message);
                switch (type) {
                    case "success":
                        newMessage = '<i class="fa fa-check" aria-hidden="true"></i> ' + message + '<i class="fa fa-remove remove_notification" aria-hidden="true" style="margin-left:10px;" id=' + message.split(" ")[1] + "'></i> ";
                        break;
                    case "warning":
                        newMessage = '<i class="fa fa-exclamation-triangle" aria-hidden="true"></i> ' + message + '<i class="fa fa-remove remove_notification" aria-hidden="true" id="2" style="margin-left:10px;"></i> ';
                        break;
                    case "info":
                        newMessage = '<i class="fa fa-info" aria-hidden="true"></i> ' + message + '<i class="fa fa-remove remove_notification" aria-hidden="true" style="margin-left:10px;" id=' + message.split(" ")[1] + "'></i> ";
                        break;
                    case "danger":
                        newMessage = '<i class="fa fa-ban" aria-hidden="true"></i> ' + message + '<i class="fa fa-remove remove_notification" aria-hidden="true" id="4" style="margin-left:10px;"></i> ';
                        break;
                }
                if ($("body").find("#" + message.split(" ")[1])) {
                    $("body")
                        .find("#" + message.split(" ")[1])
                        .parent()
                        .remove();
                }
                $("body").append('<div class="msg_div"><div id="' + message.split(" ")[1] + '">' + '<div class="alert alert-' + type + ' ">' + newMessage + "</div>" + "</div></div>");
                $("#" + message.split(" ")[1]).click(function (event) {
                    $("#" + message.split(" ")[1]).hide();
                });
            }
        },
    });
});
