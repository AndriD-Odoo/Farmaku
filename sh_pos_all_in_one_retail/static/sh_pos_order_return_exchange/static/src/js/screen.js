odoo.define("sh_pos_order_list.screen_exchange", function (require) {
    "use strict";

    const { debounce } = owl.utils;
    const PosComponent = require("point_of_sale.PosComponent");
    const Registries = require("point_of_sale.Registries");
    const { useListener } = require("web.custom_hooks");
    const rpc = require("web.rpc");
    var core = require("web.core");
    var framework = require("web.framework");
    var QWeb = core.qweb;
    const PaymentScreen = require("point_of_sale.PaymentScreen");
    var field_utils = require("web.field_utils");
    const OrderListScreen = require("sh_pos_order_list.screen");

    const PosOrderListScreen = (OrderListScreen) =>
        class extends OrderListScreen {
            sh_paid_order_filter() {
                if ($('.sh_paid_order').hasClass('highlight')) {
                    this.filter_by_paid_order = false
                    $('.sh_paid_order').removeClass('highlight')
                } else {
                    this.filter_by_paid_order = true
                    this.filter_by_posted_order = false
                    this.filter_by_invoice_order = false
                    $('.sh_paid_order').addClass('highlight')
                    $('.sh_posted_order').removeClass('highlight')
                    $('.sh_invoiced_order').removeClass('highlight')
                }
                $(".sh_pagination").pagination("selectPage", 1);
                this.render()
            }
            sh_posted_order_filter() {
                if ($('.sh_posted_order').hasClass('highlight')) {
                    this.filter_by_posted_order = false
                    $('.sh_posted_order').removeClass('highlight')
                } else {
                    this.filter_by_posted_order = true
                    this.filter_by_paid_order = false
                    this.filter_by_invoice_order = false
                    $('.sh_posted_order').addClass('highlight')
                    $('.sh_paid_order').removeClass('highlight')
                    $('.sh_invoiced_order').removeClass('highlight')
                }
                $(".sh_pagination").pagination("selectPage", 1);
                this.render()
            }
            sh_invoiced_order_filter() {
                if ($('.sh_invoiced_order').hasClass('highlight')) {
                    this.filter_by_invoice_order = false
                    $('.sh_invoiced_order').removeClass('highlight')
                } else {
                    this.filter_by_invoice_order = true
                    this.filter_by_paid_order = false
                    this.filter_by_posted_order = false
                    $('.sh_invoiced_order').addClass('highlight')
                    $('.sh_posted_order').removeClass('highlight')
                    $('.sh_paid_order').removeClass('highlight')
                }
                $(".sh_pagination").pagination("selectPage", 1);
                this.render()
            }
            get_order_by_state(name) {
                var self = this;
                if($('.return_order_button').hasClass('highlight')){
                    var templates = _.filter(self.env.pos.db.all_return_order, function (template) {
                        if (template["state"] && template["state"].indexOf(name) > -1) {
                            return true;
                        } else {
                            return false;
                        }
                    });
                    if(this.env.pos.config.sh_load_order_by && this.env.pos.config.sh_load_order_by == 'all'){                    	
                          return templates;
                    }else if (self.env.pos.config.sh_load_order_by == "session_wise") {
                          if (self.env.pos.config.sh_session_wise_option == "current_session") {
                              var display_order = []
                              display_order = templates.filter(function (order) {
                                  return order.session_id[0] == self.env.pos.pos_session.id;
                              });                  
                              return display_order;
                          }else if (self.env.pos.config.sh_session_wise_option == "last_no_session") {
                              if (self.env.pos.config.sh_last_no_session != 0) {
                                  var filter_order = []
                                  filter_order = self.env.pos.get_last_session_order(templates);
                                  return filter_order
                              }else{
                                  return []
                              }
                          }
                    }else if (self.env.pos.config.sh_load_order_by == "day_wise") {
                          if (self.env.pos.config.sh_day_wise_option == "current_day") {                    		
                              return templates.filter(function (order) {
                                  var date = new Date();
                                  var today_date = date.getFullYear() + "-" + ("0" + (date.getMonth() + 1)).slice(-2) + "-" + ("0" + date.getDate()).slice(-2);
                                  return order.date_order.split(" ")[0] === today_date;
                              });
                              
                          } else if (self.env.pos.config.sh_day_wise_option == "last_no_day") {
                              if (self.env.pos.config.sh_last_no_days != 0) {
                                  return templates.filter(function (order) {
                                      var date = new Date();
                                      var last = new Date(date.getTime() - self.env.pos.config.sh_last_no_days * 24 * 60 * 60 * 1000);
                                      var last = last.getFullYear() + "-" + ("0" + (last.getMonth() + 1)).slice(-2) + "-" + ("0" + last.getDate()).slice(-2);
                                      var today_date = date.getFullYear() + "-" + ("0" + (date.getMonth() + 1)).slice(-2) + "-" + ("0" + date.getDate()).slice(-2);
                                      
                                      var formated_last_date = field_utils.format.datetime(moment(last), {}, { timezone: false });
                                      var formated_today_date = field_utils.format.datetime(moment(today_date), {}, { timezone: false });
                                      
                                      if(order.date_order.split(" ")[0] > last && order.date_order.split(" ")[0] <= today_date){
                                          return order
                                      }else if(order.date_order.split(" ")[0] > formated_last_date && order.date_order.split(" ")[0] <= formated_today_date){
                                          return order
                                      }
                                  });
                              }else{
                                  return []
                              }
                          }                       	
                    }
                    
                }else{
                    var templates = _.filter(self.env.pos.db.all_non_return_order, function (template) {
                        if (template["state"] && template["state"].indexOf(name) > -1) {
                            return true;
                        } else {
                            return false;
                        }
                    });
                                    
                    if(this.env.pos.config.sh_load_order_by && this.env.pos.config.sh_load_order_by == 'all'){                    	
                          return templates;
                    }else if (self.env.pos.config.sh_load_order_by == "session_wise") {
                          if (self.env.pos.config.sh_session_wise_option == "current_session") {
                              var display_order = []
                              display_order = templates.filter(function (order) {
                                  return order.session_id[0] == self.env.pos.pos_session.id;
                              });                  
                              return display_order;
                          }else if (self.env.pos.config.sh_session_wise_option == "last_no_session") {
                              if (self.env.pos.config.sh_last_no_session != 0) {
                                  var filter_order = []
                                  filter_order = self.env.pos.get_last_session_order(templates);
                                  return filter_order
                              }else{
                                  return []
                              }
                          }
                    }else if (self.env.pos.config.sh_load_order_by == "day_wise") {
                          if (self.env.pos.config.sh_day_wise_option == "current_day") {                    		
                              return templates.filter(function (order) {
                                  var date = new Date();
                                  var today_date = date.getFullYear() + "-" + ("0" + (date.getMonth() + 1)).slice(-2) + "-" + ("0" + date.getDate()).slice(-2);
                                  return order.date_order.split(" ")[0] === today_date;
                              });
                              
                          } else if (self.env.pos.config.sh_day_wise_option == "last_no_day") {
                              if (self.env.pos.config.sh_last_no_days != 0) {
                                  return templates.filter(function (order) {
                                      var date = new Date();
                                      var last = new Date(date.getTime() - self.env.pos.config.sh_last_no_days * 24 * 60 * 60 * 1000);
                                      var last = last.getFullYear() + "-" + ("0" + (last.getMonth() + 1)).slice(-2) + "-" + ("0" + last.getDate()).slice(-2);
                                      var today_date = date.getFullYear() + "-" + ("0" + (date.getMonth() + 1)).slice(-2) + "-" + ("0" + date.getDate()).slice(-2);
                                      
                                      var formated_last_date = field_utils.format.datetime(moment(last), {}, { timezone: false });
                                      var formated_today_date = field_utils.format.datetime(moment(today_date), {}, { timezone: false });
                                      
                                      if(order.date_order.split(" ")[0] > last && order.date_order.split(" ")[0] <= today_date){
                                          return order
                                      }else if(order.date_order.split(" ")[0] > formated_last_date && order.date_order.split(" ")[0] <= formated_today_date){
                                          return order
                                      }
                                  });
                              }else{
                                  return []
                              }
                          }                       	
                    }
                }
            }
            get_order_by_posted_order(name) {
                var self = this;
                return _.filter(this.get_order_by_state('done'), function (template) {
                    if (template.name.indexOf(name) > -1) {
                        return true;
                    } else if (template['pos_reference'] && template["pos_reference"].indexOf(name) > -1) {
                        return true;
                    } else if (template["partner_id"] && template["partner_id"][1] && template["partner_id"][1].toLowerCase().indexOf(name) > -1) {
                        return true;
                    } else if (template["date_order"] && template["date_order"].indexOf(name) > -1) {
                        return true;
                    } else {
                        return false;
                    }
                });
            }
            get_order_by_paid_order(name) {
                var self = this;
                return _.filter(this.get_order_by_state('paid'), function (template) {
                    if (template.name.indexOf(name) > -1) {
                        return true;
                    } else if (template['pos_reference'] && template["pos_reference"].indexOf(name) > -1) {
                        return true;
                    } else if (template["partner_id"] && template["partner_id"][1] && template["partner_id"][1].toLowerCase().indexOf(name) > -1) {
                        return true;
                    } else if (template["date_order"] && template["date_order"].indexOf(name) > -1) {
                        return true;
                    } else {
                        return false;
                    }
                });
            }
            get_order_by_invoiced_order(name) {
                var self = this;
                return _.filter(this.get_order_by_state('invoiced'), function (template) {
                    if (template.name.indexOf(name) > -1) {
                        return true;
                    } else if (template['pos_reference'] && template["pos_reference"].indexOf(name) > -1) {
                        return true;
                    } else if (template["partner_id"] && template["partner_id"][1] && template["partner_id"][1].toLowerCase().indexOf(name) > -1) {
                        return true;
                    } else if (template["date_order"] && template["date_order"].indexOf(name) > -1) {
    
                        return true;
                    } else {
                        return false;
                    }
                });
            }
            get_order_by_name(name) {
                var self = this;
                if (self.return_filter) {
                    return _.filter(self.env.pos.db.all_return_order, function (template) {
                        if (template.name.indexOf(name) > -1) {
                            return true;
                        } else if (template["pos_reference"].indexOf(name) > -1) {
                            return true;
                        } else if (template["partner_id"] && template["partner_id"][1] && template["partner_id"][1].toLowerCase().indexOf(name) > -1) {
                            return true;
                        } else if (template["date_order"].indexOf(name) > -1) {
                            return true;
                        } else {
                            return false;
                        }
                    });
                } else {
                    return _.filter(self.env.pos.db.all_non_return_order, function (template) {
                        if (template.name.indexOf(name) > -1) {
                            return true;
                        } else if (template["pos_reference"].indexOf(name) > -1) {
                            return true;
                        } else if (template["partner_id"] && template["partner_id"][1] && template["partner_id"][1].toLowerCase().indexOf(name) > -1) {
                            return true;
                        } else if (template["date_order"].indexOf(name) > -1) {
                            return true;
                        } else {
                            return false;
                        }
                    });
                }

            }
            get posorderdetailhistory() {
                return super.posorderdetailhistory()
            }
            updateOrderList(event) {
                this.state.query = event.target.value;

                if (event.code === "Enter") {
                    const serviceorderlistcontents = this.posreturnorderdetail;
                    if (serviceorderlistcontents.length === 1) {
                        this.state.selectedQuotation = serviceorderlistcontents[0];
                    }
                } else {
                    this.render();
                }
            }
            get posreturnorderdetail() {
                var self = this;

                if (this.state.query && this.state.query.trim() !== "") {
                    var templates = this.get_order_by_name(this.state.query.trim());
                    return templates;
                } else {
                    self.order_no_return = [];
                    self.return_order = [];
                    _.each(self.all_order, function (order) {
                        if ((order.is_return_order && order.return_status && order.return_status != "nothing_return") || (!order.is_return_order && !order.is_exchange_order)) {
                            self.order_no_return.push(order);
                        } else {
                            self.return_order.push(order);
                        }
                    });

                    if (!self.return_filter) {
                        return self.order_no_return;
                    } else {
                        return self.return_order;
                    }
                }
            }
            return_order_filter() {
                var self = this;

                if (self.env.pos.get_order().is_client_order_filter) {
                    if (!$(".return_order_button").hasClass("highlight")) {
                        self.order_no_return = [];
                        $(".return_order_button").addClass("highlight");
                        self.return_filter = true;
                        $('.sh_pagination').pagination('updateItems', Math.ceil(self.env.pos.db.display_return_order.length / self.env.pos.config.sh_how_many_order_per_page));
                        $('.sh_pagination').pagination('selectPage', 1);
                    } else {
                        self.return_order = [];
                        $(".return_order_button").removeClass("highlight");
                        self.return_filter = false;
                        $('.sh_pagination').pagination('updateItems', Math.ceil(self.env.pos.db.display_non_return_order.length / self.env.pos.config.sh_how_many_order_per_page));
                        $('.sh_pagination').pagination('selectPage', 1);
                    }
                } else {
                    var previous_order = self.env.pos.db.all_order;
                    if (!$(".return_order_button").hasClass("highlight")) {
                        self.order_no_return = [];
                        $(".return_order_button").addClass("highlight");

                        self.return_filter = true;
                        $('.sh_pagination').pagination('updateItems', Math.ceil(self.env.pos.db.all_return_order.length / self.env.pos.config.sh_how_many_order_per_page));
                        $('.sh_pagination').pagination('selectPage', 1);
                    } else {
                        self.return_order = [];
                        $(".return_order_button").removeClass("highlight");
                        self.return_filter = false;
                        $('.sh_pagination').pagination('updateItems', Math.ceil(self.env.pos.db.all_non_return_order.length / self.env.pos.config.sh_how_many_order_per_page));
                        $('.sh_pagination').pagination('selectPage', 1);
                    }
                }


                self.render();
            }
            async exchange_pos_order(event) {
                var self = this;
                self.env.pos.is_return = false;
                self.env.pos.is_exchange = true;

                var order_line = [];


                var order_id = $(event.currentTarget.closest("tr")).attr("data-order-id");
                var order_data;
                if (order_id) {
                    order_data = self.env.pos.db.order_by_id[order_id];
                    await self.rpc({
                        model: 'pos.order',
                        domain: [['id', '=',order_id]],
                        method: 'search_read',
                    }).then(function (dataorder_id) { 
                        if(!self.env.pos.db.order_by_id[order_id]){
                            self.env.pos.db.order_by_id[order_id] = dataorder_id[0]
                        }
                        order_data = dataorder_id[0]
                    }).catch(function () {
                        return 
                    })
                    if (!order_data) {
                        order_data = self.env.pos.db.order_by_uid[order_id];
                    }
                    // if (!order_data) {
                    //     order_id = $(event.currentTarget).attr("data-id");
                    //     if (order_id) {
                    //         order_data = self.env.pos.db.order_by_uid[order_id];
                    //     }
                    // }
                }
                if (!order_id) {
                    order_id = $(event.currentTarget).attr("data-id");
                    if (order_id) {
                        order_data = self.env.pos.db.order_by_uid[order_id];
                    }
                }

                if (order_data && order_data.lines) {
                    _.each(order_data.lines, function (each_order_line) {
                        var line_data = self.env.pos.db.order_line_by_id[each_order_line];
                        if (!line_data) {
                            line_data = self.env.pos.db.order_line_by_uid[each_order_line[2].sh_line_id];
                        }
                        if (line_data) {
                            order_line.push(line_data);
                        }
                    });
                }

                let { confirmed, payload } = this.showPopup("TemplateReturnOrderPopupWidget", { lines: order_line, order: order_id });
                if (confirmed) {
                } else {
                    return;
                }
            }
            async return_pos_order(event) {
                var self = this;
                self.env.pos.is_return = true;
                self.env.pos.is_exchange = false;

                var order_id = $(event.currentTarget.closest("tr")).attr("data-order-id");

                var order_data;
                if (order_id) {
                    order_data = self.env.pos.db.order_by_id[order_id];
                    await self.rpc({
                        model: 'pos.order',
                        domain: [['id', '=',order_id]],
                        method: 'search_read',
                    }).then(function (dataorder_id) { 
                        if(!self.env.pos.db.order_by_id[order_id]){
                            self.env.pos.db.order_by_id[order_id] = dataorder_id[0]
                        }
                        order_data = dataorder_id[0]
                    }).catch(function () {
                        return 
                    })
                    if (!order_data) {
                        order_data = self.env.pos.db.order_by_uid[order_id];
                    }
                    // if (!order_data) {
                    //     order_id = $(event.currentTarget).attr("data-id");
                    //     if (order_id) {
                    //         order_data = self.env.pos.db.order_by_uid[order_id];
                    //     }
                    // }
                }
                if (!order_id) {
                    order_id = $(event.currentTarget).attr("data-id");
                    if (order_id) {
                        order_data = self.env.pos.db.order_by_uid[order_id];
                    }
                }

                var order_line = [];

                if (order_data && order_data.lines) {
                    _.each(order_data.lines, function (each_order_line) {
                        var line_data = self.env.pos.db.order_line_by_id[each_order_line];
                        if (!line_data) {
                            line_data = self.env.pos.db.order_line_by_uid[each_order_line[2].sh_line_id];
                        }
                        if (line_data) {
                            order_line.push(line_data);
                        }
                    });
                }
                let { confirmed, payload } = this.showPopup("TemplateReturnOrderPopupWidget", { lines: order_line, order: order_id });
                if (confirmed) {
                } else {
                    return;
                }
            }

            get posorderdetail() {
                var self = this;
                if(self.all_order){  
                    self.order_no_return = []
                    self.return_order = []
                    _.each(self.all_order, function (order) {
                        if ((order.is_return_order && order.return_status && order.return_status != "nothing_return") || (!order.is_return_order && !order.is_exchange_order)) {
                            self.order_no_return.push(order);
                        } else {
                            self.return_order.push(order);
                        }
                    });
                }
                if (!self.return_filter) {
                    if (this.filter_by_paid_order) {
                        if (this.state.query && this.state.query.trim() !== "") {
                          var templates = this.get_order_by_paid_order(this.state.query.trim());
                          $(".sh_pagination").pagination("updateItems", Math.ceil(templates.length / self.env.pos.config.sh_how_many_order_per_page));
                          var current_page = $(".sh_pagination").find('.active').text();
          
                              var showFrom = parseInt(self.env.pos.config.sh_how_many_order_per_page) * (parseInt(current_page) - 1);;
                              var showTo = showFrom + parseInt(self.env.pos.config.sh_how_many_order_per_page);
                              templates = templates.slice(showFrom, showTo);
                              return templates;
                        } else {
                            var templates = this.get_order_by_state('paid');
                            $(".sh_pagination").pagination("updateItems", Math.ceil(templates.length / self.env.pos.config.sh_how_many_order_per_page));
        
                            var current_page = $(".sh_pagination").find('.active').text();
        
                            var showFrom = parseInt(self.env.pos.config.sh_how_many_order_per_page) * (parseInt(current_page) - 1);
                            var showTo = showFrom + parseInt(self.env.pos.config.sh_how_many_order_per_page);
                            templates = templates.slice(showFrom, showTo);
                            
                            return templates;
                        }
                    } else if (this.filter_by_invoice_order) {
                        if (this.state.query && this.state.query.trim() !== "") {
                          var templates = this.get_order_by_invoiced_order(this.state.query.trim());
                          $(".sh_pagination").pagination("updateItems", Math.ceil(templates.length / self.env.pos.config.sh_how_many_order_per_page));
                          var current_page = $(".sh_pagination").find('.active').text();
                          var showFrom = parseInt(self.env.pos.config.sh_how_many_order_per_page) * (parseInt(current_page) - 1);;
                          var showTo = showFrom + parseInt(self.env.pos.config.sh_how_many_order_per_page);
                          templates = templates.slice(showFrom, showTo);
                          return templates;
                        } else {
                            var templates = this.get_order_by_state('invoiced');
    
                            $(".sh_pagination").pagination("updateItems", Math.ceil(templates.length / self.env.pos.config.sh_how_many_order_per_page));
    
                            var current_page = $(".sh_pagination").find('.active').text();
                            var showFrom = parseInt(self.env.pos.config.sh_how_many_order_per_page) * (parseInt(current_page) - 1);
                            var showTo = showFrom + parseInt(self.env.pos.config.sh_how_many_order_per_page);
                            templates = templates.slice(showFrom, showTo);
                            
                            return templates;
                        }
      
                    } else if (this.filter_by_posted_order) {
                        if (this.state.query && this.state.query.trim() !== "") {
                            var templates = this.get_order_by_posted_order(this.state.query.trim());
                            $(".sh_pagination").pagination("updateItems", Math.ceil(templates.length / self.env.pos.config.sh_how_many_order_per_page));
                            var current_page = $(".sh_pagination").find('.active').text();
                            var showFrom = parseInt(self.env.pos.config.sh_how_many_order_per_page) * (parseInt(current_page) - 1);;
                            var showTo = showFrom + parseInt(self.env.pos.config.sh_how_many_order_per_page);
                            templates = templates.slice(showFrom, showTo);
                            return templates
                            
                        } else {
                            var templates = this.get_order_by_state('done');
                            $(".sh_pagination").pagination("updateItems", Math.ceil(templates.length / self.env.pos.config.sh_how_many_order_per_page));
        
                            var current_page = $(".sh_pagination").find('.active').text();
                            var showFrom = parseInt(self.env.pos.config.sh_how_many_order_per_page) * (parseInt(current_page) - 1);
                            var showTo = showFrom + parseInt(self.env.pos.config.sh_how_many_order_per_page);
                            templates = templates.slice(showFrom, showTo);
                            return templates
                        }
                    }else{
                        if ($(".sh_pagination") && $(".sh_pagination").length) {
                            var templates = self.env.pos.db.all_non_return_order
                            if(this.env.pos.config.sh_load_order_by && this.env.pos.config.sh_load_order_by == 'all'){                    	
                                $(".sh_pagination").pagination("updateItems", Math.ceil(self.env.pos.db.all_non_return_order.length / self.env.pos.config.sh_how_many_order_per_page));
                            }else if (self.env.pos.config.sh_load_order_by == "session_wise") {
                                if (self.env.pos.config.sh_session_wise_option == "current_session") {                    		
                                    var display_order = self.env.pos.db.all_non_return_order.filter(function (order) {
                                        return order.session_id[0] == self.env.pos.pos_session.id;
                                    });                
                                    $(".sh_pagination").pagination("updateItems", Math.ceil(display_order.length / self.env.pos.config.sh_how_many_order_per_page));
                                }else if (self.env.pos.config.sh_session_wise_option == "last_no_session") {
                                    if (self.env.pos.config.sh_last_no_session != 0) {
                                        var filter_order = []
                                        filter_order = self.env.pos.get_last_session_order(templates);
                                        $(".sh_pagination").pagination("updateItems", Math.ceil(filter_order.length / self.env.pos.config.sh_how_many_order_per_page));
                                    }else{
                                        $(".sh_pagination").pagination("updateItems", 1);
                                        return []
                                    }
                                }
                            }else if (self.env.pos.config.sh_load_order_by == "day_wise") {
                                if (self.env.pos.config.sh_day_wise_option == "current_day") {                    		
                                    var display_order = templates.filter(function (order) {
                                        var date = new Date();
                                        var today_date = date.getFullYear() + "-" + ("0" + (date.getMonth() + 1)).slice(-2) + "-" + ("0" + date.getDate()).slice(-2);
                                        return order.date_order.split(" ")[0] === today_date;
                                    });
                                    $(".sh_pagination").pagination("updateItems", Math.ceil(display_order.length / self.env.pos.config.sh_how_many_order_per_page));
                                } else if (self.env.pos.config.sh_day_wise_option == "last_no_day") {
                                    if (self.env.pos.config.sh_last_no_days != 0) {
                                        var display_order = templates.filter(function (order) {
                                            var date = new Date();
                                            var last = new Date(date.getTime() - self.env.pos.config.sh_last_no_days * 24 * 60 * 60 * 1000);
                                            var last = last.getFullYear() + "-" + ("0" + (last.getMonth() + 1)).slice(-2) + "-" + ("0" + last.getDate()).slice(-2);
                                            var today_date = date.getFullYear() + "-" + ("0" + (date.getMonth() + 1)).slice(-2) + "-" + ("0" + date.getDate()).slice(-2);
                                            
                                            var formated_last_date = field_utils.format.datetime(moment(last), {}, { timezone: false });
                                            var formated_today_date = field_utils.format.datetime(moment(today_date), {}, { timezone: false });
                                            
                                            if(order.date_order.split(" ")[0] > last && order.date_order.split(" ")[0] <= today_date){
                                                return order
                                            }else if(order.date_order.split(" ")[0] > formated_last_date && order.date_order.split(" ")[0] <= formated_today_date){
                                                return order
                                            }                                            
                                        });
                                      $(".sh_pagination").pagination("updateItems", Math.ceil(display_order.length / self.env.pos.config.sh_how_many_order_per_page));
                                    }else{
                                        $(".sh_pagination").pagination("updateItems", 1);
                                        return []
                                    }
                                }                       	
                            }
                        }else{
                            return []
                        }
                      
                      
                        if (this.state.query && this.state.query.trim() !== "") {
                            var templates = this.get_order_by_name(this.state.query.trim());
                            $(".sh_pagination").pagination("updateItems", Math.ceil(templates.length / self.env.pos.config.sh_how_many_order_per_page));
                            var pageNumber = $(".sh_pagination").pagination("getCurrentPage");
                            var showFrom = parseInt(self.env.pos.config.sh_how_many_order_per_page) * (parseInt(pageNumber) - 1);
                            var showTo = showFrom + parseInt(self.env.pos.config.sh_how_many_order_per_page);
                            templates = templates.slice(showFrom, showTo);
                            return templates;
                        }else{
                            
                            if (self.env.pos.get_order().is_client_order_filter) {
                                return self.env.pos.db.display_all_order;
                            } else {
                                return self.order_no_return;
                            }
                            // return self.order_no_return;
                        }
                    } 
                  
                }else{
                    if (this.filter_by_paid_order) {
                        if (this.state.query && this.state.query.trim() !== "") {
                            var templates = this.get_order_by_paid_order(this.state.query.trim());
                            $(".sh_pagination").pagination("updateItems", Math.ceil(templates.length / self.env.pos.config.sh_how_many_order_per_page));
                            var current_page = $(".sh_pagination").find('.active').text();
        
                            var showFrom = parseInt(self.env.pos.config.sh_how_many_order_per_page) * (parseInt(current_page) - 1);;
                            var showTo = showFrom + parseInt(self.env.pos.config.sh_how_many_order_per_page);
                            templates = templates.slice(showFrom, showTo);
                            return templates;
                            
                        } else {
                            var templates = this.get_order_by_state('paid');
        
                            $(".sh_pagination").pagination("updateItems", Math.ceil(templates.length / self.env.pos.config.sh_how_many_order_per_page));
        
                            var current_page = $(".sh_pagination").find('.active').text();
        
                            var showFrom = parseInt(self.env.pos.config.sh_how_many_order_per_page) * (parseInt(current_page) - 1);
                            var showTo = showFrom + parseInt(self.env.pos.config.sh_how_many_order_per_page);
                            templates = templates.slice(showFrom, showTo);
                            return templates
                        }
                    } else if (this.filter_by_invoice_order) {
                        if (this.state.query && this.state.query.trim() !== "") {
                            var templates = this.get_order_by_invoiced_order(this.state.query.trim());
                            $(".sh_pagination").pagination("updateItems", Math.ceil(templates.length / self.env.pos.config.sh_how_many_order_per_page));
                            var current_page = $(".sh_pagination").find('.active').text();
                            var showFrom = parseInt(self.env.pos.config.sh_how_many_order_per_page) * (parseInt(current_page) - 1);;
                            var showTo = showFrom + parseInt(self.env.pos.config.sh_how_many_order_per_page);
                            templates = templates.slice(showFrom, showTo);
                            return templates;
                          
                        } else {
                            var templates = this.get_order_by_state('invoiced');
        
                            $(".sh_pagination").pagination("updateItems", Math.ceil(templates.length / self.env.pos.config.sh_how_many_order_per_page));
        
                            var current_page = $(".sh_pagination").find('.active').text();
                            var showFrom = parseInt(self.env.pos.config.sh_how_many_order_per_page) * (parseInt(current_page) - 1);
                            var showTo = showFrom + parseInt(self.env.pos.config.sh_how_many_order_per_page);
                            templates = templates.slice(showFrom, showTo);
        
                            return templates
                        }
      
                    } else if (this.filter_by_posted_order) {
                        if (this.state.query && this.state.query.trim() !== "") {
                            var templates = this.get_order_by_posted_order(this.state.query.trim());
                            $(".sh_pagination").pagination("updateItems", Math.ceil(templates.length / self.env.pos.config.sh_how_many_order_per_page));
                            var current_page = $(".sh_pagination").find('.active').text();
                            var showFrom = parseInt(self.env.pos.config.sh_how_many_order_per_page) * (parseInt(current_page) - 1);;
                            var showTo = showFrom + parseInt(self.env.pos.config.sh_how_many_order_per_page);
                            templates = templates.slice(showFrom, showTo);
                            return templates
                            
                        } else {
                            var templates = this.get_order_by_state('done');
        
                            $(".sh_pagination").pagination("updateItems", Math.ceil(templates.length / self.env.pos.config.sh_how_many_order_per_page));
        
                            var current_page = $(".sh_pagination").find('.active').text();
                            var showFrom = parseInt(self.env.pos.config.sh_how_many_order_per_page) * (parseInt(current_page) - 1);
                            var showTo = showFrom + parseInt(self.env.pos.config.sh_how_many_order_per_page);
                            templates = templates.slice(showFrom, showTo);
                            
                            return templates;
                        }
                    }else{
                      var templates = self.env.pos.db.all_return_order;
                      if(this.env.pos.config.sh_load_order_by && this.env.pos.config.sh_load_order_by == 'all'){                    	
                          $(".sh_pagination").pagination("updateItems", Math.ceil(templates.length / self.env.pos.config.sh_how_many_order_per_page));
                        }else if (self.env.pos.config.sh_load_order_by == "session_wise") {
                            if (self.env.pos.config.sh_session_wise_option == "current_session") {                    		
                                var display_order = self.env.pos.db.all_return_order.filter(function (order) {
                                    return order.session_id[0] == self.env.pos.pos_session.id;
                                });                
                                $(".sh_pagination").pagination("updateItems", Math.ceil(display_order.length / self.env.pos.config.sh_how_many_order_per_page));
                            }else if (self.env.pos.config.sh_session_wise_option == "last_no_session") {
                                if (self.env.pos.config.sh_last_no_session != 0) {
                                    var filter_order = []
                                    filter_order = self.env.pos.get_last_session_order(templates);
                                    $(".sh_pagination").pagination("updateItems", Math.ceil(filter_order.length / self.env.pos.config.sh_how_many_order_per_page));
                                    // return filter_order
                                }else{
                                    $(".sh_pagination").pagination("updateItems", 1);
                                    return []
                                }
                            }
                        }else if (self.env.pos.config.sh_load_order_by == "day_wise") {
                            if (self.env.pos.config.sh_day_wise_option == "current_day") {                    		
                                var display_order = templates.filter(function (order) {
                                    var date = new Date();
                                    var today_date = date.getFullYear() + "-" + ("0" + (date.getMonth() + 1)).slice(-2) + "-" + ("0" + date.getDate()).slice(-2);
                                    return order.date_order.split(" ")[0] === today_date;
                                });
                                $(".sh_pagination").pagination("updateItems", Math.ceil(display_order.length / self.env.pos.config.sh_how_many_order_per_page));
                            } else if (self.env.pos.config.sh_day_wise_option == "last_no_day") {
                                if (self.env.pos.config.sh_last_no_days != 0) {
                                    var display_order = templates.filter(function (order) {
                                        var date = new Date();
                                        var last = new Date(date.getTime() - self.env.pos.config.sh_last_no_days * 24 * 60 * 60 * 1000);
                                        var last = last.getFullYear() + "-" + ("0" + (last.getMonth() + 1)).slice(-2) + "-" + ("0" + last.getDate()).slice(-2);
                                        var today_date = date.getFullYear() + "-" + ("0" + (date.getMonth() + 1)).slice(-2) + "-" + ("0" + date.getDate()).slice(-2);
                                        
                                        var formated_last_date = field_utils.format.datetime(moment(last), {}, { timezone: false });
                                        var formated_today_date = field_utils.format.datetime(moment(today_date), {}, { timezone: false });
                                        
                                        if(order.date_order.split(" ")[0] > last && order.date_order.split(" ")[0] <= today_date){
                                            return order
                                        }else if(order.date_order.split(" ")[0] > formated_last_date && order.date_order.split(" ")[0] <= formated_today_date){
                                            return order
                                        }                                        
                                    });
                                  $(".sh_pagination").pagination("updateItems", Math.ceil(display_order.length / self.env.pos.config.sh_how_many_order_per_page));
                                }else{
                                    $(".sh_pagination").pagination("updateItems", 1);
                                    return []
                                }
                            }                       	
                        }
                      return self.return_order;
                  }
                }
            }


            mounted() {
                var self = this;
                if (self.env.pos.get_order().is_client_order_filter) {
                    $(".sh_pagination").pagination({
                        pages: 100,
                        displayedPages: 1,
                        edges: 1,
                        cssStyle: "light-theme",
                        showPageNumbers: false,
                        showNavigator: true,
                        onPageClick: function (pageNumber) {

                            self.env.pos.db.display_return_order = []
                            self.env.pos.db.display_non_return_order = []
                            var showFrom = parseInt(self.env.pos.config.sh_how_many_order_per_page) * (parseInt(pageNumber) - 1);
                            var showTo = showFrom + parseInt(self.env.pos.config.sh_how_many_order_per_page);

                            _.each(self.env.pos.db.all_display_order_temp, function (each_order) {
                                if (each_order) {
                                    if (each_order.is_return_order) {
                                        self.env.pos.db.display_return_order.push(each_order)
                                    } else {
                                        self.env.pos.db.display_non_return_order.push(each_order)
                                    }
                                }
                            })

                            if (self.return_filter) {
                                self.env.pos.db.display_all_order = self.env.pos.db.display_return_order.slice(showFrom, showTo)
                            } else {
                                self.env.pos.db.display_all_order = self.env.pos.db.display_non_return_order.slice(showFrom, showTo)
                            }
                            self.render()
                        }
                    });

                } else {
                    $(".sh_pagination").pagination({
                        pages: 100,
                        displayedPages: 1,
                        edges: 1,
                        cssStyle: "light-theme",
                        showPageNumbers: false,
                        showNavigator: true,
                        onPageClick: function (pageNumber) {

                            try {
                                if (!self.return_filter) {

                                    rpc.query({
                                        model: "pos.order",
                                        method: "search_return_order",
                                        args: [self.env.pos.config, pageNumber + 1]
                                    }).then(function (orders) {
                                        if (orders) {
                                            if (orders['order'].length == 0) {
                                                $($('.next').parent()).addClass('disabled')
                                                $(".next").replaceWith(function () {
                                                    $("<span class='current next'>Next</span>");
                                                });
                                            }
                                        }

                                    }).catch(function (reason) {

                                    });

                                    rpc.query({
                                        model: "pos.order",
                                        method: "search_return_order",
                                        args: [self.env.pos.config, pageNumber]
                                    }).then(function (orders) {
                                        self.env.pos.db.all_order = [];
                                        self.env.pos.db.order_by_id = {};

                                        if (orders) {
                                            if (orders['order']) {
                                                self.env.pos.db.all_orders(orders['order']);
                                            }
                                            if (orders['order_line']) {
                                                self.env.pos.db.all_orders_line(orders['order_line']);
                                            }
                                        }
                                        self.all_order = self.env.pos.db.all_order;

                                        self.render()
                                    }).catch(function (reason) {
                                        var showFrom = parseInt(self.env.pos.config.sh_how_many_order_per_page) * (parseInt(pageNumber) - 1)
                                        var showTo = showFrom + parseInt(self.env.pos.config.sh_how_many_order_per_page)
                                        self.env.pos.db.all_order = self.env.pos.db.all_non_return_order.slice(showFrom, showTo)
                                        self.env.pos.db.all_display_order = self.env.pos.db.all_order;
                                        self.all_order = self.env.pos.db.all_order;
                                        self.render()
                                    });

                                } else {
                                    rpc.query({
                                        model: "pos.order",
                                        method: "search_return_exchange_order",
                                        args: [self.env.pos.config, pageNumber + 1]
                                    }).then(function (orders) {
                                        if (orders) {
                                            if (orders['order'].length == 0) {
                                                $($('.next').parent()).addClass('disabled')
                                                $(".next").replaceWith(function () {
                                                    $("<span class='current next'>Next</span>");
                                                });
                                            }
                                        }
                                    }).catch(function (reason) {

                                        var showFrom = parseInt(self.env.pos.config.sh_how_many_order_per_page) * (parseInt(pageNumber + 1) - 1)
                                        var showTo = showFrom + parseInt(self.env.pos.config.sh_how_many_order_per_page)
                                        var order = self.env.pos.db.all_return_order.slice(showFrom, showTo)
                                        if (order && order.length == 0) {
                                            $($('.next').parent()).addClass('disabled')
                                            $(".next").replaceWith(function () {
                                                $("<span class='current next'>Next</span>");
                                            });
                                        }

                                    });

                                    rpc.query({
                                        model: "pos.order",
                                        method: "search_return_exchange_order",
                                        args: [self.env.pos.config, pageNumber]
                                    }).then(function (orders) {
                                        self.env.pos.db.all_order = [];
                                        self.env.pos.db.order_by_id = {};

                                        if (orders) {
                                            if (orders['order']) {
                                                self.env.pos.db.all_orders(orders['order']);
                                            }
                                            if (orders['order_line']) {
                                                self.env.pos.db.all_orders_line(orders['order_line']);
                                            }
                                        }
                                        self.all_order = self.env.pos.db.all_order;
                                        self.env.pos.db.all_display_order = self.env.pos.db.all_order;
                                        self.render()
                                    }).catch(function (reason) {

                                        var showFrom = parseInt(self.env.pos.config.sh_how_many_order_per_page) * (parseInt(pageNumber) - 1)
                                        var showTo = showFrom + parseInt(self.env.pos.config.sh_how_many_order_per_page)
                                        self.env.pos.db.all_order = self.env.pos.db.all_return_order.slice(showFrom, showTo)
                                        self.all_order = self.env.pos.db.all_order;
                                        self.render()

                                    });
                                }

                            } catch (error) {
                            }

                        }
                    });
                }
                super.mounted()
                if (self.env.pos.get_order().is_client_order_filter) {
                    $('.sh_pagination').pagination('updateItems', Math.ceil(self.env.pos.customer_order_length / self.env.pos.config.sh_how_many_order_per_page));

                } else {
                    if (!self.return_filter) {

                        $('.sh_pagination').pagination('updateItems', Math.ceil(self.env.pos.db.all_non_return_order.length / self.env.pos.config.sh_how_many_order_per_page));
                    } else {
                        $('.sh_pagination').pagination('updateItems', Math.ceil(self.env.pos.db.all_return_order.length / self.env.pos.config.sh_how_many_order_per_page));
                    }
                }
                $('.sh_pagination').pagination('selectPage', 1);
            }
        };
    Registries.Component.extend(OrderListScreen, PosOrderListScreen);

    const PosReturnPaymentScreen = (PaymentScreen) =>
        class extends PaymentScreen {
            constructor() {
                super(...arguments);
            }
            cancel_return_order() {
                var self = this;

                if (this.env.pos.get_order() && this.env.pos.get_order().get_orderlines() && this.env.pos.get_order().get_orderlines().length > 0) {
                    var orderlines = this.env.pos.get_order().get_orderlines();
                    _.each(orderlines, function (each_orderline) {
                        if (self.env.pos.get_order().get_orderlines()[0]) {
                            self.env.pos.get_order().remove_orderline(self.env.pos.get_order().get_orderlines()[0]);
                        }
                    });
                }
                self.env.pos.get_order().is_return_order(false);
                self.env.pos.get_order().return_order = false;
                self.env.pos.get_order().is_exchange_order(false);
                self.env.pos.get_order().exchange_order = false;
                self.env.pos.get_order().set_old_pos_reference(false);
                self.env.pos.get_order().set_client(0);
                self.showScreen("ProductScreen");
            }
            async _finalizeValidation() {
                var self = this;
                if (this.currentOrder.is_paid_with_cash() && this.env.pos.config.iface_cashdrawer) {
                    this.env.pos.proxy.printer.open_cashbox();
                }

                this.currentOrder.initialize_validation_date();
                this.currentOrder.finalized = true;

                let syncedOrderBackendIds = [];

                try {
                    if (this.currentOrder.is_to_invoice()) {
                        syncedOrderBackendIds = await this.env.pos.push_and_invoice_order(this.currentOrder);
                    } else {
                        syncedOrderBackendIds = await this.env.pos.push_single_order(this.currentOrder);
                    }
                } catch (error) {
                    if (error instanceof Error) {
                        throw error;
                    } else {
                        await this._handlePushOrderError(error);
                    }
                }
                if (syncedOrderBackendIds.length && this.currentOrder.wait_for_push_order()) {
                    const result = await this._postPushOrderResolve(this.currentOrder, syncedOrderBackendIds);
                    if (!result) {
                        await this.showPopup("ErrorPopup", {
                            title: "Error: no internet connection.",
                            body: error,
                        });
                    }
                }
                if (this.currentOrder.return_order) {
                    this.currentOrder.is_return_order(true);
                    if (this.currentOrder.old_pos_reference) {
                        this.currentOrder.set_old_pos_reference(this.currentOrder.old_pos_reference);
                        this.currentOrder.set_old_sh_uid(this.currentOrder.old_sh_uid);
                    }
                } else if (this.currentOrder.exchange_order) {
                    this.currentOrder.is_exchange_order(true);
                    if (this.currentOrder.old_pos_reference) {
                        this.currentOrder.set_old_pos_reference(this.currentOrder.old_pos_reference);
                        this.currentOrder.set_old_sh_uid(this.currentOrder.old_sh_uid);
                    }
                } 
                this.showScreen(this.nextScreen);
                if (syncedOrderBackendIds.length && this.env.pos.db.get_orders().length) {
                    const { confirmed } = await this.showPopup("ConfirmPopup", {
                        title: this.env._t("Remaining unsynced orders"),
                        body: this.env._t("There are unsynced orders. Do you want to sync these orders?"),
                    });
                    if (confirmed) {
                        this.env.pos.push_orders();
                    }
                }
                if (this.env.pos.config.picking_type_id) {
                    var picking_type = this.env.pos.db.picking_type_by_id[this.env.pos.config.picking_type_id[0]];

                    if (picking_type && picking_type.default_location_src_id) {
                        var location_id = picking_type.default_location_src_id[0];
                        var order = this.env.pos.get_order();
                        if (location_id) {
                            var quant_by_product_id = this.env.pos.db.quant_by_product_id;
                            $.each(quant_by_product_id, function (product, value) {
                                for (var i = 0; i < order.orderlines.models.length; i++) {
                                    if (order.orderlines.models[i].product.id && order.orderlines.models[i].product.id == product) {
                                        $.each(value, function (location, qty) {
                                            if (location == location_id) {
                                                if (self.env.pos.config.sh_update_quantity_cart_change) {
                                                    value[location] = qty + order.orderlines.models[i].quantity;
                                                }
                                                var product_id = order.orderlines.models[i].product.id;
                                                var product_name = order.orderlines.models[i].product.display_name;
                                                var list = { product_id: [product_id, product_name], location_id: self.env.pos.config.sh_pos_location, quantity: value[location], is_valid_order: true };
                                                $.get(
                                                    "/update_quanttiy",
                                                    {
                                                        passed_list: list,
                                                    },
                                                    function (result) {}
                                                );
                                            }
                                        });
                                    }
                                }
                            });
                        }
                    }
                }
            }
        };

    Registries.Component.extend(PaymentScreen, PosReturnPaymentScreen);

    return { PosReturnPaymentScreen }
});
