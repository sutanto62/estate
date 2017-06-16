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
from lxml import etree
from openerp.tools.translate import _
import babel.numbers
import decimal
import locale

from openerp.tools import (drop_view_if_exists)


class ViewGoodsInReport(models.Model):

    _name = 'view.goods.in.report'
    _description = 'Goods In Report'
    _auto = False
    _order = 'date_stock asc'

    id = fields.Integer()
    location_dest_id = fields.Many2one('stock.location','Location')
    date_stock = fields.Date('Move Date')
    product_id = fields.Many2one('product.product','Back Order')
    name_template = fields.Char('Product Name')
    default_code = fields.Char('Product Code')
    picking_id = fields.Many2one('stock.picking','Picking')
    product_uom =fields.Many2one('product.uom','UOM')
    product_qty = fields.Float('Quantity Product')
    price_unit = fields.Float('Unit Price')
    total_price = fields.Float('Total')
    partner_id = fields.Many2one('res.partner','Vendor')
    purchase_order_name = fields.Char('Purchase Order Name')
    pr_source = fields.Char('No PP')
    general_account_id = fields.Many2one('account.account','COA')

    def init(self, cr):

        drop_view_if_exists(cr, 'view_goods_in_report')

        cr.execute("""
                 create or replace view view_goods_in_report as
                        select
                            row_number() over() id ,
                            location_dest_id,
                            date_stock,
                            picking_id,
                            product_id,
                            name_template,
                            default_code ,
                            product_uom,
                            product_qty,
                            price_unit,
                            (product_qty * price_unit) total_price,
                            general_account_id,
                            partner_id,
                            purchase_order_name,
                            pr_source
                        from (
                            select
                                location_dest_id,
                                date(create_date) date_stock,
                                picking_id,
                                product_id,
                                product_uom,
                                general_account_id,
                                sum(product_qty) product_qty,
                                sum(price_unit) price_unit
                            from
                                stock_move
                                where
                                location_dest_id in (
                                    select
                                        id
                                    from
                                        stock_location
                                    where location_id in
                                    (
                                        select
                                            id
                                        from
                                            stock_location
                                        where
                                            id in
                                            (
                                                select
                                                    view_location_id
                                                from
                                                    stock_warehouse)
                                            ) and active = True
                                        ) and state = 'done' group by location_dest_id,
                                                  date_stock,
                                                  picking_id,
                                                  general_account_id,
                                                  product_id,
                                                  product_uom
                                    )stock_in
                                    inner join (
                                    select
                                            id,
                                            name_template,
                                            default_code
                                        from
                                            product_product
                                    )pp on stock_in.product_id = pp.id
                                    inner join (
                                    select
                                        id,
                                        partner_id,
                                        purchase_order_name,
                                        pr_source
                                    from stock_picking where state = 'done')sp on stock_in.picking_id = sp.id
                        """)

