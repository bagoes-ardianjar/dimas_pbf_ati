odoo.define("sh_pos_order_sync.screen", function (require) {
    "use strict";

    const { debounce } = owl.utils;
    const PosComponent = require("point_of_sale.PosComponent");
    const Registries = require("point_of_sale.Registries");
    const { useListener } = require("web.custom_hooks");
    const rpc = require("web.rpc");
    var core = require("web.core");
    var framework = require("web.framework");
    var QWeb = core.qweb;
    const orderlist_screens = require("sh_pos_order_list.screen");
    const orderlist_line_screens = require("sh_pos_order_list.order_line");
    const { Gui } = require("point_of_sale.Gui");

    const POSOrderLineListScreen = (orderlist_line_screens) => class extends orderlist_line_screens {};
    Registries.Component.extend(orderlist_line_screens, POSOrderLineListScreen);

    const POSOrderListScreen = (orderlist_screens) =>
        class extends orderlist_screens {
        	sh_paid_order_filter() {
        		this.filter_by_draft_order = false
        		super.sh_paid_order_filter()
        	}
        	sh_posted_order_filter() {
        		this.filter_by_draft_order = false
        		super.sh_posted_order_filter()
            }
        	sh_invoiced_order_filter() {
        		this.filter_by_draft_order = false
        		super.sh_invoiced_order_filter()
            }
            sync_order(event) {
                var self = this;
                $(".sh_pagination").pagination("updateItems", Math.ceil(self.env.pos.order_length / self.env.pos.config.sh_how_many_order_per_page));
                $(".sh_pagination").pagination("selectPage", 1);
            }
            
            filter_by_draft(){
                
                if ($('.sh_filter_draft').hasClass('highlight')) {
                    this.filter_by_draft_order = false
                    $('.sh_filter_draft').removeClass('highlight')
                } else {
                    this.filter_by_draft_order = true
                    this.filter_by_paid_order = false
                    this.filter_by_posted_order = false
                    this.filter_by_invoice_order = false
                    $('.sh_filter_buttons').find('button').removeClass('highlight')
                    $('.sh_paid_order').removeClass('highlight')
                    $('.sh_posted_order').removeClass('highlight')
                    $('.sh_invoiced_order').removeClass('highlight')
                    $('.sh_filter_draft').addClass('highlight')
                }
                $(".sh_pagination").pagination("selectPage", 1);
                this.render()
            }
            get posorderdetail(){
                var res = super.posorderdetail
                var self = this;
                if(this.filter_by_draft_order){
                    if (this.state.query && this.state.query.trim() !== "") {
                        var templates = this.get_order_by_paid_order(this.state.query.trim());
                        $(".sh_pagination").pagination("updateItems", Math.ceil(templates.length / self.env.pos.config.sh_how_many_order_per_page));
                        var current_page = $(".sh_pagination").find('.active').text();
    
                        var showFrom = parseInt(self.env.pos.config.sh_how_many_order_per_page) * (parseInt(current_page) - 1);;
                        var showTo = showFrom + parseInt(self.env.pos.config.sh_how_many_order_per_page);
                        templates = templates.slice(showFrom, showTo);
    
                        return templates;
                    } else {
                        var templates = this.get_order_by_state('draft');
    
                        $(".sh_pagination").pagination("updateItems", Math.ceil(templates.length / self.env.pos.config.sh_how_many_order_per_page));
    
                        var current_page = $(".sh_pagination").find('.active').text();
    
                        var showFrom = parseInt(self.env.pos.config.sh_how_many_order_per_page) * (parseInt(current_page) - 1);
                        var showTo = showFrom + parseInt(self.env.pos.config.sh_how_many_order_per_page);
                        templates = templates.slice(showFrom, showTo);
                        return templates;
                    }
                }else{ 
                    return res
                }

            }
            pay_pos_order(event) {
                var self = this;
                var order_id = event.currentTarget.closest("tr").attributes[0].value;
                var order_data = self.env.pos.db.order_by_uid[order_id];
                if (!order_data) {
                    order_data = self.env.pos.db.order_by_id[order_id];
                }
                var order_line = [];
                var current_order = self.env.pos.get_order();
                if (self.env.pos.get_order() && self.env.pos.get_order().get_orderlines() && self.env.pos.get_order().get_orderlines().length > 0) {
                    var orderlines = self.env.pos.get_order().get_orderlines();
                    _.each(orderlines, function (each_orderline) {
                        if (self.env.pos.get_order().get_orderlines()[0]) {
                            self.env.pos.get_order().remove_orderline(self.env.pos.get_order().get_orderlines()[0]);
                        }
                    });
                }
                var current_order = self.env.pos.get_order();
                $(".save_button").addClass("show_save_button");
                _.each(order_data.lines, function (each_order_line) {
                    var line_data = self.env.pos.db.order_line_by_id[each_order_line];
                    var product = self.env.pos.db.get_product_by_id(line_data.product_id[0]);
                    if (product) {
                        current_order.add_product(product, {
                            quantity: line_data.qty,
                            price: line_data.price_unit,
                            discount: line_data.discount,
                        });
                    }
                });
                if (order_data.partner_id && order_data.partner_id[0]) {
                    current_order.set_client(self.env.pos.db.get_partner_by_id(order_data.partner_id[0]));
                }
                current_order.is_edit = true;
                current_order.name = order_data.pos_reference;
                current_order.assigned_config = order_data.assigned_config;
                
                self.trigger("close-temp-screen");
                $(".pay").click();
            }
            edit_pos_order(event) {
                var self = this;
                var order_id = event.currentTarget.closest("tr").attributes[0].value;
                var order_data = self.env.pos.db.order_by_uid[order_id];
                if (!order_data) {
                    order_data = self.env.pos.db.order_by_id[order_id];
                }
                var order_line = [];
                var current_order = self.env.pos.get_order();
                if (self.env.pos.get_order() && self.env.pos.get_order().get_orderlines() && self.env.pos.get_order().get_orderlines().length > 0) {
                    var orderlines = self.env.pos.get_order().get_orderlines();
                    _.each(orderlines, function (each_orderline) {
                        if (self.env.pos.get_order().get_orderlines()[0]) {
                            self.env.pos.get_order().remove_orderline(self.env.pos.get_order().get_orderlines()[0]);
                        }
                    });
                }
                var current_order = self.env.pos.get_order();
                $(".save_button").addClass("show_save_button");
                _.each(order_data.lines, function (each_order_line) {
                    var line_data = self.env.pos.db.order_line_by_id[each_order_line];
                    var product = self.env.pos.db.get_product_by_id(line_data.product_id[0]);
                    if (product) {
                        current_order.add_product(product, {
                            quantity: line_data.qty,
                            price: line_data.price_unit,
                            discount: line_data.discount,
                        });
                    }
                });
                if (order_data.partner_id && order_data.partner_id[0]) {
                    current_order.set_client(self.env.pos.db.get_partner_by_id(order_data.partner_id[0]));
                }
                current_order.is_edit = true;
                current_order.name = order_data.pos_reference;
                current_order.assigned_config = order_data.assigned_config;
                self.trigger("close-temp-screen");
            }
            cancel_pos_order(event) {
                var self = this;
                var order_id = event.currentTarget.closest("tr").attributes[0].value;
                var params = {
                    model: "pos.order",
                    method: "cancel_order",
                    args: [order_id],
                };
                rpc.query(params, { async: false }).then(function (orders) {
                    if (orders) {
                        self.sync_order();
                    }
                });
            }
           
            reorder_pos_order(event) {
                var self = this;
                var order_id = event.currentTarget.closest("tr").attributes[0].value;
                var order_data = self.env.pos.db.order_by_uid[order_id];
                if (!order_data) {
                    order_data = self.env.pos.db.order_by_id[order_id];
                }
                var order_line = [];
                if (self.env.pos.get_order() && self.env.pos.get_order().get_orderlines() && self.env.pos.get_order().get_orderlines().length > 0) {
                    var orderlines = self.env.pos.get_order().get_orderlines();
                    _.each(orderlines, function (each_orderline) {
                        if (self.env.pos.get_order().get_orderlines()[0]) {
                            self.env.pos.get_order().remove_orderline(self.env.pos.get_order().get_orderlines()[0]);
                        }
                    });
                }
                var current_order = self.env.pos.get_order();
                _.each(order_data.lines, function (each_order_line) {
                    var line_data = self.env.pos.db.order_line_by_id[each_order_line];
                    if (!line_data) {
                        line_data = self.env.pos.db.order_line_by_uid[each_order_line[2].sh_line_id];
                    }
                    var product = self.env.pos.db.get_product_by_id(line_data.product_id[0]);
                    if (!product) {
                        product = self.env.pos.db.get_product_by_id(line_data.product_id);
                    }
                    if (product) {
                        current_order.add_product(product, {
                            quantity: line_data.qty,
                            price: line_data.price_unit,
                            discount: line_data.discount,
                        });
                    }
                });
                if (order_data.partner_id[0]) {
                    self.env.pos.get_order().set_client(self.env.pos.db.get_partner_by_id(order_data.partner_id[0]));
                }
                current_order.assigned_config = order_data.assigned_config;
                self.trigger("close-temp-screen");
            }
            print_pos_order(event) {
                var self = this;
                var order_id = event.currentTarget.closest("tr").attributes[0].value;
                var order_data = self.env.pos.db.order_by_uid[order_id];
                if (!order_data) {
                    order_data = self.env.pos.db.order_by_id[order_id];
                }
                var order_line = [];
                if (self.env.pos.get_order() && self.env.pos.get_order().get_orderlines() && self.env.pos.get_order().get_orderlines().length > 0) {
                    var orderlines = self.env.pos.get_order().get_orderlines();
                    _.each(orderlines, function (each_orderline) {
                        if (self.env.pos.get_order().get_orderlines()[0]) {
                            self.env.pos.get_order().remove_orderline(self.env.pos.get_order().get_orderlines()[0]);
                        }
                    });
                }
                var current_order = self.env.pos.get_order();
                _.each(order_data.lines, function (each_order_line) {
                    var line_data = self.env.pos.db.order_line_by_id[each_order_line];
                    if (!line_data) {
                        line_data = self.env.pos.db.order_line_by_uid[each_order_line[2].sh_line_id];
                    }
                    var product = self.env.pos.db.get_product_by_id(line_data.product_id[0]);
                    if (!product) {
                        product = self.env.pos.db.get_product_by_id(line_data.product_id);
                    }
                    if (product) {
                        current_order.add_product(product, {
                            quantity: line_data.qty,
                            price: line_data.price_unit,
                            discount: line_data.discount,
                        });
                    }
                });
                if (order_data.partner_id) {
                    current_order.set_client(self.env.pos.db.get_partner_by_id(order_data.partner_id[0]));
                }
                current_order.name = order_data.pos_reference;
                current_order.assigned_config = order_data.assigned_config;
                current_order.payment_data = order_data.payment_data;
                current_order.amount_return = order_data.amount_return;
                current_order.is_reprint = true;
                self.trigger("close-temp-screen");
                self.showScreen("ReceiptScreen");
            }
        };
    Registries.Component.extend(orderlist_screens, POSOrderListScreen);
});
