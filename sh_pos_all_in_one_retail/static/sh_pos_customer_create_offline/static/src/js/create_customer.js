odoo.define("sh_pos_customer_create_offline.Customer_creawtion", function (require) {
    "use strict";

    var models = require("point_of_sale.models");
    const ClientListScreen = require('point_of_sale.ClientListScreen')
    const ClientDetailsEdit = require('point_of_sale.ClientDetailsEdit')
    const SyncNotification = require('point_of_sale.SyncNotification')
    const Registries = require("point_of_sale.Registries");
    const { Gui } = require("point_of_sale.Gui");

    const ShClientListScreenScreen = (ClientListScreen) =>
        class extends ClientListScreen {
            constructor() {
                super(...arguments);
            }
            saveChanges(event) {
                var self = this;
                if (this.env.pos.config.sh_create_customer) {
                    try {
                        const keys = Object.keys(self.env.pos.db.partner_by_id);


                        self.env.pos.update_old_customer()
                        self.env.pos.create_offline_clients().then(function (id) {

                            self.crete_online_customer(event)
                        }).catch(function (reason) {
                            if (self.state.selectedClient) {
                                if (keys.includes(self.state.selectedClient['cid'])) {

                                    var dbcustomer = self.env.pos.db.get_customer_by_cid(self.state.selectedClient['cid'])
                                    self.env.pos.db.partner_by_id[self.state.selectedClient['cid']]['currunt_client'] = event.detail.processedChanges;
                                    event.detail.processedChanges['id'] = false

                                    const new_data = Object.assign({}, dbcustomer[0]['currunt_client'], event.detail.processedChanges);


                                    dbcustomer[0]['currunt_client'] = new_data;
                                    // dbcustomer[0]['partner_id'] = self.state.selectedClient['cid']

                                    const newObj = Object.assign({}, dbcustomer[0], new_data);

                                    newObj['id'] = dbcustomer[0]['id']
                                    newObj['country_id'] = [newObj['country_id']]
                                    newObj['state_id'] = [newObj['state_id']]

                                    self.env.pos.db.update_customer(newObj)
                                    self.env.pos.db.partner_by_id[self.state.selectedClient['cid']] = newObj;

                                    self.state.detailIsShown = false;

                                    // newObj['partner_id'] = self.state.selectedClient['cid']

                                    self.state.selectedClient = self.env.pos.db.sh_all_customers[self.env.pos.db.sh_all_customers.length - 1]
                                    self.render();
                                } else {
                                    var old_data = self.state.selectedClient

                                    const newObj = Object.assign({}, old_data, event.detail.processedChanges);
                                    self.env.pos.db.partner_by_id[self.state.selectedClient.id] = newObj;

                                    self.env.pos.db.old_customer_changes.push(event.detail.processedChanges);

                                    self.state.detailIsShown = false;

                                    self.render();
                                }
                                Gui.showPopup('ErrorPopup', {
                                    title: 'Offline',
                                    body: 'When you online Customer will be Update automiatically.',
                                });
                            } else {
                                var sh_all_customers = self.env.pos.db.sh_all_customers;
                                var newcurrentuser = self.env.pos.add_new_customer()
                                newcurrentuser.set_customer(event.detail.processedChanges)
                                self.env.pos.db.partner_by_id[newcurrentuser.export_as_JSON()['cid']] = event.detail.processedChanges


                                sh_all_customers.push(newcurrentuser.export_as_JSON());


                                self.env.pos.db.add_partners([newcurrentuser.export_as_JSON()])

                                self.env.pos.partners.push(newcurrentuser.export_as_JSON())

                                self.state.selectedClient = sh_all_customers[sh_all_customers.length - 1]
                                self.state.detailIsShown = false;
                                self.env.pos.partners.push(newcurrentuser.export_as_JSON())
                                // self.env.pos.db.all_partner.push(newcurrentuser.export_as_JSON())
                                Gui.showPopup('ErrorPopup', {
                                    title: 'Offline',
                                    body: 'When you online Customer will be created automiatically.',
                                });
                                self.env.pos.set_synch(self.env.pos.get("failed") ? "error" : "disconnected", self.env.pos.db.get_all_customers().length);
                            }
                            self.env.pos.db.save('offline_clinets', self.env.pos.db.get_all_customers())
                        });
                        self.render();

                    } catch (error) {

                        if (error instanceof Error) {
                            throw error;
                        } else {
                            self.env.pos.set_synch(self.env.pos.get("failed") ? "error" : "disconnected");
                            self._handlePushOrderError(error);
                        }
                    }
                } else {
                    super.saveChanges(event)
                }
            }
            async crete_online_customer(event) {
                try {
                    let partnerId = await this.rpc({
                        model: 'res.partner',
                        method: 'create_from_ui',
                        args: [event.detail.processedChanges],
                    });
                    await this.env.pos.load_new_partners();
                    this.state.selectedClient = this.env.pos.db.get_partner_by_id(partnerId);
                    this.state.detailIsShown = false;
                    this.render();
                } catch (error) {
                    if (error.message.code < 0) {
                        await this.showPopup('OfflineErrorPopup', {
                            title: 'Offline',
                            body: 'Unable to save changes.',
                        });
                    } else {
                        throw error;
                    }
                }
            }

        }
    Registries.Component.extend(ClientListScreen, ShClientListScreenScreen)


    const ShClientDetailsEditScreen = (ClientDetailsEdit) =>
        class extends ClientDetailsEdit {
            constructor() {
                super(...arguments);
            }
            saveChanges(event) {
                var self = this;
                if (this.env.pos.config.sh_create_customer) {
                    let processedChanges = {};
                    for (let [key, value] of Object.entries(this.changes)) {
                        if (this.intFields.includes(key)) {
                            processedChanges[key] = parseInt(value) || false;
                        } else {
                            processedChanges[key] = value;
                        }
                    }
                    if ((!this.props.partner.name && !processedChanges.name) ||
                        processedChanges.name === '') {
                        return this.showPopup('ErrorPopup', {
                            title: 'A Customer Name Is Required',
                        });
                    }
                    processedChanges.id = this.props.partner.id || false;

                    this.trigger('save-changes', { processedChanges });
                } else {
                    super.saveChanges(event)
                }
            }

        }
    Registries.Component.extend(ClientDetailsEdit, ShClientDetailsEditScreen)
});

