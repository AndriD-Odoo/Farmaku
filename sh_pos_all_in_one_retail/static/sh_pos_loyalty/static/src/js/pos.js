odoo.define("sh_pos_loyalty.pos", function (require) {
    "use strict";

    const { useState } = owl;
    var models = require('point_of_sale.models');
    var DB = require("point_of_sale.DB");
    const OrderWidget = require("point_of_sale.OrderWidget");
    const Registries = require("point_of_sale.Registries");
    const payment_screens = require("point_of_sale.PaymentScreen");
    const AbstractAwaitablePopup = require("point_of_sale.AbstractAwaitablePopup");
    const NumberBuffer = require('point_of_sale.NumberBuffer');
    const { useListener } = require('web.custom_hooks');
    const PosComponent = require("point_of_sale.PosComponent");
    const ProductScreen = require("point_of_sale.ProductScreen");
    var core = require('web.core');
    var _t = core._t;
    var rpc = require("web.rpc");
    var exports = {};

    models.load_fields("res.partner", ['sh_user_point', 'sh_user_point_amount', 'sh_expiry_date', 'sh_loyalty_card_no']);

    models.load_models({
        model: "sh.pos.loyalty",
        loaded: function (self, loyalty) {
            self.db.all_loyalty = loyalty;
            if (loyalty && loyalty.length > 0) {
                _.each(loyalty, function (each_loyalty) {
                    self.db.loyalty_by_id[each_loyalty.id] = each_loyalty
                });
            }
        },
    });

    // models.load_models({
    //     model: "res.partner",
    //     loaded: function (self, partner) {
    //         self.db.all_partner = partner
    //     },
    // });

    models.load_models({
        model: "sh.pos.coupon",
        label: "load_coupons",
        loaded: function (self, coupon) {
            self.db.all_coupon = coupon;
            if (coupon) {
                var d = new Date(),
                    month = '' + (d.getMonth() + 1),
                    day = '' + d.getDate(),
                    year = d.getFullYear();

                if (month.length < 2)
                    month = '0' + month;
                if (day.length < 2)
                    day = '0' + day;

                var today_date = [year, month, day].join('-');
                _.each(coupon, function (each_coupon) {
                    self.db.coupon_by_code[each_coupon.sh_coupon_code] = each_coupon
                    if (today_date >= each_coupon.sh_coupon_applicable_date && today_date <= each_coupon.sh_coupon_expiry_date) {
                        if (each_coupon.sh_coupon_type == 'cart_amount_validation') {
                            self.db.cart_coupon.push(each_coupon)
                        } else {
                            self.db.partial_redeemption_coupon.push(each_coupon)
                        }
                    }
                });
            }
        },
    });

    models.load_models({
        model: "sh.pos.loyalty.rule",
        loaded: function (self, loyalty_rule) {
            self.db.all_loyalty_rule = loyalty_rule;
            if (loyalty_rule && loyalty_rule.length > 0) {
                _.each(loyalty_rule, function (each_loyalty_rule) {
                    self.db.loyalty_rule_by_id[each_loyalty_rule.id] = each_loyalty_rule
                });
            }
        },
    });

    models.load_models({
        model: "sh.pos.loyalty.reward",
        loaded: function (self, loyalty_reward) {
            self.db.all_loyalty_reward = loyalty_reward;
            if (loyalty_reward && loyalty_reward.length > 0) {
                _.each(loyalty_reward, function (each_loyalty_reward) {
                    self.db.loyalty_reward_by_id[each_loyalty_reward.id] = each_loyalty_reward
                });
            }
        },
    });

    DB.include({
        init: function (options) {
            this._super(options);
            this.all_loyalty = [];
            this.loyalty_by_id = {};
            this.all_loyalty_rule = [];
            this.loyalty_rule_by_id = {};
            this.all_loyalty_reward = [];
            this.loyalty_reward_by_id = {};
            this.gift_reward = [];
            this.discount_reward;
            this.all_coupon = [];
            this.cart_coupon = [];
            this.partial_redeemption_coupon = [];
            this.coupon_by_code = {};
            this.coupon_write_date = null;
        },
        remove_all_coupon: function () {
            this.all_coupon = [];
            this.coupon_by_code = {};
            this.cart_coupon = [];
            this.partial_redeemption_coupon = [];
            //            this.note_by_uid = {};
        },
        add_coupons: function (all_coupon) {
            if (!all_coupon instanceof Array) {
                all_coupon = [all_coupon];
            }
            var new_write_date = "";

            for (var i = 0, len = all_coupon.length; i < len; i++) {
                var each_coupon = all_coupon[i];
                if (!this.coupon_by_code[each_coupon.sh_coupon_code]) {
                    this.all_coupon.push(each_coupon);
                    this.coupon_by_code[each_coupon.sh_coupon_code] = each_coupon;
                    if (each_coupon.sh_coupon_type == 'cart_amount_validation') {
                        this.cart_coupon.push(each_coupon)
                    } else {
                        this.partial_redeemption_coupon.push(each_coupon)
                    }
                }

                var local_partner_date = (this.coupon_write_date || "").replace(/^(\d{4}-\d{2}-\d{2}) ((\d{2}:?){3})$/, "$1T$2Z");
                var dist_partner_date = (each_coupon.write_date || "").replace(/^(\d{4}-\d{2}-\d{2}) ((\d{2}:?){3})$/, "$1T$2Z");

            }
            this.coupon_write_date = new_write_date || this.coupon_write_date;
        },
        get_coupon_write_date: function () {
            return this.coupon_write_date || "1970-01-01 00:00:00";
        },
        get_coupon: function () {
            return this.load("coupons", []);
        },
    });

    const POSPaymentScreen = (payment_screens) =>
        class extends payment_screens {
            async validateOrder(isForceValidate) {
                var self = this;
                super.validateOrder(isForceValidate);
                if (this.env.pos.get_order().get_client() && this.env.pos.get_order().get_loyalty_point()) {
                    this.env.pos.db.partner_by_id[this.env.pos.get_order().get_client().id].sh_user_point = this.env.pos.db.partner_by_id[this.env.pos.get_order().get_client().id].sh_user_point + this.env.pos.get_order().get_loyalty_point();
                }
            }
            redeemLoyaltyButton(event) {
                var self = this
                if (self.env.pos.get_order() && self.env.pos.get_order().get_client()) {
                    if (self.env.pos.get_order().get_client().sh_user_point > 0) {

                        if (self.env.pos.get_order().get_client().sh_expiry_date) {
                            var d = new Date(),
                                month = '' + (d.getMonth() + 1),
                                day = '' + d.getDate(),
                                year = d.getFullYear();

                            if (month.length < 2)
                                month = '0' + month;
                            if (day.length < 2)
                                day = '0' + day;

                            var today_date = [year, month, day].join('-');
                            if (today_date <= self.env.pos.get_order().get_client().sh_expiry_date) {

                                let { confirmed, payload } = this.showPopup("RedeemLoyaltyPopupWidget");
                                if (confirmed) {
                                } else {
                                    return;
                                }
                            } else {
                                alert("Your loyalty point is expired.")
                            }

                        } else {
                            let { confirmed, payload } = this.showPopup("RedeemLoyaltyPopupWidget");
                            if (confirmed) {
                            } else {
                                return;
                            }
                        }
                    } else {
                        alert("You don't have any loyalty point")
                    }
                } else {
                    alert("Please Select Customer First")
                }
            }
        };
    Registries.Component.extend(payment_screens, POSPaymentScreen);

    const PosOrderWidget = (OrderWidget) =>
        class extends OrderWidget {
            _updateSummary() {
                var self = this;
                var order = self.order;
                if (order) {
                    self.order.set_loyalty_point(0)
                    if (self.env.pos.config.sh_enable_loyalty && order.get_client() && self.env.pos.config.sh_loyalty_rule && self.env.pos.config.sh_loyalty_rule[0] && self.env.pos.db.loyalty_by_id[self.env.pos.config.sh_loyalty_rule[0]]) {
                        if (self.env.pos.db.loyalty_by_id[self.env.pos.config.sh_loyalty_rule[0]].sh_point_per_order) {
                            var point = self.env.pos.get_order().get_loyalty_point();
                            point = point + self.env.pos.db.loyalty_by_id[self.env.pos.config.sh_loyalty_rule[0]].sh_point_per_order;
                            self.env.pos.get_order().set_loyalty_point(point);
                        }
                        if (self.env.pos.db.loyalty_by_id[self.env.pos.config.sh_loyalty_rule[0]].sh_point_per_product) {
                            if (self.env.pos.get_order().get_orderlines()) {
                                var point = self.env.pos.get_order().get_loyalty_point();
                                point = point + self.env.pos.get_order().get_orderlines().length * self.env.pos.db.loyalty_by_id[self.env.pos.config.sh_loyalty_rule[0]].sh_point_per_product;
                                self.env.pos.get_order().set_loyalty_point(point);
                            }
                        }
                        if (self.env.pos.db.loyalty_by_id[self.env.pos.config.sh_loyalty_rule[0]].sh_loyalty_rule) {

                            _.each(self.env.pos.db.loyalty_by_id[self.env.pos.config.sh_loyalty_rule[0]].sh_loyalty_rule, function (each_rule) {
                                var rule = self.env.pos.db.loyalty_rule_by_id[each_rule]

                                if (rule.sh_rule_type && rule.sh_rule_type == 'product') {
                                    if (self.env.pos.get_order().get_orderlines()) {
                                        _.each(self.env.pos.get_order().get_orderlines(), function (each_orderline) {
                                            if (rule.sh_product_ids.includes(each_orderline.product.id)) {
                                                var point = self.env.pos.get_order().get_loyalty_point();
                                                point = point + (rule.sh_point_per_product * each_orderline.quantity);
                                                self.env.pos.get_order().set_loyalty_point(point);
                                            }
                                        });
                                    }
                                }
                                if (rule.sh_rule_type && rule.sh_rule_type == 'category') {
                                    if (self.env.pos.get_order().get_orderlines()) {
                                        _.each(self.env.pos.get_order().get_orderlines(), function (each_orderline) {
                                            if (rule.sh_category_ids.includes(each_orderline.product.pos_categ_id[0])) {
                                                var point = self.env.pos.get_order().get_loyalty_point();
                                                point = point + (rule.sh_point_per_product * each_orderline.quantity);
                                                self.env.pos.get_order().set_loyalty_point(point);
                                            }
                                        });
                                    }
                                }
                            });
                        }
                        if (self.env.pos.get_order().get_reward_point()) {
                            self.env.pos.get_order().set_loyalty_point(Math.abs(self.env.pos.get_order().get_loyalty_point() - self.env.pos.get_order().get_reward_point()))
                        }
                        self.state.pre_define_point = self.env.pos.get_order().get_client().sh_user_point;
                        self.state.current_point = self.env.pos.get_order().get_loyalty_point();
                        self.state.total_point = (self.env.pos.get_order().get_client().sh_user_point + self.env.pos.get_order().get_loyalty_point());
                    }
                }
                super._updateSummary()
            }
        };
    Registries.Component.extend(OrderWidget, PosOrderWidget);

    class RedeemLoyaltyPopupWidget extends AbstractAwaitablePopup {
        constructor() {
            super(...arguments);
            let startingBuffer = '';
            if (typeof this.props.startingValue === 'number' && this.props.startingValue > 0) {
                startingBuffer = this.props.startingValue.toString();
            }
            this.state = useState({ buffer: startingBuffer });
            NumberBuffer.use({
                nonKeyboardInputEvent: 'numpad-click-input',
                triggerAtEnter: 'accept-input',
                triggerAtEscape: 'close-this-popup',
                state: this.state,
            });
        }
        get inputBuffer() {
            if (this.state.buffer === null) {
                return '';
            }
            if (this.props.isPassword) {
                return this.state.buffer.replace(/./g, '•');
            } else {
                return this.state.buffer;
            }
        }
        sendInput(key) {
            this.trigger('numpad-click-input', { key });
        }
        async confirm() {
            this.props.resolve({ confirmed: true, payload: await this.getPayload() });
            var self = this;
            var redeem_point = self.state.buffer;
            var payment_method_id = $('#payment_method_selection').val()

            var loyalty_cashregister = _.find(self.env.pos.payment_methods, function (cashregister) {
                if (parseInt(cashregister.id) === parseInt(payment_method_id)) {
                    cashregister['is_loyalty_journal'] = true;
                    return cashregister
                } else {
                    cashregister['is_loyalty_journal'] = false;
                }
            });
            if (redeem_point == '') {
                alert("Enter Redeem Point.")
            } else {

                if (redeem_point > self.env.pos.get_order().get_client().sh_user_point) {
                    alert("You don't have that much loyalty point.")
                } else {

                    self.env.pos.get_order().set_redeem_point(redeem_point)
                    var order = self.env.pos.get_order();
                    if (loyalty_cashregister) {
                        var amount_to_redeem = redeem_point * self.env.pos.config.sh_loyalty_point_amount
                        order.add_paymentline(loyalty_cashregister);
                        order.selected_paymentline.set_amount(amount_to_redeem);
                        self.env.pos.get_order().set_redeem_point(redeem_point)
                        order.set_redeem_amount(amount_to_redeem);
                        order.get_client().sh_user_point = order.get_client().sh_user_point - redeem_point
                    }
                }
            }
            this.trigger("close-popup");
        }
    }

    RedeemLoyaltyPopupWidget.template = "RedeemLoyaltyPopupWidget";
    Registries.Component.add(RedeemLoyaltyPopupWidget);

    class RewardBtn extends PosComponent {
        constructor() {
            super(...arguments);
            useListener('click-reward-btn', this.onClickRewardBtn);
        }
        async onClickRewardBtn() {
            var self = this;
            if (self.env.pos.db.loyalty_by_id[self.env.pos.config.sh_loyalty_rule[0]].sh_loyalty_reward.length == 1) {
                var reward = self.env.pos.db.loyalty_reward_by_id[self.env.pos.db.loyalty_by_id[self.env.pos.config.sh_loyalty_rule[0]].sh_loyalty_reward[0]]
                if (self.env.pos.get_order().get_client()) {
                    if (self.env.pos.get_order().get_client().sh_user_point >= reward.sh_minimum_point) {
                        if (self.env.pos.get_order().get_orderlines().length > 0) {
                            if (self.env.pos.db.loyalty_by_id[self.env.pos.config.sh_loyalty_rule[0]].sh_loyalty_reward) {
                                if (self.env.pos.db.loyalty_by_id[self.env.pos.config.sh_loyalty_rule[0]].sh_loyalty_reward.length == 1) {
                                    if (reward.sh_reward_type == 'gift') {
                                        const { confirmed } = await this.showPopup('ConfirmPopup', {
                                            title: 'Are you sure you want Reward ?',
                                            body: `As a reward you get free product ${reward.sh_product_ids[1]}`,
                                        });
                                        if (confirmed) {
                                            var product = self.env.pos.db.get_product_by_id(reward.sh_product_ids[0])
                                            if (product) {

                                                self.env.pos.get_order().set_reward_point(reward.sh_point_cost)
                                                self.env.pos.get_order().add_product(product, {
                                                    quantity: 1,
                                                    price: 0,
                                                });
                                            }
                                        }

                                    }
                                }
                            }
                        } else {
                            alert("Please Add Product In Cart")
                        }
                    } else {
                        alert("Not enough Loyalty Point")
                    }
                } else {
                    alert("Please Select Customer First.")
                }
            } else {
                if (self.env.pos.get_order().get_client()) {
                    if (self.env.pos.get_order().get_orderlines().length > 0) {
                        if (self.env.pos.db.loyalty_by_id[self.env.pos.config.sh_loyalty_rule[0]].sh_loyalty_reward) {
                            self.env.pos.db.gift_reward = [];
                            _.each(self.env.pos.db.loyalty_by_id[self.env.pos.config.sh_loyalty_rule[0]].sh_loyalty_reward, function (each_reward) {
                                var reward = self.env.pos.db.loyalty_reward_by_id[each_reward];
                                if (self.env.pos.get_order().get_client().sh_user_point >= reward.sh_minimum_point) {
                                    if (self.env.pos.db.loyalty_reward_by_id[each_reward].sh_reward_type == 'gift') {
                                        self.env.pos.db.gift_reward.push(reward);
                                    } else {
                                        self.env.pos.db.discount_reward = reward;
                                    }
                                }

                            });
                            let { confirmed, payload } = this.showPopup("RewardOptionPopupWidget");
                            if (confirmed) {
                            } else {
                                return;
                            }
                        }
                    } else {
                        alert("Please Add Product In Cart")
                    }
                } else {
                    alert("Please Select Customer First.")
                }
            }
        }
    }

    RewardBtn.template = 'RewardBtn'

    ProductScreen.addControlButton({
        component: RewardBtn,
        condition: function () {
            return this.env.pos.config.sh_enable_loyalty;
        },
    });

    Registries.Component.add(RewardBtn)

    class RewardOptionPopupWidget extends AbstractAwaitablePopup {
        constructor() {
            super(...arguments);

        }
        mounted() {
            super.mounted()
            $('input[type=radio][name=reward]').change(function () {
                if (this.value == 'gift') {
                    $('.gift_selection').addClass('show')
                }
                else if (this.value == 'discount') {
                    $('.gift_selection').removeClass('show')
                }
            });
        }
        async confirm() {
            this.props.resolve({ confirmed: true, payload: await this.getPayload() });
            var self = this;

            var radioValue = $("input[name='reward']:checked").val();
            if (radioValue) {
                if (radioValue == 'gift') {
                    var gift_product = $('.gift_selection').val()



                    var loyalty_reward = self.env.pos.db.loyalty_by_id[self.env.pos.config.sh_loyalty_rule[0]].sh_loyalty_reward
                    var reward1 = [];
                    _.each(loyalty_reward, function (each_reward) {
                        if (self.env.pos.db.loyalty_reward_by_id[each_reward].sh_reward_type == 'gift') {

                            reward1.push(self.env.pos.db.loyalty_reward_by_id[each_reward])
                        }
                    });
                    var reward = self.env.pos.db.loyalty_reward_by_id[self.env.pos.db.loyalty_by_id[self.env.pos.config.sh_loyalty_rule[0]].sh_loyalty_reward[0]]
                    var product = self.env.pos.db.get_product_by_id(parseInt(gift_product))
                    if (product) {
                        var point_cost = self.env.pos.get_order().get_reward_point()

                        _.each(reward1, function (each_reward) {
                            if (each_reward.sh_product_ids[0] == product.id) {
                                self.env.pos.get_order().set_reward_point(point_cost + each_reward.sh_point_cost)
                            }
                        });
                        self.env.pos.get_order().add_product(product, {
                            quantity: 1,
                            price: 0,
                        });
                    }
                } else {
                    if (self.env.pos.db.discount_reward) {
                        var discount_reward = [self.env.pos.db.discount_reward];
                        var orderlines = self.env.pos.get_order().get_orderlines()
                        var point_cost = self.env.pos.get_order().get_reward_point()
                        self.env.pos.get_order().set_reward_point(point_cost + discount_reward[0].sh_point_cost)
                        _.each(orderlines, function (each_order_line) {
                            each_order_line.set_discount(parseFloat(discount_reward[0].sh_discount_percen));
                        });
                    } else {
                        alert("No Any Discount Reward Available or you Don't Have That Much Point.")
                    }
                }
            }
            this.trigger("close-popup");
        }
    }

    RewardOptionPopupWidget.template = "RewardOptionPopupWidget";
    Registries.Component.add(RewardOptionPopupWidget);

    class ManageCouponBtn extends PosComponent {
        constructor() {
            super(...arguments);
            useListener('click-manage-coupon-btn', this.onClickManageCouponBtn);
        }
        async onClickManageCouponBtn() {
            var self = this;
            if (self.env.pos.user.groups_id.indexOf(self.env.pos.config.sh_enable_create_coupon[0]) != -1 || self.env.pos.user.groups_id.indexOf(self.env.pos.config.sh_enable_redeem_coupon[0]) != -1) {
                let { confirmed, payload } = this.showPopup("ManageCouponPopupWidget");
                if (confirmed) {
                } else {
                    return;
                }
            } else {
                alert("You have no rights to create coupon or redeem coupon")
            }

        }

    }

    ManageCouponBtn.template = 'ManageCouponBtn'

    ProductScreen.addControlButton({
        component: ManageCouponBtn,
        condition: function () {
            return this.env.pos.config.sh_enable_coupon;
        },
    });

    Registries.Component.add(ManageCouponBtn)

    class ManageCouponPopupWidget extends AbstractAwaitablePopup {
        constructor() {
            super(...arguments);

        }
        create_coupon() {
            let { confirmed, payload } = this.showPopup("CreateCouponPopupWidget");
            if (confirmed) {
            } else {
                return;
            }
        }
        redeem_coupon() {
            let { confirmed, payload } = this.showPopup("RedeemCouponPopupWidget");
            if (confirmed) {
            } else {
                return;
            }
        }
        async confirm() {
            this.props.resolve({ confirmed: true, payload: await this.getPayload() });
            var self = this;
            this.trigger("close-popup");
        }
        mounted() {
            var self = this;
            if ((self.env.pos.user.groups_id.indexOf(self.env.pos.config.sh_enable_create_coupon[0]) != -1 && self.env.pos.user.groups_id.indexOf(self.env.pos.config.sh_enable_redeem_coupon[0]) === -1) || (self.env.pos.user.groups_id.indexOf(self.env.pos.config.sh_enable_create_coupon[0]) === -1 && self.env.pos.user.groups_id.indexOf(self.env.pos.config.sh_enable_redeem_coupon[0]) != -1)) {
                $('.sh_manage_coupon_body').addClass('sh_single_manage_coupon')
            }
            super.mounted()
        }
    }

    ManageCouponPopupWidget.template = "ManageCouponPopupWidget";
    Registries.Component.add(ManageCouponPopupWidget);

    class CreateCouponPopupWidget extends AbstractAwaitablePopup {
        constructor() {
            super(...arguments);
        }
        mounted() {
            super.mounted();
            $('.coupon_for').change(function () {
                if (this.value == 'specific_customer') {
                    $('.cpn_for_customer').addClass('show')
                }
                else if (this.value == 'all') {
                    $('.cpn_for_customer').removeClass('show')
                }
            });
        }
        async confirm() {
            this.props.resolve({ confirmed: true, payload: await this.getPayload() });
            var self = this;
            var coupon_name = $(".coupon_name").val();
            var coupon_code = $('.coupon_code').val()
            var coupon_expiry_date = $('.coupon_expiry_date').val()
            var coupon_applicable_date = $('.coupon_applicable_date').val()
            var coupon_value_type = $('.coupon_value_type').val()
            var coupon_minimum_cart_amount = $('.coupon_minimum_cart_amount').val()
            var coupon_max_discount = $('.coupon_max_discount').val()
            var coupon_value = $('.coupon_value').val()
            var coupon_type = $("input[name='coupon_type']:checked").val();
            var coupon_for = $('.coupon_for').val()
            var coupon_customer = $('.coupon_customer').val()


            if (coupon_name == "") {
                alert("Enter Valid Coupon Name")
            } else if (coupon_code == "") {
                alert("Enter Valid Coupon Code")
            } else if (coupon_expiry_date == "") {
                alert("Enter Valid Expiry Date")
            } else if (coupon_applicable_date == "") {
                alert("Enter Valid Coupon Applicable Date")
            } else if (coupon_value_type == "") {
                alert("Enter Valid Coupon Value Type")
            } else if (coupon_minimum_cart_amount == "") {
                alert("Enter Minimum Cart Amount")
            } else if (coupon_value == "") {
                alert("Enter Coupon Value")
            } else if (!coupon_type) {
                alert("Select any one coupon type")
            } else if (self.env.pos.db.coupon_by_code[coupon_code]) {
                alert("This Coupon is already exist")
            } else if (coupon_applicable_date > coupon_expiry_date) {
                alert("Coupon applicable date is less that coupon expiry date.")
            } else {

                var currentCoupon = self.env.pos.get_coupon();
                self.env.pos.add_new_coupon();
                var currentCoupon = self.env.pos.get_coupon();
                var coupon_data;
                if (coupon_for == 'all') {
                    coupon_data = { 'name': coupon_name, 'sh_coupon_code': coupon_code, 'sh_coupon_active': 'true', 'sh_coupon_for': 'all', 'sh_coupon_expiry_date': coupon_expiry_date, 'sh_coupon_applicable_date': coupon_applicable_date, 'sh_coupon_value': coupon_value, 'sh_coupon_value_type': coupon_value_type, 'sh_minimum_cart_amount': coupon_minimum_cart_amount, 'max_discount': coupon_max_discount, 'sh_coupon_type': coupon_type, 'sh_product_filter': 'all' }
                } else {
                    coupon_data = { 'name': coupon_name, 'sh_coupon_code': coupon_code, 'sh_coupon_active': 'true', 'sh_coupon_for': 'specific_customer', 'sh_coupon_expiry_date': coupon_expiry_date, 'sh_coupon_applicable_date': coupon_applicable_date, 'sh_coupon_value': coupon_value, 'sh_coupon_value_type': coupon_value_type, 'sh_minimum_cart_amount': coupon_minimum_cart_amount, 'max_discount': coupon_max_discount, 'sh_coupon_type': coupon_type, 'sh_product_filter': 'all', 'sh_coupon_partner': coupon_customer }
                }
                currentCoupon.set_coupon_data(coupon_data);

                var all_coupon = self.env.pos.db.all_coupon;
                self.env.pos.db.remove_all_coupon();
                all_coupon.push(currentCoupon.export_as_JSON());
                self.env.pos.db.add_coupons(all_coupon);

                var offline_coupons = self.env.pos.db.get_coupon();
                offline_coupons.push(currentCoupon.export_as_JSON());
                self.env.pos.db.save("coupons", offline_coupons);
                try {
                    self.env.pos.load_new_coupons();
                    self.trigger("close-popup");
                } catch (error) {
                    if (error instanceof Error) {
                        throw error;
                    } else {
                        self.env.pos.set_synch(self.env.pos.get("failed") ? "error" : "disconnected");
                    }
                }

            }
        }
    }

    CreateCouponPopupWidget.template = "CreateCouponPopupWidget";
    Registries.Component.add(CreateCouponPopupWidget);

    class RedeemCouponPopupWidget extends AbstractAwaitablePopup {
        constructor() {
            super(...arguments);
        }
        mounted() {
            super.mounted();

        }
        async confirm() {
            this.props.resolve({ confirmed: true, payload: await this.getPayload() });
            var self = this;



            if (self.env.pos.db.coupon_by_code[$('.coupon_name').val()]) {
                var coupon = self.env.pos.db.coupon_by_code[$('.coupon_name').val()]
                if (self.env.pos.get_order().applied_coupon.includes(coupon.sh_coupon_code)) {
                    alert("This coupon is already applied")
                } else if (self.env.pos.get_order().applied_coupon.length !== 0) {
                    alert(`Coupon ${self.env.pos.get_order().applied_coupon[0]} is already applied to this order. You can not use multiple coupon for same order`)
                } else {
                    var coupon_amount = 0.00;
                    if (self.env.pos.get_order().get_total_with_tax() >= coupon.sh_minimum_cart_amount) {
                        if (coupon.sh_coupon_for == 'all') {
                            if (coupon.sh_product_filter == 'specific_product') {
                                var cart_product = []
                                var total = 0.00
                                _.find(self.env.pos.get_order().get_orderlines(), function (each_product) {
                                    if (coupon.sh_coupon_product_ids.includes(each_product.product.id)) {
                                        total = total + (each_product.quantity * each_product.product.lst_price)
                                        cart_product.push(each_product)
                                    }
                                });
                                if (cart_product.length > 0) {
                                    if (coupon.sh_coupon_value_type == 'fixed') {
                                        var value = coupon.sh_coupon_value
                                        var orderlines = cart_product

                                        const { confirmed } = await this.showPopup('ConfirmPopup', {
                                            title: 'Redeem Gift Coupon',
                                            body: `Validated successfully. Using this coupon you can make discount of ${value} amount.`,
                                        });
                                        if (confirmed) {
                                            var orderlines = self.env.pos.get_order().get_orderlines();

                                            if (coupon.sh_product_filter == 'all') {
                                                _.each(orderlines, function (each_order_line) {
                                                    var percentage = (value / each_order_line.price) * 100;
                                                    var current_coupon_amount = each_order_line.price * percentage / 100 * each_order_line.quantity;
                                                    if (current_coupon_amount > coupon.max_discount){
                                                        var percentage = (coupon.max_discount / each_order_line.quantity/ each_order_line.price) * 100;
                                                        var current_coupon_amount = each_order_line.price * percentage / 100 * each_order_line.quantity;
                                                    };
                                                    each_order_line.set_discount(parseFloat(percentage));
                                                    coupon_amount = coupon_amount + current_coupon_amount;
                                                });
                                            } else {
                                                if (coupon.sh_coupon_product_ids) {
                                                    _.each(orderlines, function (each_order_line) {
                                                        if (each_order_line.product.id) {
                                                            if (coupon.sh_coupon_product_ids.includes(each_order_line.product.id)) {
                                                                var percentage = (value / each_order_line.price) * 100;
                                                                var current_coupon_amount = each_order_line.price * percentage / 100 * each_order_line.quantity;
                                                                if (current_coupon_amount > coupon.max_discount){
                                                                    var percentage = (coupon.max_discount / each_order_line.quantity/ each_order_line.price) * 100;
                                                                    var current_coupon_amount = each_order_line.price * percentage / 100 * each_order_line.quantity;
                                                                };
                                                                each_order_line.set_discount(parseFloat(percentage));
                                                                coupon_amount = coupon_amount + current_coupon_amount;
                                                            }
                                                        }
                                                    });
                                                }

                                            }
                                            // var percentage = (value / total) * 100;
                                            // _.each(cart_product, function (each_order_line) {
                                            //     each_order_line.set_discount(parseFloat(percentage));
                                            // });
                                            self.env.pos.get_order().applied_coupon.push(coupon.sh_coupon_code)
                                        }
                                    } else {
                                        var orderlines = cart_product;
                                        var value = coupon.sh_coupon_value
                                        const { confirmed } = await this.showPopup('ConfirmPopup', {
                                            title: 'Redeem Gift Coupon',
                                            body: `Validated successfully. Using this coupon you can make discount of ${value} %.`,
                                        });
                                        if (confirmed) {
                                            _.each(orderlines, function (each_order_line) {
                                                var current_coupon_amount = each_order_line.price * value / 100 * each_order_line.quantity;
                                                if (current_coupon_amount > coupon.max_discount){
                                                    value = (coupon.max_discount / each_order_line.quantity/ each_order_line.price) * 100;
                                                    var current_coupon_amount = each_order_line.price * value / 100 * each_order_line.quantity;
                                                };
                                                each_order_line.set_discount(parseFloat(value));
                                                coupon_amount = coupon_amount + current_coupon_amount;
                                            });
                                            self.env.pos.get_order().applied_coupon.push(coupon.sh_coupon_code)
                                        }
                                    }
                                } else {
                                    alert("Coupon is not valid for all of this cart product.")
                                }

                            } else {
                                if (coupon.sh_coupon_value_type == 'fixed') {
                                    var value = coupon.sh_coupon_value
                                    var orderlines = self.env.pos.get_order().get_orderlines();
                                    const { confirmed } = await this.showPopup('ConfirmPopup', {
                                        title: 'Redeem Gift Coupon',
                                        body: `Validated successfully. Using this coupon you can make discount of ${value} amount.`,
                                    });
                                    if (confirmed) {
                                        _.each(orderlines, function (each_order_line) {
                                            var percentage = (value / each_order_line.price) * 100;
                                            var current_coupon_amount = each_order_line.price * percentage / 100 * each_order_line.quantity;
                                            if (current_coupon_amount > coupon.max_discount){
                                                var percentage = (coupon.max_discount / each_order_line.quantity/ each_order_line.price) * 100;
                                                var current_coupon_amount = each_order_line.price * percentage / 100 * each_order_line.quantity;
                                            };
                                            each_order_line.set_discount(parseFloat(percentage));
                                            coupon_amount = coupon_amount + current_coupon_amount;
                                        });
                                        self.env.pos.get_order().applied_coupon.push(coupon.sh_coupon_code)
                                    }
                                } else {
                                    var value = coupon.sh_coupon_value
                                    var orderlines = self.env.pos.get_order().get_orderlines();

                                    const { confirmed } = await this.showPopup('ConfirmPopup', {
                                        title: 'Redeem Gift Coupon',
                                        body: `Validated successfully. Using this coupon you can make discount of ${value} %.`,
                                    });
                                    if (confirmed) {
                                        _.each(orderlines, function (each_order_line) {
                                            var current_coupon_amount = each_order_line.price * value / 100 * each_order_line.quantity;
                                            if (current_coupon_amount > coupon.max_discount){
                                                value = (coupon.max_discount / each_order_line.quantity/ each_order_line.price) * 100;
                                                var current_coupon_amount = each_order_line.price * value / 100 * each_order_line.quantity;
                                            };
                                            each_order_line.set_discount(parseFloat(value));
                                            coupon_amount = coupon_amount + current_coupon_amount;
                                        });
                                        self.env.pos.get_order().applied_coupon.push(coupon.sh_coupon_code)
                                    }
                                }
                            }
                        } else {
                            if (self.env.pos.get_order().get_client()) {
                                if (self.env.pos.get_order().get_client().id == coupon.sh_coupon_partner[0]) {
                                    if (coupon.sh_product_filter == 'specific_product') {
                                        var cart_product = []
                                        var total = 0.00
                                        _.find(self.env.pos.get_order().get_orderlines(), function (each_product) {
                                            if (coupon.sh_coupon_product_ids.includes(each_product.product.id)) {
                                                total = total + (each_product.quantity * each_product.product.lst_price)
                                                cart_product.push(each_product)
                                            }
                                        });
                                        if (cart_product.length > 0) {
                                            if (coupon.sh_coupon_value_type == 'fixed') {
                                                var value = coupon.sh_coupon_value
                                                var orderlines = cart_product

                                                const { confirmed } = await this.showPopup('ConfirmPopup', {
                                                    title: 'Redeem Gift Coupon',
                                                    body: `Validated successfully. Using this coupon you can make discount of ${value} amount.`,
                                                });
                                                if (confirmed) {
                                                    _.each(cart_product, function (each_order_line) {
                                                        var percentage = (value / each_order_line.price) * 100;
                                                        var current_coupon_amount = each_order_line.price * percentage / 100 * each_order_line.quantity;
                                                        if (current_coupon_amount > coupon.max_discount){
                                                            var percentage = (coupon.max_discount / each_order_line.quantity/ each_order_line.price) * 100;
                                                            var current_coupon_amount = each_order_line.price * percentage / 100 * each_order_line.quantity;
                                                        };
                                                        each_order_line.set_discount(parseFloat(percentage));
                                                        coupon_amount = coupon_amount + current_coupon_amount;
                                                    });
                                                    self.env.pos.get_order().applied_coupon.push(coupon.sh_coupon_code)
                                                }
                                            } else {
                                                var orderlines = cart_product;
                                                var value = coupon.sh_coupon_value
                                                const { confirmed } = await this.showPopup('ConfirmPopup', {
                                                    title: 'Redeem Gift Coupon',
                                                    body: `Validated successfully. Using this coupon you can make discount of ${value} %.`,
                                                });
                                                if (confirmed) {
                                                    _.each(orderlines, function (each_order_line) {
                                                        var current_coupon_amount = each_order_line.price * value / 100 * each_order_line.quantity;
                                                        if (current_coupon_amount > coupon.max_discount){
                                                            value = (coupon.max_discount / each_order_line.quantity/ each_order_line.price) * 100;
                                                            var current_coupon_amount = each_order_line.price * value / 100 * each_order_line.quantity;
                                                        };
                                                        each_order_line.set_discount(parseFloat(value));
                                                        coupon_amount = coupon_amount + current_coupon_amount;
                                                    });
                                                    self.env.pos.get_order().applied_coupon.push(coupon.sh_coupon_code)
                                                }
                                            }
                                        } else {
                                            alert("Coupon is not valid for all of this cart product.")
                                        }

                                    } else {
                                        if (coupon.sh_coupon_value_type == 'fixed') {
                                            var value = coupon.sh_coupon_value
                                            var orderlines = self.env.pos.get_order().get_orderlines();
                                            const { confirmed } = await this.showPopup('ConfirmPopup', {
                                                title: 'Redeem Gift Coupon',
                                                body: `Validated successfully. Using this coupon you can make discount of ${value} amount.`,
                                            });
                                            if (confirmed) {
                                                _.each(orderlines, function (each_order_line) {
                                                    var percentage = (value / each_order_line.price) * 100;
                                                    var current_coupon_amount = each_order_line.price * percentage / 100 * each_order_line.quantity;
                                                    if (current_coupon_amount > coupon.max_discount){
                                                        var percentage = (coupon.max_discount / each_order_line.quantity/ each_order_line.price) * 100;
                                                        var current_coupon_amount = each_order_line.price * percentage / 100 * each_order_line.quantity;
                                                    };
                                                    each_order_line.set_discount(parseFloat(percentage));
                                                    coupon_amount = coupon_amount + current_coupon_amount;
                                                });
                                                self.env.pos.get_order().applied_coupon.push(coupon.sh_coupon_code)
                                            }
                                        } else {
                                            var value = coupon.sh_coupon_value

                                            const { confirmed } = await this.showPopup('ConfirmPopup', {
                                                title: 'Redeem Gift Coupon',
                                                body: `Validated successfully. Using this coupon you can make discount of ${value} %.`,
                                            });
                                            if (confirmed) {
                                                var orderlines = self.env.pos.get_order().get_orderlines();
                                                _.each(orderlines, function (each_order_line) {
                                                    var current_coupon_amount = each_order_line.price * value / 100 * each_order_line.quantity;
                                                    if (current_coupon_amount > coupon.max_discount){
                                                        value = (coupon.max_discount / each_order_line.quantity/ each_order_line.price) * 100;
                                                        var current_coupon_amount = each_order_line.price * value / 100 * each_order_line.quantity;
                                                    };
                                                    each_order_line.set_discount(parseFloat(value));
                                                    coupon_amount = coupon_amount + current_coupon_amount;
                                                });
                                                self.env.pos.get_order().applied_coupon.push(coupon.sh_coupon_code)
                                            }
                                        }
                                    }
                                } else {
                                    alert("Coupon is not valid for this customer")
                                }
                            } else {
                                alert("Please select the customer.")
                            }
                        }
                    } else {
                        alert("Not sufficient Cart Amount")
                    }
                    self.env.pos.get_order().set_coupon_amount(coupon_amount);
                }
            } else {
                alert("Please Enter Valid Coupon Name")
            }
            self.trigger("close-popup");
        }
    }

    RedeemCouponPopupWidget.template = "RedeemCouponPopupWidget";
    Registries.Component.add(RedeemCouponPopupWidget);

    var _super_orderline = models.Orderline.prototype;
    models.Orderline = models.Orderline.extend({
        get_discount_str: function () {
            var discount_str = _super_orderline.get_discount_str.call(this);
            return (parseFloat(discount_str)).toFixed(2);
        },
    });

    var _super_order = models.Order.prototype;
    models.Order = models.Order.extend({
        initialize: function (attributes, options) {
            this.loyalty_point = 0.00
            this.coupon_amount = 0.00
            this.reward_point = 0.00
            this.applied_coupon = [];
            _super_order.initialize.apply(this, arguments);

        },
        applied_coupon: function (applied_coupon) {
            this.applied_coupon.push(applied_coupon)
        },
        set_loyalty_point: function (loyalty_point) {
            this.loyalty_point = loyalty_point
        },
        get_loyalty_point: function () {
            return this.loyalty_point;
        },
        set_coupon_amount: function (coupon_amount) {
            this.coupon_amount = coupon_amount
        },
        get_coupon_amount: function () {
            return this.coupon_amount;
        },
        set_redeem_point: function (redeem_point) {
            this.redeem_point = redeem_point
        },
        get_redeem_point: function () {
            return this.redeem_point;
        },
        set_redeem_amount: function (redeem_amount) {
            this.redeem_amount = redeem_amount
        },
        get_redeem_amount: function () {
            return this.redeem_amount;
        },
        set_reward_point: function (reward_point) {
            this.reward_point = reward_point
        },
        get_reward_point: function () {
            return this.reward_point;
        },
        export_as_JSON: function () {
            var new_val = {};
            var orders = _super_order.export_as_JSON.call(this);
            new_val = {
                loyalty_point: this.get_loyalty_point(),
                redeem_loyalty_point: this.get_redeem_point(),
                redeem_loyalty_amount: this.get_redeem_amount(),
                coupons: this.applied_coupon,
            }
            $.extend(orders, new_val);
            return orders;
        },
        apply_coupon: function () {
            var self = this;
            if (self.pos.user.groups_id.indexOf(self.pos.config.sh_enable_redeem_coupon[0]) != -1) {
                _.each(self.pos.db.cart_coupon, function (coupon) {
                    // var coupon = self.pos.db.coupon_by_code[$('.coupon_name').val()]
                    var coupon_amount = 0.00
                    if (!self.pos.get_order().applied_coupon.includes(coupon) && self.pos.get_order().get_total_with_tax() >= coupon.sh_minimum_cart_amount) {
                        if (coupon.sh_coupon_for == 'all') {
                            if (coupon.sh_product_filter == 'specific_product') {
                                var cart_product = []
                                var total = 0.00
                                _.find(self.pos.get_order().get_orderlines(), function (each_product) {
                                    if (coupon.sh_coupon_product_ids.includes(each_product.product.id)) {
                                        each_product.set_discount(0)
                                        total = total + (each_product.quantity * each_product.product.lst_price)
                                        cart_product.push(each_product)
                                    }
                                });
                                if (cart_product.length > 0) {
                                    if (coupon.sh_coupon_value_type == 'fixed') {
                                        var value = coupon.sh_coupon_value
                                        var orderlines = cart_product
                                        // var percentage = (value / total) * 100;
                                        _.each(cart_product, function (each_order_line) {
                                            var percentage = (value / each_order_line.get_display_price()) * 100;
                                            var current_coupon_amount = each_order_line.price * percentage / 100 * each_order_line.quantity;
                                            if (current_coupon_amount > coupon.max_discount){
                                                var percentage = (coupon.max_discount / each_order_line.quantity/ each_order_line.price) * 100;
                                                var current_coupon_amount = each_order_line.price * percentage / 100 * each_order_line.quantity;
                                            };
                                            each_order_line.set_discount(parseFloat(percentage));
                                            coupon_amount = coupon_amount + current_coupon_amount;
                                        });
                                        self.pos.get_order().applied_coupon.push(coupon.sh_coupon_code)
                                    } else {
                                        var orderlines = cart_product;
                                        var value = coupon.sh_coupon_value
                                        _.each(orderlines, function (each_order_line) {
                                            each_order_line.set_discount(0);
                                            coupon_amount = 0.00
                                        });
                                        _.each(orderlines, function (each_order_line) {
                                            var current_coupon_amount = each_order_line.price * value / 100 * each_order_line.quantity;
                                            if (current_coupon_amount > coupon.max_discount){
                                                value = (coupon.max_discount / each_order_line.quantity/ each_order_line.price) * 100;
                                                var current_coupon_amount = each_order_line.price * value / 100 * each_order_line.quantity;
                                            };
                                            each_order_line.set_discount(parseFloat(value));
                                            coupon_amount = coupon_amount + current_coupon_amount;
                                        });
                                        self.pos.get_order().applied_coupon.push(coupon.sh_coupon_code)
                                    }
                                }

                            } else {
                                if (coupon.sh_coupon_value_type == 'fixed') {
                                    var value = coupon.sh_coupon_value
                                    var orderlines = self.pos.get_order().get_orderlines();
                                    _.each(orderlines, function (each_order_line) {
                                        each_order_line.set_discount(0);
                                        coupon_amount = 0.00;
                                    });

                                    var orderlines = self.pos.get_order().get_orderlines();
                                    _.each(orderlines, function (each_order_line) {
                                        var percentage = (value / each_order_line.price) * 100;
                                        var current_coupon_amount = each_order_line.price * percentage / 100 * each_order_line.quantity;
                                        if (current_coupon_amount > coupon.max_discount){
                                            var percentage = (coupon.max_discount / each_order_line.quantity/ each_order_line.price) * 100;
                                            var current_coupon_amount = each_order_line.price * percentage / 100 * each_order_line.quantity;
                                        };
                                        each_order_line.set_discount(parseFloat(percentage));
                                        coupon_amount = coupon_amount + current_coupon_amount;
                                    });


                                    self.pos.get_order().applied_coupon.push(coupon.sh_coupon_code)
                                } else {
                                    var value = coupon.sh_coupon_value
                                    var orderlines = self.pos.get_order().get_orderlines();
                                    _.each(orderlines, function (each_order_line) {
                                        each_order_line.set_discount(0);
                                        coupon_amount = 0.00;
                                    });
                                    _.each(orderlines, function (each_order_line) {
                                        var current_coupon_amount = each_order_line.price * value / 100 * each_order_line.quantity;
                                        if (current_coupon_amount > coupon.max_discount){
                                            value = (coupon.max_discount / each_order_line.quantity/ each_order_line.price) * 100;
                                            var current_coupon_amount = each_order_line.price * value / 100 * each_order_line.quantity;
                                        };
                                        each_order_line.set_discount(parseFloat(value));
                                        coupon_amount = coupon_amount + current_coupon_amount;
                                    });
                                    self.pos.get_order().applied_coupon.push(coupon.sh_coupon_code)
                                }
                            }
                        } else {
                            if (self.pos.get_order().get_client()) {
                                if (self.pos.get_order().get_client().id == coupon.sh_coupon_partner[0]) {
                                    if (coupon.sh_product_filter == 'specific_product') {
                                        var cart_product = []
                                        var total = 0.00
                                        _.find(self.pos.get_order().get_orderlines(), function (each_product) {
                                            each_product.set_discount(0)
                                            if (coupon.sh_coupon_product_ids.includes(each_product.product.id)) {
                                                total = total + (each_product.quantity * each_product.product.lst_price)
                                                cart_product.push(each_product)
                                            }
                                        });
                                        if (cart_product.length > 0) {
                                            if (coupon.sh_coupon_value_type == 'fixed') {
                                                var value = coupon.sh_coupon_value
                                                var orderlines = cart_product
                                                _.each(cart_product, function (each_order_line) {
                                                    var percentage = (value / each_order_line.get_display_price()) * 100;
                                                    var current_coupon_amount = each_order_line.price * percentage / 100 * each_order_line.quantity;
                                                    if (current_coupon_amount > coupon.max_discount){
                                                        var percentage = (coupon.max_discount / each_order_line.quantity/ each_order_line.price) * 100;
                                                        var current_coupon_amount = each_order_line.price * percentage / 100 * each_order_line.quantity;
                                                    };
                                                    each_order_line.set_discount(parseFloat(percentage));
                                                    coupon_amount = coupon_amount + current_coupon_amount;
                                                });
                                                self.pos.get_order().applied_coupon.push(coupon.sh_coupon_code)
                                            } else {
                                                var orderlines = cart_product;
                                                var value = coupon.sh_coupon_value
                                                _.each(orderlines, function (each_order_line) {
                                                    each_order_line.set_discount(0);
                                                    coupon_amount = 0.00;
                                                });
                                                _.each(orderlines, function (each_order_line) {
                                                    var current_coupon_amount = each_order_line.price * value / 100 * each_order_line.quantity;
                                                    if (current_coupon_amount > coupon.max_discount){
                                                        value = (coupon.max_discount / each_order_line.quantity/ each_order_line.price) * 100;
                                                        var current_coupon_amount = each_order_line.price * value / 100 * each_order_line.quantity;
                                                    };
                                                    each_order_line.set_discount(parseFloat(value));
                                                    coupon_amount = coupon_amount + current_coupon_amount;
                                                });
                                                self.pos.get_order().applied_coupon.push(coupon.sh_coupon_code)
                                            }
                                        }

                                    } else {
                                        if (coupon.sh_coupon_value_type == 'fixed') {
                                            var value = coupon.sh_coupon_value
                                            var orderlines = self.pos.get_order().get_orderlines();
                                            _.each(orderlines, function (each_order_line) {
                                                each_order_line.set_discount(0);
                                                coupon_amount = 0.00;
                                            });
                                            _.each(orderlines, function (each_order_line) {
                                                var percentage = (value / each_order_line.price) * 100;
                                                var current_coupon_amount = each_order_line.price * percentage / 100 * each_order_line.quantity;
                                                if (current_coupon_amount > coupon.max_discount){
                                                    var percentage = (coupon.max_discount / each_order_line.quantity/ each_order_line.price) * 100;
                                                    var current_coupon_amount = each_order_line.price * percentage / 100 * each_order_line.quantity;
                                                };
                                                each_order_line.set_discount(parseFloat(percentage));
                                                coupon_amount = coupon_amount + current_coupon_amount;
                                            });
                                            self.pos.get_order().applied_coupon.push(coupon.sh_coupon_code)
                                        } else {

                                            var value = coupon.sh_coupon_value
                                            var orderlines = self.pos.get_order().get_orderlines();
                                            _.each(orderlines, function (each_order_line) {
                                                each_order_line.set_discount(0);
                                                coupon_amount = 0.00;
                                            });
                                            _.each(orderlines, function (each_order_line) {
                                                var current_coupon_amount = each_order_line.price * value / 100 * each_order_line.quantity;
                                                if (current_coupon_amount > coupon.max_discount){
                                                    value = (coupon.max_discount / each_order_line.quantity/ each_order_line.price) * 100;
                                                    var current_coupon_amount = each_order_line.price * value / 100 * each_order_line.quantity;
                                                };
                                                each_order_line.set_discount(parseFloat(value));
                                                coupon_amount = coupon_amount + current_coupon_amount;
                                            });
                                            self.pos.get_order().applied_coupon.push(coupon.sh_coupon_code)
                                        }
                                    }
                                }
                            }
                        }
                    }
                    self.env.pos.get_order().set_coupon_amount(coupon_amount);
                });
            }
        },
        // add_product: function (product, options) {
        //     _super_order.add_product.call(this, product, options);
        //     var self = this;
        //     if (self.pos.config.sh_enable_coupon && self.pos.db.cart_coupon && self.pos.db.cart_coupon.length > 0 && self.pos.get_order().get_client()) {
        //         self.apply_coupon();
        //     }
        // },
        set_client: function (client) {
            _super_order.set_client.apply(this, arguments);
            var self = this;
            if (self.pos.get_order()) {
                if (self.pos.config.sh_enable_coupon && self.pos.db.cart_coupon && self.pos.db.cart_coupon.length > 0 && self.pos.get_order().get_client()) {
                    self.apply_coupon();
                } 
                if (self.pos.config.sh_enable_customer_discount) {
                    if (self.pos.get_order().get_orderlines() && client && client.sh_customer_discount) {
                        var orderlines = self.pos.get_order().get_orderlines();
                        if (orderlines) {
                            _.each(orderlines, function (each_order_line) {
                                each_order_line.set_discount(client.sh_customer_discount);
                            });
                        }
                    }
                }
            }
        },
    });

    var OrderCollection = Backbone.Collection.extend({
        model: exports.Order,
    });

    var _super_posmodel = models.PosModel.prototype;
    models.PosModel = models.PosModel.extend({
        initialize: function (session, attributes) {
            this.set({
                synch: { status: "connected", pending: 0 },
                orders: new OrderCollection(),
                coupons: new CouponCollection(),
                selectedCoupon: null,
                selectedOrder: null,
                selectedClient: null,
                cashier: null,
                selectedCategoryId: null,
            });
            _super_posmodel.initialize.call(this, session, attributes);
        },
        push_orders: async function (order, opts) {
            this.push_notes();
            this.create_sale_order()
            this.create_purchase_order()
            this.push_coupons();
            this.push_cash_in_outs();
            this.push_closing_balance()
            opts = opts || {};
            var self = this;

            this.update_old_customer()
            if (self.db.get_offline_clients().length > 0) {
                await this.create_offline_clients()
            }

            _.each(this.db.get_orders(), function (each_order) {
                var partner = 0;
                if (each_order['data'].partner_id) {
                    if (self.env.pos.db.get_partner_by_id(each_order['data'].partner_id)) {
                        partner = self.env.pos.db.get_partner_by_id(each_order['data'].partner_id)
                    } else if (self.env.pos.db.get_partner_by_cid(each_order['data'].partner_id)) {
                        partner = self.env.pos.db.get_partner_by_cid(each_order['data'].partner_id)
                    }
                }
                //                var partner = self.env.pos.db.get_partner_by_cid(each_order['data'].partner_id)
                if (partner) {
                    each_order['data'].partner_id = partner.id
                }
                // each_order['data'].partner_id = false
            })

            self.db.remove_sh_all_customers()
            // self.env.pos.load_new_partners()
            _.each(self.db.get_all_customers(), function (each_clinet) {
                each_clinet['currunt_client'] = false
            })

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
        push_coupons: function () {
            var self = this;

            rpc.query({
                model: "sh.pos.coupon",
                method: "create_from_ui",
                args: [this.db.get_coupon()],
            })
                .then(function (server_ids) {
                    self.db.save("coupons", []);
                    var fields = _.find(self.models, function (model) {
                        return model.label === "load_coupons";
                    }).fields;

                    rpc.query(
                        {
                            model: "sh.pos.coupon",
                            method: "search_read",
                            args: [[], fields],
                        },
                        {
                            timeout: 3000,
                            shadow: true,
                        }
                    ).then(
                        function (coupons) {
                            self.db.add_coupons(coupons);
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
        },
        add_new_coupon: function (options) {
            var coupon = new exports.Coupon({}, { pos: this });
            this.set("selectedCoupon", coupon, options);
            return coupon;
        },
        get_coupon: function () {
            return this.get("selectedCoupon");
        },
        load_new_coupons: function () {
            var self = this;
            return new Promise(function (resolve, reject) {
                try {
                    rpc.query({
                        model: "sh.pos.coupon",
                        method: "create_from_ui",
                        args: [self.db.get_coupon()],
                    })
                        .then(function (server_ids) {
                            self.db.save("coupons", []);
                            var fields = _.find(self.models, function (model) {
                                return model.label === "load_coupons";
                            }).fields;

                            rpc.query(
                                {
                                    model: "sh.pos.coupon",
                                    method: "search_read",
                                    args: [[], fields],
                                },
                                {
                                    timeout: 3000,
                                    shadow: true,
                                }
                            ).then(
                                function (coupons) {
                                    self.db.remove_all_coupon();
                                    self.db.add_coupons(coupons);
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
    });

    exports.Coupon = Backbone.Model.extend({
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
        set_coupon_data: function (coupon_data) {
            this.coupon_data = coupon_data;
        },
        get_coupon_data: function () {
            return this.coupon_data;
        },
        export_as_JSON: function () {
            return {
                name: this.get_coupon_data().name,
                sh_coupon_code: this.get_coupon_data().sh_coupon_code,
                sh_coupon_active: this.get_coupon_data().sh_coupon_active,
                sh_coupon_for: this.get_coupon_data().sh_coupon_for,
                sh_coupon_expiry_date: this.get_coupon_data().sh_coupon_expiry_date,
                sh_coupon_applicable_date: this.get_coupon_data().sh_coupon_applicable_date,
                sh_coupon_value: this.get_coupon_data().sh_coupon_value,
                sh_coupon_value_type: this.get_coupon_data().sh_coupon_value_type,
                sh_minimum_cart_amount: this.get_coupon_data().sh_minimum_cart_amount,
                max_discount: this.get_coupon_data().max_discount,
                sh_coupon_type: this.get_coupon_data().sh_coupon_type,
                sh_product_filter: this.get_coupon_data().sh_product_filter,
                uid: this.uid,
                sequence_number: this.sequence_number,
                sh_coupon_partner: this.get_coupon_data().sh_coupon_partner || false,
            };
        },
        export_for_printing: function () {
            var self = this;
        },
    });

    var CouponCollection = Backbone.Collection.extend({
        model: exports.Coupon,
    });

});
