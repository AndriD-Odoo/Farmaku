14.0.1 (19 AUGUST 2021)
-------------------------

- Intial Release

14.0.2 (20 SEPTEMBER 2021)
-------------------------

- [FIX] Fix issue when install module

14.0.3 (05 OCTOBER 2021)
-------------------------

- [FIX] Fix issue in coupon that if coupon is for specific product then apply that coupon only on that product.

14.0.4 (21 OCTOBER 2021)
-------------------------

- [FIX] Fix issue when transfer order, search order in order screen, on and off rounding button

(25-10-2021)
------------
- Fix Custom Google Font Issue 

(10-11-2021)
---------
- Fixed background for when product box style is style_3 and product details is image only

14.0.5 (12 NOVEMBER 2021)
-------------------------

- [FIX] Fix issue that login screen is not display
- [FIX] Fix issue that data are redundant in shortcut tips popup.
- [FIX] Fix design of popup number.

14.0.6 (14 DECEMBER 2021)
-------------------------

- [FIX] Fix issue of global discount
- [FIX] Fix issue of decimal in total quantity

14.0.7 (16 DECEMBER 2021)
-------------------------

- [FIX] Fix issue that in some order, order detail not open
- [FIX] Fix issue that in spanish, you can not change price and also custom discount not apply correct

14.0.8 (18 DECEMBER 2021)
-------------------------

- [REMOVE] Remove blank option from order screen configuration

14.0.9 (20 DECEMBER 2021)
-------------------------
-[FIX] only last tag product displayed after search.
-[FIX] order label line -> in back-end 0.00 displayed.
-[FIX] fix issue that it display wrong data on reprint and return pos order.

14.0.10 (23 DECEMBER 2021)
-------------------------
- [UPDATE] Add Customer Creation Offline feature
- [UPDATE] Add configuration for create coupon and redeem coupon


14.0.11 (25 Dec 2021)
-------------------------
-[FIX] coupon access group throw error
-[FIX] Customer creation offline multiple customer create.

14.0.12 (29 Jan 2022)
-----------------------
-[ADD] Add Configuration for coupon
-[ADD] Add Configuration for Change UOM
-[ADD] Add Configuration for Product Suggestion

Note : create sale order code merge but not publish this feature on odoo apps now.
-[ADD] Merge CreateSo module.

14.0.13 (14 Feb 2022)
----------------------
-[ADD] Merge CreateSo module.
-[FIX] When refresh page Order label is not display.
-[FIX] Real time update qty is not working in product list view.
-[FIX] Fix load time issue ( taking to much time to load ).

14.0.14 (17 Feb 2022)
----------------------
- Fix issue when session close ( if you set closing balance = expected cash then also it display like there is difference)

14.0.15 (19 Feb 2022)
----------------------

- [Add] Add Product Variant Feature.

(22-2-2022)
------------
- fix design of variant field for list view

(23-2-2022)
------------
- Stop multiple selection attribute value from same attribute.

14.0.16 (19 Feb 2022)
----------------------

- [Add] Add Order Filter in Order Screen.

(25-2-2022)
---------------
- design of order screen (pos_order_return_exchange)

(01 March 2022)
- Make module compatible with create purchase order module.

14.0.17 (07 March 2022)
----------------------------
-[ADD] Create purchase order from pos module merged
-[UPDATE] add two shortcut keys for create SO and create PO.

(09 March 2022)
-------------------
 - Write purchase tax instead of sale tax when create PO from POS

 Date (10 Mar 2022)
 --------------------
 -Fix issue in order list when delete posted order from order list

 Date (12 March 2022)
 ---------------------------
 -[FIX] create_so and create_po module compatible with payment terms

 14.0.18 (21 March 2022)
 ---------------------------
 -[Add] Pos Min-Max price module merged.

 14.0.19 (23 March 2022)
 -----------------------------
 -[add] add po files for multi-language suport (de, es, fr and zh_HK)

 Date (24 March 2022)
 ------------------------------
 -[FIX] product template attribute load if config boolean is enable.

 14.0.20 (06 April 2022)
 ----------------------------
-[ADD] added 3 user groups
    1) Create/Delete Order in POS 
    2) Disable "Remove" Button
    3) Disable remove order-line

Date (11 April 2022)
-------------------------------
-[FIX] when serach order in order list screen and return throw error.
-[FIX] When Print invoice from portal it's gives an error
-[FIX] when transfer order.

