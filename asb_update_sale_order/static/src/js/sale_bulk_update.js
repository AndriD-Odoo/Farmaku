odoo.define('sale.SaleOrder', function (require) {
    "use strict";

    var core = require('web.core');
    var ListView = require('web.ListView');
    var ListController = require("web.ListController");

    var IncludeListView = {

        renderButtons: function() {
            this._super.apply(this, arguments);
            if (this.modelName === "sale.order") {
                var summary_apply_leave_btn = this.$buttons.find('button.o_update_sale_order');              
                summary_apply_leave_btn.on('click', this.proxy('update_sale_order'))
            }
        },
        update_sale_order: function(){
            var self = this;
            var action = {
                type: "ir.actions.act_window",
                name: "Update",
                res_model: "sale.wizard",
                views: [[false,'form']],
                target: 'new',
                views: [[false, 'form']], 
                view_mode : 'form',
                flags: {'form': {'action_buttons': true, 'options': {'mode': 'edit'}}}
            };
            return this.do_action(action);
        },


    };
    ListController.include(IncludeListView);
});