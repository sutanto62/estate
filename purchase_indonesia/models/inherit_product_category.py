# -*- coding: utf-8 -*-

from openerp import models, fields

class ProductCategoryProcurement(models.Model):
    """Extend Product Category for Estate Activity Material Line."""
    _inherit = "product.category"

    technical_checker = fields.Many2one('res.users', 'Technical Checker')
    
    def get_technical_checker(self):
        if self.technical_checker:
            return self.technical_checker
        else:
            if self.parent_id:
                return self.parent_id.get_technical_checker()
            else:
                return None