Date (12 April 2022)
--------------------------------
-[FIX] When enable return order in pos config pos order list enable automatically.
-[FIX] Display 5 buttons in raw -> owl-carousel

Date (16 April 2022)
----------------------------
-[FIX] when create pos session for user, sale installation warning remove.

 14.0.21 (16 April 2022)
 ----------------------------
-[ADD] added real time stock update feature

14.0.22 (18 April 2022)
 ----------------------------
-[FIXED] Issue fixed when country set as a saudi arabia

Date ( 21 April 2022 )
-----------------------------
-[FIX] remove sale module from depends

14.0.23 (25 April 2022)
-------------------------------
-[Update] Set Bundle Product menu image.
-[FIX] Solve cache issue.

(27-4-2022)
------------
- fixed ref code position for all product box style

14.0.24 (06 May 2022)
-------------------------------
-[FIX] Fix stock update real time feature when enable option ( update when cart change )

(03 May 2022)
-------------------------------
-[FIX] Fix issue when session close from pos side.


14.0.25 (04 May 2022)
-----------------------------
-[Update] Fix all issue which is now working with Restaurant.


v14.0.26 (24 MAy 2022)
--------------------------------
- issue FIXED =>
    - pos poroduct variant => 
        ~ hide alternative config when disable variants
    
    - Rounding =>
        ~ when add rounding product in cart validation button not working
        ~ when add customer discount in order Rounding not working
        ~ Rounding Product price not set.
    
    - offline customer creation =>
        ~ when create customer in offline mode and after sync the order, the created customer will create 2 times in backend.

    - pos shortcut keys =>
        ~ when auto-lock is enable, shortcut keys is working in bakcground. 
    
    - product creation =>
        ~ Button design update
    
    - Customer order History =>
        ~ customer order history not working, customer order not display in order list screen
    
    - pos discount =>
        ~ applied line discount not display in receipt.

    - sh_pos_line_pricelist =>
        ~ pricelist details popup will not show currect amount.
    
    - sh_pos_order_return_exchange_barcode =>
        ~ when scan order from barcode and return the products it's throw error.
    
    ~ There and 2 times add_product method is override some functinality not working.
    ~ When transfer Order from one table to other table it's throw error, transfer not working.
    

v14.0.26 (24 MAy 2022)
--------------------------------
-[update] pos category slider merged.


v14.0.27 (24 MAy 2022)
--------------------------------
-[update] pos category slider merged.

v14.0.28 ( 09 Jun 2022 )
=========================
-[FIX] Receipt expected not working with manage order screen.

v14.0.29 ( 13 June 2022)
----------------------------------
- [FIX] Fix cache issue when enable advance cash control option

v14.0.30 ( 20 June 2022)
----------------------------------
- [FIX] Display only one cash amount input in opening cash amount popup

v14.0.31 ( 23 June 2022 )
--------------------------------------
- [UPDATE] Display product template name if product variant featrue is enable.

Date (31 June 2022)
-----------------------------
-[FIX] session close not working with advance cash control. 

v14.0.32
--------------------
product load time issue fixed

--------------------------------
-[ADD] Customer MAximum Discount feature Added.

v14.0.33 Date (14 Jul 2022)
---------------------------------
-[fixed] mix max price not working with bundle product,
-[fixed] return order qry not display in backend and also in pos order list screen.
-[fixed] when reprint order from order list screen barcode not proper
-[fixed] when return order from order list screen order not get proper order line.
-[fixed] tickent screen not working when remove order add order.

Date ( 27 Jul 2022 )
--------------------------------
-[FIXED] Total qty count and toatl item count no working proper when apply prmotion program.

Date (27 july 2022)
-------------------
-[FIXED] receipt display order number not working with configuration.

V14.0.34 (Date 29 Jul 2022)
-----------------------------
-[Updaet] product perfomance improve.
-[FIX] Bag charge issue fixed.

v14.0.35 (Date 03 Aug 2022)
-----------------------------
-[ADD] Multi barcode functionality Added.0

date ( 02 Sep 2022 )
----------------------
-[FIXED] when apply custome discount not working with secondary UOM
-[FIXED] Secondary UOM not display unit name in receipt when disable secondary base (base feature interepted)

-[FIXED] cash control issue fixed. when refresh page total amount change in payment popup.

v14.0.36 (Date 15 Sep 2022)
-----------------------------
- [FIXED] When return product discount not set.
