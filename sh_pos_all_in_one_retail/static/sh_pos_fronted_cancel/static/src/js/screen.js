odoo.define("sh_pos_fronted_cancel.screen", function (require) {
    "use strict";

    const PosComponent = require("point_of_sale.PosComponent");
    const Registries = require("point_of_sale.Registries");
    const OrderListScreen = require("sh_pos_order_list.screen");
    var rpc = require("web.rpc");

    const PosOrderListScreen = (OrderListScreen) =>
        class extends OrderListScreen {
            constructor() {
                super(...arguments);
            }
            click_draft(event) {
                var self = this;
                self.env.pos.db.save("removed_notes", []);
                var order_id = event.currentTarget.closest("tr").attributes[0].value;
                return new Promise(function (resolve, reject) {
                    try {
                        rpc.query({
                            model: "pos.order",
                            method: "sh_fronted_cancel_draft",
                            args: [[parseInt(order_id)]],
                        })
                            .then(function (return_order_data) {
                                if (return_order_data) {
                                    self.env.pos.db.save("removed_draft_orders", []);
                                    self.update_order_list(return_order_data);
                                }
                            })
                            .catch(function (error) {
                                var offline_removed_draft_orders = self.env.pos.db.get_removed_draft_orders();
                                offline_removed_draft_orders.push(parseInt(order_id));

                                self.env.pos.db.save("removed_draft_orders", offline_removed_draft_orders);

                                var return_order_data = { sh_uid: parseInt(order_id) };
                                return_order_data["cancel_draft"] = true;
                                return_order_data["cancel_delete"] = false;

                                self.update_order_list([return_order_data]);
                                self.env.pos.set("synch", { state: "disconnected", pending: "error" });
                            });
                    } catch (error) {}
                });
            }
            click_delete(event) {
                event.stopPropagation()
                var self = this;
                self.env.pos.db.save("removed_notes", []);

                var order_id = parseInt($(event.currentTarget.closest("tr")).attr('data-order-id'))
                // var order_id = event.currentTarget.closest("tr").attributes[0].value;
                               
                return new Promise(function (resolve, reject) {
                    try {
                        rpc.query({
                            model: "pos.order",
                            method: "sh_fronted_cancel_delete",
                            args: [[parseInt(order_id)]],
                        }).then(function (return_order_data) {
                                if (return_order_data) {
                                    self.env.pos.db.save("removed_notes", []);
                                    self.update_order_list(return_order_data);   
                                }
                            })
                            .catch(function (error) {
                                var offline_removed_delete_orders = self.env.pos.db.get_removed_delete_orders();
                                offline_removed_delete_orders.push(parseInt(order_id));
                                
                                self.env.pos.db.save("removed_delete_orders", offline_removed_delete_orders);
                                var return_order_data = { sh_uid: parseInt(order_id) };
                                return_order_data["cancel_draft"] = false;
                                return_order_data["cancel_delete"] = true;

                                self.update_order_list([return_order_data]);
                                self.env.pos.set("synch", { state: "disconnected", pending: "error" });
                            });
                    } catch (error) {}
                });
                
            }
            update_order_list(return_order_data) {
                var self = this;
                var remove_order;
                _.each(self.env.pos.db.all_order, function (each_order) {
                    _.each(return_order_data, function (each_return_order) {
                        if (each_return_order.cancel_draft) {
                            if (each_order.sh_uid == each_return_order.sh_uid) {
                                each_order.state = "draft";
                            }
                        }
                        if (each_return_order.cancel_delete) {
                            self.env.pos.db.remove_order_by_uid(each_return_order.sh_uid);
                        }
                    });
                });
                $('.sh_service_back_btn').click()
                self.render();
                
            }
        };
    Registries.Component.extend(OrderListScreen, PosOrderListScreen);
});
