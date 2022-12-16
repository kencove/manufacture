from datetime import timedelta

from dateutil.relativedelta import relativedelta

from odoo import fields, models
from odoo.osv.expression import OR


class StockPicking(models.Model):
    _inherit = "stock.picking"

    subcontracted_unbuild_ids = fields.One2many(
        "mrp.unbuild", "picking_id", readonly=True, string="Suncontracted unbuilds"
    )

    def _prepare_subcontract_unbuild_vals(self, subcontract_move, bom):
        subcontract_move.ensure_one()
        product = subcontract_move.product_id
        group = self.env["procurement.group"].create(
            {
                "name": self.name,
                "partner_id": self.partner_id.id,
            }
        )
        warehouse = self._get_warehouse(subcontract_move)
        vals = {
            "company_id": subcontract_move.company_id.id,
            "product_id": product.id,
            "product_uom_id": subcontract_move.product_uom.id,
            "procurement_group_id": group.id,
            "bom_id": bom.id,
            "location_id": subcontract_move.picking_id.partner_id.with_company(
                subcontract_move.company_id
            ).property_stock_subcontractor.id,
            "location_dest_id": subcontract_move.picking_id.partner_id.with_company(
                subcontract_move.company_id
            ).property_stock_subcontractor.id,
            "product_qty": subcontract_move.product_uom_qty,
            "picking_type_id": warehouse.subcontracting_type_id.id,
            "date_planned_start": subcontract_move.date
            - relativedelta(days=product.produce_delay),
            "picking_id": self.id,
        }
        return vals

    def _subcontracted_produce_unbuild(self, subcontract_details):
        self.ensure_one()
        for move, bom in subcontract_details:
            unbuild = (
                self.env["mrp.unbuild"]
                .with_company(move.company_id)
                .create(self._prepare_subcontract_unbuild_vals(move, bom))
            )
            unbuild.date_planned_finished = (
                move.date
            )  # Avoid to have the picking late depending on the unbuild order
            self.subcontracted_unbuild_ids |= unbuild

    def _action_done(self):
        res = super(StockPicking, self)._action_done()
        for picking in self:
            unbuilds_to_done = (
                picking.subcontracted_unbuild_ids._subcontracting_filter_to_done()
            )
            if not unbuilds_to_done:
                continue
            unbuild_ids_backorder = []
            if not self.env.context.get("cancel_backorder"):
                unbuild_ids_backorder = unbuilds_to_done.filtered(
                    lambda u: u.state == "draft"
                ).ids
            unbuilds_to_done.with_context(
                subcontract_move_id=True, mo_ids_to_backorder=unbuild_ids_backorder
            ).action_validate()
            move = self.move_lines.filtered(lambda move: move.is_subcontract)
            finished_move = unbuilds_to_done.produce_line_ids.filtered(
                lambda m: m.product_id == move.product_id
            )
            finished_move.write({"move_dest_ids": [(4, move.id, False)]})
            # For concistency, set the date on production move before the date
            # on picking. (Traceability report + Product Moves menu item)
            minimum_date = min(picking.move_line_ids.mapped("date"))
            unbuild_moves = (
                unbuilds_to_done.produce_line_ids | unbuilds_to_done.consume_line_ids
            )
            unbuild_moves.write({"date": minimum_date - timedelta(seconds=1)})
            unbuild_moves.move_line_ids.write(
                {"date": minimum_date - timedelta(seconds=1)}
            )
        return res

    def action_view_stock_valuation_layers(self):
        action = super(StockPicking, self).action_view_stock_valuation_layers()
        subcontracted_unbuilds = self.subcontracted_unbuild_ids
        if not subcontracted_unbuilds:
            return action
        domain = action["domain"]
        domain_subcontracting = [
            (
                "id",
                "in",
                (
                    subcontracted_unbuilds.produce_line_ids
                    | subcontracted_unbuilds.consume_line_ids
                ).stock_valuation_layer_ids.ids,
            )
        ]
        domain = OR([domain, domain_subcontracting])
        return dict(action, domain=domain)
