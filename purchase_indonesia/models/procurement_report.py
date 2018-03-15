from openerp import models,fields
from openerp.tools import (drop_view_if_exists)

class ViewSLAProcurement(models.Model):
    _name = 'v.sla.procurement'
    _description = 'SLA Procurement'
    _auto = False
    
    pr_no = fields.Char('Purchase Request')
    urgency = fields.Char('Urgency')
    po_no = fields.Char('Purchase Order')
    pp_location_code = fields.Char('PR Location')
    vendor_location_code = fields.Char('Vendor Location')
    distance = fields.Char('Distance')
    pp_full_approve_date = fields.Date('PR Approved Date')
    qcf_approve_date = fields.Date('QCF Approved Date')
    grn_approve_date = fields.Date('GRN Approved Date')
    inv_received_procurement_date = fields.Date('Invoice Received Date')
    inv_paid_date = fields.Date('Invoice Paid Date')
    pp_to_qcf = fields.Float('PR to QCF')
    qcf_to_grn = fields.Float('QCF to GRN')
    grn_to_inv_received = fields.Float('GRN to Invoice')
    inv_received_to_inv_paid = fields.Float('Invoice to Paid')
    days = fields.Float('SLA (Days)')
    
    def init(self, cr):
        drop_view_if_exists(cr, 'v_sla_procurement')
        
        cr.execute("""
            create or replace view v_sla_procurement as
            with v_mapping_location_company as (
                select 
                    rc.id,
                    rc.code,
                    rc.partner_id,
                    rcs.island_name,
                    rp.name office_code
                from 
                    res_company rc
                    inner join 
                    res_partner rp
                    on rc.partner_id = rp.parent_id
                    inner join
                    (
                        select 
                            rcs_state.id,
                            rcs_island.name island_name
                        from 
                            res_country_state rcs_state
                            inner join 
                            res_country_state rcs_island
                            on rcs_state.island_id = rcs_island.id
                    )rcs on rp.state_id = rcs.id
                union all
                select 
                    rc.id,
                    rc.code,
                    rc.partner_id,
                    rcs.island_name,
                    'KPST' office_code
                from 
                    res_company rc
                    inner join 
                    res_partner rp
                    on rc.partner_id = rp.id
                    inner join
                    (
                        select 
                            rcs_state.id,
                            rcs_island.name island_name
                        from 
                            res_country_state rcs_state
                            inner join 
                            res_country_state rcs_island
                            on rcs_state.island_id = rcs_island.id
                    )rcs on rp.state_id = rcs.id
            ),v_mapping_location_vendor as (
                select 
                    rp.id,
                    rcs_island.name island_name
                from 
                    res_partner rp
                    inner join
                    res_country_state rcs_state
                    on rp.state_id = rcs_state.id
                    inner join 
                    res_country_state rcs_island
                    on rcs_state.island_id = rcs_island.id
            )
            select 
                sla_procurement.id,
                pr_no,
                urgency,
                po_no,
                pp_location_code,
                vendor_location_code,    
                pp_full_approve_date,    
                qcf_approve_date,    
                grn_approve_date,    
                inv_received_procurement_date,    
                inv_paid_date,    
                pp_to_qcf,    
                qcf_to_grn,    
                grn_to_inv_received,    
                inv_received_to_inv_paid,    
                (case when svm.name is null then 
                        case 
                            when 
                                sla_procurement.distance_code = 'local'
                            then
                                30
                            when 
                                sla_procurement.distance_code = 'inter_island'
                            then
                                60
                            else
                                svm.days
                        end
                    else 
                        svm.days 
                    end) days,
                (case when svm.name is null then 
                        case 
                            when 
                                sla_procurement.distance_code = 'local'
                            then
                                'Lokal'
                            when 
                                sla_procurement.distance_code = 'inter_island'
                            then
                                'Antar Pulau'
                            else
                                sla_procurement.distance_code
                        end
                    else 
                        svm.name 
                    end) as distance
              from
                (
                select
                    row_number() over() id,
                    pr.complete_name pr_no,
                    pr.urgency,
                    po.complete_name po_no,
                    pr.island_name pp_location_code,
                    po.island_name vendor_location_code,
                    case when pr.island_name is null or po.island_name is null then 'Vendor State Not Set Correctly' else
                    (case when pr.island_name = po.island_name then 'local' else 'inter_island' end) end distance_code,
                    pr.pp_full_approve_date,
                    po.qcf_approve_date,
                    po.grn_approve_date,
                    po.inv_received_procurement_date,
                    po.inv_paid_date,
                    EXTRACT('epoch' from po.qcf_approve_date-pr.pp_full_approve_date)/(60*60*24) pp_to_qcf,
                    EXTRACT('epoch' from po.grn_approve_date-po.qcf_approve_date)/(60*60*24) qcf_to_grn,
                    EXTRACT('epoch' from po.inv_received_procurement_date-po.grn_approve_date)/(60*60*24) grn_to_inv_received,
                    EXTRACT('epoch' from po.inv_paid_date-po.inv_received_procurement_date)/(60*60*24) inv_received_to_inv_paid
                from 
                (
                    select 
                        po.requisition_id,
                        po.complete_name,
                        po.create_date qcf_approve_date,
                        ai.create_date inv_received_procurement_date,
                        ai.inv_paid_date,
                        sp.grn_approve_date,
                        po.partner_id,
                        p."name" vendor_name,
                        vl.island_name,
                        po.state
                    from 
                        (select * from purchase_order where state = 'purchase' or state = 'done') po 
                            inner join res_partner p 
                            on po.partner_id = p.id
                            left join (
                                select 
                                    ai.*,
                                    mtv.create_date inv_paid_date
                                from 
                                    account_invoice ai
                                    left join
                                    (
                                        select 
                                            mtv.create_date,
                                            mm.res_id
                                        from 
                                            mail_tracking_value mtv inner join (
                                            select * from mail_message where model = 'account.invoice'
                                        ) mm on mm.id = mtv.mail_message_id 
                                        where mtv.field = 'state' and new_value_char = 'Paid'
                                    )mtv
                                    on ai.id = mtv.res_id
                            ) ai
                            on ai.origin = po."name"
                            left join
                            (
                                select 
                                    sp.*,
                                    mtv.create_date grn_approve_date
                                from 
                                    stock_picking sp
                                    left join
                                    (
                                        select 
                                            mtv.create_date,
                                            mm.res_id
                                        from 
                                            mail_tracking_value mtv inner join (
                                            select * from mail_message where model = 'stock.picking'
                                        ) mm on mm.id = mtv.mail_message_id 
                                        where mtv.field = 'state' and (new_value_char = 'Done' or new_value_char = 'selesai')
                                    )mtv on sp.id = mtv.res_id
                            )sp 
                            on sp.origin = po."name"
                            left join v_mapping_location_vendor vl
                            on p.id = vl.id
                    ) po inner join 
                    (
                        select 
                            r.id request_id,
                            req.id requisition_id,
                            req.create_date pp_full_approve_date,
                            r.complete_name,
                            pit."name" urgency,
                            vc.island_name
                        from
                            purchase_requisition req
                            inner join
                            purchase_request r
                            on req.request_id = r.id
                            inner join purchase_indonesia_type pit
                            on r.type_purchase = pit.id
                            left join v_mapping_location_company vc
                            on vc.id = r.company_id and vc.office_code = r.code
                    ) pr 
                    on po.requisition_id = pr.requisition_id
                )sla_procurement
                left join sla_vendor_management svm
                on sla_procurement.distance_code = svm.code;
        """)
        
