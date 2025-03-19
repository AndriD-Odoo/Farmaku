odoo.define("sh_pos_order_return_exchange_barcode.pos", function (require) {
    "use strict";

    var models = require("point_of_sale.models");
    const { Gui } = require("point_of_sale.Gui");
    const ProductScreen = require("point_of_sale.ProductScreen");
    const Registries = require("point_of_sale.Registries");

    // models.load_models({
    //     model: "pos.order",
    //     label: "load_orders",
    //     domain: function (self) {
    //         return [["user_id", "=", self.user.id]];
    //     },
    //     loaded: function (self, all_order) {
    //         self.db.add_barcodes(all_order);
    //     },
    // });
    
    const ShProductScreen = (ProductScreen) =>
    class extends ProductScreen {
    	async _barcodeProductAction(code) {
    		var self = this;
        	if (this.env.pos.config.sh_allow_return || this.env.pos.config.sh_allow_exchange) {
                    var order_data = self.env.pos.db.order_by_barcode[code.base_code];
                    var order_id;
                    if (order_data) {
                        order_id = order_data.sh_uid;
                        var order_line = [];
                        if (order_data && order_data.lines) {
                            _.each(order_data.lines, function (each_order_line) {
                                var line_data = self.env.pos.db.order_line_by_id[each_order_line];
                                if (!line_data) {
                                    line_data = self.env.pos.db.order_line_by_uid[each_order_line[2].sh_line_id];
                                }
                                if (line_data) {
                                    if (!line_data.sh_return_qty) {
                                        line_data["sh_return_qty"] = 0;
                                    }
                                    order_line.push(line_data);
                                }
                            });
                        }
                        if (this.env.pos.config.sh_allow_return) {
                            self.env.pos.is_return = true;
                            self.env.pos.is_exchange = false;
                        } else if (this.env.pos.config.sh_allow_exchange) {
                            self.env.pos.is_return = false;
                            self.env.pos.is_exchange = true;
                        } else {
                            self.env.pos.is_return = true;
                            self.env.pos.is_exchange = false;
                        }
                        console.log('Scan Barcode',order_data)
                        Gui.showPopup("OrderReturnBarcodePopupWidget", { lines: order_line, order: order_data.id || order_id });
                    }else{
                    	super._barcodeProductAction(code)
                    }
                    
            }else{
            	super._barcodeProductAction(code)
            }
    	}
    };
    Registries.Component.extend(ProductScreen, ShProductScreen);

    var _super_posmodel = models.PosModel.prototype;
    models.PosModel = models.PosModel.extend({
        scan_product: function (parsed_code) {
            var return_scan = _super_posmodel.scan_product.call(this, parsed_code);

            if (this.config.sh_allow_return || this.config.sh_allow_exchange) {
                if (!return_scan) {
                    var self = this;
                    var order_data = this.db.order_by_barcode[parsed_code.code];
                    var order_id;
                    if (order_data) {
                        order_id = order_data.sh_uid;
                        var order_line = [];
                        if (order_data && order_data.lines) {
                            _.each(order_data.lines, function (each_order_line) {
                                var line_data = self.db.order_line_by_id[each_order_line];
                                if (!line_data) {
                                    line_data = self.db.order_line_by_uid[each_order_line[2].sh_line_id];
                                }
                                if (line_data) {
                                    if (!line_data.sh_return_qty) {
                                        line_data["sh_return_qty"] = 0;
                                    }
                                    order_line.push(line_data);
                                }
                            });
                        }
                    }
                    if (this.config.sh_allow_return) {
                        self.is_return = true;
                        self.is_exchange = false;
                    } else if (this.config.sh_allow_exchange) {
                        self.is_return = false;
                        self.is_exchange = true;
                    } else {
                        self.is_return = true;
                        self.is_exchange = false;
                    }
                    Gui.showPopup("OrderReturnBarcodePopupWidget", { lines: order_line, order: order_data.id || order_id });
                }
            }
            return true;
        },
    });
});
