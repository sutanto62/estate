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


class ViewValidateTrackingPurchaseOrderInvoice(models.Model):

    _name = 'validate.tracking.purchase.order.invoice'
    _description = 'Validation Tracking Purchase Order To Invoice'
    _auto = False
    _order = 'id'

    id = fields.Char('ID')
    requisition_id = fields.Many2one('purchase.requisition')
    product_id = fields.Many2one('product.product')
    sum_quantity_tender = fields.Float('Quantity Tender')
    sum_quantity_purchase = fields.Float('Quantity Purchase')
    sum_quantity_picking = fields.Float('Quantity Picking')
    sum_quantity_invoice = fields.Float('Quantity Invoice')

    def init(self, cr):
        drop_view_if_exists(cr, 'validate_tracking_purchase_order_invoice')
        cr.execute("""create or replace view validate_tracking_purchase_order_invoice as
                        select
                            row_number() over() id,
                            tender.requisition_id,
                            tender.product_id,
                            sum_quantity_tender,
                            sum_quantity_purchase,
                            sum_quantity_picking,
                            sum_quantity_invoice
                            from (
                            select
                                requisition_id,
                                product_id,
                                sum(product_qty) sum_quantity_tender
                            from purchase_requisition_line prl group by requisition_id,product_id
                            )tender
                        left join(
                        select requisition_id,product_id,sum(quantity) sum_quantity_invoice from (
                            select
                                po.id purchase_id,
                                invoice_id,
                                requisition_id,
                                purchase_name,
                                product_id,
                                quantity from (
                                    select
                                        ai.id invoice_id,
                                        ai.origin purchase_name,
                                        product_id,
                                        quantity
                                        from account_invoice ai
                                    inner join
                                        account_invoice_line ail
                                        on ai.id = ail.invoice_id
                                        where state in ('draft','open','paid') and ai.picking_id is null
                                        )invoice
                                inner join
                                    purchase_order po
                                    on invoice.purchase_name = po.name
                                )inv  group by requisition_id,product_id
                        union all
                        select requisition_id,product_id,sum(quantity) sum_quantity_invoice from (
                            select
                                po.id purchase_id,
                                invoice_id,
                                requisition_id,
                                purchase_name,
                                product_id,
                                quantity from (
                                    select
                                        ai.id invoice_id,
                                        ai.origin purchase_name,
                                        product_id,
                                        quantity
                                        from account_invoice ai
                                    inner join
                                        account_invoice_line ail
                                        on ai.id = ail.invoice_id
                                        where state in ('draft','open','paid') and ai.picking_id is not null
                                        )invoice
                                inner join
                                    purchase_order po
                                    on invoice.purchase_name = po.name
                                )inv  group by requisition_id,product_id)invoice
                        on tender.requisition_id = invoice.requisition_id and tender.product_id = invoice.product_id
                        left join (
                        select requisition_id,product_id,sum(qty_done) sum_quantity_picking from (
                            select po.group_id,picking_id,product_id,qty_done,requisition_id from (
                                select group_id,picking_id,product_id,qty_done,state from stock_picking pick
                            inner join
                                stock_pack_operation spo on pick.id = spo.picking_id where qty_done > 0 and state in ('done')
                            )picking
                            inner join purchase_order po on picking.group_id = po.group_id
                        )order_picking group by requisition_id,product_id)picking
                        on tender.requisition_id = picking.requisition_id and tender.product_id = picking.product_id
                        left join
                        (
                         select
					        requisition_id,
					        product_id,
					        sum(qty_received) sum_quantity_purchase
					    from purchase_requisition_line prl group by requisition_id,product_id
                        )porder
                        on tender.requisition_id = porder.requisition_id and tender.product_id = porder.product_id
                        """)

