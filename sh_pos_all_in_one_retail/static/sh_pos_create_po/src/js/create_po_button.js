odoo.define("sh_pos_create_po.createpobutton", function (require) {
    "use strict";

    const PosComponent = require("point_of_sale.PosComponent");
    const ProductScreen = require("point_of_sale.ProductScreen");
    const { useListener } = require("web.custom_hooks");
    const Registries = require("point_of_sale.Registries");
    var rpc = require("web.rpc");

    class POButton extends PosComponent {
        constructor() {
            super(...arguments);
            useListener('click-Purchase-button', this.onClickTemplateLoad)
        }
        onClickTemplateLoad() {
            var self = this;
            var order = this.env.pos.get_order()
            var orderlines = order.get_orderlines()
            var client = order.get_client();
            if (client != null) {
                var purchase_payment_term = false
                    if(client && client.property_supplier_payment_term_id){
                        purchase_payment_term = client.property_supplier_payment_term_id[0]
                    }
                if (orderlines.length != 0) {
                    var purchase_order_line = []
                    _.each(orderlines, function (orderline) {
                        var product_id = orderline.product.id
                        var product_nm = orderline.product.display_name
                        var product_qty = orderline.quantity
                        var product_price = orderline.price
                        var tax = orderline.product.taxes_id

                        // po data_dictionary
                        if(orderline.product.default_code == 'sh_pos_order_label_line'){
                            purchase_order_line.push({
                                'name': orderline.add_section,
                                'display_type': 'line_section',
                                'product_qty': product_qty,
                                'price_unit': product_price,
                            })
                        }else{
                            purchase_order_line.push({
                                'product_id': product_id,
                                'name': product_nm,
                                'product_qty': product_qty,
                                'price_unit': product_price,
                                'taxes_id': tax,
                            })
                        }

                    })

                    var purchase_order = { 'partner_id': client.id,  'payment_term_id': purchase_payment_term,  'order_lines': purchase_order_line, 'state': self.env.pos.config.select_purchase_state }

                    self.env.pos.db.all_purchase_orders.push(purchase_order)

                    try {
                        self.env.pos.create_purchase_order()
                    } catch (error) {
                        if (error instanceof Error) {
                            throw error;
                        } else {
                            self.env.pos.set_synch(self.env.pos.get("failed") ? "error" : "disconnected");
                            self._handlePushOrderError(error);
                        }
                    }
                }
                else {
                    alert("Select Product...!")
                }
            }
            else {
                alert("select Customer...!")
            }
        }
    }
    POButton.template = "POButton"

    ProductScreen.addControlButton({
        component: POButton,
        condition: function () {
            return this.env.pos.config.sh_dispaly_purchase_btn;
        }
    })

    Registries.Component.add(POButton)

    return POButton
});

 