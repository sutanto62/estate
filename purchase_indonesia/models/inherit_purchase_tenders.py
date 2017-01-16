from openerp import models, fields, api, exceptions
from psycopg2 import OperationalError

from openerp import SUPERUSER_ID
import openerp
import openerp.addons.decimal_precision as dp
from openerp.tools import float_compare, float_is_zero
from datetime import datetime, date,time
from openerp.exceptions import ValidationError
from openerp.tools.translate import _
from dateutil.relativedelta import *
import calendar
from openerp.tools import DEFAULT_SERVER_DATETIME_FORMAT, DEFAULT_SERVER_DATE_FORMAT


class InheritPurchaseTenders(models.Model):

    def return_action_to_open(self, cr, uid, ids, context=None):
        """ This opens the xml view specified in xml_id for the current Quotation Comparison """
        if context is None:
            context = {}
        if context.get('xml_id'):
            res = self.pool.get('ir.actions.act_window').for_xml_id(cr, uid ,'purchase_indonesia', context['xml_id'], context=context)
            res['context'] = context
            res['context'].update({'default_requisition_id': ids[0]})
            res['domain'] = [('requisition_id','=', ids[0])]
            return res
        return False

    _inherit = 'purchase.requisition'
    _description = 'inherit purchase requisition'
    _order = 'ordering_date asc'
    _rec_name = 'complete_name'

    complete_name =fields.Char("Complete Name", compute="_complete_name", store=True)
    type_location = fields.Char('Location')
    location = fields.Char('Location')
    companys_id = fields.Many2one('res.company','Company')
    request_id = fields.Many2one('purchase.request','Purchase Request')
    due_date = fields.Date('Due Date',compute='_compute_due_date')
    validation_due_date = fields.Boolean('Validation Due Date',compute='_compute_validation_due_date')

    @api.multi
    def _get_value_low(self):
        #get Minimal value from purchase params for Purchase Request

        value_standard = self.env['purchase.params.setting'].search([('name','=',self._name)])

        price = min(value.value_params for value in value_standard)

        return float(price)

    @api.multi
    def _get_user(self):
        #find User
        user= self.env['res.users'].browse(self.env.uid)

        return user

    @api.multi
    def tender_in_progress(self):
        super(InheritPurchaseTenders,self).tender_in_progress()
        data={
            'user_id':self._get_user().id
        }
        self.write(data)
        self._change_created_by_qcf()
        return True

    @api.multi
    def _change_created_by_qcf(self):
        data = {
            'pic_id': self.user_id.id
        }
        res = self.env['quotation.comparison.form'].search([('requisition_id','=',self.id)]).write(data)

    @api.multi
    def _compute_date(self):
        arrMinDateNorm = []
        arrMaxDateNorm = []

        arrMinDateUrgent = []
        arrMaxDateUrgent = []
        res = []
        fmt = '%Y-%m-%d'
        normal = self.env['purchase.indonesia.type'].search([('name','in',['Normal','normal'])])
        urgent = self.env['purchase.indonesia.type'].search([('name','in',['Urgent','urgent'])])
        for item in normal:
            arrMaxDateNorm.append(item.max_days)
            arrMinDateNorm.append(item.min_days)

        for item in urgent:
            arrMaxDateUrgent.append(item.max_days)
            arrMinDateUrgent.append(item.min_days)

        compute = self.due_date
        try:
            fromdt = self.request_id.date_start
            init_date=datetime.strptime(str(fromdt),fmt)
        except:
            fromdt = date.today()
            init_date=datetime.strptime(str(fromdt),fmt)

        if self.request_id.type_purchase.name in ['Normal','normal']:
            min_days = arrMinDateNorm[0]
            max_days = arrMaxDateNorm[0]

            if self.request_id.code == 'KPST':
                 date_after_month = datetime.date(init_date) + relativedelta(days=min_days)
                 compute = date_after_month.strftime(fmt)

            elif self.request_id.code in ['KOKB','KPWK']:
                 date_after_month = datetime.date(init_date) + relativedelta(days=max_days)
                 compute = date_after_month.strftime(fmt)

        elif self.request_id.type_purchase.name in ['Urgent','urgent']:
            min_days = arrMinDateUrgent[0]
            max_days = arrMaxDateUrgent[0]
            if self.request_id.code == 'KPST':
                 date_after_month = datetime.date(init_date)+ relativedelta(days=min_days)
                 compute = date_after_month.strftime(fmt)

            elif self.request_id.code in ['KOKB','KPWK']:
                 date_after_month = datetime.date(init_date)+ relativedelta(days=max_days)
                 compute = date_after_month.strftime(fmt)
        res = compute
        return res

    @api.multi
    @api.depends('request_id')
    def _compute_due_date(self):
        for item in self:
            item.due_date = item._compute_date()

    @api.multi
    @api.depends('due_date')
    def _compute_validation_due_date(self):
        standard_due_date = self._get_value_low()
        fmt = '%Y-%m-%d'
        for item in self:
            try:
                fromdt = item.due_date
                init_date=datetime.strptime(str(fromdt),fmt)
                date_after_month = datetime.date(init_date)-relativedelta(days=standard_due_date)
            except:
                date_after_month = datetime.now()

            compute = date_after_month.strftime(fmt)

            delta = str(datetime.now())

            if delta == compute or delta > compute and item.state in ['draft','in_progress','open']:
                item.validation_due_date = True
        return True

    @api.one
    @api.depends('name','ordering_date','companys_id','type_location')
    def _complete_name(self):
        """ Forms complete name of location from parent category to child category.
        """
        fmt = '%Y-%m-%d'

        if self.name and self.ordering_date and self.companys_id.code and self.type_location:
            date = self.ordering_date
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

            self.complete_name = self.name + '/' \
                                 + self.companys_id.code+' - '\
                                 +'PQ'+'/'\
                                 +str(self.type_location)+'/'+str(month)+'/'+str(year)
        else:
            self.complete_name = self.name

        return True

    def _prepare_po_from_tender(self, cr, uid, tender, context=None):
        """ Prepare the values to write in the purchase order
        created from a tender.

        :param tender: the source tender from which we generate a purchase order
        """
        return {'order_line': [],
                'requisition_id': tender.id,
                'po_no':self.pool.get('ir.sequence').next_by_code(cr, uid,'purchase.po_no'),
                # 'location':tender.location,
                'source_purchase_request' : tender.origin,
                'companys_id' :tender.companys_id.id,
                'origin': tender.complete_name}

    def _prepare_purchase_backorder(self, cr, uid, requisition, supplier, context=None):
        return {
            'origin': requisition.complete_name,
            'date_order': requisition.date_end or fields.datetime.now(),
            'partner_id': supplier.id,
            'type_location':requisition.type_location,
            'location':requisition.location,
            'currency_id': requisition.company_id and requisition.company_id.currency_id.id,
            'company_id': requisition.company_id.id,
            'fiscal_position_id': self.pool.get('account.fiscal.position').get_fiscal_position(cr, uid, supplier.id, context=context),
            'requisition_id': requisition.id,
            'notes': requisition.description,
            'picking_type_id': requisition.picking_type_id.id
        }

    def _prepare_purchase_backorder_line(self, cr, uid, requisition, requisition_line, purchase_id, supplier, context=None):
        if context is None:
            context = {}
        po_obj = self.pool.get('purchase.order')
        po_line_obj = self.pool.get('purchase.order.line')
        product_uom = self.pool.get('product.uom')
        product = requisition_line.product_id
        default_uom_po_id = product.uom_po_id.id
        ctx = context.copy()
        ctx['tz'] = requisition.user_id.tz
        date_order = requisition.ordering_date  or fields.datetime.now()
        qty = product_uom._compute_qty(cr, uid, requisition_line.product_uom_id.id, requisition_line.qty_outstanding, default_uom_po_id)

        taxes = product.supplier_taxes_id
        fpos = supplier.property_account_position_id
        taxes_id = fpos.map_tax(taxes).ids if fpos else []

        po = po_obj.browse(cr, uid, [purchase_id], context=context)
        seller = requisition_line.product_id._select_seller(
            requisition_line.product_id,
            partner_id=supplier,
            quantity=qty,
            date=date_order and date_order[:10],
            uom_id=product.uom_po_id)

        price_unit = seller.price if seller else 0.0
        if price_unit and seller and po.currency_id and seller.currency_id != po.currency_id:
            price_unit = seller.currency_id.compute(price_unit, po.currency_id)

        date_planned = po_line_obj._get_date_planned(cr, uid, seller, po=po, context=context).strftime(DEFAULT_SERVER_DATETIME_FORMAT)

        product_lang = requisition_line.product_id.with_context({
            'lang': supplier.lang,
            'partner_id': supplier.id,
        })
        name = product_lang.display_name
        if product_lang.description_purchase:
            name += '\n' + product_lang.description_purchase

        vals = {
            'name': name,
            'order_id': purchase_id,
            'product_qty': qty,
            'qty_request':qty,
            'product_id': product.id,
            'product_uom': default_uom_po_id,
            'price_unit': price_unit,
            'date_planned': date_planned,
            'taxes_id': [(6, 0, taxes_id)],
            'account_analytic_id': requisition_line.account_analytic_id.id,
        }

        return vals


    def make_purchase_backorder(self, cr, uid, ids, partner_id, context=None):
        """
        Create New RFQ for Vendor
        """
        context = dict(context or {})
        assert partner_id, 'Vendor should be specified'
        purchase_order = self.pool.get('purchase.order')
        purchase_order_line = self.pool.get('purchase.order.line')
        res_partner = self.pool.get('res.partner')
        supplier = res_partner.browse(cr, uid, partner_id, context=context)
        res = {}
        for requisition in self.browse(cr, uid, ids, context=context):
            if not requisition.multiple_rfq_per_supplier and supplier.id in filter(lambda x: x, [rfq.state != 'cancel' and rfq.partner_id.id or None for rfq in requisition.purchase_ids]):
                error_msg = "You have already one  purchase order for this partner, you must cancel this purchase order to create a new quotation."
                raise exceptions.ValidationError(error_msg)
            context.update({'mail_create_nolog': True})
            purchase_id = purchase_order.create(cr, uid, self._prepare_purchase_backorder(cr, uid, requisition, supplier, context=context), context=context)
            purchase_order.message_post(cr, uid, [purchase_id], body=_("RFQ created"), context=context)
            res[requisition.id] = purchase_id
            for line in requisition.line_ids:
                purchase_order_line.create(cr, uid, self._prepare_purchase_backorder_line(cr, uid, requisition, line, purchase_id, supplier, context=context), context=context)
        return res

    @api.multi
    def generate_po(self):
        pp_data={'state':'done'}
        self.env['purchase.request'].search([('complete_name','like',self.origin)]).write(pp_data)
        res=super(InheritPurchaseTenders,self).generate_po()
        return res

class InheritPurchaseRequisitionLine(models.Model):

    _inherit = 'purchase.requisition.line'

    qty_received = fields.Float('Quantity received',readonly=True)
    qty_outstanding = fields.Float('Quantity Outstanding',readonly=True)
















