odoo.define("sh_pos_order_list.models", function (require) {
    "use strict";

    var models = require("point_of_sale.models");
    var field_utils = require("web.field_utils");

    // models.load_models({
    //     model: "pos.order",
    //     label: "load_orders",
    //     domain: function (self) {
    //         return [["user_id", "=", self.user.id]];
    //     },
    //     loaded: function (self, all_order) {
    //         self.db.all_orders(all_order);
    //     },
    // });
    // models.load_models({
    //     model: "pos.session",
    //     label: "load_sessions",
    //     domain: function (self) {
    //         return [["user_id", "=", self.user.id]];
    //     },
    //     loaded: function (self, all_session) {
    //         self.db.all_sessions(all_session);
    //     },
    // });
    // models.load_models({
    //     model: "pos.order.line",
    //     label: "load_orders_line",
    //     loaded: function (self, all_order_line) {
    //         self.db.all_orders_line(all_order_line);
    //     },
    // });

    var _super_order = models.Order.prototype;
    models.Order = models.Order.extend({
        initialize: function (attributes, options) {
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
            /*return zero_pad(this.pos.pos_session.id, 5) + "-" + zero_pad(this.pos.pos_session.login_number, 3) + "-" + zero_pad(this.sequence_number, 4);*/
            
            return (this.sequence_number + this.name.split(' ')[1]);
        },
        init_from_JSON: function (json) {
            var res = _super_order.init_from_JSON.apply(this, arguments);
            if (json.pos_session_id !== this.pos.pos_session.id) {
                this.sequence_number = this.pos.pos_session.sequence_number++;
            } else {
                this.sequence_number = json.sequence_number;
                this.pos.pos_session.sequence_number = Math.max(this.sequence_number + 1, this.pos.pos_session.sequence_number);
            }
        },

        export_as_JSON: function () {
            var json = _super_order.export_as_JSON.apply(this, arguments);
            var sh_line_id = [];
            json.sh_uid = this.sh_uid;
            json.sequence_number = this.sequence_number;

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
    });

    var _super_orderline = models.Orderline.prototype;
    models.Orderline = models.Orderline.extend({
        initialize: function (attr, options) {
            _super_orderline.initialize.call(this, attr, options);
            this.sequence_number = this.pos.pos_session.sequence_number++;
            this.sh_line_id = this.generate_sh_line_unique_id();
        },
        export_as_JSON: function () {
            var json = _super_orderline.export_as_JSON.call(this);
            json.sh_line_id = this.generate_sh_line_unique_id();
            return json;
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
            return ("sh" + this.sequence_number + this.order.name.split(' ')[1]);
        },
        init_from_JSON: function (json) {
            var res = _super_orderline.init_from_JSON.apply(this, arguments);
            if (json.pos_session_id !== this.pos.pos_session.id) {
                this.sequence_number = this.pos.pos_session.sequence_number++;
            } else {
                this.sequence_number = json.sequence_number;
                this.pos.pos_session.sequence_number = Math.max(this.sequence_number + 1, this.pos.pos_session.sequence_number);
            }
        },
    });

    var _super_posmodel = models.PosModel.prototype;
    models.PosModel = models.PosModel.extend({
        get_pos_reference: function () {
            return this.env.pos.get_order().name;
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
                        if (!self.db.order_by_uid[each_order.data.sh_uid]) {
                            if (each_order["data"]["amount_paid"] >= parseInt(each_order["data"]["amount_total"])) {
                                each_order["data"]["state"] = "paid";
                            } else {
                                each_order["data"]["state"] = "draft";
                            }
                            if(self.formatted_validation_date){
                                each_order["data"]["date_order"] = self.formatted_validation_date;
                            }
                            each_order["data"]["pos_reference"] = each_order.data.name;
                            self.db.all_order.push(each_order.data);
                            /*self.db.new_order = [each_order.data];*/
                            self.db.order_by_uid[each_order.data.sh_uid] = each_order.data;
                            _.each(each_order.data.lines, function (each_line) {
                                if (each_line[2] && each_line[2].sh_line_id) {
                                    self.db.order_line_by_uid[each_line[2].sh_line_id] = each_line[2];
                                    sh_line_id.push(each_line[2].sh_line_id);
                                }
                            });
                            each_order.data["sh_line_id"] = sh_line_id;
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
});
