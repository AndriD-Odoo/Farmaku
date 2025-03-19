odoo.define("sh_pos_create_po.Models", function (require) {
    "use strict";

    var models = require("point_of_sale.models");
    var DB = require("point_of_sale.DB");
    const { Gui } = require("point_of_sale.Gui");

    DB.include({
        init: function (options) {
            this._super(options);
            this.all_purchase_orders = [];
            this.order_uid = 0;
        },
        get_all_purchase_orders: function () {
            // save all po which is crate in offline-mode

            return this.all_purchase_orders;
        },
        remove_all_purchase_orders: function () {
            this.all_purchase_orders = [];
        }
    });

    var _super_posmodel = models.PosModel.prototype;
    models.PosModel = models.PosModel.extend({
        initialize: function (session, attributes) {
            _super_posmodel.initialize.call(this, session, attributes);
        },
        // push_orders: function (order, opts) {
        //     this.create_purchase_order()
        //     return _super_posmodel.push_orders.call(this, order, opts)
        // },
        create_purchase_order: async function () {
            var self = this;
            // return new Promise(function (resolve, reject) {
                try {
                    if (self.env.pos.db.get_all_purchase_orders().length > 0) {
                        
                        for(var po=0; po < self.env.pos.db.get_all_purchase_orders().length; po++){
                            var purchase_order = self.env.pos.db.get_all_purchase_orders()[po]
                            
                            await self.rpc({
                                model: 'purchase.order',
                                method: 'create',
                                args:[{'partner_id': purchase_order['partner_id'],'payment_term_id':purchase_order['payment_term_id']}]
                            }).then(async function (order) {
                                await self.rpc({
                                    model: 'pos.config',
                                    method: 'sh_create_purchase_line',
                                    args: [purchase_order['order_lines'],order]
                                })
                                if (purchase_order['state'] && purchase_order['state'] == 'purchase_order'){
                                    self.rpc({
                                        model: 'purchase.order',
                                        method: 'button_confirm',
                                        args:[order]
                                    })
                                }
                                if(self.env.pos.db.get_all_purchase_orders().length == 1){
                                    self.rpc({
                                        model: 'purchase.order',
                                        method: 'read',
                                        args: [order]
                                    }).then(function (order_data) {
                                        Gui.showPopup('PoPopup', {
                                            title: 'Purchase Order',
                                            body: " Purchase Order Created.",
                                            PurhcaseOrderId: order_data[0].id,
                                            PurchaseOrderName: order_data[0].name
                                        })
                                    })
                                }else{
                                    if (po == (self.env.pos.db.get_all_purchase_orders().length - 1)) {
                                        
                                        Gui.showPopup('PoPopup', {
                                            title: 'Purchase Order',
                                            body: " Purchase Order Created.",
                                        })
                                        
                                    }
                                }
                            }).catch(function (reason) {
                                Gui.showPopup('ErrorPopup', {
                                    title: 'Offline',
                                    body: 'When you online Purchase order will be created automiatically.',
                                });
                                self.set_synch(self.get("failed") ? "error" : "disconnected", self.env.pos.db.get_all_purchase_orders().length);
                            });
                           
                        }
                    }
                } catch (error) {
                    
                    self.set_synch(self.get("failed") ? "error" : "disconnected");
                }
            // });
        }
    });

})
