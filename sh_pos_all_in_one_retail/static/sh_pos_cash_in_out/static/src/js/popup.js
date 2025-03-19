odoo.define("sh_pos_cash_in_out.Popup", function (require) {
    "use strict";

    const Registries = require("point_of_sale.Registries");
    const AbstractAwaitablePopup = require("point_of_sale.AbstractAwaitablePopup");
    const rpc = require("web.rpc");
	var framework = require("web.framework");
    
    class CashInOutOptionPopupWidget extends AbstractAwaitablePopup {
        constructor() {
            super(...arguments);
        }
        click_cash_in_button(){
        	var self = this;
        	self.env.pos.cash_in_out_options = "cash_in"
        	let { confirmed, payload } = this.showPopup("CashInOutPopupWidget");
            if (confirmed) {
            } else {
                return;
            }
        }
        click_cash_out_button(){
        	var self = this;
        	self.env.pos.cash_in_out_options = "cash_out"
    		let { confirmed, payload } = this.showPopup("CashInOutPopupWidget");
            if (confirmed) {
            } else {
                return;
            }
        }
        click_set_closing_button(){
        	let { confirmed, payload } = this.showPopup("SetClosingVBalancePopupWidget");
            if (confirmed) {
            } else {
                return;
            }
        }
        click_payments(){
        	let { confirmed, payload } = this.showPopup("TransactionPopupWidget");
            if (confirmed) {
            } else {
                return;
            }
        }
    }

    CashInOutOptionPopupWidget.template = "CashInOutOptionPopupWidget";
    Registries.Component.add(CashInOutOptionPopupWidget);
    
    class CashInOutPopupWidget extends AbstractAwaitablePopup {
        constructor() {
            super(...arguments);
            
        }
        mounted(){
        	super.mounted();
        	$('.amount_input').keypress(function(event){
        		var charCode = (event.which) ? event.which : event.keyCode;
                if (charCode != 46 && charCode > 31 
                  && (charCode < 48 || charCode > 57))
                   return false;

                return true;
            });
        }
        back(){
        	let { confirmed, payload } = this.showPopup("CashInOutOptionPopupWidget");
            if (confirmed) {
            } else {
                return;
            }
        }

        cash_in_out(){
        	
        	var self = this;
            var reason = $(".reason_input").val();
            var amount = $(".amount_input").val();
            if(reason && amount){
            	this.trigger("close-popup");
            	
            	
            	var date_obj = new Date();
                var date = date_obj.getFullYear() + '-'+("0" + (date_obj.getMonth() + 1)).slice(-2) + "-" + ("0" + date_obj.getDate()).slice(-2)+" "+("0" + (date_obj.getHours())).slice(-2)+":"+("0" + (date_obj.getMinutes())).slice(-2)+":"+("0" + (date_obj.getSeconds())).slice(-2);
            	
            	
            	var data = {'sh_transaction_type':self.env.pos.cash_in_out_options,'sh_amount':parseFloat(amount),'sh_reason':reason,'sh_session':self.env.pos.pos_session.id,'sh_date':date}
            	
            	
            	if(self.env.pos.config.sh_print_information){
            		this.env.pos.cash_in_out_receipt = true;
                	this.env.pos.set('selectedData',{'reason':reason,'amount':amount})
                	this.showScreen("ReceiptScreen");
            	}
            	if(self.env.pos.cash_in_out_options == 'cash_out'){
            		amount = -amount
            	}
            	
            	var currentcash_in_out = self.env.pos.get_cash_in_out();
            	self.env.pos.add_new_cash_in_out();
            	var currentcash_in_out = self.env.pos.get_cash_in_out();
            	currentcash_in_out.set_name(data);
            	self.env.pos.db.all_cash_in_out_statement.push(data)
            	
            	var offline_cash_in_outs = self.env.pos.db.get_cash_in_outs();
            	offline_cash_in_outs.push(currentcash_in_out.export_as_JSON());
            	self.env.pos.db.save('add_cash_amount',[])
            	self.env.pos.db.save("cash_in_outs", offline_cash_in_outs);
            	
            	self.env.pos.cash_register_total_entry_encoding = self.env.pos.cash_register_total_entry_encoding + parseFloat(amount)
            	self.env.pos.cash_register_balance_end = self.env.pos.cash_register_balance_end + parseFloat(amount)
            	
            	try {
                    self.env.pos.load_new_cash_in_outs();
                } catch (error) {
                    if (error instanceof Error) {
                        throw error;
                    } else {
                        self.env.pos.set_synch(self.env.pos.get("failed") ? "error" : "disconnected");
                        self._handlePushOrderError(error);
                    }
                }
            }else if(!reason){
            	alert("Please Enter Reason.")
            }else if(!amount){
            	alert("Please Enter Amount.")
            }
        	
        }
    }

    CashInOutPopupWidget.template = "CashInOutPopupWidget";
    Registries.Component.add(CashInOutPopupWidget);
    
    class SetClosingVBalancePopupWidget extends AbstractAwaitablePopup {
    	constructor() {
            super(...arguments);
            this.closing_total = 0.00
        }
    	back(){
        	let { confirmed, payload } = this.showPopup("CashInOutOptionPopupWidget");
            if (confirmed) {
            } else {
                return;
            }
        }
    	
    	async validate(){
    		var self = this
    		var closing_balance_line = []
    		if($('.sh_closing_tr') && $('.sh_closing_tr').length > 0){
    			_.each($('.sh_closing_tr'), function(each_closing_tr){
    				
    				var number = $(each_closing_tr).find('.sh_coin_bill_value').val()
    				var coin_value = $(each_closing_tr).find('.sh_coin_value').val()
    				var subtotal = $(each_closing_tr).find('.closing_subtotal').text()
    				if(number && coin_value && subtotal){
    					closing_balance_line.push({'number':number,'coin_value':coin_value,'subtotal':subtotal,'session_id':self.env.pos.pos_session.id})
    				}
    				
    				self.env.pos.db.save("closing_balance", closing_balance_line);
    			});
    			const { confirmed } = await this.showPopup('ShConfirmPopup', {
                    title: 'Confirmation',
                    body: "Do you want to close session ?",
                });
                if (!confirmed) return;
    		}else{
    			alert("Please enter line for closing balance.")
    		}
    		
    	}
    	mounted(){
    		super.mounted();
    		
    	}
    	add_closing_line(){
    		
    		var self = this;
    		var table = $('.sh_set_closing_balance_table tbody')
    		var order_row = "<tr class='sh_closing_tr'><td><input type='text' class='sh_coin_bill_value sh_closing_bal_tbl_input'/></td><td><input type='text' class='sh_coin_value sh_closing_bal_tbl_input'/></td><td><span class='closing_subtotal'></span></td><td><span class='cancel_line'><i class='fa fa-trash-o' aria-hidden='true'></i></span></td></tr>"
    		table.append(order_row);
    		$('.cancel_line').on('click', function (event) {
                $(event.currentTarget).parent().parent().remove()
                if($('.closing_subtotal') && $('.closing_subtotal').length > 0){
            		self.closing_total = 0.00
            		_.each($('.closing_subtotal'), function(each_closing_line){
            			self.closing_total = self.closing_total + parseFloat($(each_closing_line).html())
            		});
            		if(self.closing_total){
            			$('.closing_total_data').html(self.closing_total)
            		}else{
            			$('.closing_total_data').html(0)
            		}
            		
            	}else{
            		$('.closing_total_data').html(0.00)
            	}
            });
    		$('.sh_coin_bill_value').on('keyup', function (event) {
    			var coin_bill_value = $(event.currentTarget).val()
                var coin_value = $(event.currentTarget).parent().parent().find('.sh_coin_value').val()
                if(coin_bill_value && coin_value){
                	var subtotal = parseFloat(coin_bill_value) * parseFloat(coin_value)
                	$(event.currentTarget).parent().parent().find('.closing_subtotal').html(subtotal)
                	if($('.closing_subtotal') && $('.closing_subtotal').length > 0){
                		self.closing_total = 0.00
                		_.each($('.closing_subtotal'), function(each_closing_line){
                			if($(each_closing_line).html()){
                				self.closing_total = self.closing_total + parseFloat($(each_closing_line).html())
                			}
                		});
                		$('.closing_total_data').html(self.closing_total)
                	}
                }
            });
    		
    		$('.sh_coin_value').on('keyup', function (event) {
    			var coin_bill_value = $(event.currentTarget).parent().parent().find('.sh_coin_bill_value').val()
                var coin_value = $(event.currentTarget).val()
                if(coin_bill_value && coin_value){
                	var subtotal = parseFloat(coin_bill_value) * parseFloat(coin_value)
                	$(event.currentTarget).parent().parent().find('.closing_subtotal').html(subtotal)
                	
                	if($('.closing_subtotal') && $('.closing_subtotal').length > 0){
                		self.closing_total = 0.00
                		_.each($('.closing_subtotal'), function(each_closing_line){
                			if($(each_closing_line).html()){
                				self.closing_total = self.closing_total + parseFloat($(each_closing_line).html())
                			}
                		});
                		$('.closing_total_data').html(self.closing_total)
                	}
                }
            });
    		$('.sh_coin_bill_value').keypress(function(event){
        		var charCode = (event.which) ? event.which : event.keyCode;
                if (charCode != 46 && charCode > 31 
                  && (charCode < 48 || charCode > 57))
                   return false;

                return true;
            });
    		$('.sh_coin_value').keypress(function(event){
        		var charCode = (event.which) ? event.which : event.keyCode;
                if (charCode != 46 && charCode > 31 
                  && (charCode < 48 || charCode > 57))
                   return false;

                return true;
            });
    	}
    }
    SetClosingVBalancePopupWidget.template = "SetClosingVBalancePopupWidget";
    Registries.Component.add(SetClosingVBalancePopupWidget);
    
    class ShConfirmPopup extends AbstractAwaitablePopup {
    	constructor() {
            super(...arguments);
        }
    	async pos_close(){
    		var self = this;
    		
    		try {
    			
        		this.rpc({
                    model: "pos.session",
                    method: "sh_write_close_balance",
                    args: [self.env.pos.db.load('closing_balance')],
                })
                .then(async function (session_close_data) {
                	if(session_close_data){
                		self.env.pos.db.save("closing_balance", []);
						if (self.env.pos.user && self.env.pos.user.sh_is_direct_logout) {
                            framework.redirect("/web/session/logout");
                        } else {
							window.location = '/web#action=point_of_sale.action_client_pos_menu';
						}
                	}else{
                		alert("Closing Balance Not available.")
                	}
                }).catch(function (reason) {
                    self.env.pos.set_synch(self.env.pos.get("failed") ? "error" : "disconnected");
                });
    		} catch (error) {
                self.env.pos.set_synch(self.get("failed") ? "error" : "disconnected");
            }
    		
    		
    	}
    	async pos_session_close(){
    		var self = this;
    		var total_amount = 0.00
    		if(self.env.pos.db.load('closing_balance') && self.env.pos.db.load('closing_balance').length > 0){
    			_.each(self.env.pos.db.load('closing_balance'),function(each_closing_line){
    				total_amount += parseFloat(each_closing_line['subtotal'])
    			});
    		}
    		if((self.env.pos.bank_statement.balance_start + self.env.pos.cash_register_total_entry_encoding) - total_amount == 0.00){
				self.rpc({
                    model: "pos.session",
                    method: "sh_force_cash_control_line",
                    args: [self.env.pos.db.load('closing_balance')],
                })
                .then(async function (session_close_data) {
					if (self.env.pos.user && self.env.pos.user.sh_is_direct_logout) {
                        framework.redirect("/web/session/logout");
                    }else{
						window.location = '/web#action=point_of_sale.action_client_pos_menu';
					}
                }).catch(function (reason) {
                	self.env.pos.is_session_close = true;
                    self.env.pos.set_synch(self.env.pos.get("failed") ? "error" : "disconnected");
                });
    		}else{
				
    			const { confirmed } = await self.showPopup('ConfirmPopup', {
                    title: 'Do you want to continue ?',
                    body: "There is a difference, do you want to continue ?",
                });
                if (!confirmed){
                	return;
                }else{
                	
                	self.rpc({
						model: "pos.session",
                        method: "sh_force_cash_control_line",
                        args: [self.env.pos.db.load('closing_balance')],
                    })
                    .then(async function (session_close_data) {
                    }).catch(function (reason) {
                    	self.env.pos.is_session_close = true;
                        self.env.pos.set_synch(self.env.pos.get("failed") ? "error" : "disconnected");
                    });
					if (this.env.pos.user && this.env.pos.user.sh_is_direct_logout) {
                        framework.redirect("/web/session/logout");
                    }else{
						window.location = '/web#action=point_of_sale.action_client_pos_menu';
					}
                	
                }
    		}
    	}
    };
    ShConfirmPopup.template = "ShConfirmPopup";
    Registries.Component.add(ShConfirmPopup);
    
    class TransactionPopupWidget extends AbstractAwaitablePopup {
    	constructor() {
            super(...arguments);
        }
    };
    TransactionPopupWidget.template = "TransactionPopupWidget";
    Registries.Component.add(TransactionPopupWidget);
    
    class CashInOutOptionStatementPopupWidget extends AbstractAwaitablePopup {
    	constructor() {
            super(...arguments);
        }
    	print(){
    		var self = this;
    		var statementValue = $("input[name='statement_option']:checked").val();
    		var statementPrintValue = $("input[name='print_option']:checked").val();
    		
    		if(statementValue && statementPrintValue){
    			if(statementValue == 'current_session' && statementPrintValue == 'pdf'){
    				rpc.query({
    	                model: "sh.cash.in.out",
    	                method: "search_read",
    	            })
    	            .then(function (all_cash_in_out_statement) {
    	            	self.env.pos.db.all_cash_in_out_statement_id = [];
    	            	if(all_cash_in_out_statement && all_cash_in_out_statement.length > 0){
    	                	_.each(all_cash_in_out_statement, function(each_cash_in_out_statement){
    	                		if(self.env.pos.pos_session && self.env.pos.pos_session.id && each_cash_in_out_statement.sh_session && each_cash_in_out_statement.sh_session[0] && each_cash_in_out_statement.sh_session[0] == self.env.pos.pos_session.id){
    	                			self.env.pos.db.all_cash_in_out_statement_id.push(each_cash_in_out_statement.id)
    	                		}
    	                	});
    	                }
    	            	if(self.env.pos.db.all_cash_in_out_statement_id && self.env.pos.db.all_cash_in_out_statement_id.length > 0){
    	            		self.env.pos.do_action('sh_pos_all_in_one_retail.sh_pos_cash_in_out_report', {
    	                        additional_context: {
    	                            active_ids: self.env.pos.db.all_cash_in_out_statement_id,
    	                        },
    	                    });
    	            	}else{
    	            		alert("No Any Cash In / Cash Out Statement for this Session.")
    	            	}
    	            });
    				this.trigger("close-popup");
    			}else if(statementValue == 'current_session' && statementPrintValue == 'receipt'){
    				
    				if(self.env.pos.db.all_cash_in_out_statement && self.env.pos.db.all_cash_in_out_statement.length > 0){
    					self.env.pos.db.display_cash_in_out_statement = [];
    					_.each(self.env.pos.db.all_cash_in_out_statement, function(each_cash_in_out_statement){
    	            		if(self.env.pos.pos_session && self.env.pos.pos_session.id && each_cash_in_out_statement.sh_session && each_cash_in_out_statement.sh_session[0] && each_cash_in_out_statement.sh_session[0] == self.env.pos.pos_session.id){
    	            			self.env.pos.db.display_cash_in_out_statement.push(each_cash_in_out_statement)
    	            		}else if(self.env.pos.pos_session && self.env.pos.pos_session.id && each_cash_in_out_statement.sh_session && each_cash_in_out_statement.sh_session && each_cash_in_out_statement.sh_session == self.env.pos.pos_session.id){
    	            			self.env.pos.db.display_cash_in_out_statement.push(each_cash_in_out_statement)
    	            		}
    	            		
    	            	});
    					if(self.env.pos.db.display_cash_in_out_statement && self.env.pos.db.display_cash_in_out_statement.length > 0){
    						self.env.pos.cash_in_out_statement_receipt = true;
        					self.showScreen("ReceiptScreen");
    					}else{
    						alert("No Any Cash In / Cash Out Statement avilable for this session.")
    					}
    					
    				}else{
	            		alert("No Any Cash In / Cash Out Statement avilable.")
	            	}
    				this.trigger("close-popup");
    			}else if(statementValue == 'date_wise' && statementPrintValue == 'pdf'){
    				
    				if($('.start_date').val() && $('.end_date').val()){
    					if($('.start_date').val() > $('.end_date').val()){
    						alert("Start Date must be less than End Date.")
    					}else{
    						var start_date = $('.start_date').val() + " 00:00:00"
        					var end_date = $('.end_date').val() + " 24:00:00"
        					
        					rpc.query({
    	    	                model: "sh.cash.in.out",
    	    	                method: "search_read",
    	    	                domain: [['sh_date','>=',start_date],['sh_date','<=',end_date]],
        						fields: ['id']
    	    	            })
    	    	            .then(function (all_cash_in_out_statement) {
    	    	            	self.env.pos.db.all_cash_in_out_statement_id = [];
    	    	            	if(all_cash_in_out_statement && all_cash_in_out_statement.length > 0){
    	    	            		_.each(all_cash_in_out_statement, function(each_cash_in_out_statement){
        	                			self.env.pos.db.all_cash_in_out_statement_id.push(each_cash_in_out_statement.id)
    	    	                	});
    	    	            		
    	    	            		if(self.env.pos.db.all_cash_in_out_statement_id && self.env.pos.db.all_cash_in_out_statement_id.length > 0){
    	        	            		self.env.pos.do_action('sh_pos_all_in_one_retail.sh_pos_cash_in_out_date_wise_report', {
    	        	                        additional_context: {
    	        	                            active_ids: self.env.pos.db.all_cash_in_out_statement_id,
    	        	                        },
    	        	                    });
    	        	            	}
    	    	            		self.trigger("close-popup");
    	    	            		
    	    	            	}else{
    	    	            		alert("No Cash In / Out Statement Between Given Date.")
    	    	            	}
    	    	            });
        					
    					}
    				}else{
    					alert("Enter Start Date or End Date.")
    				}
    			}else if(statementValue == 'date_wise' && statementPrintValue == 'receipt'){
    				if($('.start_date').val() && $('.end_date').val()){
    					if($('.start_date').val() > $('.end_date').val()){
    						alert("Start Date must be less than End Date.")
    					}else{
    						var start_date = $('.start_date').val() + " 00:00:00"
        					var end_date = $('.end_date').val() + " 24:00:00"
        					if(self.env.pos.db.all_cash_in_out_statement && self.env.pos.db.all_cash_in_out_statement.length > 0){
            					self.env.pos.db.display_cash_in_out_statement = [];
            					_.each(self.env.pos.db.all_cash_in_out_statement, function(each_cash_in_out_statement){
            	            		if(each_cash_in_out_statement.sh_date && each_cash_in_out_statement.sh_date >= start_date && each_cash_in_out_statement.sh_date <= end_date){
            	            			self.env.pos.db.display_cash_in_out_statement.push(each_cash_in_out_statement)
            	            		}
            	            	});
            					if(self.env.pos.db.display_cash_in_out_statement && self.env.pos.db.display_cash_in_out_statement.length > 0){
            						self.env.pos.cash_in_out_statement_receipt = true;
                					self.showScreen("ReceiptScreen");
            					}else{
            						alert("No Cash In / Out Statement Between Given Date.")
            					}
            					this.trigger("close-popup");
            					
            				}else{
        	            		alert("No Any Cash In / Cash Out Statement avilable.")
        	            	}
    					}
    				}else{
    					alert("Enter Start Date or End Date.")
    				}
    			}
    		}
    	}
    	mounted(){
            super.mounted()
            $('input[type=radio][name=statement_option]').change(function() {
                if (this.value == 'current_session') {
                    $('.sh_statement_date').removeClass('show')
                }
                else if (this.value == 'date_wise') {
                    $('.sh_statement_date').addClass('show')
                }
            });
        }
    };
    CashInOutOptionStatementPopupWidget.template = "CashInOutOptionStatementPopupWidget";
    Registries.Component.add(CashInOutOptionStatementPopupWidget);
    
    return {
    	CashInOutOptionPopupWidget,
    	CashInOutPopupWidget,
    };
});
