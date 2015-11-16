# -*- coding: utf-8 -*-

from openerp import models, fields, api, exceptions, _

# class estate_nursery(models.Model):
#     _name = 'estate_nursery.estate_nursery'

#     name = fields.Char()

class EstateLocation(models.Model):
    """Extend Location for Nursery Location"""
    _inherit = 'stock.location'

    qty_seed = fields.Integer(string="Seed Quantity")
    stage_id = fields.Many2one('estate.nursery.stage', "Nursery Stage",ondelete="set null")


class Seed(models.Model):
    _inherit = 'product.template'

    seed = fields.Boolean("Seed Product", help="Included at Seed Management.", default=False)
    # age_purchased = fields.Integer("Purchased Age", help="Fill in age of seed in month") # deprecated move to stock_quant
    variety_id = fields.Many2one('estate.nursery.variety', "Seed Variety",
                                 help="Select Seed Variety.") # todo active = true
    progeny_id = fields.Many2one('estate.nursery.progeny', "Progeny",
                                 help="Value depends on Seed Variety.") # todo filtered by variety_id, active = true


class Stage(models.Model):
    """
    Seed nursery has two kind of method. First, single stage. Second, double stage (common).
    """
    _name = 'estate.nursery.stage'
    #_sequence = 'sequence,name'
    #_defaults = { 'name': lambda self,cr,uid,context={}: self.pool.get('ir.sequence').get(cr, uid, 'code'), }

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

    name = fields.Char(_("Batch No"))
    lot_id = fields.Many2one('stock.production.lot', "Lot",required=True, ondelete="restrict", domain=[('product_id.seed','=',True)])
    variety_id = fields.Many2one('estate.nursery.variety', "Seed Variety", required=True, ondelete="restrict")
    progeny_id = fields.Many2one('estate.nursery.progeny', "Seed Progeny", required=True, ondelete="restrict",
                                 domain="[('variety_id','=',variety_id)]")
    date_received = fields.Date("Received Date",required=False,readonly=False)
    date_planted = fields.Date("Planted Date",required=False,readonly=False)
    age_seed = fields.Integer("Seed Age", required=True)
    comment = fields.Text("Additional Information")
    qty_received = fields.Integer("Quantity Received")
    qty_normal = fields.Integer("Normal Seed Quantity")
    qty_abnormal = fields.Integer("Abnormal Seed Quantity")
    qty_planted = fields.Integer(_("Planted"), compute='_compute_total',store=True)
    qty_planted_temp = fields.Integer(_("Planted"), compute='_compute_total_temp',store=True)
    batchline_ids = fields.One2many('estate.nursery.batchline', 'batch_id', _("Seed Boxes")) # Detailed selection
    selection_ids = fields.One2many('estate.nursery.selection', 'batch_id', _("Selection"))# Detaileld selection
    product_id = fields.Many2one('product.product', "Product", related="lot_id.product_id")
    picking_id = fields.Many2one('stock.picking', "Picking", readonly=True ,)
    culling_location_id = fields.Many2one('stock.location', _("Culling Location"),
                                          domain=[('estate_location', '=', True),
                                                  ('estate_location_level', '=', '3'),
                                                  ('estate_location_type', '=', 'nursery'),('scrap_location', '=', True)])
    nursery_stage = fields.Selection([
        ('draft', 'Draft'),
        ('0', 'Seed Selection'),
        ('1', 'Seed Planted'),
        ('2', 'Selection 1 (PN)'),
        ('3', 'Selection 2 (PN)'),
        ('4', 'Selection 1 (MN)'),
        ('5', 'Selection 2 (MN)'),
        ('6', 'Selection 3 (MN)'),
        ('done', 'Done')], default='draft', string="Selection State")

    state = fields.Selection([
        ('draft', 'Draft'),
        ('confirmed', 'Confirmed'),
        ('done', 'Done')], string="State")

    @api.one
    def action_draft(self):
        """Set Batch State to Draft."""
        self.state = 'draft'

    @api.one
    def action_confirmed(self):
        """Set Batch state to Confirmed."""
        self.state = 'confirmed'

    @api.one
    def action_approved(self):
        """Approved Batch is planted Seed."""
        self.action_receive()
        self.state = 'done'

    @api.one
    def action_receive(self):
        """Count quantity of seed received and planted."""
        self.qty_normal = 0
        self.qty_abnormal = 0
        for item in self.batchline_ids:
            self.qty_normal += item.subtotal_normal
            self.qty_abnormal += item.subtotal_abnormal
        self.write({'nursery_stage': '0' , 'qty_normal': self.qty_normal, 'qty_abnormal': self.qty_abnormal})

        self.action_planted()

        return True

    @api.one
    def action_selection_next(self):
        """Set Batch State to next selection"""
        if int(self.nursery_stage) < 6:
            self.nursery_stage = str(int(self.nursery_stage)+1)

    @api.one
    def action_create_selection(self):
        print "Create Selection for batch %s" % self.name

    @api.one
    def action_planted(self):
        """
        Planted do two actions:
        1. Set state to Seed Planted.
        2. Move quantity of selection to production location.
        """

        self.nursery_stage = '1'

        # Get unique location of planted location
        location_ids = set()
        for item in self.batchline_ids:
            if item.location_id and item.qty_planted > 0: # todo do not include empty quantity location
                location_ids.add(item.location_id)

        # Move quantity normal seed
        for location in location_ids:
            qty_total_planted = 0
            bags = self.env['estate.nursery.batchline'].search([('location_id', '=', location.id),
                                                                   ('batch_id', '=', self.id)])
            for i in bags:
                qty_total_planted += i.qty_planted

            move_data = {
                'product_id': self.lot_id.product_id.id,
                'product_uom_qty': qty_total_planted,
                'product_uom': self.lot_id.product_id.uom_id.id,
                'name': 'Planted: %s' % self.lot_id.product_id.display_name,
                'date_expected': self.date_planted,
                'location_id': self.picking_id.location_dest_id.id,
                'location_dest_id': location.id,
                'state': 'confirmed', # set to done if no approval required
                'restrict_lot_id': self.lot_id.id # required by check tracking product
            }

            move = self.env['stock.move'].create(move_data)
            move.action_confirm()
            move.action_done()

        # Move quantity abnormal seed
        if self.qty_abnormal > 0:
            move_data = {
                'product_id': self.lot_id.product_id.id,
                'product_uom_qty': self.qty_abnormal,
                'product_uom': self.lot_id.product_id.uom_id.id,
                'name': 'Selection: %s' % self.lot_id.product_id.display_name,
                'date_expected': self.date_planted,
                'location_id': self.picking_id.location_dest_id.id,
                'location_dest_id': self.culling_location_id.id,
                'state': 'confirmed', # set to done if no approval required
                'restrict_lot_id': self.lot_id.id # required by check tracking product
            }

            move = self.env['stock.move'].create(move_data)
            move.action_confirm()
            move.action_done()

        return True

    @api.one
    @api.depends('batchline_ids','selection_ids')
    def _compute_total(self):
        self.qty_planted = 0
        for item in self.batchline_ids:
            self.qty_planted += item.qty_planted
        if self.selection_ids:
            for a in self.selection_ids:
                self.qty_planted -=a.qty_abnormal

        return True
        self.write({'qty_planted' : self.qty_planted})

    @api.one
    @api.depends('batchline_ids',)
    def _compute_total_temp(self):
        self.qty_planted_temp = 0
        for item in self.batchline_ids:
            self.qty_planted_temp += item.qty_planted
        return True


