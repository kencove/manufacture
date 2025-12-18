# Copyright 2025 Kencove
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo.tests.common import TransactionCase


class TestMrpBomCosting(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        # Create products
        cls.product_finished = cls.env["product.product"].create(
            {
                "name": "Finished Product",
                "type": "product",
            }
        )

        cls.component1 = cls.env["product.product"].create(
            {
                "name": "Component 1",
                "type": "product",
                "standard_price": 10.0,
            }
        )

        cls.component2 = cls.env["product.product"].create(
            {
                "name": "Component 2",
                "type": "product",
                "standard_price": 20.0,
            }
        )

        # Create supplier info for components
        cls.env["product.supplierinfo"].create(
            {
                "product_tmpl_id": cls.component1.product_tmpl_id.id,
                "partner_id": cls.env.ref("base.res_partner_1").id,
                "price": 15.0,
            }
        )

        # Create workcenter
        cls.workcenter = cls.env["mrp.workcenter"].create(
            {
                "name": "Test Workcenter",
                "costs_hour": 50.0,
            }
        )

    def test_bom_cost_calculation_materials_only(self):
        """Test cost calculation with only materials (no operations)"""
        bom = self.env["mrp.bom"].create(
            {
                "product_tmpl_id": self.product_finished.product_tmpl_id.id,
                "product_qty": 1.0,
                "type": "normal",
                "bom_line_ids": [
                    (
                        0,
                        0,
                        {
                            "product_id": self.component1.id,
                            "product_qty": 2.0,
                        },
                    ),
                    (
                        0,
                        0,
                        {
                            "product_id": self.component2.id,
                            "product_qty": 1.0,
                        },
                    ),
                ],
            }
        )

        # Expected cost: (2 * 15.0) + (1 * 20.0) = 50.0
        # Component 1 uses supplier price (15.0), Component 2 uses standard_price (20.0)
        self.assertEqual(bom.next_production_cost, 50.0)
        self.assertTrue(bom.next_production_cost_write_date)

    def test_bom_cost_calculation_with_operations(self):
        """Test cost calculation including labor costs"""
        bom = self.env["mrp.bom"].create(
            {
                "product_tmpl_id": self.product_finished.product_tmpl_id.id,
                "product_qty": 1.0,
                "type": "normal",
                "bom_line_ids": [
                    (
                        0,
                        0,
                        {
                            "product_id": self.component1.id,
                            "product_qty": 1.0,
                        },
                    ),
                ],
                "operation_ids": [
                    (
                        0,
                        0,
                        {
                            "name": "Assembly",
                            "workcenter_id": self.workcenter.id,
                            "time_cycle": 60.0,  # 60 minutes
                        },
                    ),
                ],
            }
        )

        # Expected cost: (1 * 15.0) + (1 hour * 50.0/hour) = 65.0
        self.assertEqual(bom.next_production_cost, 65.0)

    def test_cost_update_on_price_change(self):
        """Test that cost updates when component price changes"""
        bom = self.env["mrp.bom"].create(
            {
                "product_tmpl_id": self.product_finished.product_tmpl_id.id,
                "product_qty": 1.0,
                "type": "normal",
                "bom_line_ids": [
                    (
                        0,
                        0,
                        {
                            "product_id": self.component1.id,
                            "product_qty": 1.0,
                        },
                    ),
                ],
            }
        )

        initial_cost = bom.next_production_cost
        self.assertEqual(initial_cost, 15.0)

        # Update supplier price
        supplier = self.component1.seller_ids[0]
        supplier.write({"price": 25.0})

        # Force recomputation by invalidating and flushing
        bom.env.flush_all()
        bom.invalidate_recordset(["next_production_cost"])

        # Cost should update to reflect new supplier price
        self.assertEqual(bom.next_production_cost, 25.0)