class ViewRequisitionTracking(models.Model):

    _name = 'view.requisition.tracking'
    _description = 'Tracking Purchase Requisition'
    _auto = False
    _order = 'pr_id'

    pr_id = fields.Many2one('purchase.request')
    requisition_id = fields.Many2one('purchase.requisition')
    complete_name = fields.Char('Complete Name')

    def init(self, cr):
        drop_view_if_exists(cr, 'view_requisition_tracking')
        cr.execute("""create or replace view view_requisition_tracking as
                        select pr.id pr_id , prq.id requisition_id,pr.complete_name complete_name
                        from purchase_requisition prq
                        inner join
                        purchase_request pr
                        on prq.request_id  = pr.id
                        where pr.state in ('done','approved') group by pr.id,prq.id
                        """)

class ViewRequestRequisitionTracking(models.Model):

    _name = 'view.request.requisition.tracking'
    _description = 'Global Tracking Purchase Requisition'
    _auto = False
    _order = 'pr_id'
    _inherit=['mail.thread']

    id = fields.Char('ID')
    pr_id = fields.Many2one('purchase.request')
    date_start = fields.Date('Date Start')
    requisition_id = fields.Many2one('purchase.requisition')
    complete_name = fields.Char('Complete Name')
    detail_ids = fields.One2many('view.detail.request.requisition.tracking','vrrt_id')
    status_po = fields.Char(compute='status_tracking', translate=True)
    status_picking = fields.Char(compute='status_tracking', translate=True)
    status_invoice = fields.Char(compute='status_tracking', translate=True)
    type_location = fields.Char('Location')
    company_id = fields.Many2one('res.company','Company')

    def init(self, cr):
        drop_view_if_exists(cr, 'view_request_requisition_tracking')
        cr.execute("""create or replace view view_request_requisition_tracking as
                        select
                            row_number() over() id,
                            pr.date_start date_start,
                            pr_id,
                            requisition_id,
                            vrrt.complete_name,
                            vrrt.type_location,
                            vrrt.company_id
                        from (
                            select
                                row_number() over() id,
                                pr_id,
                                requisition_id,
                                parent_tracking.complete_name complete_name,
                                type_location,
                                company_id
                                from (
                                    select pr_id,vqt.requisition_id,complete_name
                                        from validate_tracking_purchase_order_invoice vtpo
                                            inner join
                                            view_requisition_tracking vqt
                                            on vqt.requisition_id = vtpo.requisition_id
                                            group by pr_id,vqt.requisition_id,complete_name
                                    )parent_tracking
                                    inner join purchase_request pr on parent_tracking.pr_id = pr.id
                                )vrrt inner join purchase_request pr on vrrt.pr_id = pr.id
                                order by pr_id asc
                        """)

    @api.multi
    @api.depends('detail_ids')
    def status_tracking(self):
        for item in self:
            if item.detail_ids :
                initial = len(item.detail_ids)

                item.env.cr.execute("select count(CASE WHEN progress_po = 'Done' THEN 1 END) from view_detail_request_requisition_tracking where vrrt_id = %d" %(item.id))
                po_done = item.env.cr.fetchone()[0]

                item.env.cr.execute("select count(CASE WHEN progress_po = 'in Progress' THEN 1 END) from view_detail_request_requisition_tracking where vrrt_id = %d" %(item.id))
                po_notdone = item.env.cr.fetchone()[0]

                item.env.cr.execute("select count(CASE WHEN progress_picking = 'Done' THEN 1 END) from view_detail_request_requisition_tracking where vrrt_id = %d" %(item.id))
                picking_done = item.env.cr.fetchone()[0]

                item.env.cr.execute("select count(CASE WHEN progress_picking = 'in Progress' THEN 1 END) from view_detail_request_requisition_tracking where vrrt_id = %d" %(item.id))
                picking_not_done = item.env.cr.fetchone()[0]

                item.env.cr.execute("select count(CASE WHEN progress_invoice = 'Done' THEN 1 END) from view_detail_request_requisition_tracking where vrrt_id = %d" %(item.id))
                invoice_done = item.env.cr.fetchone()[0]

                item.env.cr.execute("select count(CASE WHEN progress_invoice = 'in Progress' THEN 1 END) from view_detail_request_requisition_tracking where vrrt_id = %d" %(item.id))
                invoice_not_done = item.env.cr.fetchone()[0]


                if po_notdone > 0 :
                    item.status_po = 'In Progress'
                elif po_done == initial:
                    item.status_po = 'Done'
                if picking_not_done > 0:
                    item.status_picking = 'In Progress'
                elif picking_done == initial:
                    item.status_picking = 'Done'
                if invoice_not_done > 0 :
                    item.status_invoice = 'In Progress'
                elif invoice_done == initial:
                    item.status_invoice = 'Done'

