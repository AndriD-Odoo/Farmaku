odoo.define("sh_pos_order_list.modelsexchange", function (require) {
    "use strict";

    var models = require("point_of_sale.models");
    var field_utils = require("web.field_utils");
    const rpc = require("web.rpc");

    models.load_models({
        label: 'Loading POS Order',
        loaded: function (self) {
            if (self && self.config && self.config.sh_mode && self.config.sh_mode == 'offline_mode') {

                rpc.query({
                    model: "pos.order",
                    method: "search_return_order_length",
                    args: [self.config]

                }).then(function (orders) {

                    if (orders) {
                        if (orders['order']) {
                            _.each(orders['order'], function (each_order) {
                                if (each_order.is_return_order || each_order.is_exchange_order) {
                                    self.env.pos.db.all_return_order.push(each_order)
                                } else if (!each_order.is_return_order && !each_order.is_exchange_order) {
                                    self.env.pos.db.all_non_return_order.push(each_order)
                                }
                            });
                            self.env.pos.order_length = orders['order'].length
                            self.env.pos.db.all_orders(orders['order']);
                            self.env.pos.db.add_barcodes(orders['order']);
                            self.env.pos.db.all_display_order = orders['order'];
                        }
                        if (orders['order_line']) {
                            self.env.pos.db.all_orders_line(orders['order_line']);
                        }
                    }
                });


            } if (self && self.config && self.config.sh_mode && self.config.sh_mode == 'online_mode') {
                rpc.query({
                    model: "pos.order",
                    method: "sh_get_all_order",
                    args: [self.user.id]
                }).then(function (all_order) {
                	self.env.pos.db.all_return_order = all_order.return_order;
                	self.env.pos.db.all_non_return_order = all_order.non_return_order;
                	self.env.pos.db.order_by_id_temp = all_order.order_by_id;
                	self.env.pos.db.order_by_id = all_order.order_by_id;
                	self.env.pos.db.order_line_by_id = all_order.order_line_by_id;
                	self.env.pos.db.all_display_order = all_order.order_data;
                	self.env.pos.order_length = all_order.order_data.length;
                	self.env.pos.db.add_barcodes(all_order.order_data);
                });
            }
        }
    });

    models.load_models({
        model: "pos.session",
        label: "load_sessions",
        domain: function (self) {
            return [["user_id", "=", self.user.id]];
        },
        loaded: function (self, all_session) {
            self.db.all_sessions(all_session);
        },
    });

    // models.load_fields("product.product", ["sh_product_non_returnable", "sh_product_non_exchangeable"]);

    var _super_posmodel = models.PosModel.prototype;
    models.PosModel = models.PosModel.extend({
        initialize: function (session, attributes) {
            self.is_return = false;
            self.is_exchange = false;
            _super_posmodel.initialize.apply(this, arguments);
        },
        get_last_session_order: function (orders) {
            for (var i = 0; i < this.env.pos.db.all_session.length; i++) {
                if (i < this.env.pos.db.all_session.length - 1) {
                    if (this.env.pos.db.all_session[i].stop_at && this.env.pos.db.all_session[i + 1].stop_at) {
                        if (this.env.pos.db.all_session[i].stop_at < this.env.pos.db.all_session[i + 1].stop_at) {
                            var temp = this.env.pos.db.all_session[i];
                            this.env.pos.db.all_session[i] = this.env.pos.db.all_session[i + 1];
                            this.env.pos.db.all_session[i + 1] = temp;
                        }
                    }
                }
            }
            var session = [];
            for (var i = 0; i < this.env.pos.config.sh_last_no_session; i++) {
                if(this.env.pos.db.all_session && this.env.pos.db.all_session[i]){
                    session.push(this.env.pos.db.all_session[i].name);
                }
            }
            return orders.filter(function (order) {
                return session.includes(order.session_id[1]);
            });
        },
        get_current_session_order: function (orders) {
            var self = this;
            return orders.filter(function (order) {
                return order.session_id[0] == self.env.pos.pos_session.id;
            });
        },
        get_last_day_order: function (orders) {
            var self = this;
            return orders.filter(function (order) {
                var date = new Date();
                var last = new Date(date.getTime() - self.env.pos.config.sh_last_no_days * 24 * 60 * 60 * 1000);
                var last = last.getFullYear() + "-" + ("0" + (last.getMonth() + 1)).slice(-2) + "-" + ("0" + last.getDate()).slice(-2);
                var today_date = date.getFullYear() + "-" + ("0" + (date.getMonth() + 1)).slice(-2) + "-" + ("0" + date.getDate()).slice(-2);
                return order.date_order.split(" ")[0] > last && order.date_order.split(" ")[0] <= today_date;
            });
        },
        get_current_day_order: function (orders) {
            return orders.filter(function (order) {
                var date = new Date();
                var today_date = date.getFullYear() + "-" + ("0" + (date.getMonth() + 1)).slice(-2) + "-" + ("0" + date.getDate()).slice(-2);
                return order.date_order.split(" ")[0] === today_date;
            });
        },

        _save_to_server: function (orders, options) {
            if (!orders || !orders.length) {
                return Promise.resolve([]);
            }

            options = options || {};

            var self = this;
            var timeout = typeof options.timeout === "number" ? options.timeout : 30000 * orders.length;

            // Keep the order ids that are about to be sent to the
            // backend. In between create_from_ui and the success callback
            // new orders may have been added to it.
            var order_ids_to_sync = _.pluck(orders, "id");

            // we try to send the order. shadow prevents a spinner if it takes too long. (unless we are sending an invoice,
            // then we want to notify the user that we are waiting on something )
            var args = [
                _.map(orders, function (order) {
                    order.to_invoice = options.to_invoice || false;
                    return order;
                }),
            ];
            args.push(options.draft || false);
            self.formatted_validation_date = "";
            if(self.get_order() && self.get_order().validation_date){
                self.formatted_validation_date = field_utils.format.datetime(moment(self.get_order().validation_date), {}, { timezone: false });
            }
            _.each(orders, function (each_order) {
                var new_line = [];
                if (!each_order.to_invoice && each_order["data"]["amount_paid"] >= parseInt(each_order["data"]["amount_total"])) {
                    each_order["data"]["state"] = "paid";
                }
                else if (each_order.to_invoice) {
                    each_order["data"]["state"] = "invoiced";
                }
                else {
                    each_order["data"]["state"] = "draft";
                }
                if(self.formatted_validation_date){
                    each_order["data"]["date_order"] = self.formatted_validation_date;
                }
                each_order["data"]["pos_reference"] = each_order.data.name;

            });
            return this.rpc(
                {
                    model: "pos.order",
                    method: "create_from_ui",
                    args: args,
                    kwargs: { context: this.session.user_context },
                },
                {
                    timeout: timeout,
                    shadow: !options.to_invoice,
                }
            )
                .then(function (server_ids) {
                    _.each(order_ids_to_sync, function (order_id) {
                        self.db.remove_order(order_id);
                    });

                    var order_ids = []
                    if (server_ids && server_ids.length > 0) {
                        for (var i = 0; i < server_ids.length; i++) {
                            order_ids.push(server_ids[i].id)
                        }
                    }
                    setTimeout(() => {
                    	
                    	rpc.query({
                            model: "pos.order",
                            method: "order_by_id",
                            args: [order_ids]
//                            domain: [['id', 'in', order_ids]],
                        }).then(function (orders) {
                        	if(orders && orders['order_line_data']){
                        		_.each(orders['order_line_data'], function(each_line){
                        			self.db.order_line_by_id[each_line.id] = each_line
                        		});
                        	}
                        	if(orders && orders['order_data']){                        		
                        		_.each(orders['order_data'], function (order) {
                        			self.db.all_display_order.unshift(order)
                        			var data = $.grep(self.db.all_display_order, function (e) {
                        				return e.name != order.pos_reference;
                        			});
                        			self.db.all_display_order = data
                        			if(order.is_return_order || order.is_exchange_order){
                        				var return_orders = $.grep(self.db.all_return_order, function (e) {
                        					return e.name != order.pos_reference;
                        				});
                        				self.db.all_return_order = return_orders
                        				self.db.all_return_order.unshift(order)
                        			}else{
                        				self.db.all_non_return_order.unshift(order)
                        			}
                        		})
                        	}
                        	
                        });
                    }, 500);

                    self.set("failed", false);
                    return server_ids;
                })
                .catch(function (reason) {
                    var error = reason.message;

                    console.warn("Failed to send orders:", orders);
                    self.formatted_validation_date = ""
                    if(self.get_order() && self.get_order().validation_date){
                        self.formatted_validation_date = field_utils.format.datetime(moment(self.get_order().validation_date), {}, { timezone: false });
                    }

                    var sh_line_id = [];
                    _.each(orders, function (each_order) {
                        var new_line = [];
                        if (!each_order.to_invoice && each_order["data"]["amount_paid"] >= parseInt(each_order["data"]["amount_total"])) {
                            each_order["data"]["state"] = "paid";
                        } else if (each_order.to_invoice) {
                            each_order["data"]["state"] = "invoiced";
                        }else {
                            each_order["data"]["state"] = "draft";
                        }
                        if(self.formatted_validation_date){
                            each_order["data"]["date_order"] = self.formatted_validation_date;
                        }
                        each_order["data"]["pos_reference"] = each_order.data.name;
                        each_order['data']['session_id'] = [self.pos_session.id, self.pos_session.name]

                        self.db.all_order = self.db.all_order_temp;


                        if (each_order.data && each_order.data.partner_id && self.db.get_partner_by_id(each_order.data.partner_id)) {
                            each_order.data['sh_partner_id'] = [each_order.data.partner_id, self.db.get_partner_by_id(each_order.data.partner_id).name]
                        }
                        else if (each_order.data && each_order.data.partner_id && self.db.get_partner_by_cid(each_order.data.partner_id)) {
                            each_order.data['sh_partner_id'] = [each_order.data.partner_id, self.db.get_partner_by_cid(each_order.data.partner_id).name]
                        }


                        self.db.all_order.push(each_order.data);
                        self.db.all_display_order.push(each_order.data)

                        self.db.order_by_uid[each_order.data.sh_uid] = each_order.data;
                        if (each_order && each_order.data && each_order.data.old_sh_uid && self.db.order_by_uid[each_order.data.old_sh_uid]) {
                            if (self.db.order_by_uid[each_order.data.old_sh_uid]["old_pos_reference"]) {
                                self.db.order_by_uid[each_order.data.old_sh_uid]["old_pos_reference"] = self.db.order_by_uid[each_order.data.old_sh_uid]["old_pos_reference"] + " , " + each_order.data.name;
                            } else {
                                self.db.order_by_uid[each_order.data.old_sh_uid]["old_pos_reference"] = each_order.data.name;
                            }
                        }
                        if (each_order["data"]["is_exchange_order"] == true || each_order["data"]["is_return_order"] == true) {
                            self.db.all_return_order.unshift(each_order.data);
                        } else {
                            self.db.all_non_return_order.unshift(each_order.data);
                        }
                        _.each(each_order.data.lines, function (each_line) {
                            if (each_line[2] && each_line[2].sh_line_id) {
                                if (each_order.data.is_return_order) {
                                    if (each_line[2].old_line_id) {
                                        if (self.db.order_line_by_uid[each_line[2].old_line_id]["sh_return_qty"]) {
                                            each_line[2]["sh_return_qty"] = 0;
                                            self.db.order_line_by_uid[each_line[2].old_line_id]["sh_return_qty"] = self.db.order_line_by_uid[each_line[2].old_line_id]["sh_return_qty"] + each_line[2].qty * -1;
                                        } else {
                                            each_line[2]["sh_return_qty"] = 0;
                                            self.db.order_line_by_uid[each_line[2].old_line_id]["sh_return_qty"] = each_line[2].qty * -1;
                                        }
                                    } else {
                                        each_line[2]["sh_return_qty"] = 0;
                                    }
                                } else if (each_order.data.is_exchange_order) {
                                    if (each_line[2].old_line_id) {
                                        if (self.db.order_line_by_uid[each_line[2].old_line_id]["sh_return_qty"]) {
                                            each_line[2]["sh_return_qty"] = 0;
                                            self.db.order_line_by_uid[each_line[2].old_line_id]["sh_return_qty"] = self.db.order_line_by_uid[each_line[2].old_line_id]["sh_return_qty"] + each_line[2].qty * -1;
                                        } else {
                                            each_line[2]["sh_return_qty"] = 0;
                                            self.db.order_line_by_uid[each_line[2].old_line_id]["sh_return_qty"] = each_line[2].qty * -1;
                                        }
                                    } else {
                                        each_line[2]["sh_return_qty"] = 0;
                                    }
                                } else {
                                    each_line[2]["sh_return_qty"] = 0;
                                }
                                self.db.order_line_by_uid[each_line[2].sh_line_id] = each_line[2];
                                sh_line_id.push(each_line[2].sh_line_id);
                            }
                        });
                        each_order.data["sh_line_id"] = sh_line_id;
                        self.db.order_by_uid[each_order.data.sh_uid] = each_order.data;

                        if (each_order.data.old_sh_uid) {
                            var old_order = self.db.order_by_uid[each_order.data.old_sh_uid];
                            var flag = true;
                            if (old_order && old_order.sh_line_id) {
                                _.each(old_order.sh_line_id, function (each_old_line) {
                                    var old_order_line = self.db.order_line_by_uid[each_old_line];
                                    if (flag) {
                                        if (old_order_line.qty > old_order_line.sh_return_qty) {
                                            flag = false;
                                        }
                                    }
                                });
                                if (flag) {
                                    old_order["return_status"] = "fully_return";
                                } else {
                                    old_order["return_status"] = "partialy_return";
                                }
                            } else if (old_order && old_order.lines) {
                                _.each(old_order.lines, function (each_old_line) {
                                    var old_order_line = self.db.order_line_by_id[each_old_line];
                                    if (old_order_line) {
                                        if (flag) {
                                            if (old_order_line.qty > old_order_line.sh_return_qty) {
                                                flag = false;
                                            }
                                        }
                                    }
                                });
                                if (flag) {
                                    old_order["return_status"] = "fully_return";
                                } else {
                                    old_order["return_status"] = "partialy_return";
                                }
                            }
                        }
                    });

                    if (error.code === 200) {
                        // Business Logic Error, not a connection problem
                        // Hide error if already shown before ...
                        if ((!self.get("failed") || options.show_error) && !options.to_invoice) {
                            self.set("failed", error);
                            throw error;
                        }
                    }
                    throw error;
                });
        },
    });

    var _super_order = models.Order.prototype;
    models.Order = models.Order.extend({
        initialize: function () {
            var self = this;
            self.return_order = false;
            self.exchange_order = false;
            self.old_pos_reference = false;
            _super_order.initialize.apply(this, arguments);
            this.sequence_number = this.pos.pos_session.sequence_number++;
            this.sh_uid = this.generate_sh_unique_id();
        },
        generate_sh_unique_id: function () {
            // Generates a public identification number for the order.
            // The generated number must be unique and sequential. They are made 12 digit long
            // to fit into EAN-13 barcodes, should it be needed

            function zero_pad(num, size) {
                var s = "" + num;
                while (s.length < size) {
                    s = "0" + s;
                }
                return s;
            }
            return this.sequence_number;
        },
        is_return_order: function (is_return_order) {
            this.return_order = is_return_order;
            return this.return_order;
        },
        get_is_return_order: function () {
            return this.return_order;
        },
        is_exchange_order: function (is_exchange_order) {
            this.exchange_order = is_exchange_order;
            return this.exchange_order;
        },
        get_is_exchange_order: function () {
            return this.exchange_order;
        },
        set_old_pos_reference: function (old_pos_reference) {
            this.old_pos_reference = old_pos_reference;
        },
        get_old_pos_reference: function (old_pos_reference) {
            return this.old_pos_reference;
        },
        set_old_sh_uid: function (old_sh_uid) {
            this.old_sh_uid = old_sh_uid;
        },
        get_old_sh_uid: function () {
            return this.old_sh_uid;
        },
        export_as_JSON: function () {
            var json = _super_order.export_as_JSON.apply(this, arguments);
            var sh_line_id = [];
            json.sh_uid = this.sh_uid;
            json.sequence_number = this.sequence_number;
            json.is_return_order = this.return_order || null;
            json.is_exchange_order = this.exchange_order || null;
            json.old_pos_reference = this.old_pos_reference || null;
            json.old_sh_uid = this.old_sh_uid || null;
            if (this.orderlines.models) {
                _.each(this.orderlines.models, function (each_order_line) {
                    if (each_order_line.sh_line_id) {
                        sh_line_id.push(each_order_line.sh_line_id);
                    }
                });
            }
            json.sh_order_line_id = sh_line_id;
            return json;
        },
        export_for_printing: function () {
            var self = this;
            var orders = _super_order.export_for_printing.call(this);
            var new_val = {
                is_return_order: this.return_order || false,
                is_exchange_order: this.exchange_order || false,
                old_pos_reference: this.old_pos_reference || false,
            };
            $.extend(orders, new_val);
            return orders;
        },
        // add_product: function (product, options) {
        //     var order = this.pos.get_order();
        //     _super_order.add_product.call(this, product, options);
        //     if (options !== undefined) {
        //         if (options.line_id) {
        //             order.selected_orderline.set_line_id(options.line_id);
        //             order.selected_orderline.set_old_line_id(options.old_line_id);
        //         }
        //     }
        // },
        init_from_JSON: function (json) {
            var res = _super_order.init_from_JSON.apply(this, arguments);
            if (json.pos_session_id !== this.pos.pos_session.id) {
                this.sequence_number = this.pos.pos_session.sequence_number++;
            } else {
                this.sequence_number = json.sequence_number;
                this.pos.pos_session.sequence_number = Math.max(this.sequence_number + 1, this.pos.pos_session.sequence_number);
            }
        },
    });

    var _super_orderline = models.Orderline;
    models.Orderline = models.Orderline.extend({
        initialize: function (attr, options) {
            _super_orderline.prototype.initialize.call(this, attr, options);
            this.sequence_number = this.pos.pos_session.sequence_number++;
            this.sh_line_id = this.generate_sh_line_unique_id();
        },
        set_line_id: function (line_id) {
            this.line_id = line_id;
        },
        set_old_line_id: function (old_line_id) {
            this.old_line_id = old_line_id;
        },
        generate_sh_line_unique_id: function () {
            // Generates a public identification number for the order.
            // The generated number must be unique and sequential. They are made 12 digit long
            // to fit into EAN-13 barcodes, should it be needed

            function zero_pad(num, size) {
                var s = "" + num;
                while (s.length < size) {
                    s = "0" + s;
                }
                return s;
            }
            return "sh" + this.sequence_number;
        },
        export_as_JSON: function () {
            var json = _super_orderline.prototype.export_as_JSON.apply(this, arguments);
            json.line_id = this.line_id;
            json.old_line_id = this.old_line_id;
            json.sh_line_id = this.generate_sh_line_unique_id();
            return json;
        },
        init_from_JSON: function (json) {
            _super_orderline.prototype.init_from_JSON.apply(this, arguments);
            this.line_id = json.line_id;
            if (json.pos_session_id !== this.pos.pos_session.id) {
                this.sequence_number = this.pos.pos_session.sequence_number++;
            } else {
                this.sequence_number = json.sequence_number;
                this.pos.pos_session.sequence_number = Math.max(this.sequence_number + 1, this.pos.pos_session.sequence_number);
            }
        },
    });
});
