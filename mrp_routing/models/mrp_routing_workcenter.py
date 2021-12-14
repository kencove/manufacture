# Copyright 2021 ForgeFlow S.L.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).
from odoo import fields, models


class MrpRoutingWorkcenter(models.Model):

    _inherit = "mrp.routing.workcenter"

    template_id = fields.Many2one(
        comodel_name="mrp.routing.workcenter.template",
        string="Template",
        readonly=True,
    )

    on_template_change = fields.Selection(
        string="On template change?",
        selection=[
            ("nothing", "Do nothing"),
            ("sync", "Sync"),
        ],
        required=False,
        default="nothing",
    )
