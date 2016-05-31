from openerp import models, fields, api, exceptions, _
from datetime import datetime, date
from openerp.exceptions import ValidationError
from dateutil.relativedelta import *
import calendar


class TransferStocktoMn(models.Model):

    _name='estate.nursery.transfermn'
    _inherit = ['mail.thread',]

    def _default_session(self):
        return self.env['estate.nursery.batch'].browse(self._context.get('active_id'))

    name=fields.Char()
    transfermn_code=fields.Char()
    batch_id=fields.Many2one('estate.nursery.batch',string="Batch No", required=True, default=_default_session,ondelete="cascade")
    partner_id = fields.Many2one('res.partner')
    qty_move =fields.Integer('Quantity Move',compute="_compute_total_normal" , store=True)
    location_mn_id = fields.Many2one('estate.block.template', "Plot",
                                  domain=[('estate_location', '=', True),
                                          ('estate_location_level', '=', '3'),
                                          ('estate_location_type', '=', 'nursery'),
                                          ('stage_id','=',2),
                                          ('scrap_location', '=', False)],
                                  help="Fill in location seed planted.", store=True)
    vehicle_timesheet_ids = fields.One2many('estate.timesheet.activity.transport','owner_id')
    transfermnline_ids=fields.One2many('estate.nursery.transfermnline','transfermn_id')

    date_transfer = fields.Date('Date Transfer Mn',required=True,store=True)

    state= fields.Selection([
        ('draft', 'Draft'),
        ('confirmed', 'Confirmed'),
        ('done', 'Done')], string="State",store=True)


    #sequence
    def create(self, cr, uid, vals, context=None):
        vals['transfermn_code']=self.pool.get('ir.sequence').get(cr, uid,'estate.nursery.transfermn')
        res=super(TransferStocktoMn, self).create(cr, uid, vals)
        return res

    #workflow state
    @api.one
    def action_draft(self):
        """Set Selection State to Draft."""
        self.state = 'draft'

    @api.one
    def action_confirmed(self):
        """Set Selection state to Confirmed."""
        self.state = 'confirmed'

    @api.one
    def action_approved(self):
        """Approved Selection is planted Seed."""
        batch = self.batch_id.name
        self.write({'name':"Transfer MN for %s" %(batch)})
        self.action_receive()
        self.state = 'done'


    @api.one
    def action_receive(self):
        self.qty_move = 0
        for itemmove in self.transfermnline_ids:
            self.qty_move += itemmove.qty_move
        self.write({'qty_move':self.qty_move})
        self.action_move()
        return True

    @api.one
    def action_move(self):

        location_ids = set()
        for item in self.transfermnline_ids:
            if item.location_pn_id and item.qty_move > 0: # todo do not include empty quantity location
                location_ids.add(item.location_pn_id.inherit_location_id)

        for location in location_ids:
            qty_total_normal = 0
            qty = self.env['estate.nursery.transfermnline'].search([('location_pn_id.inherit_location_id', '=', location.id),
                                                                   ('transfermn_id', '=', self.id)
                                                                   ])
            for i in qty:
                qty_total_normal += i.qty_move

            move_data = {
                'product_id': self.batch_id.product_id.id,
                'product_uom_qty': qty_total_normal,
                'origin':self.batch_id.name,
                'product_uom': self.batch_id.product_id.uom_id.id,
                'name': ' %s Transfer MN: for %s'%(self.transfermn_code,self.batch_id),
                'date_expected': self.date_transfer,
                'location_id': location.id,
                'location_dest_id': self.location_mn_id.inherit_location_id.id,
                'state': 'confirmed', # set to done if no approval required
                'restrict_lot_id': self.batch_id.lot_id.id # required by check tracking product
            }

            move = self.env['stock.move'].create(move_data)
            move.action_confirm()
            move.action_done()

    #Compute quantity move
    @api.one
    @api.depends('transfermnline_ids')
    def _compute_total_normal(self):
        if self.transfermnline_ids:
            for item in self.transfermnline_ids:
                self.qty_move += item.qty_move
        return True


    #constraint quantity move not more than qty plated batch
    @api.constrains('batch_id','transfermnline_ids')
    def constraint_quantity_move(self):
        if self.transfermnline_ids:
           for qtymove in self.transfermnline_ids:
               qty_move = qtymove.qty_move
               if qty_move > self.batch_id.qty_planted:
                    error_msg = "Quantity Move  is set not more than Quantity Planted in Batch "
                    raise exceptions.ValidationError(error_msg)
        return True

    @api.multi
    @api.constrains('vehicle_timesheet_ids')
    def _constraints_line_timesheet_mustbe_filled(self):
        #Constraint Line activity_Transfer must be filled
            countActivity = 0
            for item in self:
                countActivity += len(item.vehicle_timesheet_ids)
            if countActivity == 0 :
                error_msg = "Line Activity Must be filled"
                raise exceptions.ValidationError(error_msg)

    @api.one
    @api.constrains('vehicle_timesheet_ids')
    def _constraints_timesheet_unit(self):
        #constraint timesheet for quantity unit not more than qty move
        qty_unit = 0
        if self.vehicle_timesheet_ids:
            for timesheet in self.vehicle_timesheet_ids:
                qty_unit += timesheet.unit
            if qty_unit > self.qty_move:
                error_msg = "Unit not more than \"%s\" in qty move" % self.qty_move
                raise exceptions.ValidationError(error_msg)
        return True

    @api.one
    @api.constrains('vehicle_timesheet_ids')
    def _constraint_date_timesheet(self):
        #constraint date in move to mn must be same in time sheet ids
        if self.vehicle_timesheet_ids:
            for vehicletimesheet in self.vehicle_timesheet_ids:
                date = vehicletimesheet.date_activity_transport
            if date > self.date_transfer:
                error_msg = "Date not more than \"%s\" in Date move" % self.date_transfer
                raise exceptions.ValidationError(error_msg)
            elif date < self.date_transfer:
                error_msg = "Date must be same \"%s\" in Date move" % self.date_transfer
                raise exceptions.ValidationError(error_msg)



class transferpntomnline(models.Model):

    _name="estate.nursery.transfermnline"

    name=fields.Char("")
    batch_id=fields.Many2one('estate.nursery.batch')
    transfermn_id=fields.Many2one('estate.nursery.transfermn')
    qty_move = fields.Integer('Quantity to Move')
    location_pn_id = fields.Many2one('estate.block.template', "Bedengan",
                                  domain=[('estate_location', '=', True),
                                          ('estate_location_level', '=', '3'),
                                          ('estate_location_type', '=', 'nursery'),
                                          ('stage_id','=',3),
                                          ('scrap_location', '=', False)],
                                  help="Fill in location seed planted.")
    @api.multi
    @api.onchange('location_pn_id','batch_id')
    def _change_domain_locationpnid(self):
        batchline=self.env['estate.nursery.batchline'].search([('batch_id.id','=',self.batch_id.id),('location_id.id','!=',False)])
        if self:
            arrBatchline = []
            for a in batchline:
                estate=self.env['estate.block.template'].search([('id','=',a.location_id[0].id)])
                stock=self.env['stock.location'].search([('id','=',estate.inherit_location_id[0].id)])
                idlot= self.env['estate.nursery.batch'].search([('id','=',self.batch_id.id)])
                qty = self.env['stock.quant'].search([('lot_id.id','=',idlot[0].lot_id.id),('location_id.id','=',stock[0].id)])
                if qty[0].qty > 0:
                    arrBatchline.append(a.location_id.id)

            print arrBatchline
            return {
                    'domain': {'location_pn_id': [('id','in',arrBatchline)]},
            }
        return True
