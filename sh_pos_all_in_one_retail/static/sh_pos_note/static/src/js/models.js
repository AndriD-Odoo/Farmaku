odoo.define("sh_pos_note.Models", function (require) {
    "use strict";

    var models = require("point_of_sale.models");
    var DB = require("point_of_sale.DB");
    var exports = {};
    exports.Note = Backbone.Model.extend({
        initialize: function (attributes, options) {
            Backbone.Model.prototype.initialize.apply(this, arguments);
            var self = this;
            options = options || {};
            this.pos = options.pos;
            if (options.json) {
                this.init_from_JSON(options.json);
            } else {
                this.sequence_number = this.pos.pos_session.sequence_number++;
                this.uid = this.generate_unique_id();
            }
            return this;
        },
        generate_unique_id: function () {
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
            return zero_pad(this.pos.pos_session.id, 5) + "-" + zero_pad(this.pos.pos_session.login_number, 3) + "-" + zero_pad(this.sequence_number, 4);
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
            this.display_name = name;
        },
        get_name: function () {
            return this.name;
        },
        export_as_JSON: function () {
            return {
                name: this.get_name(),
                display_name: this.get_name(),
                uid: this.uid,
                sequence_number: this.sequence_number,
            };
        },
        export_for_printing: function () {
            var self = this;
        },
    });

    var NoteCollection = Backbone.Collection.extend({
        model: exports.Note,
    });

    DB.include({
        init: function (options) {
            this._super(options);
            this.all_note = [];
            this.note_by_id = {};
            this.note_by_uid = {};
            this.note_write_date = null;
        },
        get_notes: function () {
            return this.load("notes", []);
        },
        get_removed_notes: function () {
            return this.load("removed_notes", []);
        },
        remove_note_by_uid: function (uid) {
            var all_note = this.all_note;
            this.remove_all_notes();

            for (var i = 0, len = all_note.length; i < len; i++) {
                var each_note = all_note[i];
                if (each_note["uid"] != uid) {
                    this.all_note.push(each_note);
                }
            }
            
        },
        remove_all_notes: function () {
            this.all_note = [];
            this.note_by_id = {};
            this.note_by_uid = {};
        },
        add_notes: function (all_note) {
            if (!all_note instanceof Array) {
                all_note = [all_note];
            }
            var new_write_date = "";
            for (var i = 0, len = all_note.length; i < len; i++) {
                var each_note = all_note[i];
                this.all_note.push(each_note);
                this.note_by_id[each_note.id] = each_note;
                this.note_by_uid[each_note.uid] = each_note;
                var local_partner_date = (this.note_write_date || "").replace(/^(\d{4}-\d{2}-\d{2}) ((\d{2}:?){3})$/, "$1T$2Z");
                var dist_partner_date = (each_note.write_date || "").replace(/^(\d{4}-\d{2}-\d{2}) ((\d{2}:?){3})$/, "$1T$2Z");
                if (this.note_write_date && this.note_by_id[each_note.id] && new Date(local_partner_date).getTime() + 1000 >= new Date(dist_partner_date).getTime()) {
                    continue;
                } else if (new_write_date < each_note.write_date) {
                    new_write_date = each_note.write_date;
                }
            }
            this.note_write_date = new_write_date || this.note_write_date;
        },
        get_note_write_date: function () {
            return this.note_write_date || "1970-01-01 00:00:00";
        },
    });
    models.load_models({
        model: "pre.define.note",
        label: "load_notes",
        fields: ["id", "name", "display_name", "write_date", "sequence_number", "uid"],
        domain: function (self) {
            return [];
        },
        loaded: function (self, all_note) {
            self.all_note_name = [];
            _.each(all_note, function (each_note) {
                self.all_note_name.push(each_note.display_name);
            });
            self.db.add_notes(all_note);
        },
    });

    var _super_orderline = models.Orderline.prototype;
    models.Orderline = models.Orderline.extend({
        initialize: function (attr, options) {
            this.line_note = "";
            _super_orderline.initialize.call(this, attr, options);
        },
        set_line_note: function (line_note) {
            this.set("line_note", line_note);
        },
        get_line_note: function () {
            return this.get("line_note");
        },
        export_for_printing: function () {
            var self = this;
            self.pos.product_note = self.pos.config.is_productnote_receipt;
            var lines = _super_orderline.export_for_printing.call(this);
            var new_attr = {
                line_note: this.get_line_note() || false,
            };
            $.extend(lines, new_attr);
            return lines;
        },
        export_as_JSON: function () {
            var json = _super_orderline.export_as_JSON.apply(this, arguments);
            json.line_note = this.get("line_note") || null;
            return json;
        },
    });

    var _super_order = models.Order.prototype;
    models.Order = models.Order.extend({
        init_from_JSON: function (json) {
            _super_order.init_from_JSON.call(this, json);
        },
        set_global_note: function (order_note) {
            this.order_note = order_note;
        },
        get_global_note: function () {
            return this.order_note;
        },

        export_as_JSON: function () {
            var json = _super_order.export_as_JSON.apply(this, arguments);
            json.order_note = this.get_global_note() || null;

            return json;
        },
        export_for_printing: function () {
            var self = this;
            var orders = _super_order.export_for_printing.call(this);
            var new_val = {
                order_note: this.get_global_note() || false,
            };
            $.extend(orders, new_val);
            return orders;
        },
    });  
    
    var OrderCollection = Backbone.Collection.extend({
        model: exports.Order,
    });

    var _super_posmodel = models.PosModel.prototype;
    models.PosModel = models.PosModel.extend({
        initialize: function (attributes) {
            // these dynamic attributes can be watched for change by other models or widgets
            this.set({
                synch: { status: "connected", pending: 0 },
                orders: new OrderCollection(),
                notes: new NoteCollection(),
                selectedNote: null,
                selectedOrder: null,
                selectedClient: null,
                cashier: null,
                selectedCategoryId: null,
            });
            this.is_open_variant_popup = false;
            _super_posmodel.initialize.call(this, attributes);
        },
        // reload the list of partner, returns as a promise that resolves if there were
        // updated partners, and fails if not
        prepare_new_note_domain: function () {
            return [["write_date", ">", this.db.get_note_write_date()]];
        },
        set_note: function (note, options) {
            this.set({ selectedNote: note }, options);
        },

        // creates a new empty order and sets it as the current order
        add_new_note: function (options) {
            var note = new exports.Note({}, { pos: this });
            this.get("notes").add(note);
            this.set("selectedNote", note, options);

            // call using this.env.pos.add_new_note();
            return note;
        },
        get_note: function () {
            return this.get("selectedNote");
        },

        push_notes: function () {
            var self = this;

            this.rpc({
                model: "pre.define.note",
                method: "create_from_ui",
                args: [this.db.get_notes()],
            })
                .then(function (server_ids) {
                    self.db.save("notes", []);
                    self.db.save("removed_notes", []);
                    var fields = _.find(self.models, function (model) {
                        return model.label === "load_notes";
                    }).fields;

                    self.rpc(
                        {
                            model: "pre.define.note",
                            method: "search_read",
                            args: [[], fields],
                        },
                        {
                            timeout: 3000,
                            shadow: true,
                        }
                    ).then(
                        function (notes) {
                            self.db.remove_all_notes();
                            self.db.add_notes(notes);
                        },
                        function (type, err) {
                            reject();
                        }
                    );
                })
                .catch(function (reason) {
                    var error = reason.message;

                    throw error;
                });

            try {
                self.rpc({
                    model: "pre.define.note",
                    method: "remove_from_ui",
                    args: [this.db.get_removed_notes()],
                }).then(function (server_ids) {
                    self.env.pos.db.save("removed_notes", []);
                    var fields = _.find(self.models, function (model) {
                        return model.label === "load_notes";
                    }).fields;

                    self.rpc(
                        {
                            model: "pre.define.note",
                            method: "search_read",
                            args: [[], fields],
                        },
                        {
                            timeout: 3000,
                            shadow: true,
                        }
                    ).then(
                        function (notes) {
                            self.db.remove_all_notes();
                            self.db.add_notes(notes);
                        },
                        function (type, err) {
                            reject();
                        }
                    );
                });
            } catch (error) {
                self.set_synch(self.get("failed") ? "error" : "disconnected");
                self._handlePushOrderError(error);
            }
        },

        push_orders: function (order, opts) {
            this.push_notes();
            opts = opts || {};
            var self = this;

            if (order) {
                this.db.add_order(order.export_as_JSON());
            }
            return new Promise(function (resolve, reject) {
                self.flush_mutex.exec(function () {
                    var flushed = self._flush_orders(self.db.get_orders(), opts);

                    flushed.then(resolve, reject);

                    return flushed;
                });
            });
        },
        load_new_notes: function () {
            var self = this;
            return new Promise(function (resolve, reject) {
                try {
                    self.rpc({
                        model: "pre.define.note",
                        method: "create_from_ui",
                        args: [self.env.pos.db.get_notes()],
                    })
                        .then(function (server_ids) {
                            self.env.pos.db.save("notes", []);
                            var fields = _.find(self.models, function (model) {
                                return model.label === "load_notes";
                            }).fields;

                            self.rpc(
                                {
                                    model: "pre.define.note",
                                    method: "search_read",
                                    args: [[], fields],
                                },
                                {
                                    timeout: 3000,
                                    shadow: true,
                                }
                            ).then(
                                function (notes) {
                                    self.db.remove_all_notes();
                                    self.db.add_notes(notes);
                                },
                                function (type, err) {
                                    reject();
                                }
                            );
                        })
                        .catch(function (reason) {
                            self.set_synch(self.get("failed") ? "error" : "disconnected");
                        });
                } catch (error) {
                    self.set_synch(self.get("failed") ? "error" : "disconnected");
                }
            });
        },
        delete_notes: function () {
            var self = this;
            return new Promise(function (resolve, reject) {
                try {
                    self.rpc({
                        model: "pre.define.note",
                        method: "remove_from_ui",
                        args: [self.env.pos.db.get_removed_notes()],
                    }).then(function (server_ids) {
                        self.env.pos.db.save("removed_notes", []);
                        var fields = _.find(self.models, function (model) {
                            return model.label === "load_notes";
                        }).fields;

                        self.rpc(
                            {
                                model: "pre.define.note",
                                method: "search_read",
                                args: [[], fields],
                            },
                            {
                                timeout: 3000,
                                shadow: true,
                            }
                        ).then(
                            function (notes) {
                                self.db.remove_all_notes();
                                self.db.add_notes(notes);
                            },
                            function (type, err) {
                                reject();
                            }
                        );
                    });
                } catch (error) {
                    self.set_synch(self.get("failed") ? "error" : "disconnected");
                    self._handlePushOrderError(error);
                }
            });
        },
    });

    return exports;
});
