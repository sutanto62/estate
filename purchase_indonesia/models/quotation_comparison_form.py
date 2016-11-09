from openerp import models, fields, api, exceptions
from psycopg2 import OperationalError

from openerp import SUPERUSER_ID
import openerp
import openerp.addons.decimal_precision as dp
from openerp.tools import float_compare, float_is_zero
from datetime import datetime, date,time
from openerp.exceptions import ValidationError
from dateutil.relativedelta import *
import calendar
from openerp import tools
import re

class QuotationComparisonForm(models.Model):

    _name = 'quotation.comparison.form'
    _description = 'Form Quotation Comparison'


    name = fields.Char('name')
    complete_name =fields.Char("Complete Name", compute="_complete_name", store=True)
    date_pp = fields.Date('Date')
    type_location = fields.Selection([('KOKB','Estate'),
                                     ('KPST','HO'),('KPWK','RO')],'Location Type')
    origin = fields.Char('Source Purchase Request')
    company_id = fields.Many2one('res.company','Company')
    requisition_id = fields.Many2one('purchase.requisition','Purchase Requisition')
    state = fields.Selection([
        ('draft', 'Draft'),
        ('confirm', 'Send Request'),
        ('approve', 'Confirm'),
        ('done', 'Done'),
        ('reject', 'Rejected'),
        ('cancel', 'Canceled')], string="State",store=True)
    quotation_comparison_line_ids = fields.One2many('v.quotation.comparison.form.line','requisition_id','Comparison Line')
    _defaults = {
        'state' : 'draft'
    }
    def create(self, cr, uid,vals, context=None):
        vals['name']=self.pool.get('ir.sequence').get(cr, uid,'quotation.comparison.form')
        res=super(QuotationComparisonForm, self).create(cr, uid,vals)
        return res

    @api.one
    @api.depends('name','date_pp','company_id','type_location')
    def _complete_name(self):
        """ Forms complete name of location from parent category to child category.
        """
        fmt = '%Y-%m-%d'

        if self.name and self.date_pp and self.company_id.code and self.type_location:
            date = self.date_pp
            conv_date = datetime.strptime(str(date), fmt)
            month = conv_date.month
            year = conv_date.year

            #change integer to roman
            if type(month) != type(1):
                raise TypeError, "expected integer, got %s" % type(month)
            if not 0 < month < 4000:
                raise ValueError, "Argument must be between 1 and 3999"
            ints = (1000, 900,  500, 400, 100,  90, 50,  40, 10,  9,   5,  4,   1)
            nums = ('M',  'CM', 'D', 'CD','C', 'XC','L','XL','X','IX','V','IV','I')
            result = ""
            for i in range(len(ints)):
              count = int(month / ints[i])
              result += nums[i] * count
              month -= ints[i] * count
            month = result

            self.complete_name = self.name + ' / ' \
                                 + self.company_id.code+' - '\
                                 +'QCF'+' / '\
                                 +str(self.type_location)+'/'+str(month)+'/'+str(year)
        else:
            self.complete_name = self.name

        return True

