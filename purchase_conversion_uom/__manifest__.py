# -*- coding: utf-8 -*-
{
    "name": "Purchase Conversion UOM",
    "summary": """
        Conversion sepsific unit of measure in Product
    """,
    "author": "Arkana Solusi Bisnis, RomySkuy <trianperfecto@gmail.com>",
    "website": "https://arkana.co.id/",
    "category": "Inventory",
    "version": "14.0.1.0.0",
    "images": [
        "static/image/uom_conversion.jpg",
    ],
    "depends": [
        "base",
        "purchase",
        "stock",
        "uom",
        "purchase_stock",
        "purchase_discount",
        "purchase_extended",
    ],
    "data": [
        "security/ir.model.access.csv",
        "views/view_product.xml",
        "views/product_uom_line_view.xml",
        "views/uom_uom_view.xml",
        "views/product_supplier_info_views.xml",
    ],
    "demo": [

    ],
}
