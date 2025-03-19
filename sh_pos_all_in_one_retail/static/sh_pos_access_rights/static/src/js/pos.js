odoo.define("sh_pos_access_rights.screens", function (require) {
    "use strict";

    const ActionpadWidget = require("point_of_sale.ActionpadWidget");
    const NumpadWidget = require("point_of_sale.NumpadWidget");
    const PaymentScreen = require("point_of_sale.PaymentScreen");
    const TicketScreen = require('point_of_sale.TicketScreen')
    const ProductScreen = require("point_of_sale.ProductScreen");
    const NumberBuffer = require('point_of_sale.NumberBuffer');
    const Registries = require("point_of_sale.Registries");
    const OrderWidget = require("point_of_sale.OrderWidget");

    const ShTicketScreen = (TicketScreen) =>
        class extends TicketScreen {
            mounted() {
                super.mounted()
                var self = this;
                _.each(self.env.pos.users, function (user) {
                    if (user["id"] == self.env.pos.get_cashier().user_id[0]) {
                        if (user.groups_id.indexOf(self.env.pos.config.group_disable_hide_orders[0]) === -1) {
                            $('button.highlight').show()
                            $('.delete-button').show()
                        } else {
                            $('button.highlight').hide()
                            $('.delete-button').hide()
                        }
                    }
                })
            }
        }
    Registries.Component.extend(TicketScreen, ShTicketScreen);

    const SHPaymentScreen = (PaymentScreen) =>
        class extends PaymentScreen {
            mounted() {
                super.mounted();
                var self = this;
                _.each(this.env.pos.users, function (user) {
                    if (user["id"] == self.env.pos.get_cashier().user_id[0]) {
                        // Enable-disable customer selection Button
                        if (user.groups_id.indexOf(self.env.pos.config.group_select_customer[0]) === -1) {
                            $(".customer-button").prop("disabled", false);
                            $(".customer-button").removeClass("sh_disabled");
                        } else {
                            $(".customer-button").prop("disabled", true);
                            $(".customer-button").addClass("sh_disabled");
                        }
                    }
                });
            }
        };
    Registries.Component.extend(PaymentScreen, SHPaymentScreen);


    const ShProductScreen = (ProductScreen) =>
        class extends ProductScreen {
            async _updateSelectedOrderline(event) {
                var self = this;
                var is_Backspace = false
                const selectedLine = this.currentOrder.get_selected_orderline();
                await _.each(self.env.pos.users, function (user) {
                    if (user["id"] == self.env.pos.get_cashier().user_id[0]) {
                        if (!(user.groups_id.indexOf(self.env.pos.config.group_disable_remove[0]) === -1)) {
                            if (selectedLine && event.detail.key === 'Backspace') {
                                is_Backspace = true
                            }
                        } 
                    }
                })
                if(is_Backspace){
                    return false
                }
                if (event.detail.buffer == "") {
                    super._updateSelectedOrderline(event);
                } else {
                    if (this.state.numpadMode === "quantity") {
                        if (self.env.pos.user.groups_id.indexOf(self.env.pos.config.group_disable_qty[0]) === -1) {
                            super._updateSelectedOrderline(event);
                        } else {
                            NumberBuffer.reset();
                        }
                    }
                    if (this.state.numpadMode === "discount") {
                        if (self.env.pos.user.groups_id.indexOf(self.env.pos.config.group_disable_discount[0]) === -1) {
                            super._updateSelectedOrderline(event);
                        } else {
                            NumberBuffer.reset();
                        }
                    }
                    if (this.state.numpadMode === "price") {
                        if (self.env.pos.user.groups_id.indexOf(self.env.pos.config.group_disable_price[0]) === -1) {
                            super._updateSelectedOrderline(event);
                        } else {
                            NumberBuffer.reset();
                        }
                    }
                }
            }
        };
    Registries.Component.extend(ProductScreen, ShProductScreen);

    const RoundingOrderWidget = (OrderWidget) =>
    class extends OrderWidget {
        constructor() {
            super(...arguments);
        }
        _updateSummary() {
            var self = this;
            setTimeout(() => {
                if (self.env.pos.user.groups_id.indexOf(self.env.pos.config.group_disable_remove_ordeline[0]) === -1) {
                    if ($('.span_delete_icon') && $('.span_delete_icon').length > 0) {
                        $('.span_delete_icon').prop("disabled", false);
                        $('.span_delete_icon').removeClass("sh_disabled")
                    }
                } else {
                    if ($('.span_delete_icon') && $('.span_delete_icon').length > 0) {
                        $('.span_delete_icon').prop("disabled", true);
                        $('.span_delete_icon').addClass("sh_disabled")
                    }
                }
            }, 100);
            super._updateSummary();
        }
    };

    Registries.Component.extend(OrderWidget, RoundingOrderWidget);

    const SHNumpadWidget = (NumpadWidget) =>
        class extends NumpadWidget {
            mounted() {
                var self = this;
                super.mounted(...arguments);
                _.each(self.env.pos.users, function (user) {
                    if (user["id"] == self.env.pos.get_cashier().user_id[0]) {
                        // Enable-disable discount Button
                        if (user.groups_id.indexOf(self.env.pos.config.group_disable_discount[0]) === -1) {
                            $($(".mode-button")[1]).prop("disabled", false);
                            $($(".mode-button")[1]).removeClass("sh_disabled_qty");
                        } else {
                            $($(".mode-button")[1]).prop("disabled", true);
                            $($(".mode-button")[1]).addClass("sh_disabled_qty");
                        }
                        // Enable-disable qty Button
                        if (user.groups_id.indexOf(self.env.pos.config.group_disable_qty[0]) === -1) {
                            $($(".mode-button")[0]).prop("disabled", false);
                            $($(".mode-button")[0]).removeClass("sh_disabled_qty");
                        } else {
                            $($(".mode-button")[0]).prop("disabled", true);
                            $($(".mode-button")[0]).addClass("sh_disabled_qty");
                        }
                        // Enable-disable price Button
                        if (user.groups_id.indexOf(self.env.pos.config.group_disable_price[0]) === -1) {
                            $($(".mode-button")[2]).prop("disabled", false);
                            $($(".mode-button")[2]).removeClass("sh_disabled_qty");
                        } else {
                            $($(".mode-button")[2]).prop("disabled", true);
                            $($(".mode-button")[2]).addClass("sh_disabled_qty");
                        }
                        // Enable-disable Plus Minus
                        if (user.groups_id.indexOf(self.env.pos.config.group_disable_plus_minus[0]) === -1) {
                            $(".numpad-minus").prop("disabled", false);
                            $(".numpad-minus").removeClass("sh_disabled");
                        } else {
                            $(".numpad-minus").prop("disabled", true);
                            $(".numpad-minus").addClass("sh_disabled");
                        }
                        // Enable-disable Numpad
                        if (user.groups_id.indexOf(self.env.pos.config.group_disable_numpad[0]) === -1) {
                            $(".number-char").prop("disabled", false);
                            $(".number-char").removeClass("sh_disabled");
                        } else {
                            $(".number-char").prop("disabled", true);
                            $(".number-char").addClass("sh_disabled");
                        }
                        // Disable Remove Button
                        if (user.groups_id.indexOf(self.env.pos.config.group_disable_remove[0]) === -1) {
                            $(".numpad-backspace").prop("disabled", false);
                            $(".numpad-backspace").removeClass("sh_disabled")
                        } else {
                            $(".numpad-backspace").prop("disabled", true);
                            $(".numpad-backspace").addClass("sh_disabled")
                        }
                    }
                });
                this.changeMode("quantity");
            }
            changeMode(mode) {
                super.changeMode(...arguments);

                if (this.env.pos.user.groups_id.indexOf(this.env.pos.config.group_disable_qty[0]) != -1 && this.env.pos.user.groups_id.indexOf(this.env.pos.config.group_disable_price[0]) != -1) {
                    mode = "discount";
                    this.trigger("set-numpad-mode", { mode });
                    this.props.activeMode = "discount";
                } else if (this.env.pos.user.groups_id.indexOf(this.env.pos.config.group_disable_qty[0]) != -1) {
                    mode = "price";
                    this.trigger("set-numpad-mode", { mode });
                    this.props.activeMode = "price";
                }
            }
        };

    Registries.Component.extend(NumpadWidget, SHNumpadWidget);

    const SHActionpadWidget = (ActionpadWidget) =>
        class extends ActionpadWidget {
            mounted() {
                super.mounted(...arguments);
                var self = this;
                _.each(this.env.pos.users, function (user) {
                    if (user["id"] == self.env.pos.get_cashier().user_id[0]) {
                        // Enable-disable Payment Button
                        if (user.groups_id.indexOf(self.env.pos.config.disable_payment_id[0]) === -1) {
                            $(".pay").prop("disabled", false);
                            $(".pay").removeClass("sh_disabled");
                        } else {
                            $(".pay").prop("disabled", true);
                            $(".pay").addClass("sh_disabled");
                        }
                        // Enable-disable customer selection Button
                        if (user.groups_id.indexOf(self.env.pos.config.group_select_customer[0]) === -1) {
                            $(".set-customer").prop("disabled", false);
                            $(".set-customer").removeClass("sh_disabled");
                        } else {
                            $(".set-customer").prop("disabled", true);
                            $(".set-customer").addClass("sh_disabled");
                        }
                    }
                });
            }
        };

    Registries.Component.extend(ActionpadWidget, SHActionpadWidget);

    return {
        NumpadWidget,
        ActionpadWidget,
    };
});
