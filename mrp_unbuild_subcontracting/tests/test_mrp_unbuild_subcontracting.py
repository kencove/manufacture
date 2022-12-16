from odoo.tests import Form, TransactionCase


class TestSubcontractingPurchaseFlows(TransactionCase):
    def setUp(self):
        super().setUp()

        self.subcontractor = self.env["res.partner"].create(
            {"name": "SuperSubcontractor"}
        )

        self.finished, self.compo = self.env["product.product"].create(
            [
                {
                    "name": "SuperProduct",
                    "type": "product",
                },
                {
                    "name": "Component",
                    "type": "consu",
                },
            ]
        )

        self.bom = self.env["mrp.bom"].create(
            {
                "product_tmpl_id": self.finished.product_tmpl_id.id,
                "type": "subcontract",
                "subcontractor_ids": [(6, 0, self.subcontractor.ids)],
                "bom_line_ids": [
                    (
                        0,
                        0,
                        {
                            "product_id": self.compo.id,
                            "product_qty": 1,
                        },
                    )
                ],
            }
        )

    def test_purchase_and_return(self):
        """
        The user buys 10 x a subcontracted product P. He receives the 10
        products and then does a return with 3 x P. The test ensures that
        the unbuild is created with the correct quantities and states
        """
        po = self.env["purchase.order"].create(
            {
                "partner_id": self.subcontractor.id,
                "order_line": [
                    (
                        0,
                        0,
                        {
                            "name": self.finished.name,
                            "product_id": self.finished.id,
                            "product_uom_qty": 10,
                            "product_uom": self.finished.uom_id.id,
                            "price_unit": 1,
                        },
                    )
                ],
            }
        )
        po.button_confirm()

        mo = self.env["mrp.production"].search([("bom_id", "=", self.bom.id)])
        self.assertTrue(mo)

        receipt = po.picking_ids
        receipt.move_lines.quantity_done = 10
        receipt.button_validate()

        return_form = Form(
            self.env["stock.return.picking"].with_context(
                active_id=receipt.id, active_model="stock.picking"
            )
        )
        with return_form.product_return_moves.edit(0) as line:
            line.quantity = 3
            line.to_refund = True
        return_wizard = return_form.save()
        return_id, _ = return_wizard._create_returns()

        return_picking = self.env["stock.picking"].browse(return_id)
        return_picking.move_lines.quantity_done = 3
        subcontractor_location = self.subcontractor.property_stock_subcontractor
        unbuild = self.env["mrp.unbuild"].search([("bom_id", "=", self.bom.id)])

        self.assertTrue(unbuild)
        self.assertEqual(
            unbuild.state, "draft", "The state of the unbuild should be draft"
        )
        self.assertEqual(
            unbuild.product_qty, 3, "The quantity of the unbuild should be 3"
        )
        self.assertEqual(
            unbuild.location_id,
            subcontractor_location,
            "The source location of the unbuild should be the property stock "
            "of the subcontractor",
        )
        self.assertEqual(
            unbuild.location_dest_id,
            subcontractor_location,
            "The destination location of the unbuild should be the property "
            "stock of the subcontractor",
        )

        return_picking.button_validate()

        self.assertEqual(self.finished.qty_available, 7.0)
        self.assertEqual(po.order_line.qty_received, 7.0)
        self.assertEqual(
            unbuild.state, "done", "The state of the unbuild should be done"
        )
        # Check that the filter return False if the state is done
        filter_done = unbuild._subcontracting_filter_to_done()
        self.assertFalse(
            filter_done,
        )

        move = return_picking.move_lines
        self.assertEqual(
            move.location_id,
            receipt.location_dest_id,
            "The source location of the stock move should be the same as "
            "destination location of the original purchase",
        )
        self.assertEqual(
            move.location_dest_id,
            subcontractor_location,
            "The destination location of the stock move should be the property "
            "stock of the subcontractor",
        )

        # Call the action to view the layers associated to the pickings
        result1 = return_picking.action_view_stock_valuation_layers()
        result2 = receipt.action_view_stock_valuation_layers()
        layers1 = result1["domain"][2][2]
        layers2 = result2["domain"][2][2]
        self.assertTrue(
            layers1,
        )
        self.assertTrue(
            layers2,
        )
