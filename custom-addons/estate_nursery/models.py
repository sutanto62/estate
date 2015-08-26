# -*- coding: utf-8 -*-

from openerp import models, fields, api

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
                                 help="Select Seed Variety.") # todo active = true
    progeny_id = fields.Many2one('estate.nursery.progeny', "Progeny",
                                 help="Value depends on Seed Variety.") # todo filtered by variety_id, active = true


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
    # partner_id = fields.Many2one('res.partner', string="Supplier", domain=[('supplier','=',True)]) # fixme company?
    active = fields.Boolean("Planting Allowed", default=True, help="Seed Variety allowed to be planted.")


class Progeny(models.Model):
    """Seed Progeny"""
    _name = 'estate.nursery.progeny'

    name = fields.Char(string="Progeny Name")
    code = fields.Char(string="Short Name", help="Use for reporting label purposes.", size=3)
    variety_id = fields.Many2one('estate.nursery.variety', "Seed Variety")
    comment = fields.Text(string="Additional Information")
    active = fields.Boolean("Planting Allowed", default=True, help="Seed Progeny allowed to be planted.")


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
    lot_id = fields.Many2one('stock.production.lot', required=True, ondelete="restrict",
                             domain=[('product_id.seed','=',True)])
    variety_id = fields.Many2one('estate.nursery.variety', "Seed Variety", required=True, ondelete="restrict")
    progeny_id = fields.Many2one('estate.nursery.progeny', "Seed Progeny", required=True, ondelete="restrict",
                                 domain="[('variety_id','=',variety_id)]")
    date_received = fields.Date("Received Date")
    age_seed = fields.Integer("Seed Age", required=True)
    batchline_ids = fields.One2many('estate.nursery.batchline', 'batch_id', "Seed Boxes")
    comment = fields.Text("Additional Information")

class Batchline(models.Model):
    """Batch Line to record seed in box/bag."""
    _name = 'estate.nursery.batchline'
    _description = "Seed Batch Line (Box/Bag)"
    _parent_store = True
    _parent_name = "parent_id"
    _parent_order = "name"

    name = fields.Char("Name")
    packaging_id = fields.Many2one('product.packaging', "Packaging Type")
    parent_id = fields.Many2one('estate.nursery.batchline', "Parent Package", ondelete="restrict")
    parent_left = fields.Integer('Parent Left', index=True)
    parent_right = fields.Integer('Parent Left', index=True)
    child_ids = fields.One2many('estate.nursery.batchline', 'parent_id', "Contains")
    batch_id = fields.Many2one('estate.nursery.batch', "Batch")


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

    quant_id = fields.Many2one('stock.quant') #bag
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
    _inherit = 'stock.transfer_details'

    date_received = fields.Date("Date Received") # todo hide if stock move product is not seed

    @api.one
    def do_detailed_transfer(self):
        """
        Extend stock transfer wizard for seed batch
        """
        for item in self.item_ids:
            # super(TransferDetail, self).do_detailed_transfer()
            # Create Seed Batch
            if item.product_id.seed:
                self.do_create_batch(item.lot_id)
                print "%s is a seed with Lot %s" % (item.product_id.seed, item.lot_id.name)

        return True

    @api.one
    def do_create_batch(self, lot):
        """
        Create Seed Batch
        """
