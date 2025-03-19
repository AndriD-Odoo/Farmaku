odoo.define('sh_pos_customer_discount.pos', function (require) {
    'use strict';

    const ClientDetailsEdit = require('point_of_sale.ClientDetailsEdit')
    const ClientListScreen = require('point_of_sale.ClientListScreen')
    const Registries = require("point_of_sale.Registries");
    var models = require('point_of_sale.models');
    var core = require('web.core');
    var _t = core._t;

    models.load_fields('res.partner', ['sh_customer_discount', 'property_payment_term_id', 'property_supplier_payment_term_id', 'sh_own_customer', 'sh_enable_max_dic', 'sh_maximum_discount', 'sh_discount_type'])

    const ShClientDetailsEdit = (ClientDetailsEdit) =>
        class extends ClientDetailsEdit {
            constructor() {
                super(...arguments);
            }
            saveChanges() {
                if (this.env.pos.config.sh_enable_customer_discount) {
                    var discount = $('#sh_customer_discount').val();
                    let processedChanges = {};
                    for (let [key, value] of Object.entries(this.changes)) {
                        if (this.intFields.includes(key)) {
                            processedChanges[key] = parseInt(value) || false;
                        } else {
                            processedChanges[key] = value;
                        }
                    }
                    if (discount) {
                        processedChanges['sh_customer_discount'] = discount || 0
                    }
                    if ((!this.props.partner.name && !processedChanges.name) ||
                        processedChanges.name === '') {
                        return this.showPopup('ErrorPopup', {
                            title: _t('A Customer Name Is Required'),
                        });
                    }
                    processedChanges.id = this.props.partner.id || false;
                    this.trigger('save-changes', { processedChanges });
                }
                else {
                    super.saveChanges()
                }
            }

        }
    Registries.Component.extend(ClientDetailsEdit, ShClientDetailsEdit)

    const ShClientListScreen = (ClientListScreen) =>
        class extends ClientListScreen {
            constructor() {
                super(...arguments);
            }
            confirm() {
                super.confirm()
                if (this.env.pos.config.sh_enable_customer_discount) {
                    var self = this
                    var old_client = this.env.pos.get_order().get_client()
                    _.each(this.env.pos.get_order().get_orderlines(), function (orderline) {
                        if (!orderline.discount) {
                            if (orderline && self.state.selectedClient) {
                                orderline.set_discount(self.state.selectedClient.sh_customer_discount)
                            }
                        } else {
                            if (old_client && old_client.sh_customer_discount == orderline.discount) {
                                if (self.state.selectedClient) {
                                    orderline.set_discount(self.state.selectedClient.sh_customer_discount)
                                } else {
                                    orderline.discount = 0
                                    orderline.discountStr = '' + 0
                                }
                            }
                        }
                    })
                }
            }

        }
    Registries.Component.extend(ClientListScreen, ShClientListScreen)
});