class ViewSLAVendor(models.Model):
    _name = 'v.sla.vendor'
    _description = 'SLA Vendor'
    _auto = False
    
    no_vendor = fields.Char('No Vendor')
    vendor_name = fields.Char('Vendor')
    po_no = fields.Char('PO ke-')
    qcf_approved = fields.Date('QCF Approved Date')
    grn_picked = fields.Date('GRN Picked Date')
    sla_vendor = fields.Float('SLA Vendor')
    status = fields.Char('Status')
    total_transaction = fields.Float('Total Transaction')
    product_category = fields.Char('Product Category')
    total_po_per_product_category = fields.Char('Total PO per Product Category')
    
    def init(self, cr):
        drop_view_if_exists(cr, 'v_sla_vendor')
        
        cr.execute("""
            create or replace view v_sla_vendor as
            select 
                row_number() over() id,
                (case when po_no = 1 then no_vendor||'' else '' end) no_vendor,
                (case when po_no = 1 then vendor_name||'' else '' end) vendor_name,
                po_no,
                qcf_approved,
                grn_picked,
                sla_vendor,
                status,
                total_transaction,
                product_category,
                '' total_po_per_product_category
            from 
            (
                select 
                    dense_rank() over(order by po.display_name) no_vendor,
                    po.display_name vendor_name,
                    row_number() over(partition by po.display_name order by po.create_date asc) po_no,
                    po.create_date qcf_approved,
                    sp.date_done grn_picked,
                    EXTRACT('epoch' from sp.date_done-po.create_date)/(60*60*24) sla_vendor,
                    po.state status,
                    po.amount_total total_transaction,
                    po.product_category,
                    '' total_po_per_product_category
                from 
                    (select origin,min(date_done) date_done from stock_picking group by origin) sp
                    inner join (
                        select 
                            po.*,rp.display_name,preq.product_category 
                        from 
                            (
                                select 
                                    * 
                                from 
                                    purchase_order where state in ('purchase','done','received_force_done')) po 
                                    inner join res_partner rp 
                                    on po.partner_id = rp.id
                                    inner join (
                                                select 
                                                    preq.id,pc."name" product_category
                                                from 
                                                    purchase_requisition preq 
                                                    inner join purchase_request pr 
                                                    on preq.request_id = pr.id 
                                                    inner join product_category pc
                                                    on pr.product_category_id = pc.id
                                                ) preq 
                            on preq.id = po.requisition_id
                    ) po
                    on sp.origin = po.name
            )sla_vendor;
        """)

