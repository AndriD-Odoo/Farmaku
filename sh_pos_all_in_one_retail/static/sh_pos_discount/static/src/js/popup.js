odoo.define("sh_pos_discount.Popup", function (require) {
    "use strict";

    const Registries = require("point_of_sale.Registries");
    const AbstractAwaitablePopup = require("point_of_sale.AbstractAwaitablePopup");
    const { useListener } = require("web.custom_hooks");

    // class DiscountPopupWidget extends AbstractAwaitablePopup {
    class CustomDiscountPopupWidget extends AbstractAwaitablePopup {
        constructor() {
            super(...arguments);
            useListener("discount_row highlight", this.onClickDiscountRow);
        }
        async confirm() {
            var self = this;
            this.props.resolve({ confirmed: true, payload: await this.getPayload() });
            var apply_discount_code_value = [];
            var apply_discount_code = [];
            var apply_discount_value = 0;
            _.each($("tr.highlight"), function (each_highlight_row) {
                apply_discount_code_value.push(each_highlight_row.dataset.code + " ( " + each_highlight_row.dataset.value + "% )");
                apply_discount_code.push(each_highlight_row.dataset.code);
                apply_discount_value += parseInt(each_highlight_row.dataset.value);
            });
            self.env.pos.get_order().get_selected_orderline().set_line_discount(apply_discount_code_value);
            self.env.pos.get_order().get_selected_orderline().set_line_discount_code(apply_discount_code);
            self.trigger("close-popup");
            self.env.pos.get_order().get_selected_orderline().set_discount(apply_discount_value);
        }
        async onClickDiscountRow(event) {
            var value = $(event.currentTarget).data("value");
            if ($(event.currentTarget)[0].classList.length == 2) {
                $(event.currentTarget)[0].classList.remove("highlight");
            } else {
                $(event.currentTarget)[0].classList.add("highlight");
            }
        }
    }

    CustomDiscountPopupWidget.template = "CustomDiscountPopupWidget";
    Registries.Component.add(CustomDiscountPopupWidget);

    return {
        CustomDiscountPopupWidget,
    };
});
