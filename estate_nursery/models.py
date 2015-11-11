# -*- coding: utf-8 -*-

from openerp import models, fields, api, exceptions

# class estate_nursery(models.Model):
#     _name = 'estate_nursery.estate_nursery'

#     name = fields.Char()

class EstateLocation(models.Model):
    """Extend Location for Nursery Location"""
    _inherit = 'stock.location'

    qty_seed = fields.Integer(string="Seed Quantity")
    stage_id = fields.Many2one('estate.nursery.stage', "Nursery Stage")


class Seed(models.Model):
    _inherit = 'product.template'

    seed = fields.Boolean("Seed Product", help="Included at Seed Management.", default=False)
    # age_purchased = fields.Integer("Purchased Age", help="Fill in age of seed in month") # deprecated move to stock_quant
    variety_id = fields.Many2one('estate.nursery.variety', "Seed Variety",
                                 help="Select Seed Variety.")
    progeny_id = fields.Many2one('estate.nursery.progeny', "Progeny",
                                 help="Value depends on Seed Variety.")


class Stage(models.Model):
    """
    Seed nursery has two kind of method. First, single stage. Second, double stage (common).
    """
    _name = 'estate.nursery.stage'
    _sequence = 'sequence, name'

    name = fields.Char("Nursery Stage", required=True)
    code = fields.Char("Short Name", help="Use for reporting label purposes.", size=3)
    sequence = fields.Integer("Sequence No")
    age_minimum = fields.Integer("Minimum Age", help="Minimum age required to be at this stage. 0 is unlimited.")
    age_maximum = fields.Integer("Maximum Age", help="Maximum age required to be at this stage. 0 is unlimited.")


class Variety(models.Model):
    """Seed Variety"""
    _name = 'estate.nursery.variety'

    name = fields.Char(string="Variety Name")
    code = fields.Char(string="Short Name", help="Use for reporting label purposes.", size=3)
    comment = fields.Text(string="Additional Information")
    active = fields.Boolean("Planting Allowed", default=True, help="Seed Variety allowed to be planted.")


class Progeny(models.Model):
    """Seed Progeny"""
    _name = 'estate.nursery.progeny'

    name = fields.Char(string="Progeny Name")
    code = fields.Char(string="Short Name", help="Use for reporting label purposes.", size=3)
    variety_id = fields.Many2one('estate.nursery.variety', "Seed Variety")
    comment = fields.Text(string="Additional Information")
    active = fields.Boolean("Planting Allowed", default=True, help="Seed Progeny allowed to be planted.")
    supplier_id = fields.Many2one('res.partner', string="Supplier", domain=[('supplier','=',True)])
    height_tree = fields.Float('Tree Height', digits=(2,2))
    height_growth_speed= fields.Float('Average Growth Speed', help='Average growth speed per metric/year', digts=(2,2))
    age_harvest = fields.Integer('Harvested Age', help='Ripe Age in Month')
    weight_bunch = fields.Float('Average Weight FBR', help='Average weight in kilograms.')
    oil_production = fields.Float('Oil Production', help='Average oil production per tonne/hectare/year', digits=(2,2))


class Condition(models.Model):
    _name = 'estate.nursery.condition'

    name = fields.Char("Box/Plastic Condition")
    condition_category = fields.Selection([('1','Box'),('2','Bag/Plastic')], "Category")
    broken = fields.Boolean("Broken Condition", help="Condition marked as broken will go to Culling.", default=False)
    sequence = fields.Integer("Sequence No")
    comment = fields.Text("Additional Information")


class Batch(models.Model):
    """Delegation Inheritance Product for Seed Batch"""
    _name = 'estate.nursery.batch'
    _description = "Seed Batch"
    _inherits = {'stock.production.lot': 'lot_id'}

    name = fields.Char("Batch No")
    lot_id = fields.Many2one('stock.production.lot', required=False, ondelete="restrict", domain=[('product_id.seed','=',True)])
    variety_id = fields.Many2one('estate.nursery.variety', "Seed Variety", required=True, ondelete="restrict")
    progeny_id = fields.Many2one('estate.nursery.progeny', "Seed Progeny", required=True, ondelete="restrict",
                                 domain="[('variety_id','=',variety_id)]")
    date_received = fields.Date("Received Date")
    age_seed = fields.Integer("Seed Age", required=True)
    batchline_ids = fields.One2many('estate.nursery.batchline', 'batch_id', "Seed Boxes")
    comment = fields.Text("Additional Information")
    state = fields.Selection([
        ('draft','Draft'),
        ('0','Seed Selection'),
        ('1','Selection 1 (PN)'),
        ('2','Selection 2 (PN)'),
        ('3','Selection 1 (MN)'),
        ('4','Selection 2 (MN)'),
        ('5','Selection 3 (MN)'),
        ('done','Done')], default='draft', string="Phase")

    @api.one
    def action_draft(self):
        """Set Batch State to draft"""
        self.state = 'draft'

    @api.one
    def action_selection(self):
        """Set Batch State to selection"""
        self.state = '0'

    @api.one
    def action_selection_next(self):
        """Set Batch State to next selection"""
        if int(self.state) < 6:
            self.state = str(int(self.state)+1)

