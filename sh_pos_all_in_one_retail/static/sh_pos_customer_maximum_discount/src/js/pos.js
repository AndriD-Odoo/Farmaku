odoo.define('sh_pos_retail_customer_maximum_discount.pos', function (require) {
    'use strict';

    var models = require('point_of_sale.models')
    const ClientDetailsEdit = require('point_of_sale.ClientDetailsEdit')
    const ClientListScreen = require('point_of_sale.ClientListScreen')
    const ProductScreen = require('point_of_sale.ProductScreen')
    const Registries = require("point_of_sale.Registries")
    const { Gui } = require("point_of_sale.Gui");

    const ShClientListScreen = (ClientListScreen) =>
        class extends ClientListScreen {
            confirm() {
                var self = this;
                var Order = self.env.pos.get_order()
                var Client = this.state.selectedClient

                if (Client && Client.sh_enable_max_dic) {
                    var sh_total_after_dic = Order.get_total_with_tax()
                    var sh_product_total = Order.get_total_without_tax() + Order.get_total_discount()
                    var sh_customer_max_dis = Client.sh_maximum_discount
                    if (Client.sh_discount_type == "percentage") {
                        var sh_customer_discount_per = ((sh_product_total - sh_total_after_dic) * 100) / sh_product_total

                        if (sh_customer_discount_per > sh_customer_max_dis) {

                            var body = "Sorry, " + sh_customer_discount_per.toFixed(2) + "% discount is not allowed. Maximum discount for this customer is " + sh_customer_max_dis + "%";
                            Gui.showPopup('ErrorPopup', {
                                title: 'Exceed Discount Limit !',
                                body: body,
                            })
                        } else {
                            return super.confirm()
                        }

                    }
                    else {
                        var sh_customer_discount_fixed = Order.get_total_discount()

                        if (sh_customer_discount_fixed > sh_customer_max_dis) {

                            var body = "Sorry, " + sh_customer_discount_fixed.toFixed(2) + " discount is not allowed. Maximum discount for this customer is " + sh_customer_max_dis;
                            Gui.showPopup('ErrorPopup', {
                                title: 'Exceed Discount Limit !',
                                body: body,
                            })
                        } else {
                            return super.confirm()
                        }
                    }
                } else {
                    return super.confirm()
                }
            }
        }

    Registries.Component.extend(ClientListScreen, ShClientListScreen)

    const ShProductScren = (ProductScreen) =>
        class extends ProductScreen {
            _onClickPay() {
                var self = this;
                var Order = self.env.pos.get_order()
                if (self.env.pos.config.sh_pos_enable_customer_max_discount) {
                    if (Order && Order.get_client()) {
                        var Client = Order.get_client()
                        if (Client.sh_enable_max_dic) {
                            var sh_total_after_dic = Order.get_total_with_tax()
                            var sh_product_total = Order.get_total_without_tax() + Order.get_total_discount()
                            var sh_customer_max_dis = Client.sh_maximum_discount

                            if (Client.sh_discount_type == "percentage") {
                                var sh_customer_discount_per = ((sh_product_total - sh_total_after_dic) * 100) / sh_product_total
                                
                                if (sh_customer_discount_per > sh_customer_max_dis) {
                                    var body = "Sorry, " + sh_customer_discount_per.toFixed(2) + "% discount is not allowed. Maximum discount for this customer is " + sh_customer_max_dis + "%";
                                    Gui.showPopup('ErrorPopup', {
                                        title: 'Exceed Discount Limit !',
                                        body: body,
                                    })
                                }
                                else {
                                    super._onClickPay()
                                }
                            }
                            else {
                                var sh_customer_discount_fixed = Order.get_total_discount()

                                if (sh_customer_discount_fixed > sh_customer_max_dis) {
                                    var body = "Sorry, " + sh_customer_discount_fixed.toFixed(2) + " discount is not allowed. Maximum discount for this customer is " + sh_customer_max_dis;
                                    Gui.showPopup('ErrorPopup', {
                                        title: 'Exceed Discount Limit !',
                                        body: body,
                                    })
                                } else {
                                    super._onClickPay()
                                }
                            }
                        } else {
                            super._onClickPay()
                        }
                    } else {
                        super._onClickPay()
                    }
                }
                else {
                    super._onClickPay()
                }

            }
        }

    Registries.Component.extend(ProductScreen, ShProductScren)


    const ShClientDetailsADD = (ClientDetailsEdit) =>
        class extends ClientDetailsEdit {
            constructor() {
                super(...arguments);
            }
            mounted() {
                super.mounted()
                var self = this
                var detail_div = document.createElement('div')
                $(detail_div).addClass('client-detail sh_discount')
                var lable_span = document.createElement('span')
                $(lable_span).addClass('label')
                $(lable_span).text('Max Discount')
                $(detail_div).append(lable_span)
                var detail_input = document.createElement('input')
                $(detail_input).attr({ 'name': 'Discount', 'id': 'customer_discount', 'class': 'detail', 'value': 0.00 })

                var detail_div1 = document.createElement('div')
                $(detail_div1).addClass('client-detail sh_discount')
                var lable_span1 = document.createElement('span')
                $(lable_span1).addClass('label')
                $(detail_div1).append(lable_span1)
                $(lable_span1).text('Discount Type')
                var type_selection = document.createElement('select')
                $(type_selection).attr({ 'id': 'sh_discount_type' })
                var option = document.createElement('option')
                $(option).val('percentage')
                $(option).text('Percentage')
                var option1 = document.createElement('option')
                $(option1).val('fixed')
                $(option1).text('Fixed')


                if ($("#Set_customer_discount").is(":checked")) {
                    var value = this.props.partner.sh_maximum_discount
                    $(detail_input).attr({ 'name': 'Discount', 'id': 'customer_discount', 'class': 'detail', 'value': value })
                    $(detail_div).append(detail_input)

                    var type_val = this.props.partner.sh_discount_type
                    $(type_selection).append(option, option1)
                    $(type_selection).val(type_val).change()

                    $(detail_div1).append(type_selection)
                    $('.client-details-left').append(detail_div, detail_div1)

                }

                $("#Set_customer_discount").change(function () {
                    if ($("#Set_customer_discount").is(":checked")) {
                        var value = self.props.partner.sh_maximum_discount
                        $(detail_input).attr({ 'name': 'Discount', 'id': 'customer_discount', 'class': 'detail', 'value': value })
                        var type_val = self.props.partner.sh_discount_type
                        $(type_selection).val(type_val).change()

                        $(detail_div).append(detail_input)
                        $(type_selection).append(option, option1)
                        $(detail_div1).append(type_selection)

                        $('.client-details-left').append(detail_div, detail_div1)

                        $('.client-details-left').append()
                    } else {
                        $('.client-details-left').find('.sh_discount').remove()
                    }
                })

            }
            saveChanges() {
                this.changes['sh_enable_max_dic'] = $("#Set_customer_discount").is(":checked")
                if ($('#customer_discount').val()) {
                    this.changes['sh_maximum_discount'] = $('#customer_discount').val()
                }
                if ($('#sh_discount_type').val()) {
                    this.changes['sh_discount_type'] = $('#sh_discount_type').val()
                }

                super.saveChanges()
            }
        }
    Registries.Component.extend(ClientDetailsEdit, ShClientDetailsADD);

});