class ViewHistoryProduct(models.Model):
    _name = 'v.history.product'
    _description = 'History Product'
    _auto = False
    
    code = fields.Char('Product Code')
    product_category = fields.Char('Product Category')
    product_name = fields.Char('Product Name')
    uom = fields.Char('UoM') 
    purchase_no = fields.Float('PO ke-')
    product_qty = fields.Float('Product Qty')
    accumulation_qty = fields.Float('Accumulation Qty')
    product_unit_price = fields.Float('Unit Price')
    avg_price = fields.Float('Average Price')
    ranked_by_purchase = fields.Char('Ranked by Purchase')
    ranked_by_qty = fields.Char('Ranked by Qty')
    product_id = fields.Integer('Product Id')
    po_create_date = fields.Date('PO Date')
    
    def init(self, cr):
        drop_view_if_exists(cr, 'v_history_product')
        
        cr.execute("""
            create or replace view v_history_product as
            with po_accumulation as (
                SELECT
                  product_id, purchase_no,
                  SUM(SUM(product_qty)) OVER (partition by product_id ORDER BY product_id, purchase_no ASC) AS accumulation_qty
                FROM
                (
                    select
                        row_number() over(partition by product_id order by pol.create_date asc) purchase_no,
                        product_id,
                        product_qty
                    from 
                        purchase_order_line pol 
                        inner join (select * from purchase_order where state in ('purchase','done','received_force_done')) po on pol.order_id = po.id
                )po
                GROUP BY product_id, purchase_no 
                ORDER BY product_id, purchase_no 
            ),
            po_average as (
                SELECT
                  product_id, purchase_no,
                  AVG(AVG(price_unit)) OVER (partition by product_id ORDER BY product_id, purchase_no ASC) AS avg_price
                FROM
                (
                    select
                        row_number() over(partition by product_id order by pol.create_date asc) purchase_no,
                        product_id,
                        price_unit
                    from 
                        purchase_order_line pol 
                        inner join (select * from purchase_order where state in ('purchase','done','received_force_done')) po on pol.order_id = po.id
                )po
                GROUP BY product_id, purchase_no 
                ORDER BY product_id, purchase_no 
            )
            select
                row_number() over() id,
                po.product_id,
                po.code,
                po.product_category,
                po.product_name,
                po.uom,
                po.purchase_no,
                po.product_qty,
                pa.accumulation_qty,
                po.product_unit_price,
                pavg.avg_price,
                '' ranked_by_purchase,
                '' ranked_by_qty,
                po.create_date po_create_date
            from
            (
                select 
                    pol.product_id,
                    pp.default_code code, 
                    pc."name" product_category,
                    pp.name_template product_name,
                    pu."name" uom,
                    row_number() over(partition by pp.name_template order by pol.create_date asc) purchase_no,
                    product_qty,
                    price_unit product_unit_price,
                    pol.create_date
                from 
                    purchase_order_line pol 
                    inner join (select * from purchase_order where state in ('purchase','done','received_force_done')) po on pol.order_id = po.id
                    inner join product_product pp on pol.product_id = pp.id
                    inner join product_template pt on pp.product_tmpl_id = pt.id
                    inner join product_category pc on pt.categ_id = pc.id
                    inner join product_uom pu on pol.product_uom = pu.id
            )po inner join po_accumulation pa
            on po.product_id = pa.product_id and po.purchase_no = pa.purchase_no
            inner join po_average pavg
            on po.product_id = pavg.product_id and po.purchase_no = pavg.purchase_no;
        """)
    

class ViewSumHistoryProduct(models.Model):
    _name = 'v.sum.history.product'
    _description = 'Summary History Product'
    _auto = False
    
    sum_purchase_no = fields.Float('Total PO')
    sum_product_qty = fields.Float('Total Product Qty')
    avg_price = fields.Float('Average Price')
    code = fields.Char('Product Code')
    product_category = fields.Char('Product Category')
    product_name = fields.Char('Product Name')
    uom = fields.Char('UoM')
    line_ids = fields.One2many('v.history.product','product_id','History Product Line')
    
    def init(self, cr):
        drop_view_if_exists(cr, 'v_sum_history_product')
        
        cr.execute("""
            create or replace view v_sum_history_product as
            select 
                sum_per_product.product_id as id,
                sum_per_product.sum_purchase_no,
                sum_per_product.sum_product_qty,
                sum_per_product.avg_price,
                pp.default_code code, 
                pc."name" product_category,
                pp.name_template product_name,
                pu."name" uom    
            from 
            (
            select 
                product_id, 
                max(purchase_no) sum_purchase_no, 
                sum(product_qty) sum_product_qty, 
                avg(product_unit_price) avg_price 
            from v_history_product group by product_id
            )sum_per_product
            inner join product_product pp on sum_per_product.product_id = pp.id
            inner join product_template pt on pp.product_tmpl_id = pt.id
            inner join product_category pc on pt.categ_id = pc.id
            inner join product_uom pu on pt.uom_id = pu.id;
        """)