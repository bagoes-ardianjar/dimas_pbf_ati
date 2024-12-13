odoo.define("sh_pos_order_sync.popup", function (require) {
    "use strict";

    const Registries = require("point_of_sale.Registries");
    const AbstractAwaitablePopup = require("point_of_sale.AbstractAwaitablePopup");

    class TemplateReceiverPopupWidget extends AbstractAwaitablePopup {
        constructor() {
            super(...arguments);
        }
        async confirm() {
            this.props.resolve({ confirmed: true, payload: await this.getPayload() });
            var self = this;
            var assigned_config = [];
            _.each($("tr.highlight"), function (each_config_line) {
                assigned_config.push(parseInt(each_config_line.getAttribute("data-value")));
            });
            self.env.pos.get_order().set_assigned_config(assigned_config);
            self.env.pos.get_order().is_order_send = true;
            self.env.pos.push_orders(self.env.pos.get_order());
            self.env.pos.is_new = true;
            self.env.pos.get_order().destroy();
            self.env.pos.is_new = false
            self.env.pos.add_new_order();
            this.trigger("close-popup");
            if (this.env.pos.config.module_pos_restaurant){ 
                this.showScreen('FloorScreen');
            }
        }
        async onClickSessionRow(event) {
            var self = this;

            if (!self.env.pos.config.sh_allow_multiple_selection) {
                $(".session_row.highlight").removeClass("highlight");
            }
            if ($(event.currentTarget).hasClass("highlight")) {
                $(event.currentTarget).removeClass("highlight");
            } else {
                $(event.currentTarget).addClass("highlight");
            }
            if (!self.env.pos.config.sh_allow_multiple_selection) {
                self.env.pos.get_order().set_assigned_config([$(event.currentTarget).data("value")]);
                self.env.pos.get_order().is_order_send = true;
                self.env.pos.push_orders(self.env.pos.get_order());
                
                self.env.pos.is_new = true;
                self.env.pos.get_order().destroy();
                self.env.pos.is_new = false
                self.env.pos.add_new_order();
                self.trigger("close-popup");
            }
        }
    }

    TemplateReceiverPopupWidget.template = "TemplateReceiverPopupWidget";
    Registries.Component.add(TemplateReceiverPopupWidget);
});
