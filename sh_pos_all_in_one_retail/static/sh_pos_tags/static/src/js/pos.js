odoo.define("sh_pos_tags.pos", function (require) {
    "use strict";

    
    var module = require("point_of_sale.models");
    const Registries = require("point_of_sale.Registries");
    const ProductsWidget = require("point_of_sale.ProductsWidget")
    var models = module.PosModel.prototype.models;
    var DB = require("point_of_sale.DB");
    var utils = require('web.utils');

    for (var i = 0; i < models.length; i++) {
        var model = models[i];
        if (model.model === "product.product") {
            model.fields.push("sh_product_tag_ids");
        }
    }
    var models = require("point_of_sale.models");

    models.load_models({
        model: 'sh.product.tag',
        fields: [],
        loaded: function (self, Tags) {
            self.tags = Tags
            self.db.product_by_tag_id = [];
            _.each(Tags, function (tag) {
                if (tag) {
                    self.db.product_by_tag_id[tag.id] = tag
                }
            })
        }
    })

    DB.include({
        init: function (options) {
            this._super(options);
            this.product_by_tag_id = {};
            this.tag_search_string = {};
        },
        search_tag_in_category: function (category_id, Tags, query) {
            var self = this
            this.tag_search_string = {}
            for (var i = 1; i < Tags.length; i++) {
                var tag = Tags[i]
                var search_tag = utils.unaccent(self.tag_product_search_string(tag))
                self.tag_search_string += search_tag
            }
            try {
                query = query.replace(/[\[\]\(\)\+\*\?\.\-\!\&\^\$\|\~\_\{\}\:\,\\\/]/g, '.');
                query = query.replace(/ /g, '.+');
                var re = RegExp("([0-9]+):.*?" + utils.unaccent(query), "gi");
            } catch (e) {
                return [];
            }
            var results = [];
            for (var i = 0; i < this.limit; i++) {
                var tag_pro = re.exec(this.tag_search_string)
                if (tag_pro) {
                    var id = Number(tag_pro[1]);
                    var tag_id = this.get_product_by_tag_id(id)
                    var tag_product_ids = tag_id.product_ids
                    results.push(self.get_product_by_template(category_id, tag_product_ids))

                } else {
                    break;
                }
            }
            return results;
        },
        get_product_by_tag_id: function (id) {
            return this.product_by_tag_id[id];
        },
        get_product_by_template: function (category_id, id) {
            var variants = this.product_by_id
            var result = []
            for (var i = 0; i < id.length; i++) {
                _.each(variants, function (variant) {
                    if (variant.product_tmpl_id == id[i] && variant.pos_categ_id[0] == category_id) {
                        result.push(variant)
                    } else if (variant.product_tmpl_id == id[i] && category_id == 0) {
                        result.push(variant)
                    }
                })
            }
            return result
        },
        tag_product_search_string: function (product) {
            if (product){
                var str = product.display_name;
                if (product.id) {
                    str += '|' + product.id;
                }
                if (product.default_code) {
                    str += '|' + product.default_code;
                }
                if (product.description) {
                    str += '|' + product.description;
                }
                if (product.description_sale) {
                    str += '|' + product.description_sale;
                }
                str = product.id + ':' + str.replace(/:/g, '') + '\n';
            }else{
                var str = '';
            }

            return str;
        },
    });

    const PosProductsWidget = (ProductsWidget) =>
        class extends ProductsWidget {
            constructor() {
                super(...arguments);
                this.final_tag_products = [];
            }
            get tagproduct() {
                return this.final_tag_products;
            }
        }


    Registries.Component.extend(ProductsWidget, PosProductsWidget);
});