class ViewResultTrackingPurchaseOrderInvoice(models.Model):

    _name = 'result.tracking.purchase.order'
    _description = 'Result Tracking Purchase Order To Invoice'
    _auto = False
    _order = 'id'
    _inherit=['mail.thread']

    id = fields.Char('ID')
    requisition_id = fields.Many2one('purchase.requisition')
    date_report = fields.Datetime('Date',track_visibility='onchange')
    product_id = fields.Many2one('product.product')
    status_pp = fields.Char('Status PP',track_visibility='onchange')
    progress_po = fields.Char('Status PO',track_visibility='onchange')
    progress_picking = fields.Char('Status Picking',track_visibility='onchange')
    progress_invoice = fields.Char('Status Invoice',track_visibility='onchange')
    sum_quantity_tender = fields.Float('Quantity Tender')
    sum_quantity_purchase = fields.Float('Quantity Purchase')
    sum_quantity_picking = fields.Float('Quantity Picking')
    sum_quantity_invoice = fields.Float('Quantity Invoice')

    def init(self, cr):
        drop_view_if_exists(cr, 'result_tracking_purchase_order')
        cr.execute("""create or replace view result_tracking_purchase_order as
                        select id,now() date_report,
                            requisition_id ,
                            product_id ,
                            case
                            when sum_quantity_tender = sum_quantity_purchase and sum_quantity_tender = sum_quantity_picking and sum_quantity_tender = sum_quantity_invoice then 'PP Closed' else 'PP Outstanding' end status_pp,
                            case when sum_quantity_tender = sum_quantity_purchase then 'Done' else 'in Progress' end progress_po,
                            case when sum_quantity_tender = sum_quantity_picking then 'Done' else 'in Progress' end progress_picking,
                            case when sum_quantity_tender = sum_quantity_invoice then 'Done' else 'in Progress' end progress_invoice,
                            sum_quantity_tender,sum_quantity_purchase,sum_quantity_picking,sum_quantity_invoice
                            from validate_tracking_purchase_order_invoice
                        """)

class ViewDetailRequestRequisitionTracking(models.Model):

    _name = 'view.detail.request.requisition.tracking'
    _description = 'Tracking Detail Purchase Requisition'
    _auto = False
    _order = 'vrrt_id'

    id = fields.Char('ID')
    vrrt_id = fields.Many2one('view.request.requisition.tracking')
    date_report = fields.Datetime('Date',track_visibility='onchange')
    product_id = fields.Many2one('product.product')
    requisition_id = fields.Many2one('purchase.requisition')
    progress_po = fields.Char('Status PO',track_visibility='onchange')
    progress_picking = fields.Char('Status Picking',track_visibility='onchange')
    progress_invoice = fields.Char('Status Invoice',track_visibility='onchange')

    def init(self, cr):
        drop_view_if_exists(cr, 'view_detail_request_requisition_tracking')
        cr.execute("""create or replace view view_detail_request_requisition_tracking as
                        select row_number() over() id,vrrt.id vrrt_id,
                                now() date_report,
                                vrrt.requisition_id , product_id,progress_po,progress_picking,progress_invoice
                            from
                            result_tracking_purchase_order rtpo
                            inner join
                            view_request_requisition_tracking vrrt on rtpo.requisition_id = vrrt.requisition_id
                        """)