{
    "name": "POS Return Restriction",
    "summary": """Employee wise return restriction in POS""",
    "description": """
        In Odoo Point of Sale, currently there are no restriction in the case of returns.
        This module will bring in a restriction in the case of returns. The employees who can do the
        returns should be selected in each POS shop configuration.
    """,
    "author": "Sanesquare Technologies",
    "website": "https://www.sanesquare.com/",
    "support": "odoo@sanesquare.com",
    "license": "OPL-1",
    "category": "Sales/Point of Sale",
    "version": "15.0.1.0.1",
    "depends": ["pos_hr"],
    "images": ["static/description/pos_return_restriction_v15.png"],
    "data": [
        "views/pos_config_view.xml",
    ],
    "assets": {
        "point_of_sale.assets": [
            "/ssq_pos_return_restriction/static/src/js/ProductScreen.js",
        ],
    },
}
