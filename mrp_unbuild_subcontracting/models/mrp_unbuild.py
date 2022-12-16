import datetime

from odoo import api, fields, models


class MrpUnbuild(models.Model):
    _inherit = "mrp.unbuild"

    @api.model
    def _get_default_date_planned_finished(self):
        if self.env.context.get("default_date_planned_start"):
            return fields.Datetime.to_datetime(
                self.env.context.get("default_date_planned_start")
            ) + datetime.timedelta(hours=1)
        return datetime.datetime.now() + datetime.timedelta(hours=1)

    @api.model
    def _get_default_date_planned_start(self):
        if self.env.context.get("default_date_deadline"):
            return fields.Datetime.to_datetime(
                self.env.context.get("default_date_deadline")
            )
        return datetime.datetime.now()

    @api.model
    def _get_default_picking_type(self):
        company_id = self.env.context.get("default_company_id", self.env.company.id)
        return (
            self.env["stock.picking.type"]
            .search(
                [
                    ("code", "=", "mrp_operation"),
                    ("warehouse_id.company_id", "=", company_id),
                ],
                limit=1,
            )
            .id
        )

    date_planned_start = fields.Datetime(
        "Scheduled Date",
        copy=False,
        default=_get_default_date_planned_start,
        help="Date at which you plan to start the unbuild.",
        index=True,
        required=True,
    )
    date_planned_finished = fields.Datetime(
        "Scheduled End Date",
        default=_get_default_date_planned_finished,
        help="Date at which you plan to finish the unbuild.",
        copy=False,
    )
    picking_type_id = fields.Many2one(
        "stock.picking.type",
        "Operation Type",
        domain="[('code', '=', 'mrp_operation'), ('company_id', '=', company_id)]",
        default=_get_default_picking_type,
        required=True,
        check_company=True,
        readonly=True,
        states={"draft": [("readonly", False)]},
    )
    picking_id = fields.Many2one("stock.picking", "Operation id", readonly=True)
    procurement_group_id = fields.Many2one(
        "procurement.group", "Procurement Group", copy=False
    )

    def _subcontracting_filter_to_done(self):
        """Filter subcontracting unbuilds where composant is already
        recorded and should be considered to be validated"""

        def filter_in(unbuild):
            if unbuild.state in "done":
                return False
            return True

        return self.filtered(filter_in)
