odoo.define("sh_pos_order_list.db_exchange", function (require) {
    "use strict";

    var DB = require("point_of_sale.DB");
    DB.include({
    	init: function (options) {
            this._super(options);
            this.all_order = [];
            this.order_by_id = {};
            this.order_line_by_id = {};
            this.all_session = [];
            this.order_by_uid = {};
            this.all_display_order_temp = [];
            this.display_by_id = {};
            this.display_order_by_uid = {};
            this.order_line_by_uid = {};
            this.all_order_temp = [];
            this.all_display_order = [];
            this.all_return_order = [];
            this.all_non_return_order = [];
            this.display_return_order = [];
            this.display_non_return_order = [];
            this.order_by_id_temp = {};
            
        },
        all_sessions: function (all_session) {
            this.all_session = all_session;
        },
        get_all_orders: function () {
            return this.all_order1;
        },
        all_orders_line: function (all_order_line) {
            var new_write_date = "";
            for (var i = 0, len = all_order_line.length; i < len; i++) {
                var each_order_line = all_order_line[i];
                this.order_line_by_id[each_order_line.id] = each_order_line;
                this.order_line_by_uid[each_order_line.sh_line_id] = each_order_line;
            }
        },
    });
});
