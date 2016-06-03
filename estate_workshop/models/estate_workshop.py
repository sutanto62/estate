from openerp import models, fields, api, exceptions
from datetime import datetime, date
from openerp.exceptions import ValidationError
from dateutil.relativedelta import *
import calendar
import time
import datetime
from openerp import tools

class InheritSparepartLog(models.Model):

    _inherit='estate.vehicle.log.sparepart'

    maintenance_id = fields.Integer()

class InheritProduct(models.Model):

    _inherit = 'product.template'

    part_number = fields.Char('Part Number')

class InheritSparepartids(models.Model):

    _inherit = 'mro.order'

    type_service = fields.Selection([('1','Vehicle'),
                                     ('2','Building'),('3','Machine'),('4','Computing'),('5','ALL')],readonly=True)
    # sparepartlog_ids=fields.One2many('estate.vehicle.log.sparepart','maintenance_id',"Part Log",
    #                                          readonly=True, states={'draft':[('readonly',False)]})

    #onchange
    @api.multi
    @api.onchange('asset_id','type_service')
    def onchange_type_service(self):
        if self.asset_id:
            self.type_service = self.asset_id.type_asset

class InheritTypeAsset(models.Model):

    _inherit =  'mro.request'
    _description = 'Notification workshop for corrective Maintenance'

    type_asset = fields.Selection([('1','Vehicle'),
                                     ('2','Building'),('3','Machine'),('4','Computing'),('5','ALL')],readonly=True)

    #onchange
    @api.multi
    @api.onchange('asset_id','type_asset')
    def onchange_type_asset(self):
        if self.asset_id:
            self.type_asset = self.asset_id.type_asset

    def action_confirmed(self, cr, uid, ids, context=None):
        """
        Update type_service into approved
        :return: True
        """
        order = self.pool.get('mro.order')
        order_id = False

        for request in self.browse(cr, uid, ids, context=context):
                order_id = order.create(cr, uid, {
                    'type_service' :request.type_asset
                })
        self.write(cr, uid, ids, {'state': 'run'})
        return super(InheritTypeAsset, self).action_confirmed()

class MasterTask(models.Model):

    _name = 'estate.workshop.mastertask'
    _description = 'Master task for maintenance'

    name=fields.Char('Master Task')
    mastertaskline_ids= fields.One2many('estate.workshop.mastertaskline','mastertask_id')
    type_task = fields.Selection([('1','Preventiv'),('2','Corective')])
    type_preventive = fields.Selection([('1','Periodic'),('2','Schedule Overhoul'),('3','Condition')],defaults=1)
    type_corective = fields.Selection([('1','Repair'),('2','BreakDown')])
    typetask_id = fields.Many2one('estate.master.type.task')

    #onchange
    @api.multi
    @api.onchange('type_task','type_preventive','type_corective','typetask_id')
    def _onchange_typetask_id(self):
        arrType=[]
        if self.type_task == '1':
            if self.type_preventive == '1':
                listtype = self.env['estate.master.type.task'].search([('type_task','=','1'),('type','=','normal')])
                for a in listtype:
                    arrType.append(a.id)
                return {
                    'domain':{
                        'typetask_id':[('id','in',arrType)]
                    }
                }
            elif self.type_preventive == '2':
                listtype = self.env['estate.master.type.task'].search([('type_task','=','2'),('type','=','normal')])
                for a in listtype:
                    arrType.append(a.id)
                return {
                    'domain':{
                        'typetask_id':[('id','in',arrType)]
                    }
                }
            elif self.type_preventive == '3' :
                listtype = self.env['estate.master.type.task'].search([('type_task','=','3'),('type','=','normal')])
                for a in listtype:
                    arrType.append(a.id)
                return {
                    'domain':{
                        'typetask_id':[('id','in',arrType)]
                    }
                }

        elif self.type_task == '2' :
            if self.type_corective == '1' :
                listtype = self.env['estate.master.type.task'].search([('type_task','=','4'),('type','=','normal')])
                for a in listtype:
                    arrType.append(a.id)
                return {
                    'domain':{
                        'typetask_id':[('id','in',arrType)]
                    }
                }
            elif self.type_corective == '2' :
                listtype = self.env['estate.master.type.task'].search([('type_task','=','5'),('type','=','normal')])
                for a in listtype:
                    arrType.append(a.id)
                return {
                    'domain':{
                        'typetask_id':[('id','in',arrType)]
                    }
                }


class MasterTaskLine(models.Model):

    _name = 'estate.workshop.mastertaskline'

    name=fields.Char('Master Task Line')
    task_id=fields.Many2one('mro.task')
    mastertask_id = fields.Integer()

class MasterTypeTask(models.Model):

    _name = 'estate.master.type.task'

    name=fields.Char('Name Type')
    complete_name = fields.Char("Complete Name", compute="_complete_name", store=True)
    parent_id = fields.Many2one('estate.master.type.task', "Parent Category", ondelete='restrict')
    parent_left = fields.Integer("Parent Left",	index=True)
    parent_right = fields.Integer("Parent Right", index=True)
    child_ids = fields.One2many('estate.master.type.task', 'parent_id', "Child Type")
    type= fields.Selection([('view', "View"),
                             ('normal', "Normal")], "Type",
                            required=True,
                            help="Select View to create group of activities.")
    type_task= fields.Selection([('1','Periodic'),('2','Schedule Overhoul'),
                            ('3','Condition'),('4','Repair'),('5','BreakDown')])
    description=fields.Text()

    @api.one
    @api.depends('name', 'parent_id')
    def _complete_name(self):
        """ Forms complete name of location from parent category to child category.
        """
        if self.parent_id:
            self.complete_name = self.parent_id.complete_name + ' / ' + self.name
        else:
            self.complete_name = self.name

        return True

class MasterSheduleMaintenance(models.Model):

    _name = 'estate.master.shedule'

    name= fields.Char()
    date = fields.Date()
    odometer_min = fields.Float()
    odometer_max = fields.Float()


class MasterCatalog(models.Model):

    _name='estate.part.catalog'
    _order = 'complete_name'

    name=fields.Char('Master Catalog')
    complete_name =fields.Char("Complete Name", compute="_complete_name", store=True)
    parent_id = fields.Many2one('estate.part.catalog', "Parent Category", ondelete='restrict')
    parent_left = fields.Integer("Parent Left",	index=True)
    parent_right = fields.Integer("Parent Right", index=True)
    child_ids = fields.One2many('estate.part.catalog', 'parent_id', "Child Type")
    type= fields.Selection([('view', "View"),
                             ('normal', "Normal")], "Type",
                            required=True,
                            help="Select View to create group of activities.")
    asset_id = fields.Many2one('asset.asset')
    categoryline_ids = fields.One2many('estate.part.catalogline','catalog_id','catalog_line')
    category_id = fields.Many2one('master.category.unit')


    @api.one
    @api.depends('name', 'parent_id')
    def _complete_name(self):
        """ Forms complete name of location from parent category to child category.
        """
        if self.parent_id:
            self.complete_name = self.parent_id.complete_name + ' / ' + self.name
        else:
            self.complete_name = self.name

        return True

class MasterCatalogLine(models.Model):

    _name = 'estate.part.catalogline'

    name = fields.Char('Catalog Line')
    product_id = fields.Many2one('product.product')
    part_number = fields.Char('Part Number')
    quantity_part = fields.Float('Quantity Part')
    catalog_id = fields.Integer()
