# Copyright 2025 Kencove
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

{
    "name": "MRP BoM Costing",
    "summary": "Track next production cost for BOMs with automatic updates",
    "version": "16.0.1.0.0",
    "development_status": "Beta",
    "category": "Manufacturing",
    "website": "https://github.com/OCA/manufacture",
    "author": "Kencove, Odoo Community Association (OCA)",
    "maintainers": [],
    "license": "AGPL-3",
    "application": False,
    "installable": True,
    "depends": [
        "mrp",
        "purchase",
    ],
    "data": [
        "views/mrp_bom_views.xml",
    ],
}
