odoo.define("sh_pos_fronted_cancel.db", function (require) {
    "use strict";

    var DB = require("point_of_sale.DB");

    DB.include({
        remove_order_by_uid: function (uid) {
            var all_order = this.all_order;
            this.remove_all_orders();

            for (var i = 0, len = all_order.length; i < len; i++) {
                var each_order = all_order[i];
                if (each_order["sh_uid"] != uid) {
                    this.all_order.push(each_order);
                    this.order_by_id[each_order.id] = each_order;
                    this.order_by_uid[each_order.sh_uid] = each_order;
                }
            }
        },
        get_removed_ordes: function () {
            return this.load("removed_orders", []);
        },
        get_removed_draft_orders: function () {
            return this.load("removed_draft_orders", []);
        },
        get_removed_delete_orders: function () {
            return this.load("removed_delete_orders", []);
        },
        remove_all_orders: function () {
            this.all_order = [];
            this.order_by_id = {};
            this.order_by_uid = {};
        },
    });
});
