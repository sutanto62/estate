from openerp import models, fields, api, _
from openerp.exceptions import ValidationError
from datetime import datetime

class InheritEstateUpkeepLabour(models.Model):
    
    _inherit = 'estate.upkeep.labour'
    
    @api.multi
    @api.constrains('quantity_piece_rate')
    def _onchange_piece_rate(self):
        """Piece rate should be:
        1. Labor should achieved standard work result/day.
        2. Piece rate is given if standard work result/day achieved.
        3. Not excedd variance of daily standard and activity quantity.
        4. Used to calculate PKWT Daily Target achievement (condition: no attendance, unclosed block)
        """
        self.ensure_one()
        
        if self.upkeep_id.is_harvest == True:
            return True
        
        base = self.activity_standard_base
        att_ratio = self.attendance_code_ratio
        quantity = self.quantity
        employee = self.employee_id.name
        activity = self.activity_id.name

        # validate labour quantity and piece rate to standard activity
        if self.quantity_piece_rate:
            standard_work_result = quantity - (base * att_ratio)

            if self.attendance_code_id.contract:
                return

            if standard_work_result < 0:
                error_msg = _("%s not allowed to have piece rate due to under achievement of %s" % (employee, activity))
                raise ValidationError(error_msg)
            elif self.quantity_piece_rate > standard_work_result:
                if self.activity_contract:
                    return
                error_msg = _("%s work at %s piece rate quantity should not exceed %s" % (employee, activity, standard_work_result))
                raise ValidationError(error_msg)
            
    @api.one
    @api.depends('quantity_piece_rate', 'activity_id', 'quantity', 'location_id', 'attendance_code_id')
    def _compute_wage_piece_rate(self):
        """"Piece rate applied only for PKWT labour (see view xml)
        """
        # Piece rate wage based on piece rate price unless it not defined.
        if self.upkeep_id.is_harvest == True:
            estate_ffb_weight_id = self.env['estate.ffb.weight'].current()
            estate_ffb_yield_obj = self.env['estate.ffb.yield']
            bjr = estate_ffb_yield_obj.search([
                                        ('ffb_weight_id', '=', estate_ffb_weight_id.id),
                                        ('location_id', '=', self.location_id.id)
                                        ])
            self.wage_piece_rate = self.quantity_piece_rate * bjr.rp_ffb_base_kg 
            return True
        
        unit_price = 0.00
        if self.activity_id.piece_rate_price:
            unit_price = self.activity_id.piece_rate_price
        else:
            unit_price = self.activity_id.standard_price

        # Piece rate as borongan
        if self.quantity_piece_rate and self.attendance_code_id.contract:
            self.wage_piece_rate = self.quantity_piece_rate * unit_price

        # Piece rate as bonus after standard quantity achieved
        if self.quantity_piece_rate and self.quantity > self.activity_id.qty_base:
            self.wage_piece_rate = self.quantity_piece_rate * unit_price

        # Piece rate as contract activity
        if self.quantity_piece_rate and self.activity_contract:
            self.wage_piece_rate = self.quantity_piece_rate * unit_price

class InheritEstateUpkeep(models.Model):
     
    _inherit = 'estate.upkeep'
    
    is_harvest = fields.Boolean('Harvest')
     
    @api.one
    @api.constrains('date')
    def _check_date(self):
        """Upkeep date should be limited. Didn't support different timezone
        Condition:
        1. Zero value of max entry day = today transaction should be entry today.
        2. Positive value of max entry day = allowed back/future dated transaction.
        """
         
        if self.is_harvest == True:
            return True
         
        if self.date:
            fmt = '%Y-%m-%d'
            d1 = datetime.strptime(self.date, fmt)
            d2 = datetime.strptime(fields.Date.today(), fmt)
            delta = (d2 - d1).days
            if self.max_day == 0 and abs(delta) > self.max_day:
                error_msg = _("Transaction date should be today")
                raise ValidationError(error_msg)
            elif self.max_day != 0 and abs(delta) > self.max_day:
                error_msg = _(
                    "Transaction date should not be less than/greater than or equal to %s day(s)" % self.max_day)
                raise ValidationError(error_msg)
            else:
                return True