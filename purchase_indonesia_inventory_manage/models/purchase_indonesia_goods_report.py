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


class ViewGoodsInReport(models.Model):

    _name = 'view.goods.in.report'
    _description = 'Goods In Report'
    _auto = False
    _order = 'move_date asc'

    id = fields.Integer()
    complete_name_picking = fields.Char('Complete Name Picking')
    backorder_id= fields.Many2one('stock.picking','Back Order')
    purchase_order_name = fields.Char('Purchase Order Name')
    move_date = fields.Datetime('Move Date')
    product_id = fields.Many2one('product.product','Back Order')
    picking_id = fields.Many2one('stock.picking','Picking')
    product_uom =fields.Many2one('product.uom','UOM')
    product_uom_qty = fields.Float('Quantity Product')
    price_unit = fields.Float('Unit Price')
    total = fields.Float('Total')

    def init(self, cr):
        cr.execute("""
                 create or replace view view_goods_in_report as
                    select row_number() over() id ,
                                complete_name_picking,
                                backorder_id,
                                purchase_order_name,
                                move_date,
                                move.product_id,
                                move.picking_id,
                                product_uom,
                                product_uom_qty,
                                price_unit ,(product_uom_qty*price_unit)total
                        from (
                        select date move_date,
                                product_id,
                                picking_id,
                                product_uom,
                                product_uom_qty,
                                price_unit from stock_move where state = 'done'
                        )move
                    left join (
                    select sp.id picking_id,
                            date_done date_in,
                            complete_name_picking,
                            purchase_order_name,backorder_id,
                            product_id,qty_done
                            from
                                stock_picking  sp
                            inner join
                                stock_pack_operation spo
                            on sp.id = spo.picking_id
                            where name like '%WH/IN/%' and state = 'done' and qty_done > 0)picking
                    on move.picking_id = picking.picking_id
                        """)

class ViewGoodsOutReport(models.Model):

    _name = 'view.goods.out.report'
    _description = 'Goods Out Report'
    _auto = False
    _order = 'move_date asc'

    id = fields.Integer()
    move_date = fields.Datetime('Move Date')
    product_id = fields.Many2one('product.product','Back Order')
    picking_id = fields.Many2one('stock.picking','Picking')
    product_uom =fields.Many2one('product.uom','UOM')
    product_uom_qty = fields.Float('Quantity Product')
    price_unit = fields.Float('Unit Price')
    total = fields.Float('Total')
    general_account_id = fields.Many2one('account.account','General Account')
    description = fields.Text('Description')


    def init(self, cr):
        cr.execute("""
               create or replace view view_goods_out_report as
                    select row_number() over() id ,
                                move_date,
                                move.product_id,
                                move.picking_id,
                                product_uom,
                                product_uom_qty,
                                price_unit ,
                                (product_uom_qty*price_unit)total,
                                general_account_id,
                                description
                        from (
                        select date move_date,
                                product_id,
                                picking_id,
                                product_uom,
                                product_uom_qty,
                                price_unit,general_account_id,description from stock_move where state = 'done'
                        )move
                    left join (
                    select sp.id picking_id,
                            date_done date_in,
                            complete_name_picking,
                            purchase_order_name,backorder_id,
                            product_id,qty_done
                            from
                                stock_picking  sp
                            inner join
                                stock_pack_operation spo
                            on sp.id = spo.picking_id
                            where name like '%WH/OUT/%' and state = 'done' and qty_done > 0)picking
                    on move.picking_id = picking.picking_id
                        """)