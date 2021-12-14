# Copyright 2021 ForgeFlow S.L.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).
from odoo import api, fields, models


class MrpBom(models.Model):

    _inherit = "mrp.bom"

    routing_id = fields.Many2one(
        comodel_name="mrp.routing", string="Routing", check_company=True, tracking=True
    )

    @api.onchange("routing_id")
    def onchange_routing_id(self):
        opeartion_model = self.env["mrp.routing.workcenter"]
        if self.routing_id and self.routing_id.operation_ids:
            new_operations = opeartion_model.browse()
            for template_operation in self.routing_id.operation_ids:
                operation_data = template_operation.read(load="_classic_write")[0]
                if "operation_ids" in operation_data:
                    operation_data.pop("operation_ids")
                operation_data.update(
                    {
                        "template_id": template_operation.id,
                    }
                )
                new_operations |= opeartion_model.new(operation_data)
            self.operation_ids = new_operations