class Batchline(models.Model):
    """Batch Line to record seed in box/bag."""
    _name = 'estate.nursery.batchline'
    _description = "Seed Batch Line (Box/Bag)"
    _parent_store = True
    _parent_name = "parent_id"
    _parent_order = "name"

    name = fields.Char("Name")
    complete_name = fields.Char("Supplier Name")
    packaging_id = fields.Many2one('product.packaging', "Packaging Type")
    parent_id = fields.Many2one('estate.nursery.batchline', "Parent Package", ondelete="restrict")
    parent_left = fields.Integer('Parent Left', index=True)
    parent_right = fields.Integer('Parent Right', index=True)
    child_ids = fields.One2many('estate.nursery.batchline', 'parent_id', "Contains")
    batch_id = fields.Many2one('estate.nursery.batch', "Batch")
    seed_qty = fields.Integer("Seed Quantity")


class Box(models.Model):
    """Deprecated. Use Batchline."""
    _name = 'estate.nursery.box'

    name = fields.Char("Box Number")
    batch_id = fields.Many2one('estate.nursery.batch', "Box Number")
    condition_id = fields.Many2one('estate.nursery.condition', "Box Condition", domain="[('condition_category','=','1')]")
    bag_ids = fields.One2many('estate.nursery.bag', 'box_id', "Bags/Plastics")

class Bag(models.Model):
    """Deprecated. Use Batchline."""
    _name = 'estate.nursery.bag'

    name = fields.Char("Bag Number")
    box_id = fields.Many2one('estate.nursery.batch', "Box Number")
    condition_id = fields.Many2one('estate.nursery.condition', "Bag/Plastic Condition", domain="[('condition_category','=','1')]")
    qty_seed = fields.Integer("Seed Quantity")


class Selection(models.Model):
    """Delegation Inheritance Stock Quant for Seed Selection"""
    _name = 'estate.nursery.selection'
    _inherits = {'stock.quant': 'quant_id'}

    #quant_id = fields.Many2one('stock.quant') #bag
    bag_selection_ids = fields.One2many('estate.nursery.selection_line','selection_id',"Selection")


class SelectionLine(models.Model):
    """Quantity and condition of Seed Selection per Bag"""
    _name = 'estate.nursery.selection_line'

    selection_id = fields.Many2one('estate.nursery.selection',"Selection")
    qty = fields.Integer('Quantity')
    cause_id = fields.Many2one('estate.nursery.cause', "Cause")

class Cause(models.Model):
    """Selection Cause (normal, afkir, etc)."""
    _name = 'estate.nursery.cause'
    _sequence = 'sequence'

    name = fields.Char('Name')
    comment = fields.Text('Cause Description')
    code = fields.Char('Cause Abbreviation', size=3)
    sequence = fields.Integer('Sequence No')
    selection_type = fields.Selection([('0', 'Broken'),('1', 'Normal'),('2', 'Politonne')], "Selection Type")
    stage_id = fields.Many2one('estate.nursery.stage', "Nursery Stage")

