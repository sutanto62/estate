# -*- coding: utf-8 -*-

from openerp import models, fields, api, exceptions
from datetime import datetime, date
from dateutil.relativedelta import *
import calendar



select_category = ([('0','untimely'),('1','late'),('2','pass')])

class Selection(models.Model):
    """Seed Selection"""
    _name = 'estate.nursery.selection'

    names = fields.Char(related='batch_id.name')
    picking_id= fields.Many2one('stock.picking', "Picking",related="batch_id.picking_id")
    lot_id = fields.Many2one('stock.production.lot', "Lot",required=True, ondelete="restrict",
                             domain=[('product_id.seed','=',True)],related="batch_id.lot_id")
    selectionline_ids = fields.One2many('estate.nursery.selectionline', 'selection_id', "Selection Lines")
    batch_id = fields.Many2one('estate.nursery.batch', "Batch",)
    stage_id = fields.Many2one('estate.nursery.stage',"Stage")
    selectionstage_id = fields.Many2one('estate.nursery.selectionstage',"Selection Stage",
                                        required=True)
    qty_normal = fields.Integer("Normal Seed Quantity",compute="_compute_plannormal",store=True)
    qty_abnormal = fields.Integer("Abnormal Seed Quantity",compute='_compute_total')
    date_plant = fields.Date("Planted Date",required=False,readonly=True,related='batch_id.date_planted',store=True)
    qty_plant = fields.Integer("Planted Quantity",compute="_compute_plannormal",store=True)
    qty_plante = fields.Integer("plan qty")
    qty_batch = fields.Integer("DO Quantity",required=False,readonly=True,related='batch_id.qty_received',store=True)
    presentage_normal = fields.Float("Persentage Normal",digits=(2,2),required=False)
    presentage_abnormal = fields.Float("Persentage Abnormal",digits=(2,2), required=False)
    selection_date = fields.Date("Selection Date",required=True)
    selection_type = fields.Selection([('0', 'Broken'),('1', 'Normal'),('2', 'Politonne')], "Selection Type")
    selec = fields.Integer(related='selectionstage_id.age_selection')
    maxa = fields.Integer(related='selectionstage_id.age_limit_max')
    mina = fields.Integer(related='selectionstage_id.age_limit_min')
    comment = fields.Text("Additional Information")
    product_id = fields.Many2one('product.product', "Product", related="lot_id.product_id")
    nursery_information = fields.Selection([('draft','Draft'),
                                            ('0','untimely'),
                                            ('1','late'),('2','passed'),
                                            ('3','very late/Not recomend'),('4','very untimely/not recomend')],
                                           compute='dateinformation', default='draft', string="Information Time" ,
                                           readonly=True,required=False)
    nursery_lapseday = fields.Integer(string="Information Lapse of Day",
                                      required=False,readonly=True,compute='calculatedays',multi='sums',store=True)
    nursery_lapsemonth = fields.Integer(string="Information Lapse of Month",
                                        required=False,readonly=True,compute='calculatemonth',multi='sums',store=True)
    nursery_plandate = fields.Char('Planning Date',readonly=True,compute="calculateplandate",visible=True)
    nursery_plandatemax = fields.Char('Planning Date max',readonly=True,compute="calculateplandatemax",visible=True)
    nursery_plandatemin = fields.Char('Planning Date min',readonly=True,compute="calculateplandatemin",visible=True)
    nursery_persentagen = fields.Float(digit=(2.2),compute='computepersentage')
    nursery_persentagea = fields.Float(digit=(2.2),compute='computepersentage')
    state = fields.Selection([
        ('draft', 'Draft'),
        ('confirmed', 'Confirmed'),
        ('done', 'Done')], string="State")
    culling_location_id = fields.Many2one('stock.location',("Culling Location"),
                                          domain=[('estate_location', '=', True),
                                                  ('estate_location_level', '=', '3'),
                                                  ('estate_location_type', '=', 'nursery'),('scrap_location', '=', True)]
                                          ,related="batch_id.culling_location_id")


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
        self.action_receive()
        self.state = 'done'

    @api.one
    def action_receive(self):
        normal = self.qty_normal
        abnormal = self.qty_abnormal
        selectionlineids = self.selectionline_ids
        for item in selectionlineids:
            # normal += abnormal
            abnormal += item.qty
        self.write({'qty_abnormal': self.qty_abnormal, 'qty_normal' : self.qty_normal ,'qty_plant' : self.qty_plant})

        self.action_move()
        return True
    @api.one
    def action_move(self):


        # Move quantity abnormal seed
        if self.qty_abnormal > 0:
            move_data = {
                'product_id': self.batch_id.product_id.id,
                'product_uom_qty': self.qty_abnormal,
                'product_uom': self.batch_id.product_id.uom_id.id,
                'name': 'Selection Abnormal.%s: %s'%(self.selectionstage_id.name,self.lot_id.product_id.display_name),
                'date_expected': self.date_plant,
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
    @api.depends('batch_id','selectionline_ids')
    def _temp(self):
        if self.selectionline_ids:
            a = self.batch_id.qty_planted - self.qty_plant



    #compute qtyplant :
    @api.one
    @api.depends('qty_plant','qty_abnormal','batch_id','qty_plante','selectionline_ids')
    def _compute_plannormal(self):
        abn = self.qty_abnormal
        nrml = self.qty_normal
        plante = int(self.qty_plante)
        for qtyplanted in self.batch_id:
            qty_planted = 0
            src = self.env['estate.nursery.batch'].search([('qty_planted', '=', True),
                                                  ])
            src2 = self.env['estate.nursery.selection'].search([('qty_plant','=',True)])
        if self.selectionline_ids :
            hasil = plante - abn
            self.qty_normal = hasil
            self.qty_plant = hasil
            print hasil
        return  True

    #compute selectionLine
    @api.one
    @api.depends('selectionline_ids')
    def _compute_total(self):
        self.qty_abnormal = 0
        for item in self.selectionline_ids:
            self.qty_abnormal += item.qty
        return True

    #compute persentage
    @api.one
    @api.depends('qty_batch','qty_normal','qty_abnormal')
    def computepersentage(self):
        d1 = self.nursery_persentagen
        d2 = self.nursery_persentagea
        d3 = int(self.qty_normal)+int(self.qty_abnormal)
        if self.qty_abnormal and self.qty_normal:
            d1 =float(self.qty_normal)/float(self.qty_batch)*float(100.00)
            d2 =float(self.qty_abnormal)/float(self.qty_batch)*float(100.00)
            self.nursery_persentagea = d2
            self.nursery_persentagen = d1

    #compute lapseday
    @api.one
    @api.depends('date_plant','selection_date',)
    def calculatedays(self):
        res={}
        fmt = '%Y-%m-%d'
        if self.date_plant and self.selection_date :
            from_date = self.date_plant
            to_date = self.selection_date
            conv_fromdate = datetime.strptime(str(from_date), fmt)
            conv_todate = datetime.strptime(str(to_date),fmt)
            d1= conv_fromdate
            d2= conv_todate
            hasil= str((d2-d1).days)
            self.nursery_lapseday = hasil
        return res

    #compute lapse month
    @api.one
    @api.depends('date_plant','selection_date')
    def calculatemonth(self):
        res={}
        fmt = '%Y-%m-%d'
        if self.date_plant and self.selection_date:
            from_date = self.date_plant
            to_date = self.selection_date
            conv_fromdate = datetime.strptime(str(from_date), fmt)
            conv_todate = datetime.strptime(str(to_date), fmt)
            d1 = conv_fromdate.month
            d2 = conv_todate.month
            rangeyear = conv_todate.year
            rangeyear1 = conv_fromdate.year
            rsult = rangeyear - rangeyear1
            yearresult = rsult * 12
            self.nursery_lapsemonth = (d2 + yearresult) - d1

        return res

    #compute planning date
    @api.one
    @api.depends('date_plant','nursery_plandate','selec','selectionstage_id')
    def calculateplandate(self):

         fmt = '%Y-%m-%d'

         a = self.selec
         b = int(a)
         if self.selectionstage_id and self.date_plant :
             from_date = self.date_plant
             d1=datetime.strptime(str(from_date),fmt)
             date_after_month = datetime.date(d1)+ relativedelta(months=b)
             compute = date_after_month.strftime(fmt)
             self.nursery_plandate = compute
             return True

    #compute planning max date
    @api.one
    @api.depends('date_plant','nursery_plandate','maxa','selectionstage_id')
    def calculateplandatemax(self):

         fmt = '%Y-%m-%d'
         a = self.maxa
         b = int(a)
         if self.date_plant and self.selectionstage_id:
             from_date = self.date_plant
             d1=datetime.strptime(str(from_date),fmt)
             date_after_month = datetime.date(d1)+ relativedelta(months=b)
             compute = date_after_month.strftime(fmt)
             self.nursery_plandatemax = compute
             return True

    #compute planning min date
    @api.one
    @api.depends('date_plant','nursery_plandate','mina','selectionstage_id')
    def calculateplandatemin(self):

         fmt = '%Y-%m-%d'
         a = self.mina
         b = int(a)
         if self.date_plant and self.selectionstage_id:
             from_date = self.date_plant
             d1=datetime.strptime(str(from_date),fmt)
             date_after_month = datetime.date(d1)+ relativedelta(months=b)
             compute = date_after_month.strftime(fmt)
             self.nursery_plandatemin = compute
             return True

    #information
    @api.one
    @api.depends('nursery_information','nursery_lapsemonth','nursery_plandate','selection_date',
                 'nursery_plandatemin','nursery_plandatemax')
    def dateinformation(self):

         fmt = '%Y-%m-%d'

         if  self.selection_date:
             fromdt = self.selection_date
             plan = self.nursery_plandate
             planmax = self.nursery_plandatemax
             planmin = self.nursery_plandatemin
             pmax = planmax
             pmin = planmin
             planning=plan
             conv_fromdt = datetime.strptime(str(fromdt),fmt)
             conv_plan = datetime.strptime(str(planning),fmt)
             conv_planmax = datetime.strptime(str(pmax),fmt)
             conv_planmin = datetime.strptime(str(pmin),fmt)
             dmax = conv_planmax.month
             dmin = conv_planmin.month
             dmaxd = conv_planmax.day
             date_convfromdtM = conv_fromdt.month
             date_convplanM = conv_plan.month
             date_convfromdtD = conv_fromdt.day
             date_convplanD = conv_plan.day

             for c in range(1,8):
                 dateplanmax = date_convplanD + c
                 dateplanmin = date_convplanD - c

             #calculate range date
             if conv_fromdt and conv_plan and conv_planmax and conv_planmin:
                 # if date_convplany and dmaxy and dminy != loope and loopd and loopc:
                if date_convfromdtM == date_convplanM:
                    if date_convfromdtD == date_convplanD :
                        self.nursery_information = '2'#pass
                    elif  dateplanmax >= date_convfromdtD and date_convfromdtD >= dateplanmin:
                        self.nursery_information='2'
                    elif dateplanmax <= date_convfromdtD:
                        self.nursery_information='1' #late
                    else:
                        self.nursery_information='0'# untimely
                elif conv_fromdt > conv_planmax:
                    if date_convfromdtM >=dmax:
                        self.nursery_information = '3'#very late
                elif conv_fromdt < conv_planmin :
                     if date_convfromdtM > dmin:
                         self.nursery_information ='1'
                     elif date_convfromdtM <= dmin :
                         self.nursery_information = '4'# very untimely
                return True

class SelectionStage(models.Model):
    _name = 'estate.nursery.selectionstage'
    #_inherit = 'estate.nursery.selection'

    name = fields.Char(string="Selection Stage")
    age_limit_max= fields.Integer(string="Age Max",required=True)
    age_limit_min= fields.Integer(string="Age Min",required=True)
    age_selection= fields.Integer(string="Age Selection",required=True)
    info = fields.Selection([('draft','Draft'),('0','Age selection not less than age limit min'),
                             ('1','Age selection not more than age limit max'),
                             ('2','passed'),("3","Age Limit min not less than 1"),
                             ("4","Age Limit min not more than 12")],
                            compute='calculateinfo', default='draft', string="Information" ,
                            readonly=True,required=False)
    comment = fields.Text(string="Description or Comment")
    stage_id = fields.Many2one('estate.nursery.stage',"Nursery Stage",)

    #Limit age
    @api.one
    @api.depends("age_limit_max","age_limit_min","age_selection","info",)
    def calculateinfo(self):
        maxa =self.age_limit_max
        mina=self.age_limit_min
        limitmax = self.age_limit_max
        limitmin = 1
        limit=[1,2,3,4,5,6,7,8,9,10,11,12]
        for a in limit:
            limitmax = a
        if maxa and mina :
            if maxa == limitmax:
                self.info = "2"
                if self.age_selection >= maxa:
                    self.info = "1"
                elif self.age_selection <= mina:
                    self.info = "0"
                else:
                    inf = "2"
            elif maxa >= limitmax:
                self.info="4"
            elif mina < limitmin:
                self.info="3"




class SelectionLine(models.Model):
    """Seed Selection Line"""
    _name = 'estate.nursery.selectionline'

    qty = fields.Integer("Quantity Abnormal",required=True)
    qty_abnormal = fields.Integer("Abnormal Quantity",required=False,
                                  readonly=True,related='selection_id.qty_abnormal',store=True)
    qty_batch = fields.Integer("DO Quantity",required=False,readonly=True,related='selection_id.qty_batch',store=True)
    cause_id = fields.Many2one("estate.nursery.cause",string="Cause",required=True)
    comment = fields.Text("Additional Information")
    selection_id = fields.Many2one('estate.nursery.selection',"Selection",readonly=True)
    location_id = fields.Many2one('stock.location', "Bedengan",
                                  domain=[('estate_location', '=', True),
                                          ('estate_location_level', '=', '3'),
                                          ('estate_location_type', '=', 'nursery')],
                                  help="Fill in location seed planted.",required=True)



class Cause(models.Model):
    """Selection Cause (normal, afkir, etc)."""
    _name = 'estate.nursery.cause'

    name = fields.Char('Name')
    comment = fields.Text('Cause Description')
    code = fields.Char('Cause Abbreviation', size=3)
    selection_type = fields.Selection([('0', 'Broken'),('1', 'Normal'),('2', 'Politonne')], "Selection Type")
    selectionline_ids = fields.One2many('estate.nursery.selectionline',"cause_id","Selection Line",ondelete="cascade")