class ViewGoodsOutReport(models.Model):

    _name = 'view.goods.out.report'
    _description = 'Goods Out Report'
    _auto = False
    _order = 'date_stock asc'

    id = fields.Integer()
    location_dest_id = fields.Many2one('stock.location','Location')
    date_stock = fields.Date('Move Date')
    product_id = fields.Many2one('product.product','Back Order')
    name_template = fields.Char('Product Name')
    default_code = fields.Char('Product Code')
    picking_id = fields.Many2one('stock.picking','Picking')
    product_uom =fields.Many2one('product.uom','UOM')
    product_qty = fields.Float('Quantity Product')
    price_unit = fields.Float('Unit Price')
    total_price = fields.Float('Total')
    description = fields.Char('Description')
    company_id = fields.Many2one('res.company','Company')
    general_account_id = fields.Many2one('account.account','COA')


    def init(self, cr):

        drop_view_if_exists(cr, 'view_goods_out_report')

        cr.execute("""
              create or replace view view_goods_out_report as
            select
                row_number() over() id ,
                location_dest_id,
                date_stock,
                company_id,
                stock_out.picking_id,
                stock_out.product_id,
                general_account_id,
                product_total_qty product_qty,
                price_total_unit price_unit,
                name_template,
                default_code,
                product_uom,
                (product_total_qty * price_total_unit) total_price,
                description
            from (
                select
                    location_dest_id,
                    date(create_date) date_stock,
                    picking_id,
                    product_id,
                    company_id,
                    general_account_id,
                    product_uom,
                    sum(product_qty) product_total_qty,
                    sum(price_unit) price_total_unit
                from
                    stock_move
                    where
                    location_dest_id not in (
                        select
                            id
                        from
                            stock_location
                        where location_id in
                        (
                            select
                                id
                            from
                                stock_location
                            where
                                id in
                                (
                                    select
                                        view_location_id
                                    from
                                        stock_warehouse)
                                ) and active = True
                        )and state = 'done' group by
                                  company_id,
                                  location_dest_id,
                                  create_date,
                                  picking_id,
                                  product_id,
                                  product_uom,
                                  general_account_id
                        )stock_out
                        inner join(
                        select
                                id,
                                name_template,
                                default_code
                            from
                                product_product
                        )pp on stock_out.product_id = pp.id
                        left join
                        (
                            select
                                picking_id,
                                product_id,
                                description
                            from stock_move
                        )stock_move
                        on
                        stock_out.product_id = stock_move.product_id
                        and
                        stock_out.picking_id = stock_move.picking_id
                        """)

class StockMin(models.Model):

    _name = 'stock.min'
    _description = 'Stock Min'
    _auto = False
    _order = 'location_id asc'

    location_id = fields.Many2one('stock.location','Location')
    date_stock = fields.Date('Move Date')
    product_id = fields.Many2one('product.product','Back Order')
    cost = fields.Float('Cost')
    qty =fields.Float('Qty')
    negative_move_id = fields.Float('Negative Move')

    def init(self, cr):

        drop_view_if_exists(cr, 'stock_min')

        cr.execute("""
              create or replace view stock_min as
                select
                    location_id,
                    date(create_date) date_stock,
                    product_id,
                    qty,
                    cost,
                    negative_move_id from stock_quant
                where
                    negative_move_id
                    is not null
                        """)

class StockPlus(models.Model):

    _name = 'stock.plus'
    _description = 'Stock Plus'
    _auto = False
    _order = 'location_id asc'

    location_id = fields.Many2one('stock.location','Location')
    date_stock = fields.Date('Move Date')
    product_id = fields.Many2one('product.product','Back Order')
    cost = fields.Float('Cost')
    qty =fields.Float('Qty')
    negative_move_id = fields.Float('Negative Move')

    def init(self, cr):
        drop_view_if_exists(cr, 'stock_plus')

        cr.execute("""
              create or replace view stock_plus as
                    select
                        location_id,
                        date(create_date) date_stock,
                        product_id,
                        qty,
                        cost,
                        negative_move_id from stock_quant
                    where
                        negative_move_id
                        is null
                        """)

