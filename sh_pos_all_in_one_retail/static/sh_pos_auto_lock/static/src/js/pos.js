odoo.define("sh_pos_auto_lock.pos", function (require) {
    "use strict";

    const Chrome = require("point_of_sale.Chrome");
    const Registries = require("point_of_sale.Registries");
    const models = require("point_of_sale.models");
    const { Component } = owl;

    const useSelectEmployee = require("pos_hr.useSelectEmployee");

    const PosResChrome = (Chrome) =>
        class extends Chrome {
            async askPin(employee) {
                const { confirmed, payload: inputPin } = await this.showPopup("NumberPopup", {
                    isPassword: true,
                    title: this.env._t("Password ?"),
                    startingValue: null,
                });

                if (!confirmed) return false;
                if (employee.pin === Sha1.hash(inputPin)) {
                    this.env.pos.set_cashier(employee);
                    return employee;
                } else {
                    this.showPopup("ErrorPopup", {
                        title: this.env._t("Incorrect Password"),
                    });
                    return false;
                }
            }
            async start() {
                try {
                    const posModelDefaultAttributes = {
                        env: this.env,
                        rpc: this.rpc.bind(this),
                        session: this.env.session,
                        do_action: this.props.webClient.do_action.bind(this.props.webClient),
                        setLoadingMessage: this.setLoadingMessage.bind(this),
                        showLoadingSkip: this.showLoadingSkip.bind(this),
                        setLoadingProgress: this.setLoadingProgress.bind(this),
                    };
                    this.env.pos = new models.PosModel(posModelDefaultAttributes);
                    await this.env.pos.ready;
                    this._buildChrome();
                    this.env.pos.set("selectedCategoryId", this.env.pos.config.iface_start_categ_id ? this.env.pos.config.iface_start_categ_id[0] : 0);
                    this.state.uiState = "READY";
                    this.env.pos.on("change:selectedOrder", this._showSavedScreen, this);
                    this._showStartScreen();
                    if (_.isEmpty(this.env.pos.db.product_by_category_id)) {
                        this._loadDemoData();
                    }
                    var self = this;
                    if (this.env.pos.config.sh_enable_auto_lock) {
                        var set_logout_interval = function (time) {
                            time = time || self.env.pos.config.sh_lock_timer * 1000;
                            if (time) {
                                self.env.pos.logout_timer = setTimeout(function () {
                                    $(".pos").before('<div class="blur_screen"><h3>Tap to unlock...</h3></div>');
                                }, time);
                            }
                        };
                    }
                    if (this.env.pos.config.sh_enable_auto_lock && this.env.pos.config.sh_lock_timer) {
                        $(document).on("click", async function (event) {
                            if (self.env.pos.config.sh_enable_auto_lock && self.env.pos.config.sh_lock_timer) {
                                clearTimeout(self.env.pos.logout_timer);
                                set_logout_interval();
                                if ($(".blur_screen").length > 0) {
                                    $(".blur_screen").remove();
                                    const current = Component.current;
                                    if (self.env.pos.config.module_pos_hr) {
                                        const list = self.env.pos.employees.map((employee) => {
                                            if (employee.name == self.env.pos.get_cashier().name) {
                                                return {
                                                    id: employee.id,
                                                    item: employee,
                                                    label: employee.name,
                                                    isSelected: true,
                                                };
                                            } else {
                                                return {
                                                    id: employee.id,
                                                    item: employee,
                                                    label: employee.name,
                                                    isSelected: false,
                                                };
                                            }
                                        });

                                        const { confirmed, payload: selectedCashier } = await self.showPopup("SelectionPopup", {
                                            title: self.env._t("Change Cashier"),
                                            list: list,
                                        });

                                        if (!confirmed) {
                                            return false;
                                        }
                                        if (!selectedCashier.pin) {
                                            self.env.pos.set_cashier(selectedCashier);
                                            return selectedCashier;
                                        } else {
                                            return self.askPin(selectedCashier);
                                        }
                                    }
                                }
                            }
                        });
                        set_logout_interval();
                    }

                    setTimeout(() => {
                        this.env.pos.push_orders();
                        this._preloadImages();
                    });
                    if (this.env.pos.config.module_pos_hr) this.showTempScreen('LoginScreen');
                } catch (error) {
                    let title = "Unknown Error",
                        body;

                    if (error.message && [100, 200, 404, -32098].includes(error.message.code)) {
                        if (error.message.code === -32098) {
                            title = "Network Failure (XmlHttpRequestError)";
                            body = "The Point of Sale could not be loaded due to a network problem.\n" + "Please check your internet connection.";
                        } else if (error.message.code === 200) {
                            title = error.message.data.message || this.env._t("Server Error");
                            body = error.message.data.debug || this.env._t("The server encountered an error while receiving your order.");
                        }
                    } else if (error instanceof Error) {
                        title = error.message;
                        body = error.stack;
                    }

                    await this.showPopup("ErrorTracebackPopup", {
                        title,
                        body,
                        exitButtonIsShown: true,
                    });
                }
            }
            /*async start() {
                try {
                    const posModelDefaultAttributes = {
                        env: this.env,
                        rpc: this.rpc.bind(this),
                        session: this.env.session,
                        do_action: this.props.webClient.do_action.bind(this.props.webClient),
                        setLoadingMessage: this.setLoadingMessage.bind(this),
                        showLoadingSkip: this.showLoadingSkip.bind(this),
                        setLoadingProgress: this.setLoadingProgress.bind(this),
                    };
                    this.env.pos = new models.PosModel(posModelDefaultAttributes);
                    await this.env.pos.ready;
                    this._buildChrome();
                    this.env.pos.set("selectedCategoryId", this.env.pos.config.iface_start_categ_id ? this.env.pos.config.iface_start_categ_id[0] : 0);
                    this.state.uiState = "READY";
                    this.env.pos.on("change:selectedOrder", this._showSavedScreen, this);
                    this._showStartScreen();
                    if (_.isEmpty(this.env.pos.db.product_by_category_id)) {
                        this._loadDemoData();
                    }
                    var self = this;
                    if (this.env.pos.config.sh_enable_auto_lock) {
                        var set_logout_interval = function (time) {
                            time = time || self.env.pos.config.sh_lock_timer * 1000;
                            if (time) {
                                self.env.pos.logout_timer = setTimeout(function () {
                                    $(".pos").before('<div class="blur_screen"><h3>Tap to unlock...</h3></div>');
                                }, time);
                            }
                        };
                    }
                    if (this.env.pos.config.sh_enable_auto_lock && this.env.pos.config.sh_lock_timer) {
                        $(document).on("click", async function (event) {
                            if (self.env.pos.config.sh_enable_auto_lock && self.env.pos.config.sh_lock_timer) {
                                clearTimeout(self.env.pos.logout_timer);
                                set_logout_interval();
                                if ($(".blur_screen").length > 0) {
                                    $(".blur_screen").remove();
                                    const current = Component.current;
                                    if (self.env.pos.config.module_pos_hr) {
                                        const list = self.env.pos.employees.map((employee) => {
                                            if (employee.name == self.env.pos.get_cashier().name) {
                                                return {
                                                    id: employee.id,
                                                    item: employee,
                                                    label: employee.name,
                                                    isSelected: true,
                                                };
                                            } else {
                                                return {
                                                    id: employee.id,
                                                    item: employee,
                                                    label: employee.name,
                                                    isSelected: false,
                                                };
                                            }
                                        });

                                        const { confirmed, payload: selectedCashier } = await self.showPopup("SelectionPopup", {
                                            title: self.env._t("Change Cashier"),
                                            list: list,
                                        });

                                        if (!confirmed) return false;

                                        if (!selectedCashier.pin) {
                                            self.env.pos.set_cashier(selectedCashier);
                                            return selectedCashier;
                                        }
                                    }
                                }
                            }
                        });
                        set_logout_interval();
                    }

                    setTimeout(() => {
                        this.env.pos.push_orders();
                        this._preloadImages();
                    });
                    if (this.env.pos.config.module_pos_hr) this.showTempScreen('LoginScreen');
                } catch (error) {
                    let title = "Unknown Error",
                        body;

                    if (error.message && [100, 200, 404, -32098].includes(error.message.code)) {
                        if (error.message.code === -32098) {
                            title = "Network Failure (XmlHttpRequestError)";
                            body = "The Point of Sale could not be loaded due to a network problem.\n" + "Please check your internet connection.";
                        } else if (error.message.code === 200) {
                            title = error.message.data.message || this.env._t("Server Error");
                            body = error.message.data.debug || this.env._t("The server encountered an error while receiving your order.");
                        }
                    } else if (error instanceof Error) {
                        title = error.message;
                        body = error.stack;
                    }

                    await this.showPopup("ErrorTracebackPopup", {
                        title,
                        body,
                        exitButtonIsShown: true,
                    });
                }
            }*/
        };

    Registries.Component.extend(Chrome, PosResChrome);

    return Chrome;
});
