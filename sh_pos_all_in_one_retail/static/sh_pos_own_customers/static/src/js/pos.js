odoo.define('sh_pos_own_customers.pos', function (require, factory) {
    'use strict';

    var models = require('point_of_sale.models');
    const ClientListScreen = require('point_of_sale.ClientListScreen')
    const Registries = require("point_of_sale.Registries");
    var DB = require("point_of_sale.DB");
    var utils = require('web.utils');
    
    // models.load_fields('res.partner', ['sh_own_customer'])

    DB.include({
        init: function (options) {
            this._super(options);
        },
        search_visible_partner: function (query) {
            try {
                query = query.replace(/[\[\]\(\)\+\*\?\.\-\!\&\^\$\|\~\_\{\}\:\,\\\/]/g, '.');
                query = query.replace(/ /g, '.+');
                var re = RegExp("([0-9]+):.*?" + utils.unaccent(query), "gi");
            } catch (e) {
                return [];
            }
            var results = [];
            for (var i = 0; i < this.limit; i++) {
                var r = re.exec(this.partner_search_string);
                if (r) {
                    var id = Number(r[1]);
                    var customer = this.get_partner_by_id(id)
                    if (customer.sh_own_customer && customer.sh_own_customer.length > 0) {
                        results.push(customer);
                    }
                } else {
                    break;
                }
            }
            return results
        },
    })

    const sh_client_screen = (ClientListScreen) =>
        class extends ClientListScreen {
            constructor() {
                super(...arguments);
                this.customer_list = []
            }
            get clients() {
                var self = this
                var customer_list = []
                if(this.env.pos.config.sh_enable_own_customer){
                    if (this.state.query && this.state.query.trim() !== '') {
                        if (this.customer_list && this.customer_list.length > 0) {
                            return this.env.pos.db.search_visible_partner(this.state.query.trim());
                        } else {
                            return this.env.pos.db.search_partner(this.state.query.trim());
                        }
                    } else {
                        var Partners = this.env.pos.db.partner_by_id
                        var p = {}
                        if (self.env.pos.user.role != 'manager') {
                            _.each(Partners, function (partner) {
                                if (partner.sh_own_customer.includes(self.env.pos.user.id)) {
                                    if (partner.sh_own_customer.length > 0) {
                                        self.customer_list.push(1)
                                        customer_list.push(partner)
                                    }
                                }
                            })
                            if (customer_list.length > 0) {
                                return customer_list
                            }
                            else {
                                return []
                            }
                        } else {
                            this.customer_list = []
                            return self.env.pos.db.get_partners_sorted(1000)
                        }
                    }
                }else{
                    if (this.state.query && this.state.query.trim() !== '') {
                        return this.env.pos.db.search_partner(this.state.query.trim());
                    } else {
                        return this.env.pos.db.get_partners_sorted(1000);
                    }
                }
            }
        }

    Registries.Component.extend(ClientListScreen, sh_client_screen)
});