class StockDetailSummaryReport(models.Model):

    _name = 'summary.goods.detail.report'
    _description = 'Stock Detail Summary Report'
    _auto = False
    _order = 'id asc'

    id = fields.Integer()
    code = fields.Char('Code')
    date_stock = fields.Date('Move Date')
    product_id = fields.Many2one('product.product','Back Order')
    cost = fields.Float('Cost')
    name_template = fields.Char('Product Name')
    default_code = fields.Char('Code')
    product_qty =fields.Float('Qty')
    price_qty = fields.Float('Price')

    def init(self, cr):

        drop_view_if_exists(cr, 'summary_goods_detail_report')

        cr.execute("""
              create or replace view summary_goods_detail_report as
                    select
                        row_number() over() id ,
                        date_stock ,
                        code ,
                        product_id ,
                        cost ,
                        name_template,
                        default_code,
                        product_qty ,
                        price_unit
                        from(
                            select
                                date_stock,
                                product_id,
                                'result' code,
                                product_qty,
                                (product_qty * price_unit ) price_unit
                            from (
                                select
                                    date_stock,
                                    product_id,
                                    'result' code,
                                    sum(qty) product_qty,
                                    sum(cost) price_unit
                                from (
                                    select * from stock_plus
                                    union all
                                    select * from stock_min
                                )last_stock
                            group by
                                date_stock,
                                product_id
                            )stock
                            union all
                            select
                                   date_stock,
                                   product_id,
                                   'out' code,
                                   sum(product_qty) product_qty,
                                   sum(total_price) price_unit
                                   from view_goods_out_report
                                   group by date_stock,product_id
                            union all
                            select
                                   date_stock,
                                   product_id,
                                   'in' code,
                                   sum(product_qty) product_qty,
                                   sum(total_price) price_unit
                                   from view_goods_in_report group by date_stock,product_id
                        )summary
                        inner join
                        (
                            select id,
                                   name_template,
                                   default_code,
                                   cost
                            from (
                                    select
                                        id,
                                        name_template,
                                        default_code
                                    from
                                        product_product
                                    ) pp
                                inner join
                                (
                                select
                                    pph1.product_id product_id,cost
                                from (
                                    select
                                        max(id) max_id,
                                        product_id from product_price_history
                                        group by product_id)pph1
                                    inner join (
                                    select
                                        id,
                                        product_id,
                                        cost from
                                        product_price_history) pph2
                                        on
                                            pph1.max_id = pph2.id
                                            and
                                            pph1.product_id = pph2.product_id
                                        order by product_id asc
                                    )prod_history on pp.id = prod_history.product_id
                                )pp
                                on pp.id = summary.product_id
                                order by id,code asc
                        """)

class SummaryStock(models.Model):

    _name = 'summary.stock'
    _description = 'Stock Plus'
    _auto = False
    _order = 'categ_id asc'

    id = fields.Integer()
    categ_id = fields.Many2one('product.category','Category')
    date_stock = fields.Date('Move Date')
    product_id = fields.Many2one('product.product','Back Order')
    cost = fields.Float('Cost')
    goods_in_qty = fields.Float('Product In')
    goods_in_price = fields.Float('In Price')
    goods_out_qty =fields.Float('Out Qty')
    goods_out_price = fields.Float('Out Price')
    goods_result_qty = fields.Float('Result Qty')
    goods_result_price = fields.Float('Result Price')


    def init(self, cr):
        drop_view_if_exists(cr, 'summary_stock')

        cr.execute("""
              create or replace view summary_stock as
                    select
                        row_number() over() id ,
                        categ_id,
                        summary.product_id product_id,
                        date_stock,
                        cost,
                        goods_in_qty,
                        goods_in_price,
                        goods_out_qty,
                        goods_out_price,
                        goods_result_qty,
                        goods_result_price
                    from (
                    select
                        date_stock,product_id,cost,
                        max(CASE WHEN code = 'in' THEN product_qty ELSE 0 END) AS goods_in_qty,
                        max(CASE WHEN code = 'in' THEN price_unit ELSE 0 END) AS goods_in_price,
                        max(CASE WHEN code = 'out' THEN product_qty ELSE 0 END) AS goods_out_qty,
                        max(CASE WHEN code = 'out' THEN price_unit ELSE 0 END) AS goods_out_price,
                        max(CASE WHEN code = 'result' THEN product_qty ELSE 0 END) AS goods_result_qty,
                        max(CASE WHEN code = 'result' THEN price_unit ELSE 0 END) AS goods_result_price
                    from summary_goods_detail_report group by date_stock,product_id,cost)summary
                    inner join
                    (
                        select pp.id product_id,product_tmpl_id,categ_id
                        from product_product pp
                        inner join product_template pt on pt.id = pp.product_tmpl_id
                    )category on summary.product_id = category.product_id
                        """)