odoo.define("sh_pos_cash_in_out.db", function (require) {
    "use strict";

    var DB = require("point_of_sale.DB");
    
    DB.include({
        init: function (options) {
            this._super(options);
            this.all_order = [];
            this.all_payment_method = [];
            this.all_cash_in_out_statement = [];
            this.all_cash_in_out_statement_id = [];
            this.display_cash_in_out_statement = [];
            this.payment_method_by_id = {};
            this.all_payment = [];
            this.payment_line_by_id = {};
            this.payment_line_by_ref = {};
            /*this.all_cash_in_out = [];*/
            this.all_cash_in_out = [];
            this.cash_in_out_by_id = {};
            this.cash_in_out_by_uid = {};
            this.save("closing_balance", []);
        },
        get_cash_in_outs: function () {
            return this.load("cash_in_outs", []);
        },
        remove_all_cash_in_outs: function () {
            /*this.all_cash_in_out = [];*/
        	this.all_cash_in_out = [];
            this.cash_in_out_by_id = {};
            this.cash_in_out_by_uid = {};
        },
        add_cash_in_outs: function (all_cash_in_out) {
            if (!all_cash_in_out instanceof Array) {
            	all_cash_in_out = [all_cash_in_out];
            }
            var new_write_date = "";
            for (var i = 0, len = all_cash_in_out.length; i < len; i++) {
                var each_cash_in_out = all_cash_in_out[i];
                this.all_cash_in_out.push(each_cash_in_out);
                this.cash_in_out_by_id[each_cash_in_out.id] = each_cash_in_out;
                this.cash_in_out_by_uid[each_cash_in_out.uid] = each_cash_in_out;
                this.all_cash_in_out_name.push(each_cash_in_out.display_name);
                var local_partner_date = (this.cash_in_out_write_date || "").replace(/^(\d{4}-\d{2}-\d{2}) ((\d{2}:?){3})$/, "$1T$2Z");
                var dist_partner_date = (each_cash_in_out.write_date || "").replace(/^(\d{4}-\d{2}-\d{2}) ((\d{2}:?){3})$/, "$1T$2Z");
                if (this.cash_in_out_write_date && this.cash_in_out_by_id[each_cash_in_out.id] && new Date(local_partner_date).getTime() + 1000 >= new Date(dist_partner_date).getTime()) {
                    continue;
                } else if (new_write_date < each_cash_in_out.write_date) {
                    new_write_date = each_cash_in_out.write_date;
                }
            }
            this.cash_in_out_write_date = new_write_date || this.cash_in_out_write_date;
        },
        get_cash_in_out_write_date: function () {
            return this.cash_in_out_write_date || "1970-01-01 00:00:00";
        },
    });

});