class QuotationComparisonFormLine(models.Model):

    _name = 'v.quotation.comparison.form.line'
    _description = 'Quotation Comparison Line'
    _auto = False
    _order = 'isheader'

    id = fields.Integer()
    rownum = fields.Integer()
    cheapest = fields.Integer()
    isheader = fields.Integer()
    requisition_id = fields.Many2one('purchase.requisition','Purchase Requisition')
    # company_id = fields.Many2one('res.company','Company')
    product_id = fields.Many2one('product.product','Product')
    product_qty = fields.Float('Product Quantity')
    product_uom = fields.Many2one('product.uom','Unit Of Measurement')
    # partner_id = fields.Many2one('res.partner','Vendor')
    vendor1 = fields.Char('Vendor')
    vendor2 = fields.Char('Vendor')
    vendor3 = fields.Char('Vendor')
    vendor4 = fields.Char('Vendor')
    vendor5 = fields.Char('Vendor')
    # price_unit = fields.Float('Price Unit')
    # price_subtotal = fields.Float('Price Subtotal')
    # amount_untaxed = fields.Float('Amount Untaxed')
    # price_tax = fields.Float('Price Tax')
    # amount_total = fields.Float('Amount Total')
    # payment_term_id = fields.Many2one('account.payment.term','Payment Term')
    # date_planned = fields.Datetime('Planned Date')
    # incoterm_id = fields.Many2one('stock.incoterms','Incoterms')


    def init(self, cr):
        cr.execute("""create or replace view quotation_comparison_form_line as
                    select row_number() over() id,
                            com_id company_id,po_pol_all.requisition_id,
                            po_pol_all.product_id,
                            row_number() over (partition by po_pol_all.requisition_id,po_pol_all.product_id order by po_pol_all.product_id asc) rownum,
                            product_qty,
                            product_uom,
                            part_id partner_id,
                            price_unit,
                            price_subtotal,
                            amount_untaxed,
                            price_tax,
                            amount_total,
                            payment_term_id,date_planned,incoterm_id,
                            po_pol_min.cheapest from
                    (
                        select row_number() over() id,po.company_id com_id,po.partner_id part_id,*
                            from purchase_order po inner join (
                                select * from purchase_order_line
                                    )pol on po.id = pol.order_id and po.requisition_id is not null
                            ) po_pol_all
                        inner join
                        (
                            select requisition_id, product_id, min(price_subtotal) cheapest
                            from (
                                select * from purchase_order po inner join (
                                    select * from purchase_order_line
                                )pol on po.id = pol.order_id and po.requisition_id is not null
                            )po_pol group by po_pol.requisition_id, product_id
                        ) po_pol_min
                        on po_pol_all.requisition_id = po_pol_min.requisition_id and po_pol_all.product_id = po_pol_min.product_id
                        """)

        cr.execute("""
                    create or replace view v_quotation_comparison_form_line as
                        select row_number() over() id,* from (
                        select * from (
                        select requisition_id,0 product_id,0 product_qty,0 product_uom,max(vendor1) vendor1,max(vendor2) vendor2,max(vendor3) vendor3,max(vendor4) vendor4,max(vendor5) vendor5,1 isheader from (
                            SELECT r.requisition_id,r.product_id,product_qty,product_uom,
                                     MAX(CASE WHEN r.rownum = 1 THEN r.name ELSE NULL END) AS "vendor1",
                                     MAX(CASE WHEN r.rownum = 2 THEN r.name ELSE NULL END) AS "vendor2",
                                     MAX(CASE WHEN r.rownum = 3 THEN r.name ELSE NULL END) AS "vendor3",
                                     MAX(CASE WHEN r.rownum = 4 THEN r.name ELSE NULL END) AS "vendor4",
                                     MAX(CASE WHEN r.rownum = 5 THEN r.name ELSE NULL END) AS "vendor5"
                                FROM  (select rownum,name,requisition_id,product_id,product_qty,product_uom,price_unit from (
                                  select qcfl_rn.id rownum,company_id,
                                    qcfl_rn.requisition_id,qcfl_rn.partner_id,
                                    product_id,price_unit,product_qty,product_uom,price_subtotal from quotation_comparison_form_line qcfl inner join (
                                                select row_number() over(PARTITION BY requisition_id
                                                            ORDER BY partner_id DESC NULLS LAST) id,partner_id,requisition_id
                                                            from  quotation_comparison_form_line
                                                            group by partner_id,requisition_id order by requisition_id desc)qcfl_rn on qcfl.partner_id = qcfl_rn.partner_id
                                )con_qcfl_rn inner join (select id,name from res_partner)partner on con_qcfl_rn.partner_id = partner.id) r
                            GROUP BY r.product_id,r.requisition_id,product_qty,product_uom  order by requisition_id
                        )h group by requisition_id)header
                           union all
                         select *, 2 isheader from (
                           SELECT r.requisition_id,r.product_id,product_qty,product_uom,
                                 MAX(CASE WHEN r.rownum = 1 THEN CAST(r.price_unit as varchar) ELSE NULL END) AS "vendor1",
                                 MAX(CASE WHEN r.rownum = 2 THEN CAST(r.price_unit as varchar) ELSE NULL END) AS "vendor2",
                                 MAX(CASE WHEN r.rownum = 3 THEN CAST(r.price_unit as varchar) ELSE NULL END) AS "vendor3",
                                 MAX(CASE WHEN r.rownum = 4 THEN CAST(r.price_unit as varchar) ELSE NULL END) AS "vendor4",
                                 MAX(CASE WHEN r.rownum = 5 THEN CAST(r.price_unit as varchar) ELSE NULL END) AS "vendor5"
                            FROM  (select rownum,name,requisition_id,product_id,product_qty,product_uom,price_unit from (
                              select qcfl_rn.id rownum,company_id,
                                qcfl_rn.requisition_id,qcfl_rn.partner_id,
                                product_id,price_unit,product_qty,product_uom,price_subtotal from quotation_comparison_form_line qcfl inner join (
                                            select row_number() over(PARTITION BY requisition_id
                                                        ORDER BY partner_id DESC NULLS LAST) id,partner_id,requisition_id
                                                        from  quotation_comparison_form_line
                                                        group by partner_id,requisition_id order by requisition_id desc)qcfl_rn on qcfl.partner_id = qcfl_rn.partner_id
                            )con_qcfl_rn inner join (select id,name from res_partner)partner on con_qcfl_rn.partner_id = partner.id) r
                        GROUP BY r.product_id,r.requisition_id,product_qty,product_uom  order by requisition_id asc )content
                        union all
                        select * from (
                        select requisition_id,0 product_id,0 product_qty,0 product_uom,cast(sum(vendor1) as varchar) vendor1,cast(sum(vendor2) as varchar) vendor2,cast(sum(vendor3) as varchar) vendor3,cast(sum(vendor4) as varchar) vendor4,cast(sum(vendor5) as varchar) vendor5,3 isheader from (
                            SELECT r.requisition_id,r.product_id,product_qty,product_uom,
                                     MAX(CASE WHEN r.rownum = 1 THEN r.price_unit ELSE NULL END) AS "vendor1",
                                     MAX(CASE WHEN r.rownum = 2 THEN r.price_unit ELSE NULL END) AS "vendor2",
                                     MAX(CASE WHEN r.rownum = 3 THEN r.price_unit ELSE NULL END) AS "vendor3",
                                     MAX(CASE WHEN r.rownum = 4 THEN r.price_unit ELSE NULL END) AS "vendor4",
                                     MAX(CASE WHEN r.rownum = 5 THEN r.price_unit ELSE NULL END) AS "vendor5"
                                FROM  (select rownum,name,requisition_id,product_id,product_qty,product_uom,price_unit from (
                                  select qcfl_rn.id rownum,company_id,
                                    qcfl_rn.requisition_id,qcfl_rn.partner_id,
                                    product_id,price_unit,product_qty,product_uom,price_subtotal from quotation_comparison_form_line qcfl inner join (
                                                select row_number() over(PARTITION BY requisition_id
                                                            ORDER BY partner_id DESC NULLS LAST) id,partner_id,requisition_id
                                                            from  quotation_comparison_form_line
                                                            group by partner_id,requisition_id order by requisition_id desc)qcfl_rn on qcfl.partner_id = qcfl_rn.partner_id
                                )con_qcfl_rn inner join (select id,name from res_partner)partner on con_qcfl_rn.partner_id = partner.id) r
                            GROUP BY r.product_id,r.requisition_id,product_qty,product_uom  order by requisition_id
                        )h group by requisition_id)footer
                        )qcf
        """)