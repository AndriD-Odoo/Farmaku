{
    "name": "Account Journal Sequence",
    "summary": """
        Fixed sequence number for customer invoice, vendor bill and journal entry
    """,
    "description": """
    """,
    "author": "Miftahussalam",
    "website": "https://blog.miftahussalam.com/",
    "category": "Invoices & Payments",
    "version": "14.0.1.0.0",
    "depends": [
        "base",
        "account",
        "account_payment",
    ],
    "data": [
        "security/ir.model.access.csv",
        "views/account_journal_views.xml",
        "views/account_move_views.xml",
    ],
    "demo": [

    ],
    "images": [
        "static/description/images/main_screenshot.png",
    ],
    "license": "OPL-1",
    "price": 10,
    "currency": "USD",
}
