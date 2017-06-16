from openerp import models, fields, api, exceptions
from openerp.exceptions import ValidationError
from datetime import datetime, date
from dateutil.relativedelta import *
from openerp.tools import (drop_view_if_exists)

class ViewPurchaseRequestLine(models.Model):

    _name = 'v.p.request.line'
    _description = 'Purchase Request Get Line'
    _auto = False
    _order = 'request_id asc'

    request_id = fields.Many2one('purchase.request','Purchase Request')
    request_state = fields.Char('State Purchase Request')
    product_id = fields.Many2one('product.product','Product')
    qty = fields.Float('Purchase Request Line Product Qty')

    def init(self, cr):
        drop_view_if_exists(cr, 'v_p_request_line')

        cr.execute("""create or replace view v_p_request_line as
                        select
                            request_id,
                            product_id,
                            request_state,
                            (case when control_unit != Null  then control_unit \
                            else product_qty end) as qty from purchase_request_line
                        where request_state in ('approved','done')
                        """)

class ViewPurchaseOrderLine(models.Model):

    _name = 'v.p.order.line'
    _description = 'Purchase Order Get Line'
    _auto = False
    _order = 'request_id asc'

    request_id = fields.Many2one('purchase.request','Purchase Request')
    product_id = fields.Many2one('product.product','Product')
    product_qty = fields.Float('Purchase Order Line Product Qty')

    def init(self, cr):
        drop_view_if_exists(cr, 'v_p_order_line')

        cr.execute("""create or replace view v_p_order_line as
                        select request_id,product_id,
                            (case when request_id = request_id and product_id = \
                            product_id then sum(product_qty) else product_qty end) product_qty   from (
                            select
                                request_id,
                                id
                            from
                                purchase_order
                            where
                                state not in ('draft','sent','to_approve','cancel') order by request_id)p_order
                        inner join (
                            select
                                order_id,
                                product_id,
                                (case when order_id = order_id and product_id = \
                                product_id then sum(product_qty) else product_qty end) product_qty
                                from purchase_order_line group by order_id,product_id,\
                                product_qty order by order_id asc
                                )order_line
                        on
                            p_order.id = order_line.order_id
                        group by request_id,product_id,product_qty
                        order by request_id asc
                        """)

class ViewGetPurchaseOrder(models.Model):

    _name = 'v.p.order'
    _description = 'Purchase Order Get Order '
    _auto = False
    _order = 'request_id asc'

    request_id = fields.Many2one('purchase.request','Purchase Request')
    product_id = fields.Many2one('product.product','Product')
    product_qty = fields.Float('Purchase Order Line Product Qty')

    def init(self, cr):
        drop_view_if_exists(cr, 'v_p_order')

        cr.execute("""create or replace view v_p_order as
                        select \
                            request_id,
                            product_id,
                            sum(case when request_id = request_id and product_id = product_id \
                            then product_qty else product_qty end) product_qty
                            from v_p_order_line
                        group by request_id,product_id
                        """)

class ViewGetPurchaseOrderAndRequest(models.Model):

    _name = 'v.p.line.request.order'
    _description = 'Purchase Order Get Order and get Request '
    _auto = False
    _order = 'request_id asc'

    request_id = fields.Many2one('purchase.request','Purchase Request')
    type_location = fields.Char('Type Location')

    def init(self, cr):
        drop_view_if_exists(cr, 'v_p_line_request_order')

        cr.execute("""create or replace view v_p_line_request_order as
                        select
                            request_id ,
                            (case when type_location < 0  then 'Undone' else 'Done' end) type_location
                        from (
                            select
                                request_id,
                                sum(qty-qty_po) type_location
                            from(
                                select
                                    v_p_order.request_id,
                                    v_p_order.product_id,
                                    product_qty qty_po , qty from v_p_order
                                inner join
                                    v_p_request_line
                                    on v_p_order.request_id = v_p_request_line.request_id
                                    and v_p_order.product_id = v_p_request_line.product_id
                            )line_request_order group by request_id
                        )order_po
                        """)

class ViewJoinPurchaseOrderAndRequest(models.Model):

    _name = 'v.p.request.order.join'
    _description = 'Join Get Purchase Order and Get Purchase Request'
    _auto = False
    _order = 'request_id asc'

    request_id = fields.Many2one('purchase.request','Purchase Request')
    type_location = fields.Char('Type Location')
    date_start = fields.Date('Date Start')
    company_id = fields.Many2one('res.company','Company')
    type_purchase = fields.Many2one('purchase.indonesia.type','Purchase Type')
    count_id = fields.Integer('Count ID')

    def init(self, cr):
        drop_view_if_exists(cr, 'v_p_request_order_join')

        cr.execute("""create or replace view v_p_request_order_join as
                        select
                            date_start,
                            company_id,
                            type_purchase,
                            id request_id,
                            line.type_location,
                            count_id
                        from
                            purchase_request pr
                        inner join
                        (
                            select
                                request_id,
                                type_location ,
                                count(*) count_id
                                from (
                                    select
                                        id request_id,
                                        pr.type_location
                                        from purchase_request  pr
                                    inner join
                                        v_p_line_request_order on v_p_line_request_order.request_id = pr.id
                                        union all
                                    select request_id,type_location
                                    from v_p_line_request_order group by request_id, type_location
                            ) request_location
                            group by
                                request_id,
                                type_location  order by request_id asc
                        )line on pr.id = line.request_id
                        """)

class DashboardProgressPpAndPo(models.Model):

    _name = 'dashboard.progress.pp.and.po'
    _description = 'Dashboard Resume Purchase Order and Purchase Request'
    _auto = False
    _order = 'company_name asc'

    id = fields.Char('ID')
    company_name = fields.Char('Company Name')
    type_name = fields.Char('Purchase Type Name')
    company_id = fields.Many2one('res.company','Company')
    type_purchase = fields.Many2one('purchase.indonesia.type','Purchase Type')
    estate = fields.Integer('Estate')
    ho = fields.Integer('HO')
    done = fields.Integer('Done')
    undone = fields.Integer('Undone')


    def init(self, cr):
        drop_view_if_exists(cr, 'dashboard_progress_pp_and_po')

        cr.execute("""create or replace view dashboard_progress_pp_and_po as
                          select
                            row_number() over() id,
                            (case when rc.id = 1 then rc.company_name else '' end) as company_name,
                            rc.type_name, po_pp.*
                          from
                            (
                                select
                                    row_number() over(PARTITION BY rcy.id order by pit.id) id,
                                    rcy.id company_id,
                                    rcy.name company_name,
                                    pit.id type_id,
                                    pit.name type_name
                                from
                                    purchase_indonesia_type pit, res_company rcy
                            ) rc
                            left join
                            (
                                SELECT
                                    company_id,
                                    type_purchase,
                                    SUM(CASE WHEN type_location = 'Estate' THEN count_id ELSE 0 END) AS Estate,
                                    SUM(CASE WHEN type_location = 'HO' THEN count_id ELSE 0 END) AS HO,
                                    SUM(CASE WHEN type_location = 'Done' THEN count_id ELSE 0 END) AS Done,
                                    SUM(CASE WHEN type_location = 'Undone' THEN count_id ELSE 0 END) AS Undone
                                FROM (
                                    select
                                        *
                                    from
                                        v_p_request_order_join
                                )pp_po_result
                                group by
                                    company_id,
                                    type_purchase
                            ) po_pp
                            on
                                rc.company_id = po_pp.company_id
                                and rc.type_id = po_pp.type_purchase
                        """)




