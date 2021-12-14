# Copyright 2021 ForgeFlow S.L.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from odoo import _, api, fields, models


class MrpRouting(models.Model):

    _name = "mrp.routing"
    _description = "Manufacturing Routing"

    name = fields.Char("Routing", required=True)
    active = fields.Boolean(
        "Active",
        default=True,
        help="If the active field is set to False, "
        "it will allow you to hide the routing without removing it.",
    )
    code = fields.Char(
        "Reference", copy=False, default=lambda self: _("New"), readonly=True
    )
    note = fields.Text("Description")
    operation_ids = fields.Many2many(
        comodel_name="mrp.routing.workcenter.template", string="Operations"
    )
    company_id = fields.Many2one(
        "res.company", "Company", default=lambda self: self.env.company
    )

    @api.model
    def create(self, vals):
        if "code" not in vals or vals["code"] == _("New"):
            vals["code"] = self.env["ir.sequence"].next_by_code("mrp.routing") or _(
                "New"
            )
        return super(MrpRouting, self).create(vals)
