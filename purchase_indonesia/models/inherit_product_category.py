# -*- coding: utf-8 -*-

from openerp import models, fields, api

class ProductCategoryProcurement(models.Model):
    """Extend Product Category for Estate Activity Material Line."""
    _inherit = "product.category"

    technical_checker = fields.Many2one('res.users', 'Technical Checker')
    code = fields.Char('Naming Code')
    allowed_company_ids = fields.Many2many('res.company',string='Allowed Company')
    
    #return the first found technical checker
    def get_technical_checker(self):
        if self.technical_checker:
            return self.technical_checker
        else:
            if self.parent_id:
                return self.parent_id.get_technical_checker()
            else:
                return None
    
    #return the first found allowed company        
    def get_allowed_company_ids(self):
        if self.allowed_company_ids:
            return self.allowed_company_ids
        else:
            if self.parent_id:
                return self.parent_id.get_allowed_company_ids()
            else:
                return False

class ProductCustomFunction(models.Model):
    _name = 'product.custom.function'
    _description = 'Product Custom Function'
                
    def init(self, cr):
        cr.execute("""
            CREATE OR REPLACE FUNCTION public.get_next_product_code_number(i_category_code varchar)
            RETURNS varchar
            LANGUAGE plpgsql
            AS $function$
                declare
                    product_code_number varchar ;
                BEGIN
                   select 
                        (category_code || lpad((max(product_code)+1)::text,4,'0')) into product_code_number
                    from (
                        select 
                            left(default_code,4) category_code, right(default_code, 4)::int product_code, default_code 
                        from 
                            product_product
                        where
                            default_code not like (
                                '%Lenovo%'
                            )
                            and id not in (
                                15319
                            )
                        )product
                    where
                        product.category_code = $1
                    group by
                        product.category_code;
                   RETURN product_code_number;
                END;
            $function$
        """)
        
class InheritProductTemplate(models.Model):
    _inherit = 'product.template'
    
    @api.onchange('categ_id')
    def _onchange_categ_id(self):
        for item in self:
            category_code = (item.categ_id.parent_id.code + item.categ_id.code)
            if category_code:
                query = """SELECT get_next_product_code_number('"""+category_code+"""')"""
                item.env.cr.execute(query)
                item.default_code = item.env.cr.fetchone()[0]