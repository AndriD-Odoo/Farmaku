odoo.define("sh_pos_customer_order_history.db", function (require) {
    "use strict";

    var DB = require("point_of_sale.DB");

    DB.include({
        init: function (options) {
            this._super(options);
            this.display_all_order = [];
        },
    });
});
