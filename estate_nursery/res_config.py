from openerp.osv import fields, osv

class NurseryConfigSettings(osv.osv_memory):
    _inherit = 'estate.config.settings'

    _columns = {
        'nursery_stage': fields.selection([
            ('1', 'Single Stage'),
            ('2', 'Double Stage')], 'Default Nursery Stage',
            help="""Set Nursery Stage.""")
    }