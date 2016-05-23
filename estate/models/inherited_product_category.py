# -*- coding: utf-8 -*-

from openerp import models, fields, api, osv

class ProductCategory(models.Model):
    """Extend Product Category for Estate Activity Material Line."""
    _inherit = "product.category"

    estate_product = fields.Boolean("Contains Estate Products", default=False,
                                    help="Set true to set all childs products as Upkeep Material Line.")
