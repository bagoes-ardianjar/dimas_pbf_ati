odoo.define("sh_pos_order_sync.chrome", function (require) {
    "use strict";

    const Chrome = require("point_of_sale.Chrome");
    const Registries = require("point_of_sale.Registries");
    var bus_service = require("bus.BusService");
    const bus = require("bus.Longpolling");
    const session = require("web.session");
    const { loadCSS } = require("web.ajax");
    var rpc = require("web.rpc");
    var core = require("web.core");

    var _t = core._t;

    const PosResChrome = (Chrome) =>
        class extends Chrome {
            _buildChrome() {
                super._buildChrome();
                var bus_service_obj = bus_service.prototype;
                bus_service_obj["env"] = this.env;
                bus_service_obj.call("bus_service", "updateOption", "order.pos", session.uid);
                bus_service_obj.call("bus_service", "onNotification", this, this._onNotification);
                bus_service_obj.call("bus_service", "startPolling");
            }
            _onNotification(notifications) {
                var self = this;
                for (var notif of notifications) {
                    if (notif['payload'] && notif['payload']["edit_pos_order"]) {
                        if (self.env.pos.db.order_by_id[notif['payload'].edit_pos_order[0].id]) {
                            if (notif['payload'].edit_pos_order[0].state == "draft") {
                                if (notif['payload'].edit_pos_order[0].floor_id && notif['payload'].edit_pos_order[0].floor_id[1] && notif['payload'].edit_pos_order[0].table_id && notif['payload'].edit_pos_order[0].table_id[1]) {
                                    self.env.pos.notification(
                                        "success",
                                        _t(notif['payload'].edit_pos_order[0].pos_reference + " ( " + notif['payload'].edit_pos_order[0].floor_id[1] + " - " + notif['payload'].edit_pos_order[0].table_id[1] + " ) order has been edited.")
                                    );
                                } else {
                                    self.env.pos.notification("success", _t(notif['payload'].edit_pos_order[0].pos_reference + " order has been edited."));
                                }
                                self.env.pos.db.order_by_id[notif['payload'].edit_pos_order[0].id] = notif['payload'].edit_pos_order[0];
                                _.each(notif['payload'].edit_pos_order[0].lines, function (each_order_line) {
                                    rpc.query({
                                        model: "pos.order.line",
                                        method: "search_read",
                                        domain: [["id", "=", each_order_line]],
                                    }).then(function (order_line) {
                                        if (order_line) {
                                            self.env.pos.db.order_line_by_id[order_line[0].id] = order_line[0];
                                        }
                                    });
                                });
                            }
                        }
                    } else if (notif['payload'] && notif['payload']["new_pos_order"]) {
                        self.env.pos.db.all_order.push(notif['payload'].new_pos_order[0]);
                        
                        if (self.env.pos.get_order() && notif['payload'].new_pos_order[0].session_id[0] != self.env.pos.get_order().pos_session_id) {
                            
                            if (notif['payload'].new_pos_order[0].sh_is_order_send) {
                                self.env.pos.db.all_display_order.push(notif['payload'].new_pos_order[0]);
                            }
                        }
                        self.env.pos.order_length = self.env.pos.order_length + 1;
                        self.env.pos.db.order_by_id[notif['payload'].new_pos_order[0].id] = notif['payload'].new_pos_order[0];
                        _.each(notif['payload'].new_pos_order[0].lines, function (each_order_line) {
                            rpc.query({
                                model: "pos.order.line",
                                method: "search_read",
                                domain: [["id", "=", each_order_line]],
                            }).then(function (order_line) {
                                self.env.pos.db.order_line_by_id[order_line[0].id] = order_line[0];
                            });
                        });
                        if (notif['payload'].new_pos_order[0].user_id[0] != self.env.pos.user.id) {
                            if (notif['payload'].new_pos_order[0].floor_id && notif['payload'].new_pos_order[0].floor_id[1] && notif['payload'].new_pos_order[0].table_id && notif['payload'].new_pos_order[0].table_id[1]) {
                                self.env.pos.notification(
                                    "success",
                                    _t(notif['payload'].new_pos_order[0].pos_reference + " ( " + notif['payload'].new_pos_order[0].floor_id[1] + " - " + notif['payload'].new_pos_order[0].table_id[1] + " ) order has been created.")
                                );
                            } else {
                                self.env.pos.notification("success", _t(notif['payload'].new_pos_order[0].pos_reference + " order has been created."));
                            }
                        }
                    } else if (notif['payload'] && notif['payload']["paid_pos_order"]) {
                        if (self.env.pos.db.order_by_id[notif['payload'].paid_pos_order[0].id]) {
                            if (notif['payload'].paid_pos_order[0].floor_id && notif['payload'].paid_pos_order[0].floor_id[1] && notif['payload'].paid_pos_order[0].table_id && notif['payload'].paid_pos_order[0].table_id[1]) {
                                self.env.pos.notification(
                                    "success",
                                    _t(notif['payload'].paid_pos_order[0].pos_reference + " ( " + notif['payload'].paid_pos_order[0].floor_id[1] + " - " + notif['payload'].paid_pos_order[0].table_id[1] + " ) order has been paid.")
                                );

                            } else {
                                var data = $.grep(self.env.pos.db.all_display_order, function (e) {
                                    return e.id != notif['payload'].paid_pos_order[0].id;
                                });
                                
                                self.env.pos.db.all_display_order = data
                                if(self.env.pos.get_order() && notif['payload'].paid_pos_order[0].session_id[0] != self.env.pos.get_order().pos_session_id){
                                    self.env.pos.notification("success", _t(notif['payload'].paid_pos_order[0].pos_reference + " order has been paid."));
                                }
                            }
                            self.env.pos.db.order_by_id[notif['payload'].paid_pos_order[0].id] = notif['payload'].paid_pos_order[0];
                            if(notif['payload'].paid_pos_order[0] && notif['payload'].paid_pos_order[0].session_id && notif['payload'].paid_pos_order[0].session_id[0] && notif['payload'].paid_pos_order[0].session_id[0] != self.env.pos.pos_session.id){                            	
                            	if(notif['payload'].paid_pos_order[0] && notif['payload'].paid_pos_order[0]['to_invoice']){
                            		notif['payload'].paid_pos_order[0]['state'] = 'invoiced'
                            	}
                            	self.env.pos.db.all_display_order.unshift(self.env.pos.db.order_by_id[notif['payload'].paid_pos_order[0].id])
                            }

                            _.each(notif['payload'].paid_pos_order[0].lines, function (each_order_line) {
                                rpc.query({
                                    model: "pos.order.line",
                                    method: "search_read",
                                    domain: [["id", "=", each_order_line]],
                                }).then(function (order_line) {
                                    if (order_line) {
                                        self.env.pos.db.order_line_by_id[order_line[0].id] = order_line[0];
                                    }
                                });
                            });
                        }
                    } else if (notif['payload'] && notif['payload']["cancel_pos_order"]) {
                        if (self.env.pos.db.order_by_id[notif['payload'].cancel_pos_order[0].id]) {
                            if (self.env.pos.db.order_by_id[notif['payload'].cancel_pos_order[0].id]) {
                                self.env.pos.notification("success", _t(notif['payload'].cancel_pos_order[0].pos_reference + " order has been cancelled."));
                                delete self.env.pos.db.order_by_id[notif['payload'].cancel_pos_order[0].id];
                                _.each(notif['payload'].cancel_pos_order[0].lines, function (each_order_line) {
                                    if (self.env.pos.db.order_line_by_id[each_order_line]) {
                                        delete self.env.pos.db.order_line_by_id[each_order_line];
                                        self.env.pos.order_length = self.env.pos.order_length - 1;
                                    }
                                });
                            }
                        }
                    }
                }
            }
        };

    Registries.Component.extend(Chrome, PosResChrome);

    return Chrome;
});