class TransferDetail(models.TransientModel):
    """Extend Transfer Detail to create Seed Batch."""
    _inherit = 'stock.transfer_details'

    age_seed = fields.Integer("Seed Age")

    @api.one
    def do_detailed_transfer(self):
        """
        Extend stock transfer wizard to create stock move and lot.
        """
        date_done = self.picking_id.date_done
        partner = self.picking_id.partner_id
        lot_new = self.env['stock.production.lot']

        for item in self.item_ids:

            print "Create stock move Supplier to Internal Warehouse (super)."

            if item.product_id.seed:
                print "Create stock move from Internal Warehouse to Production."

                if date_done or item.variety_id or item.progeny_id:
                    lot_new = self.do_create_lot(item.product_id)
                    item.write({'lot_id': lot_new[0].id})
                    batch = self.do_create_batch(item, self, lot_new[0])
                    batchlines = self.do_create_batchline(item, batch[0])
                else:
                    raise exceptions.Warning('Required Date of Transfer, Variety and Progeny.')

            # Create stock move Supplier to Internal Warehouse (Gudang Kebun)
            super(TransferDetail, self).do_detailed_transfer()
        return True

    @api.one
    def do_create_lot(self, product):
        serial = self.env['estate.nursery.batch'].search_count([]) + 1

        lot_data = {
            'name': "Batch %d" % serial,
            'product_id': product.id
        }

        return self.env['stock.production.lot'].create(lot_data)

    @api.one
    def do_create_batch(self, item, transfer, lot):
        """Create Lot and Seed Batch per transfer item."""
        date_done = transfer.picking_id.date_done
        partner =  transfer.picking_id.partner_id
        product = item.product_id
        packaging = product.packaging_ids[0]

        serial = self.env['estate.nursery.batch'].search_count([]) + 1

        batch_data = {
            'name': "Batch %d" % serial,
            'lot_id': lot.id,
            'variety_id': item.variety_id.id,
            'progeny_id': item.progeny_id.id,
            'date_received': date_done,
            'age_seed': transfer.age_seed
        }

        # print "Create Seed Batch. %s (v: %s, p: %s) is received at %s from %s" % (item.product_id.name,
        #                                                                                 item.variety_id.name,
        #                                                                                 item.progeny_id.name,
        #                                                                                 date_done,
        #                                                                                 partner.name)

        # Check and create batch (box) and batchline (bag) for seed product.
        #       if product has no package
        #           create one box and one bag
        #       else
        #           create batch and its batchline as product package.
        # Check and create lot for current good receipt
        # print "Create Box and Bag Packaging is %s (box: %s, bag: %s @ %s)" % (product.name,
        #                                                    packaging.ul_container.name,
        #                                                    packaging.ul.name,
        #                                                    packaging.qty * packaging.ul_qty)

        return self.env['estate.nursery.batch'].create(batch_data)

    @api.one
    def do_create_batchline(self, item, batch):
        """Calculate and create seed bag"""
        product = item.product_id
        pak = product.packaging_ids[0]

        if pak:
            pak_row = pak.rows
            pak_row_bag = pak.ul_qty
            pak_total_bag = pak.rows * pak.ul_qty
            pak_bag_content = pak.qty
        else:
            pak_row = 3
            pak_row_bag = 9
            pak_total_bag = pak.rows * pak.ul_qty
            pak_bag_content = 200

        pak_content = pak_row * pak_row_bag * pak_bag_content

        item_qty = item.quantity
        serial = 0

        # Count full box
        box_amount_full = int(item_qty/pak_content)

        if item_qty % pak_content:
            box_amount_half = 1
        else:
            box_amount_half = 0

        total_box = box_amount_full + box_amount_half

        if box_amount_full:
            for i in range(box_amount_full):
                serial += 1
                bag_serial = 0
                box_data = {
                    'name': "%s / Box %d" % (batch.name, serial),
                    'batch_id': batch.id,
                    'packaging_id': pak.id,
                    'batch_id': batch.id
                }
                box = self.env['estate.nursery.batchline'].create(box_data)
                for d in range(pak_total_bag):
                    bag_serial += 1
                    bag_data = {
                        'name': "%s / Bag %d.%d" % (box.name, serial, bag_serial),
                        'batch_id': batch.id,
                        'packaging_id': pak.id,
                        'parent_id': box.id,
                        'seed_qty': pak_bag_content
                    }
                    self.env['estate.nursery.batchline'].create(bag_data)

        if box_amount_half:
            print "Create 1 half box (amount %d seed)" % (item_qty % pak_content)
            serial += 1
            bag_serial = 0
            seed_qty = item_qty % pak_content
            bag_amount_full = int(seed_qty/pak_bag_content)

            box_data = {
                'name': "%s / Box %d" % (batch.name, serial),
                'batch_id': batch.id,
                'packaging_id': pak.id,
            }
            box = self.env['estate.nursery.batchline'].create(box_data)

            if bag_amount_full:
                print "  Create %d full bag" % bag_amount_full
                for i in range(bag_amount_full):
                    bag_serial += 1
                    bag_data = {
                        'name': "%s / Bag %d.%d" % (box.name, serial, bag_serial),
                        'batch_id': batch.id,
                        'packaging_id': pak.id,
                        'parent_id': box.id,
                        'seed_qty': pak_bag_content
                    }
                    self.env['estate.nursery.batchline'].create(bag_data)

            if seed_qty % pak_bag_content:
                bag_amount_half = 1
                bag_serial += 1
                bag_data = {
                    'name': "%s / Bag %d.%d" % (box.name, serial, bag_serial),
                    'batch_id': batch.id,
                    'packaging_id': pak.id,
                    'parent_id': box.id,
                    'seed_qty': seed_qty % pak_bag_content
                }
                self.env['estate.nursery.batchline'].create(bag_data)

        return True

class TransferDetailItem(models.TransientModel):
    """
    Extend Transfer Detail Items to include Variety and Progeny information
    """
    _inherit = 'stock.transfer_details_items'

    is_seed = fields.Boolean("Is Seed", related='product_id.seed')
    variety_id = fields.Many2one('estate.nursery.variety', "Seed Variety", ondelete="restrict")
    progeny_id = fields.Many2one('estate.nursery.progeny', "Seed Progeny", ondelete="restrict",
                                 domain="[('variety_id','=',variety_id)]")