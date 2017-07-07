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
from openerp.tools import (DEFAULT_SERVER_DATETIME_FORMAT, DEFAULT_SERVER_DATE_FORMAT,drop_view_if_exists)


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
    state = fields.Selection(selection_add = [('rollback','Roll Back PP'),
                                              ('closed','PP Closed'),
                                              ('open', 'PP Outstanding'),
                                              ('done', 'Shipment')])
    validation_check_backorder = fields.Boolean('Confirm backorder')
    validation_missing_product = fields.Boolean('Missing Product',compute='compute_validation_check_product')
    location = fields.Char('Location')
    companys_id = fields.Many2one('res.company','Company')
    request_id = fields.Many2one('purchase.request','Purchase Request')
    due_date = fields.Date('Due Date',compute='_compute_due_date')
    validation_due_date = fields.Boolean('Validation Due Date',compute='_compute_validation_due_date')
    quotation_state = fields.Char('QCF state',compute='_compute_quotation_state')
    validation_correction = fields.Boolean('Validation Correction',compute='_compute_validation_correction')
    validation_qcf = fields.Boolean('Validation QCF',compute='_compute_validation_qcf')
    validation_button_correction = fields.Boolean('Validation Button Correction',compute='_compute_button_correction')
    check_missing_product = fields.Boolean('Check Missing Product')
    force_closing = fields.Boolean('Force Closing Tender')
    comparison_id = fields.Integer('Comparison ID')
    check_backorder = fields.Boolean('Check Backorder',compute='compute_validation_check_backorder')

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
        for item in self:
            super(InheritPurchaseTenders,item).tender_in_progress()
            data={
                'user_id':item._get_user().id
            }
            item.write(data)
            item._change_created_by_qcf()
            return True

    @api.multi
    def tender_open(self):
        for item in self:
            count_order = 0
            order = item.env['purchase.order'].search([('requisition_id','=',item.id),('state','in',['draft'])])
            for record in order:
                if len(record) > 0 :
                    count_order = count_order + 1
            if (count_order == 0):
                super(InheritPurchaseTenders,item).tender_open()
            else:
                msg_error = 'You Must Proceed Your Order'
                raise exceptions.ValidationError(msg_error)

    @api.multi
    def tender_state_closed(self):
        for item in self:
            tracking = item.env['validate.tracking.purchase.order.invoice'].search([('requisition_id','=',item.id)])
            for record in tracking:
                if (record.sum_quantity_tender == record.sum_quantity_purchase) and (record.sum_quantity_tender == record.sum_quantity_picking) and (record.sum_quantity_tender == record.sum_quantity_invoice):
                    return item.write({'state':'closed'})
                elif item.force_closing == True and ((record.sum_quantity_tender == record.sum_quantity_purchase) and (record.sum_quantity_tender == record.sum_quantity_picking) and (record.sum_quantity_tender == record.sum_quantity_invoice)):
                    return item.write({'state':'closed'})
                elif item.force_closing == True:
                    return item.write({'state':'closed'})
                else:
                    raise exceptions.ValidationError('You Must Complete Your Purchase Order')


    @api.multi
    def _change_created_by_qcf(self):
        data = {
            'pic_id': self.user_id.id
        }
        res = self.env['quotation.comparison.form'].search([('requisition_id','=',self.id)]).write(data)

    @api.multi
    @api.depends('request_id')
    def _compute_validation_correction(self):

        for item in self:
            arrOutstanding = []
            domain = [('requisition_id','=',item.id),('check_missing_product','=',False),('qty_outstanding','>',0)]

            for line in item.line_ids.search(domain):
                arrOutstanding.append(line.id)

            if (item.request_id.validation_correction_procurement == True and item.request_id.state in ['done','approved'] and item.validation_missing_product == False) or (item.request_id.validation_correction_procurement == False and item.state not in ['draft','done','open','closed'] and item.validation_missing_product == False) :

                item.validation_correction = True
            elif (item.request_id.validation_correction_procurement == False and item.state in ['in_progress','done','open']) and item.validation_missing_product == True:

                item.validation_correction = False

            else:
               if item.validation_check_backorder == True and len(arrOutstanding) > 0:

                   item.validation_correction = True

               elif item.validation_check_backorder == False and item.state in ['draft','open','done','closed'] and item.check_missing_product == False:

                   item.validation_correction = False

               elif item.validation_missing_product == False and item.check_missing_product == True:

                   item.validation_correction = True

               else:

                   item.validation_correction = False

    @api.multi
    @api.depends('validation_check_backorder')
    def compute_validation_check_backorder(self):
        for record in self:
            arrOutstanding = []
            arrMissing = []
            domain = [('requisition_id','=',record.id),('check_missing_product','=',False),('qty_outstanding','>',0)]
            domain2 = [('requisition_id','=',record.id),('check_missing_product','=',True)]

            for line in record.line_ids.search(domain2):
                arrMissing.append(line.id)
            for line in record.line_ids.search(domain):
                arrOutstanding.append(line.id)

            if record.state in ['draft','cancel','closed']:
                record.check_backorder = True
            else:
                if record.validation_check_backorder == False and len(arrOutstanding) > 0 and len(arrMissing) > 0:
                    record.check_backorder = True
                elif record.validation_check_backorder == False and len(arrOutstanding) > 0 and len(arrMissing) == 0:
                    record.check_backorder = False
                else:
                    record.check_backorder = True

    @api.multi
    @api.depends('purchase_ids')
    def compute_validation_check_product(self):
        for item in self:
            #change Validation missing Product

            if item.state in ['open']:
                if len(item.purchase_ids.search([('requisition_id','=',item.id),('state','in',('purchase','received_all','received_force_done'))])) > 0:
                    item.validation_missing_product = item.checking_validation_missing_and_backorder()
                    if item.validation_missing_product == True:
                        item.change_line_tender_missing()
            elif item.state in ['in_progress']:

                if len(item.purchase_ids.search([('requisition_id','=',item.id),('state','=','purchase')])) > 0:
                    item.validation_missing_product = item.checking_validation_missing_and_backorder()
                    if item.validation_missing_product == True:
                        item.change_line_tender_missing()

    @api.multi
    def checking_validation_missing_and_backorder(self):
        for item in self:

                #search Missing Product or Outstanding product starts Here

                arrOutstanding = []
                arrMissing = []

                domain = [('requisition_id','=',item.id),('check_missing_product','=',False),('qty_outstanding','>',0)]

                domain2 = [('requisition_id','=',item.id),('check_missing_product','=',True)]

                for line in item.line_ids.search(domain):
                    arrOutstanding.append(line.id)

                for line in item.line_ids.search(domain2):
                    arrMissing.append(line.id)

                if list(item.list_product()) != [] and item.check_missing_product == False:
                    validation_missing_product = True
                elif list(item.list_product()) != [] and item.check_missing_product == True:
                    validation_missing_product = False
                else:
                    validation_missing_product = False

                    if len(arrOutstanding) > 0 and len(arrMissing) == 0 :
                        validation_missing_product = False
                    elif len(arrOutstanding) > 0 and len(arrMissing) > 0 :
                        validation_missing_product = True

                return validation_missing_product

    @api.multi
    def list_product(self):
        for item in self:
            #to list product if check back order missing is True
            arrProductLine = []
            arrPurchase = []
            arrPurchaseProduct = []
            tender_line = item.env['purchase.requisition.line']
            purchase = item.env['purchase.order']
            purchase_line = item.env['purchase.order.line']

            product_tender_line = tender_line.search([('requisition_id','=',item.id)])
            for product in product_tender_line:
                arrProductLine.append(product.product_id.id)

            purchase_id = purchase.search([('requisition_id','=',item.id),('state','in',['purchase','done','received_all','received_force_done']),('validation_check_backorder','=',False)])
            for purchase in purchase_id:
                arrPurchase.append(purchase.id)
            purchase_line_id = purchase_line.search([('order_id','in',arrPurchase)])

            for product_purchase in purchase_line_id:
                arrPurchaseProduct.append(product_purchase.product_id.id)

            set_product = set(arrProductLine) - set(arrPurchaseProduct)

            return set_product

    @api.multi
    def change_line_tender_missing(self):
        for item in self:
            #change Line tender Missing in Requisition line
            tender_line = item.env['purchase.requisition.line']
            line_tender_missing = tender_line.search([('requisition_id','=',item.id),('product_id','in',list(item.list_product()))])
            line_tender_missing.write({'check_missing_product' : True})

    @api.multi
    @api.depends('purchase_ids')
    def _compute_button_correction(self):

        for item in self:
            count_order = 0
            order = item.env['purchase.order'].search([('requisition_id','=',item.id),('state','in',['purchase','done','receive_all','receive_force_done'])])
            for record in order:
                if len(record) > 0 :
                    count_order = count_order + 1
            if (count_order == 0) and item.state in('in_progress'):
                item.validation_button_correction = True
            else:
                item.validation_button_correction = False

    @api.multi
    @api.depends('purchase_ids')
    def _compute_validation_qcf(self):
        for item in self:
            count_confirm = 0
            count_purchase = len(item.purchase_ids)
            order = item.env['purchase.order'].search([('requisition_id','=',item.id),('state','in',['draft','sent'])])
            count_order = len(order)
            if count_purchase > 0:
                for record in order:
                    if record.validation_check_confirm_vendor == True:
                        count_confirm = count_confirm + 1
                    if count_order == count_confirm:
                        item.validation_qcf = True
                    elif (count_order == count_confirm) and (record.validation_check_backorder == True):
                        item.validation_qcf = True
                    else:
                        if item.state in ['draft','cancel','closed','done','rollback']:
                            item.validation_qcf = False


    @api.multi
    @api.depends('quotation_state')
    def _compute_quotation_state(self):
        for item in self:
            domain1 = [('requisition_id','=',item.id)]
            qcf = item.env['quotation.comparison.form'].search(domain1)
            count_qcf = len(qcf)
            index_a = 0
            if count_qcf > 1:
                for record in qcf:
                    if record.state == 'done':
                        index_a = index_a + 1
                if index_a == count_qcf:
                    qcf_state = 'QCF Done'
                    item.quotation_state = qcf_state
                else :
                    qcf_state = 'In Progress QCF'
                    item.quotation_state = qcf_state
            else:
                qcf_state = qcf.state
                categ_state = dict(qcf._columns['state'].selection).get(qcf_state)

                if qcf_state in [True,False]:
                    item.quotation_state = qcf_state
                else:
                    item.quotation_state = categ_state

    @api.multi
    def purchase_request_correction(self):
        for item in self:
            item.state = 'rollback'
            purchase_request = item.env['purchase.request'].search([('id','=',item.request_id.id)])
            update_purchase_request = purchase_request.write({
                'state':'budget' if purchase_request._get_max_price() < purchase_request._get_price_low() else'approval4' ,
                'assigned_to' : purchase_request._get_budget_manager() if purchase_request._get_max_price() < purchase_request._get_price_low() else purchase_request._get_division_finance(),
                'validation_correction_procurement' : True
            })
            item.send_mail_template()


    @api.multi
    def create_backorder_quotation_comparison_form(self):
        for record in self:
            purchase_requisition = record.env['purchase.requisition'].search([('id','=',record.id)])
            try:
                company_code = record.env['res.company'].search([('id','=',record.companys_id.id)]).code
            except:
                raise exceptions.ValidationError('Company Code is Null')
            sequence_name = 'quotation.comparison.form.'+record.request_id.code.lower()+'.'+company_code.lower()
            purchase_data = {
                    'name' : record.env['ir.sequence'].next_by_code(sequence_name),
                    'company_id': purchase_requisition.companys_id.id,
                    'date_pp': datetime.today(),
                    'requisition_id': purchase_requisition.id,
                    'origin' : purchase_requisition.origin,
                    'type_location' : purchase_requisition.type_location,
                    'location':purchase_requisition.location,
                    'state':'draft',
                    'pic_id': record.user_id.id,

                    'validation_check_backorder':True
                }
            arrOutstanding = []
            domain = [('requisition_id','=',record.id),('check_missing_product','=',False),('qty_outstanding','>',0)]

            for line in record.line_ids.search(domain):
                arrOutstanding.append(line.id)

            if len(arrOutstanding) > 0:
                res = record.env['quotation.comparison.form'].create(purchase_data)
                record.write({'validation_check_backorder' : True})
                quotation_comparison_form = self.env['quotation.comparison.form'].search([('requisition_id','=',record.id),('validation_check_backorder','=',True)])
                arrQcfid = []
                for item in quotation_comparison_form:
                    arrQcfid.append(item.id)
                data = {
                    'comparison_id' : max(arrQcfid)
                }
                record.write(data)
            else:
                raise exceptions.ValidationError('You Cannot Run This Process, cause no product have Qty OutStanding')

    @api.multi
    def create_missing_product_quotation_comparison_form(self):
        for record in self:
            purchase_requisition = record.env['purchase.requisition'].search([('id','=',record.id)])
            try:
                company_code = record.env['res.company'].search([('id','=',record.companys_id.id)]).code
            except:
                raise exceptions.ValidationError('Company Code is Null')
            sequence_name = 'quotation.comparison.form.'+record.request_id.code.lower()+'.'+company_code.lower()
            purchase_data = {
                    'name' : record.env['ir.sequence'].next_by_code(sequence_name),
                    'company_id': purchase_requisition.companys_id.id,
                    'date_pp': datetime.today(),
                    'requisition_id': purchase_requisition.id,
                    'origin' : purchase_requisition.origin,
                    'type_location' : purchase_requisition.type_location,
                    'location':purchase_requisition.location,
                    'state':'draft',
                    'pic_id': record.user_id.id,

                    'validation_missing_product':True
                }
            record.check_missing_product = True
            res = record.env['quotation.comparison.form'].create(purchase_data)
            quotation_comparison_form = self.env['quotation.comparison.form'].search([('requisition_id','=',record.id),('validation_missing_product','=',True)])
            arrQcfid = []
            for item in quotation_comparison_form:
                arrQcfid.append(item.id)
            data = {
                'comparison_id' : max(arrQcfid)
            }
            record.write(data)

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
        sequence_name = 'purchase.order.seq.'+tender.type_location.lower()+'.'+tender.companys_id.code.lower()
        return {'order_line': [],
                'requisition_id': tender.id,
                'po_no':self.pool.get('ir.sequence').next_by_code(cr, uid,sequence_name),
                # 'location':tender.location,
                'source_purchase_request' : tender.origin,
                'request_id':tender.request_id.id,
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
            'companys_id': requisition.companys_id.id,
            'fiscal_position_id': self.pool.get('account.fiscal.position').get_fiscal_position(cr, uid, supplier.id, context=context),
            'requisition_id': requisition.id,
            'request_id':requisition.request_id.id,
            'notes': requisition.description,
            'picking_type_id': requisition.picking_type_id.id,
            'comparison_id' : requisition.comparison_id,
            'validation_check_backorder':True
        }

    def _prepare_missing_purchase_backorder(self, cr, uid, requisition, supplier, context=None):
        return {
            'origin': requisition.complete_name,
            'date_order': requisition.date_end or fields.datetime.now(),
            'partner_id': supplier.id,
            'type_location':requisition.type_location,
            'location':requisition.location,
            'currency_id': requisition.company_id and requisition.company_id.currency_id.id,
            'companys_id': requisition.companys_id.id,
            'fiscal_position_id': self.pool.get('account.fiscal.position').get_fiscal_position(cr, uid, supplier.id, context=context),
            'requisition_id': requisition.id,
            'request_id':requisition.request_id.id,
            'notes': requisition.description,
            'picking_type_id': requisition.picking_type_id.id,
            'comparison_id' : requisition.comparison_id,
            'validation_check_backorder':False
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
            'comparison_id' : requisition.comparison_id,
            'trigger_draft' : True,
            'taxes_id': [(6, 0, taxes_id)],
            'account_analytic_id': requisition_line.account_analytic_id.id,
        }

        return vals

    def _prepare_missing_purchase_backorder_line(self, cr, uid, requisition, requisition_line, purchase_id, supplier, context=None):
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
        qty = product_uom._compute_qty(cr, uid, requisition_line.product_uom_id.id, requisition_line.product_qty, default_uom_po_id)
        qty1 = product_uom._compute_qty(cr, uid, requisition_line.product_uom_id.id, requisition_line.qty_outstanding, default_uom_po_id)

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

        seller2 = requisition_line.product_id._select_seller(
            requisition_line.product_id,
            partner_id=supplier,
            quantity=qty1,
            date=date_order and date_order[:10],
            uom_id=product.uom_po_id)

        price_unit = seller.price if seller else 0.0
        if price_unit and seller and po.currency_id and seller.currency_id != po.currency_id:
            price_unit = seller.currency_id.compute(price_unit, po.currency_id)

        price_unit2 = seller2.price if seller2 else 0.0
        if price_unit and seller2 and po.currency_id and seller2.currency_id != po.currency_id:
            price_unit = seller2.currency_id.compute(price_unit2, po.currency_id)

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
            'product_qty': qty if requisition_line.qty_outstanding == 0 else qty1,
            'qty_request':qty if requisition_line.qty_outstanding == 0 else qty1,
            'product_id': product.id,
            'product_uom': default_uom_po_id,
            'price_unit': price_unit,
            'date_planned': date_planned,
            'taxes_id': [(6, 0, taxes_id)],
            'comparison_id' : requisition.comparison_id,
            'trigger_draft' : True,
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
            #todo use constraint for vendor.
            if not requisition.multiple_rfq_per_supplier and supplier.id in filter(lambda x: x, [((rfq.validation_check_backorder == True and rfq.state  not in ('cancel')) or (rfq.validation_check_backorder == False and rfq.state in ('draft')))and rfq.partner_id.id or None for rfq in requisition.purchase_ids]):
                error_msg = "You have already one  purchase order for this partner, you must cancel this purchase order to create a new quotation."
                raise exceptions.ValidationError(error_msg)
            context.update({'mail_create_nolog': True})
            if requisition.validation_check_backorder == True:
                purchase_id = purchase_order.create(cr, uid, self._prepare_purchase_backorder(cr, uid, requisition, supplier, context=context), context=context)
            elif requisition.validation_check_backorder == True and requisition.validation_missing_product == True:
                purchase_id = purchase_order.create(cr, uid, self._prepare_missing_purchase_backorder(cr, uid, requisition, supplier, context=context), context=context)
            elif requisition.validation_missing_product == True:
                purchase_id = purchase_order.create(cr, uid, self._prepare_missing_purchase_backorder(cr, uid, requisition, supplier, context=context), context=context)
            else:
                purchase_id = purchase_order.create(cr, uid, self._prepare_missing_purchase_backorder(cr, uid, requisition, supplier, context=context), context=context)
            purchase_order.message_post(cr, uid, [purchase_id], body=_("RFQ created"), context=context)
            res[requisition.id] = purchase_id
            for line in requisition.line_ids:
                if line.qty_outstanding > 0 and line.check_missing_product == False:
                    purchase_order_line.create(cr, uid, self._prepare_purchase_backorder_line(cr, uid, requisition, line, purchase_id, supplier, context=context), context=context)
                elif line.check_missing_product == True :
                    purchase_order_line.create(cr, uid, self._prepare_missing_purchase_backorder_line(cr, uid, requisition, line, purchase_id, supplier, context=context), context=context)
                elif line.check_missing_product == True and line.qty_outstanding > 0:
                    purchase_order_line.create(cr, uid, self._prepare_missing_purchase_backorder_line(cr, uid, requisition, line, purchase_id, supplier, context=context), context=context)
        return res

    def _prepare_purchase_order_line(self, cr, uid, requisition, requisition_line, purchase_id, supplier, context=None):
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
        qty = product_uom._compute_qty(cr, uid, requisition_line.product_uom_id.id, requisition_line.product_qty, default_uom_po_id)

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
            'product_id': product.id,
            'product_uom': default_uom_po_id,
            'price_unit': price_unit,
            'date_planned': date_planned,
            'taxes_id': [(6, 0, taxes_id)],
            'trigger_draft' : True,
            'account_analytic_id': requisition_line.account_analytic_id.id,
        }

        return vals

    def _prepare_po_line_from_tender(self, cr, uid, tender, line, purchase_id, context=None):
        """ Prepare the values to write in the purchase order line
        created from a line of the tender.

        :param tender: the source tender from which we generate a purchase order
        :param line: the source tender's line from which we generate a line
        :param purchase_id: the id of the new purchase
        """
        return {
                'trigger_draft' : False,
                'product_qty': line.quantity_tendered,
                'order_id': purchase_id
               }

    # @api.multi
    # def generate_po(self):
    #     for item in self:
    #         super(InheritPurchaseTenders,item).generate_po()


    @api.multi
    def set_done(self):
        for item in self:
            # Set To Done Purchase Tender
            pp_data={'state':'done'}
            item.env['purchase.request'].search([('complete_name','like',item.origin)]).write(pp_data)
            item.write({'state' : 'done'})


    @api.multi
    @api.constrains('purchase_ids')
    def _constraint_po_line_ids(self):

        for item in self:

            arrPoid = []
            tender_line =item.env['purchase.requisition.line']
            tender_line_id = tender_line.search([('requisition_id','=',item.id)])
            if item.purchase_ids:
                for record in item.purchase_ids:
                    arrPoid.append(record.id)

                for tender in tender_line_id:

                    order_line_ids = item.env['purchase.order.line'].search([('order_id','in',arrPoid),('product_id','=',tender.product_id.id)])

                    for order in order_line_ids:
                        if order.quantity_tendered > tender.product_qty:
                            error_msg = 'Quantity tendered cannot more than Product Quantity in Tender Line'
                            raise exceptions.ValidationError(error_msg)
                        elif order.product_qty > tender.product_qty:
                            error_msg = 'Product Quantity \"%s\" cannot greater than Product Quantity \"%s\" in Tender Line Vendor \"%s\"'%(order.product_id.name,tender.product_id.name,order.partner_id.name)
                            raise exceptions.ValidationError(error_msg)

    #Email Template Code Starts Here

    @api.one
    def send_mail_template(self):
            # Find the e-mail template
            template = self.env.ref('purchase_indonesia.email_template_correction_purchase_request')
            # You can also find the e-mail template like this:
            # template = self.env['ir.model.data'].get_object('mail_template_demo', 'example_email_template')
            # Send out the e-mail template to the user
            self.env['mail.template'].browse(template.id).send_mail(self.id,force_send=True)

    @api.multi
    def database(self):
        for item in self:
            db = item.env.cr.dbname

            return db

    @api.multi
    def web_url(self):
        for item in self:
            web = item.env['ir.config_parameter'].sudo().get_param('web.base.url')
            return web

    @api.multi
    def email_model(self):
        for item in self:
            model = item._name
            return model

class InheritPurchaseRequisitionLine(models.Model):

    _inherit = 'purchase.requisition.line'

    qty_received = fields.Float('Quantity received',readonly=True)
    qty_outstanding = fields.Float('Quantity Outstanding',readonly=True)
    check_missing_product = fields.Boolean('Checking Missing Product')
    est_price = fields.Float('Estimated Price',compute='_compute_est_price')

    @api.multi
    @api.depends('est_price')
    def _compute_est_price(self):
        if self.est_price == 0 :
            for item in self:
                request_line  = item.env['purchase.request.line'].search([('request_id','=',item.requisition_id.request_id.id),
                                                                          ('product_id','=',item.product_id.id)]).price_per_product
                item.est_price = request_line




















