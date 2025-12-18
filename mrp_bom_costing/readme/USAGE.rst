After installing the module:

1. Navigate to Manufacturing > Products > Bills of Materials
2. Open any BOM record
3. The "Next Production Cost" field will automatically display the calculated cost
4. The cost is updated automatically when:

   * Component purchase prices change
   * Workcenter hourly costs change
   * Operation times are modified
   * BOM structure is updated

The calculation includes:

* **Material costs**: Sum of (component quantity × purchase price) for all components
* **Labor costs**: Sum of (operation time × workcenter hourly rate) for all operations
