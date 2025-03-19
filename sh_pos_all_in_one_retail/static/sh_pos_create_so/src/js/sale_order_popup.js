odoo.define("sh_pos_create_so.saleorderbuttonpopup", function (require) {
    "use strict";

    const Registries = require("point_of_sale.Registries");
    const AbstractAwaitablePopup = require("point_of_sale.AbstractAwaitablePopup");

    class saleOrderPopup extends AbstractAwaitablePopup {
        constructor() {
            super(...arguments);
            //   useSubEnv({ attribute_components: [] })
        }
    }
    saleOrderPopup.template = 'saleOrderPopup'

    Registries.Component.add(saleOrderPopup)

    return saleOrderPopup
});
