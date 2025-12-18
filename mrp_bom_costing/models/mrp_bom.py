# Copyright 2025 Kencove
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, fields, models


class MrpBom(models.Model):
    _inherit = "mrp.bom"

    next_production_cost = fields.Float(
        compute="_compute_next_production_cost",
        store=True,
        digits="Product Price",
        help="Estimated cost for the next production based on current component "
        "purchase prices and workcenter operation costs",
    )
    next_production_cost_write_date = fields.Datetime(
        readonly=True,
        help="Last date when the next production cost was calculated",
    )

    @api.depends(
        "bom_line_ids.product_id",
        "bom_line_ids.product_qty",
        "operation_ids.workcenter_id.costs_hour",
        "operation_ids.time_cycle",
        "product_id.seller_ids.price",
    )
    def _compute_next_production_cost(self):
        """
        Calculate the estimated cost for the next production run.

        Cost components:
        1. Component materials: Sum of (component qty * purchase price)
        2. Labor costs: Sum of (operation time * workcenter hourly cost)
        """
        for bom in self:
            total_cost = 0.0

            # Get base product and quantity
            product = bom.product_id or bom.product_tmpl_id.product_variant_id
            if not product:
                bom.next_production_cost = 0.0
                bom.next_production_cost_write_date = fields.Datetime.now()
                continue

            # Explode BOM to get all components with their quantities
            try:
                bom_data = bom.explode(product, bom.product_qty or 1.0)[0]
            except Exception:
                # If explode fails, set cost to 0
                bom.next_production_cost = 0.0
                bom.next_production_cost_write_date = fields.Datetime.now()
                continue

            # Calculate material costs from components
            for bom_line, line_data in bom_data:
                component = bom_line.product_id
                component_qty = line_data["qty"]

                # Get the current or next purchase price for the component
                purchase_price = 0.0

                # First try to get price from supplier info
                seller = component.seller_ids.filtered(
                    lambda s: not s.company_id or s.company_id == bom.company_id
                )[:1]
                if seller:
                    purchase_price = seller.price
                else:
                    # Fallback to standard price if no supplier info
                    purchase_price = component.standard_price

                total_cost += component_qty * purchase_price

            # Calculate labor costs from operations
            for operation in bom.operation_ids:
                if operation.workcenter_id and operation.workcenter_id.costs_hour:
                    # time_cycle is in minutes, convert to hours
                    operation_hours = operation.time_cycle / 60.0
                    total_cost += operation_hours * operation.workcenter_id.costs_hour

            bom.next_production_cost = total_cost
            bom.next_production_cost_write_date = fields.Datetime.now()
