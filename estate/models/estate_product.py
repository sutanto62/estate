# -*- coding: utf-8 -*-

from openerp import models, fields, api, osv

class ProductCategory(models.Model):
    """Extend Product Category for Estate Activity Material Line."""
    _inherit = "product.category"

    estate_product = fields.Boolean("Contains Estate Produdcts", default=False,
                                    help="All products with this category will be used at Estate Activity Material Line.")
