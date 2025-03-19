odoo.define("sh_pos_cash_in_out.models", function (require) {
    "use strict";

    var models = require("point_of_sale.models");
    var exports = {};
    const { Gui } = require('point_of_sale.Gui');

    models.load_fields("pos.session", ["cash_register_total_entry_encoding","cash_register_balance_end","cash_register_balance_end_real","cash_register_balance_start"]);
    
    models.load_models({
        model: "pos.payment.method",
        label: "load_payment",
        loaded: function (self, all_payment_method) {
            self.db.all_payment_method = all_payment_method;
            if(all_payment_method && all_payment_method.length > 0){
            	_.each(all_payment_method, function(each_payment_method){
            		self.db.payment_method_by_id[each_payment_method.id] = each_payment_method
            	});
            }
        },
    });
    
    models.load_models({
        model: "sh.cash.in.out",
        label: "load_cash_in_out_statement",
        loaded: function (self, all_cash_in_out_statement) {
            if(all_cash_in_out_statement && all_cash_in_out_statement.length > 0){
            	self.db.all_cash_in_out_statement = all_cash_in_out_statement
            }
        },
    });
    
    // models.load_models({
    //     model: "pos.session",
    //     label: "load_session",
    // 	domain: [['state','=','opened']],
    //     loaded: function (self, all_session) {
    //         if(all_session && all_session.length > 0){
    //         	_.each(all_session, function(each_session){
    //         		if(self.pos_session.id == each_session.id){
    //         			self.cash_register_total_entry_encoding = each_session.cash_register_total_entry_encoding;
    //         			self.cash_register_balance_end = each_session.cash_register_balance_end;
    //         			self.cash_register_balance_end_real = each_session.cash_register_balance_end_real;
    //         			self.cash_register_balance_start = each_session.cash_register_balance_start;
    //         		}
    //         	});
    //         }
    //     },
    // });
    
    models.load_models({
        model: "pos.payment",
        label: "load_pos_payment",
        loaded: function (self, all_payment) {
            if(all_payment && all_payment.length > 0){
            	_.each(all_payment, function(each_payment){
            		if(each_payment.session_id[0] == self.pos_session.id){
            			self.db.all_payment.push(each_payment)
            			self.db.payment_line_by_id[each_payment.id] = each_payment
            		}
            	});
            }
        },
    });
    
    // models.load_models({
    //     model: "pos.order",
    //     label: "load_pos_order",
    //     loaded: function (self, all_order) {
            
    //         if(all_order && all_order.length > 0){
    //         	self.env.pos.order_length = all_order.length
    // 			self.env.pos.db.all_display_order = all_order;
    //         	_.each(all_order, function(each_order){
    //         		if(self.pos_session.id == each_order.session_id[0]){
    //         			self.db.all_order.push(each_order)
    //         		}
    //         	});
    //         }
    //     },
    // });
    
    exports.cash_in_out = Backbone.Model.extend({
        initialize: function (attributes, options) {
            Backbone.Model.prototype.initialize.apply(this, arguments);
            var self = this;
            options = options || {};
            this.pos = options.pos;
            if (options.json) {
                this.init_from_JSON(options.json);
            } 
            return this;
        },
        init_from_JSON: function (json) {
            if (json.pos_session_id !== this.pos.pos_session.id) {
                this.sequence_number = this.pos.pos_session.sequence_number++;
            } else {
                this.sequence_number = json.sequence_number;
                this.pos.pos_session.sequence_number = Math.max(this.sequence_number + 1, this.pos.pos_session.sequence_number);
            }
        },
        set_name: function (name) {
            this.name = name;
        },
        get_name: function () {
            return this.name;
        },
        export_as_JSON: function () {
            return {
            	sh_transaction_type: this.get_name().sh_transaction_type,
            	sh_amount: this.get_name().sh_amount,
            	sh_reason: this.get_name().sh_reason,
            	sh_session: this.get_name().sh_session,
                
            };
        },
        
    });

    var cash_in_outCollection = Backbone.Collection.extend({
        model: exports.cash_in_out,
    });
    
    var OrderCollection = Backbone.Collection.extend({
        model: exports.Order,
    });

    var _super_posmodel = models.PosModel.prototype;
    models.PosModel = models.PosModel.extend({
    	initialize: function (attributes) {
            this.cash_in_out_options;
            this.cash_in_out_receipt = false;
            this.cash_in_out_statement_receipt = false;
            this.is_session_close = false;
            this.cash_register_total_entry_encoding = 0.00;
            this.cash_register_balance_end = 0.00
            this.cash_register_balance_end_real = 0.00
            this.cash_register_balance_start = 0.00
            this.set({
                synch: { status: "connected", pending: 0 },
                orders: new OrderCollection(),
                cash_in_outs: new cash_in_outCollection(),
                cashInData: null,
                selectedcash_in_out: null,
                selectedOrder: null,
                selectedClient: null,
                cashier: null,
                selectedCategoryId: null,
            });
            var posmodel = _super_posmodel.initialize.call(this, attributes);
        },
        get_cash_in_data: function () {
            return this.get("cashInData");
        },
        add_new_cash_in_out: function (options) {
            var cash_in_out = new exports.cash_in_out({}, { pos: this });
            this.get("cash_in_outs").add(cash_in_out);
            this.set("selectedcash_in_out", cash_in_out, options);

            // call using this.env.pos.add_new_cash_in_out();
            return cash_in_out;
        },
        get_cash_in_out: function () {
            return this.get("selectedcash_in_out");
        },
        push_closing_balance(){
        	var self = this;
        	if(self.is_session_close){
        		this.rpc({
                    model: "pos.session",
                    method: "sh_cash_control_line",
                    args: [self.env.pos.db.load('closing_balance')],
                })
                .then(async function (session_close_data) {
                	if(!session_close_data){
                		const { confirmed } = await Gui.showPopup('ConfirmPopup', {
                            title: 'Do you want to continue ?',
                            body: "There is a difference, do you want to continue ?",
                        });
                        if (!confirmed){
                        	return;
                        }else{
                        	
                        	
                        	self.rpc({
                                model: "pos.session",
                                method: "sh_force_cash_control_line",
                                args: [self.env.pos.db.load('closing_balance')],
                            })
                            .then(async function (session_close_data) {
                            });
                        	self.db.save("closing_balance", []);
                        	window.location = '/web#action=point_of_sale.action_client_pos_menu';
                        }
                	}else{
                		self.db.save("closing_balance", []);
                		window.location = '/web#action=point_of_sale.action_client_pos_menu';
                	}
                });
        	}else{
        		this.rpc({
                    model: "pos.session",
                    method: "sh_write_close_balance",
                    args: [self.db.load('closing_balance')],
                })
                .then(async function (session_close_data) {
                	if(session_close_data){
                		self.db.save("closing_balance", []);
                		window.location = '/web#action=point_of_sale.action_client_pos_menu';
                	}
                });
        	}
    		
        },
        push_cash_in_outs: function () {
            var self = this;
            this.rpc({
                model: "cash.box.out",
                method: "sh_run",
                args: [this.db.get_cash_in_outs()],
            })
            .then(function (cash_in_out_data) {
            	self.db.save("cash_in_outs", []);
            });
        },
        push_orders: function (order, opts) {
        	this.push_cash_in_outs();
        	this.push_closing_balance()
        	_super_posmodel.push_orders.call(this, order, opts);
        },
        load_new_cash_in_outs: function () {
            var self = this;
            return new Promise(function (resolve, reject) {
                try {
                	self.rpc({
                        model: "cash.box.out",
                        method: "sh_run",
                        args: [self.db.get_cash_in_outs()],
                    })
                    .then(function (cash_in_out_data) {
                    	self.db.save("cash_in_outs", []);
                    }).catch(function (reason) {
                        self.set_synch(self.get("failed") ? "error" : "disconnected");
                    });
                } catch (error) {
                    self.set_synch(self.get("failed") ? "error" : "disconnected");
                }
            });
        },
    });
});
