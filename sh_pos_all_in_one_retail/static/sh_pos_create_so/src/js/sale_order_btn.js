odoo.define("sh_pos_create_so.saleOrderbtn", function (require) {
    "use strict";

    const PosComponent = require("point_of_sale.PosComponent");
    const ProductScreen = require("point_of_sale.ProductScreen");
    const { useListener } = require("web.custom_hooks");
    const Registries = require("point_of_sale.Registries");
    var rpc = require("web.rpc");

    class SaleOrderBtn extends PosComponent {
        constructor() {
            super(...arguments);
            useListener('click-sale-order-button', this.onClickTemplateLoad)
        }
        onClickTemplateLoad() {
            var self = this
            var order = this.env.pos.get_order();
            var orderlines = order.get_orderlines();
            var client = this.env.pos.get_client();

            if (orderlines.length > 0) {
                if (client != null) {
                    var sale_payment_term = false
                    if(client && client.property_payment_term_id){
                        sale_payment_term = client.property_payment_term_id[0]
                    }
                    var sale_order_line = []
                    _.each(orderlines, function (orderline) {
                        var product_id = orderline.product.id
                        var product_nm = orderline.product.display_name
                        var product_qty = orderline.quantity
                        var product_price = orderline.price
                        var product_discount = orderline.discount
                        var tax = orderline.product.taxes_id

                        if(orderline.product.default_code == 'sh_pos_order_label_line'){
                            sale_order_line.push({
                                'name': orderline.add_section,
                                'display_type': 'line_section',
                            })
                        }else{
                            sale_order_line.push({
                                'product_id': product_id,
                                'name': product_nm,
                                'product_uom_qty': product_qty,
                                'price_unit': product_price,
                                'discount': product_discount,
                                'tax_id': tax,
                            })
                        }
                    })

                    var sale_order = { 'partner_id': client.id, 'payment_term_id': sale_payment_term,  'order_lines': sale_order_line }
                    
                    if(self.env.pos.config.select_order_state == 'confirm'){
                        sale_order['state'] = 'confirm'
                    }

                    self.env.pos.db.all_sale_orders.push(sale_order)

                    try {
                        self.env.pos.create_sale_order()
                    } catch (error) {
                        if (error instanceof Error) {
                            throw error;
                        } else {
                            self.env.pos.set_synch(self.env.pos.get("failed") ? "error" : "disconnected");
                            self._handlePushOrderError(error);
                        }
                    }


                } else {
                    alert("Select Customer...!")
                }
            } else {
                alert("Please Add Product...!")
            }
        }
    }
    SaleOrderBtn.template = "SaleOrderBtn";

    ProductScreen.addControlButton({
        component: SaleOrderBtn,
        condition: function () {
            return this.env.pos.config.sh_display_sale_btn;
        },
    })

    Registries.Component.add(SaleOrderBtn)

    return SaleOrderBtn;
});
