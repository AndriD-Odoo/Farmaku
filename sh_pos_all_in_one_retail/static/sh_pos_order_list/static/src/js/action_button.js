odoo.define("sh_pos_order_list.action_button", function (require) {
    "use strict";

    const PosComponent = require("point_of_sale.PosComponent");
    const { useListener } = require("web.custom_hooks");
    const Registries = require("point_of_sale.Registries");
    const ProductScreen = require("point_of_sale.ProductScreen");
    const rpc = require("web.rpc");
    
    class OrderHistoryButton extends PosComponent {
        constructor() {
            super(...arguments);
            useListener("click-order-history-button", this.onClickOrderHistoryButton);
        }
        onClickOrderHistoryButton() {
            var self = this;
            try {
                rpc.query({
                    model: "pos.order",
                    method: "search_read",
                    domain: [["user_id", "=", self.env.pos.user.id]],
                })
                    .then(function (orders) {
                        self.env.pos.db.all_order = [];
                        self.env.pos.db.order_by_id = {};
                        if (orders) {
                            rpc.query({
                                model: "pos.order.line",
                                method: "search_read",
                            }).then(function (order_line) {
                                self.env.pos.db.order_line_by_id = {};
                                if (order_line) {
                                    self.env.pos.db.all_orders_line(order_line);
                                    self.env.pos.db.all_orders(orders);
                                    if (self.env.pos.db.all_order.length > 0) {
                                        var today = new Date();
                                        var dd = today.getDate();
                                        var mm = today.getMonth() + 1;
                                        var yyyy = today.getFullYear();
                                        var today_date = yyyy + "-" + mm + "-" + dd;
                                        if (self.env.pos.config.sh_load_order_by == "day_wise") {
                                            if (self.env.pos.config.sh_day_wise_option == "current_day") {
                                                self.env.pos.db.all_order = self.env.pos.get_current_day_order(self.env.pos.db.all_order);
                                            } else if (self.env.pos.config.sh_day_wise_option == "last_no_day") {
                                                if (self.env.pos.config.sh_last_no_days != 0) {
                                                    self.env.pos.db.all_order = self.env.pos.get_last_day_order(self.env.pos.db.all_order);
                                                }
                                            }
                                        } else if (self.env.pos.config.sh_load_order_by == "session_wise") {
                                            if (self.env.pos.config.sh_session_wise_option == "current_session") {
                                                self.env.pos.db.all_order = self.env.pos.get_current_session_order(self.env.pos.db.all_order);
                                            } else if (self.env.pos.config.sh_session_wise_option == "last_no_session") {
                                                if (self.env.pos.config.sh_last_no_session != 0) {
                                                    self.env.pos.db.all_order = self.env.pos.get_last_session_order(self.env.pos.db.all_order);
                                                }
                                            }
                                        }
                                    }
                                    const { confirmed, payload } = self.showTempScreen("OrderListScreen");
                                    if (confirmed) {
                                    }
                                }
                            });
                        }
                    })
                    .catch(function (reason) {
                        const { confirmed, payload } = self.showTempScreen("OrderListScreen");
                        if (confirmed) {
                        }
                    });
            } catch (error) {
                self.set_synch(self.get("failed") ? "error" : "disconnected");
                self._handlePushOrderError(error);
            }
        }
    }
    OrderHistoryButton.template = "OrderHistoryButton";
    ProductScreen.addControlButton({
        component: OrderHistoryButton,
        condition: function () {
            return this.env.pos.config.sh_enable_order_list;
        },
    });
    Registries.Component.add(OrderHistoryButton);

    return OrderHistoryButton;
});
