odoo.define("sh_pos_fronted_cancel.models", function (require) {
    "use strict";

    var models = require("point_of_sale.models");
    var rpc = require("web.rpc");
    
    models.load_fields("res.company", ["pos_operation_type", "pos_cancel_delivery", "pos_cancel_invoice"]);

    var _super_posmodel = models.PosModel.prototype;
    models.PosModel = models.PosModel.extend({
        _flush_orders: function (orders, options) {
            var self = this;
            this.set_synch("connecting", orders.length);
            return this._save_to_server(orders, options)
                .then(function (server_ids) {
                    self.set_synch("connected");
                    for (let i = 0; i < server_ids.length; i++) {
                        self.validated_orders_name_server_id_map[server_ids[i].pos_reference] = server_ids[i].id;
                    }
                    self.push_cancel_order();
                    return _.pluck(server_ids, "id");
                })
                .catch(function (error) {
                    self.set_synch(self.get("failed") ? "error" : "disconnected");
                    return Promise.reject(error);
                });
        },
        push_cancel_order: function () {
            var self = this;
            try {
                rpc.query({
                    model: "pos.order",
                    method: "sh_fronted_cancel_draft",
                    args: [this.db.get_removed_draft_orders()],
                })
                    .then(function (return_order_data) {
                        if (return_order_data) {
                            self.db.save("removed_draft_orders", []);
                        }
                    })
                    .catch(function (error) {});
            } catch (error) {}

            try {
                self.db.save("removed_delete_orders", []);
                rpc.query({
                    model: "pos.order",
                    method: "sh_fronted_cancel_delete",
                    args: [this.db.get_removed_delete_orders()],
                })
                    .then(function (return_order_data) {
                        if (return_order_data) {
                            self.db.save("removed_delete_orders", []);
                        }
                    })
                    .catch(function (error) {});
            } catch (error) {}
        },
    });
});
