odoo.define("sh_pos_create_po.create_po_popup", function (require) {
    "use strict";

    const Registries = require("point_of_sale.Registries");
    const AbstractAwaitablePopup = require("point_of_sale.AbstractAwaitablePopup");

    class PoPopup extends AbstractAwaitablePopup{
        constructor(){
            super(...arguments);
        }
        click_ok(){
            this.env.pos.db.remove_all_purchase_orders();
            
            this.trigger("close-popup");
        }
    }
    PoPopup.template = 'PoPopup'

    Registries.Component.add(PoPopup)

    return PoPopup
});