class Batchline(models.Model):
    """Batch Line to record seed selection and planting by box/bag."""
    _name = 'estate.nursery.batchline'
    _description = "Seed Batch Line (Box/Bag)"
    _parent_store = True
    _parent_name = "parent_id"
    _parent_order = "name"

    name = fields.Char("Name")
    complete_name = fields.Char("Supplier Packaging ID")
    packaging_id = fields.Many2one('product.packaging', "Packaging Type")
    parent_id = fields.Many2one('estate.nursery.batchline', "Parent Package", ondelete="restrict")
    parent_left = fields.Integer('Parent Left', index=True)
    parent_right = fields.Integer('Parent Right', index=True)
    child_ids = fields.One2many('estate.nursery.batchline', 'parent_id', "Contains")
    batch_id = fields.Many2one('estate.nursery.batch', "Batch")
    seed_qty = fields.Integer("DO Quantity")
    qty_single = fields.Integer("Single Tone Quantity")
    qty_double = fields.Integer("Double Tone Quantity")
    qty_broken = fields.Integer("Broken Seed Quantity")
    qty_dead = fields.Integer("Dead Seed Quantity")
    qty_fungus = fields.Integer("Fungus Seed Quantity")
    subtotal_normal = fields.Integer("Normal Seed Quantity", compute='_compute_subtotal')
    subtotal_abnormal = fields.Integer("Abnormal Seed Quantity", compute='_compute_subtotal')
    percentage_normal = fields.Float("Normal Ratio", digits=(2,2), compute='_compute_subtotal')
    percentage_abnormal = fields.Float("Abnormal Ratio", digits=(2,2), compute='_compute_subtotal')
    selection_do_var = fields.Integer("Variance", help="Seed selection ratio.", compute='_compute_variance')
    planting_selection_var = fields.Integer("Variance", help="Seed planted ratio", compute='_compute_variance')
    qty_planted = fields.Integer("Planted Quantity")
    location_id = fields.Many2one('stock.location', "Bedengan/Plot",
                                  domain=[('estate_location', '=', True),
                                          ('estate_location_level', '=', '3'),
                                          ('estate_location_type', '=', 'nursery'),('scrap_location', '=', False)],
                                  help="Fill in location seed planted.")

    @api.one
    @api.depends('qty_single', 'qty_double', 'qty_broken', 'qty_dead', 'qty_fungus')
    def _compute_subtotal(self):
        """Compute number and percentage of subtotal"""
        self.subtotal_normal = self.qty_single + self.qty_double
        self.subtotal_abnormal = self.qty_broken + self.qty_dead + self.qty_fungus
        total = self.subtotal_normal + self.subtotal_abnormal

        # Prevent division by zero as selection did not happen yet
        if total:
            self.percentage_normal = float(self.subtotal_normal) / float(total) * 100.00
            self.percentage_abnormal = float(self.subtotal_abnormal) / float(total) * 100.00

    @api.one
    @api.depends('subtotal_normal', 'subtotal_abnormal', 'qty_planted')
    def _compute_variance(self):
        """Compute variance of received and planted."""
        self.selection_do_var = (self.subtotal_normal + self.subtotal_abnormal) - self.seed_qty
        self.planting_selection_var = self.qty_planted - self.subtotal_normal

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

        # Iterate through transfer detail item
        for item in self.item_ids:
            if item.product_id.seed:
                if date_done or item.variety_id or item.progeny_id:
                    lot_new = self.do_create_lot(item.product_id)
                    item.write({'lot_id': lot_new[0].id})
                    batch = self.do_create_batch(item, self, lot_new[0])
                    self.do_create_batchline(item, batch[0])
                else:
                    raise exceptions.Warning('Required Date of Transfer, Variety and Progeny.')
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
            'age_seed': transfer.age_seed,
            'qty_received': item.quantity,
            'picking_id': transfer.picking_id.id,
            'state': 'draft'
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
            raise exceptions.Warning('Product %s has no packaging. Contact Administrator.' % product.name)

        pak_content = pak_row * pak_row_bag * pak_bag_content

        item_qty = item.quantity
        serial = 0

        # todo recode using recursive call (http://goo.gl/rjRtEs)

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