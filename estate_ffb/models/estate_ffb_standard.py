from openerp import models, fields
from datetime import datetime

class EstateFFBWeight(models.Model):
    """
    Master FFB Average. It record harvest labour activity.
    """
    _name = 'estate.ffb.weight'
    _description = 'Average Weight FFB'
    _inherit=['mail.thread']
    
    name = fields.Char("Name", required=True, store=True, default='New')
    date_start  = fields.Date("Start Date", default=fields.Date.context_today, required=True)
    date_end = fields.Date("End Date", default=fields.Date.context_today, required=True)
    yield_ids = fields.One2many('estate.ffb.yield', string='FFB Yield Average', 
                                inverse_name='ffb_weight_id')
    
    def current(self, date=datetime.today()):
        contract_ids = self.env['estate.ffb.weight'].search([('date_start', '<=', date)],
                                                      order='date_start desc')

        if len(contract_ids) > 0:
            return contract_ids[0]
        else:
            return None

class EstateFFBYield(models.Model):
    """
    Master FFB Average. It record harvest labour activity.
    """
    _name = 'estate.ffb.yield'
    _description = 'Average Weight FFB'
    _inherit=['mail.thread']
    
    ffb_weight_id = fields.Many2one('estate.ffb.weight', string='FFB Weight', ondelete='cascade')
    location_id = fields.Many2one('estate.block.template', 'Location', store=True)
    planted_year_id = fields.Many2one(related='location_id.planted_year_id', 
                                      string='Planted Year', store=True)
    qty_ffb_base_jjg = fields.Float('Qty FFB (Janjang)', track_visibility='onchange',
                                       help='Define quantity FFB Janjang', digits=(4,0))
    qty_ffb_base_kg = fields.Float('Qty FFB (Kg)', track_visibility='onchange',
                                       help='Define quantity FFB kg', digits=(4,0))
    rp_ffb_base_jjg = fields.Float('Rp/Janjang', track_visibility='onchange',
                                       help='Define quantity Rp per Janjang', digits=(4,0))
    rp_ffb_base_kg = fields.Float('Rp/Kg', track_visibility='onchange',
                                       help='Define quantity Rp per kg', digits=(4,0))

class EstateFFBActivity(models.Model):
    """
    Master FFB Activity. in order to set activity used in harvest.
    """
    _name = 'estate.ffb.activity'
    _description = 'Activity FFB'
    _inherit=['mail.thread']
    
    activity_type = fields.Selection([('panen_janjang', 'Panen Janjang'),
                              ('panen_brondolan', 'Panen Brondolan')], required=True)
    activity_id = fields.Many2one('estate.activity', 'Activity', 
                                  domain=[('type', '=', 'normal'),('activity_type', '=', 'harvest')],
                                  help='Any update will reset Block.', required=True)
    
# class EstateFFBPenalty(models.Model):
#     """
#     Master FFB Average. It record harvest labour activity.
#     """
#     _name = 'estate.ffb.penalty'
#     _description = 'Penalty FFB'
#     _inherit=['mail.thread']
#     
# class EstateFFBSeason(models.Model):
#     """
#     Master FFB Season. It record harvest labour activity.
#     """
#     _name = 'estate.ffb.season'
#     _description = 'Penalty FFB'
#     _inherit=['mail.thread']       