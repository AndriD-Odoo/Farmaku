-- REVISI TAX PO DAN BILL

-- delete duplicate tax
DELETE FROM account_tax_purchase_order_line_rel r USING account_tax_purchase_order_line_rel r2 WHERE r.account_tax_id < r2.account_tax_id AND r.purchase_order_line_id = r2.purchase_order_line_id;
DELETE FROM account_move_line_account_tax_rel r USING account_move_line_account_tax_rel r2 WHERE r.account_tax_id < r2.account_tax_id AND r.account_move_line_id = r2.account_move_line_id;
-- revisi tax PO company solusi sarana sehat
UPDATE account_tax_purchase_order_line_rel r set account_tax_id=5 FROM purchase_order_line l left join purchase_order po on po.id=l.order_id WHERE r.purchase_order_line_id=l.id AND po.company_id=1 AND r.account_tax_id=4;
-- revisi tax bill company solusi sarana sehat
UPDATE account_move_line_account_tax_rel r set account_tax_id=5 FROM account_move_line aml left join account_move am on am.id=aml.move_id WHERE r.account_move_line_id=aml.id AND am.company_id=1 AND am.move_type IN ('in_invoice', 'in_refund') AND r.account_tax_id=4;
-- revisi CoA tax company solusi sarana sehat
UPDATE account_move_line aml set account_id=2730 FROM account_move am WHERE am.id=aml.move_id AND am.company_id=1 AND am.move_type IN ('in_invoice', 'in_refund') AND aml.account_id=2758;
-- revisi tax PO company solusi nusantara sehat
UPDATE account_tax_purchase_order_line_rel r set account_tax_id=10 FROM purchase_order_line l left join purchase_order po on po.id=l.order_id WHERE r.purchase_order_line_id=l.id AND po.company_id=2 AND r.account_tax_id IN (4, 9);
-- revisi tax bill company solusi nusantara sehat
UPDATE account_move_line_account_tax_rel r set account_tax_id=10 FROM account_move_line aml left join account_move am on am.id=aml.move_id WHERE r.account_move_line_id=aml.id AND am.company_id=2 AND am.move_type IN ('in_invoice', 'in_refund') AND r.account_tax_id IN (4, 9);
-- revisi CoA tax company solusi nusantara sehat
UPDATE account_move_line aml set account_id=3262 FROM account_move am WHERE am.id=aml.move_id AND am.company_id=2 AND am.move_type IN ('in_invoice', 'in_refund') AND aml.account_id IN (2758, 3298);
