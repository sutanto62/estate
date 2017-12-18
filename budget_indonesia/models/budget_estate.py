from openerp import models, fields, api
from openerp.tools import ustr
from openerp.exceptions import UserError
from openerp.tools import (drop_view_if_exists)

class InheritAccountAccount(models.Model):
    _inherit = 'account.account'

    budget_line_type = fields.Char('Budget Type',compute='_compute_budget_line_type')
    
    @api.multi
    def _compute_budget_line_type(self):
        for item in self:
            if '-Upah' in item.name:
                item.budget_line_type = 'amount_labour'
            elif '-Bahan' in item.name:
                item.budget_line_type = 'amount_material'
            elif '-Lain Lain' in item.name:
                item.budget_line_type = 'amount_other'
            else:
                item.budget_line_type = ''
                
class InheritAccountBudgetPost(models.Model):
    _inherit = 'account.budget.post'
    
    is_budget_estate = fields.Boolean('Budget Estate?')
    coa_account = fields.Many2one('account.account','Account')
    
    @api.multi
    def get_account_ids_labour(self):
        for item in self:
            code_coa_labour = item.coa_account.code[:-1]+'1'
            account_ids_labour = self.env['account.account'].search([('code','=',code_coa_labour)])
            return account_ids_labour
        
    @api.multi
    def get_account_ids_material(self):
        for item in self:
            code_coa_material = item.coa_account.code[:-1]+'2'
            account_ids_material = self.env['account.account'].search([('code','=',code_coa_material)])
            return account_ids_material
        
    @api.multi
    def get_account_ids_other(self):
        for item in self:
            code_coa_other = item.coa_account.code[:-1]+'3'
            account_ids_other = self.env['account.account'].search([('code','=',code_coa_other)])
            return account_ids_other
    
class InheritBudgetLine(models.Model):
    _inherit = 'crossovered.budget.lines'
    
    budget_line_type = fields.Selection([
                                            ('unit','QTY'),
                                            ('amount_labour','LABOUR'),
                                            ('amount_material','MATERIAL'),
                                            ('amount_other','OTHER')
                                            ]
                                        )
    varian_amount = fields.Float('Varian Amount', compute='_compute_varian_amount')
    account_name = fields.Char('Account Name', compute='_compute_account_name')
    account_code = fields.Char('Account Code', compute='_compute_account_code')
    
    @api.multi
    def _compute_account_name(self):
        for item in self:
            item.account_name = item.general_budget_id.coa_account.name
            
    @api.multi
    def _compute_account_code(self):
        for item in self:
            item.account_code = item.general_budget_id.coa_account.code
    
    @api.multi
    def _compute_varian_amount(self):
        for item in self:
            item.varian_amount = item.planned_amount - item.practical_amount
        
    def _prac_amt(self, cr, uid, ids, context=None):
        res = {}
        if context is None:
            context = {}
        for line in self.browse(cr, uid, ids, context=context):
            date_to = context.get('wizard_date_to') or line.date_to
            date_from = context.get('wizard_date_from') or line.date_from
            
            if line.general_budget_id.is_budget_estate: 
                if line.budget_line_type == 'amount_labour':
                    acc_labour_ids = [x.id for x in line.general_budget_id.get_account_ids_labour()]
                    if not acc_labour_ids:
                        raise UserError(_("The Budget '%s' has no accounts!") % ustr(line.general_budget_id.name))
                    if line.analytic_account_id.id:
                        cr.execute("SELECT SUM(amount) FROM account_analytic_line WHERE account_id=%s AND (date "
                               "between to_date(%s,'yyyy-mm-dd') AND to_date(%s,'yyyy-mm-dd')) AND "
                               "general_account_id=ANY(%s)", (line.analytic_account_id.id, date_from, date_to,acc_labour_ids,))
                        result = cr.fetchone()[0]
                        if result is None:
                            result = 0.0
                    else:
                        result = 0.0
                elif line.budget_line_type == 'amount_material':
                    acc_material_ids = [x.id for x in line.general_budget_id.get_account_ids_material()]
                    if not acc_material_ids:
                        raise UserError(_("The Budget '%s' has no accounts!") % ustr(line.general_budget_id.name))
                    if line.analytic_account_id.id:
                        cr.execute("SELECT SUM(amount) FROM account_analytic_line WHERE account_id=%s AND (date "
                               "between to_date(%s,'yyyy-mm-dd') AND to_date(%s,'yyyy-mm-dd')) AND "
                               "general_account_id=ANY(%s)", (line.analytic_account_id.id, date_from, date_to,acc_material_ids,))
                        result = cr.fetchone()[0]
                        if result is None:
                            result = 0.0
                    else:
                        result = 0.0
                elif line.budget_line_type == 'amount_other':
                    acc_other_ids = [x.id for x in line.general_budget_id.get_account_ids_other()]
                    if not acc_other_ids:
                        raise UserError(_("The Budget '%s' has no accounts!") % ustr(line.general_budget_id.name))
                    if line.analytic_account_id.id:
                        cr.execute("SELECT SUM(amount) FROM account_analytic_line WHERE account_id=%s AND (date "
                               "between to_date(%s,'yyyy-mm-dd') AND to_date(%s,'yyyy-mm-dd')) AND "
                               "general_account_id=ANY(%s)", (line.analytic_account_id.id, date_from, date_to,acc_other_ids,))
                        result = cr.fetchone()[0]
                        if result is None:
                            result = 0.0
                    else:
                        result = 0.0
                elif line.budget_line_type == 'unit':
                    acc_labour_ids = [x.id for x in line.general_budget_id.get_account_ids_labour()]
                    if not acc_labour_ids:
                        raise UserError(_("The Budget '%s' has no accounts!") % ustr(line.general_budget_id.name))
                    if line.analytic_account_id.id:
                        cr.execute("SELECT SUM(unit_amount) FROM account_analytic_line WHERE account_id=%s AND (date "
                               "between to_date(%s,'yyyy-mm-dd') AND to_date(%s,'yyyy-mm-dd')) AND "
                               "general_account_id=ANY(%s)", (line.analytic_account_id.id, date_from, date_to,acc_labour_ids,))
                        result = cr.fetchone()[0]
                        if result is None:
                            result = 0.0
                    else:
                        result = 0.0
            else:
                acc_ids = [x.id for x in line.general_budget_id.account_ids]
                if not acc_ids:
                    raise UserError(_("The Budget '%s' has no accounts!") % ustr(line.general_budget_id.name))
                if line.budget_line_type != 'unit':
                    if line.analytic_account_id.id:
                        cr.execute("SELECT SUM(amount) FROM account_analytic_line WHERE account_id=%s AND (date "
                               "between to_date(%s,'yyyy-mm-dd') AND to_date(%s,'yyyy-mm-dd')) AND "
                               "general_account_id=ANY(%s)", (line.analytic_account_id.id, date_from, date_to,acc_ids,))
                        result = cr.fetchone()[0]
                        if result is None:
                            result = 0.0
                    else:
                        result = 0.0
                else:
                    if line.analytic_account_id.id:
                        cr.execute("SELECT SUM(unit_amount) FROM account_analytic_line WHERE account_id=%s AND (date "
                               "between to_date(%s,'yyyy-mm-dd') AND to_date(%s,'yyyy-mm-dd')) AND "
                               "general_account_id=ANY(%s)", (line.analytic_account_id.id, date_from, date_to,acc_ids,))
                        result = cr.fetchone()[0]
                        if result is None:
                            result = 0.0
                    else:
                        result = 0.0
            
            res[line.id] = result
        return res

class InheritBudgeteryPosition(models.Model):
    _inherit = 'crossovered.budget'
    
    is_budget_estate = fields.Boolean('Budget Estate?')
    analytic_account_id = fields.Many2one('account.analytic.account', 'Analytic Account', domain=[('account_type', '=', 'normal')])
    crossovered_budget_line_qty = fields.One2many('crossovered.budget.lines', 'crossovered_budget_id', 'Budget Lines', domain=[('budget_line_type', '=', 'unit')], states={'done':[('readonly',True)]}, copy=True)
    crossovered_budget_line_manpower = fields.One2many('crossovered.budget.lines', 'crossovered_budget_id', 'Budget Lines', domain=[('budget_line_type', '=', 'amount_labour')], states={'done':[('readonly',True)]}, copy=True)
    crossovered_budget_line_material = fields.One2many('crossovered.budget.lines', 'crossovered_budget_id', 'Budget Lines', domain=[('budget_line_type', '=', 'amount_material')], states={'done':[('readonly',True)]}, copy=True)
    crossovered_budget_line_other = fields.One2many('crossovered.budget.lines', 'crossovered_budget_id', 'Budget Lines', domain=[('budget_line_type', '=', 'amount_other')], states={'done':[('readonly',True)]}, copy=True)
    is_parent_budget = fields.Boolean('Budget Parent?')
    parent_budget = fields.Many2one('crossovered.budget', 'Budget Parent')

class BudgetLinesPivot(models.Model):
    _name = 'v.budget.lines.pivot'
    _description = 'Budget Lines Pivot'
    _auto = False

    crossovered_budget_id = fields.Many2one("crossovered.budget","Budget")
    analytic_account_id = fields.Many2one("account.analytic.account","Analytic Account")
    general_budget_id = fields.Many2one("account.budget.post","Budgetery Position")
    budget_year = fields.Integer("Budget Year Value")
    budget_year_str = fields.Char("Budget Year")
    budget_date_from = fields.Date("Budget Start Date")
    date_from = fields.Date("Start Date")
    date_to = fields.Date("End Date")
    qty = fields.Float("Planned Qty")
    tenaga = fields.Float("Planned Tenaga")
    material = fields.Float("Planned Material")
    lain = fields.Float("Planned Lain-lain")
    act_qty = fields.Float("Actual Qty")
    act_tenaga = fields.Float("Actual Tenaga")
    act_material = fields.Float("Actual Material")
    act_lain = fields.Float("Actual Lain-lain")
    var_qty = fields.Float("Varian Qty")
    var_tenaga = fields.Float("Varian Tenaga")
    var_material = fields.Float("Varian Material")
    var_lain = fields.Float("Varian Lain-lain")
    total_money_planned = fields.Float("Planned Total Rupiah")
    total_money_actual = fields.Float("Actual Total Rupiah")
    money_per_ha_planned = fields.Float("Planned Rupiah/Ha")
    money_per_ha_actual = fields.Float("Actual Rupiah/Ha")
    achievement_percentage_qty = fields.Char("% Achievement Qty")
    achievement_percentage_tenaga = fields.Char("% Achievement Tenaga")
    achievement_percentage_material = fields.Char("% Achievement Material")
    achievement_percentage_lain = fields.Char("% Achievement Lain lain")
    
#     def init(self, cr):
#         drop_view_if_exists(cr, 'v_budget_lines_pivot')
#         cr.execute("""
#                     create or replace view v_budget_lines_pivot
#                     as
#                     select 
#                             row_number() over() id,
#                             cb.analytic_account_id,
#                             date_part('year', cb.date_from) as budget_year,
#                             ''||date_part('year', cb.date_from) as budget_year_str,
#                             cb.date_from as budget_date_from,
#                             cbl.crossovered_budget_id,
#                             cbl.general_budget_id,
#                             cbl.date_from,
#                             cbl.date_to,
#                             cbl.qty,
#                             round((cbl.tenaga/1000000)::numeric,2) tenaga,
#                             round((cbl.material/1000000)::numeric,2) material,
#                             round((cbl.lain/1000000)::numeric,2) lain,
#                             cbl.act_qty,
#                             round((cbl.act_tenaga/1000000)::numeric,2) act_tenaga,
#                             round((cbl.act_material/1000000)::numeric,2) act_material,
#                             round((cbl.act_lain/1000000)::numeric,2) act_lain,
#                             cbl.var_qty,
#                             round((cbl.var_tenaga/1000000)::numeric,2) var_tenaga,
#                             round((cbl.var_material/1000000)::numeric,2) var_material,
#                             round((cbl.var_lain/1000000)::numeric,2) var_lain,
#                             round(((cbl.tenaga + cbl.material + cbl.lain)/1000000)::numeric,2) total_money_planned, 
#                             round(((cbl.act_tenaga + cbl.act_material + cbl.act_lain)/1000000)::numeric,2) total_money_actual,
#                             round(((case when cbl.qty = 0  then 0 else (cbl.tenaga + cbl.material + cbl.lain)/cbl.qty end)/1000000)::numeric,2) money_per_ha_planned,
#                             round(((case when cbl.act_qty = 0  then 0 else (cbl.act_tenaga + cbl.act_material + cbl.act_lain)/cbl.act_qty end)/1000000)::numeric,2) money_per_ha_actual,
#                             case when cbl.qty = 0 or cbl.act_qty = 0 then 0.0 else to_char((cbl.act_qty/cbl.qty)*100,'FM999999999.00')::float end achievement_percentage_qty,
#                             case when cbl.tenaga = 0 or cbl.act_tenaga = 0.0 then 0 else to_char((cbl.act_tenaga/cbl.tenaga)*100,'FM999999999.00')::float end achievement_percentage_tenaga,
#                             case when cbl.material = 0 or cbl.act_material = 0.0 then 0 else to_char((cbl.act_material/cbl.material)*100,'FM999999999.00')::float end achievement_percentage_material,
#                             case when cbl.lain = 0 or cbl.act_lain = 0.0 then 0 else to_char((cbl.act_lain/cbl.lain)*100,'FM999999999.00')::float end achievement_percentage_lain
#                         from 
#                         (
#                         SELECT 
#                             v_budget_lines.crossovered_budget_id,
#                             v_budget_lines.general_budget_id,
#                             v_budget_lines.date_from,
#                             v_budget_lines.date_to,
#                             sum(
#                                 CASE
#                                     WHEN ((v_budget_lines.budget_line_type)::text = 'unit'::text) THEN v_budget_lines.planned_amount
#                                     ELSE (0)::numeric
#                                 END) AS qty,
#                             sum(
#                                 CASE
#                                     WHEN ((v_budget_lines.budget_line_type)::text = 'amount_labour'::text) THEN v_budget_lines.planned_amount
#                                     ELSE (0)::numeric
#                                 END) AS tenaga,
#                             sum(
#                                 CASE
#                                     WHEN ((v_budget_lines.budget_line_type)::text = 'amount_material'::text) THEN v_budget_lines.planned_amount
#                                     ELSE (0)::numeric
#                                 END) AS material,
#                             sum(
#                                 CASE
#                                     WHEN ((v_budget_lines.budget_line_type)::text = 'amount_other'::text) THEN v_budget_lines.planned_amount
#                                     ELSE (0)::numeric
#                                 END) AS lain,
#                              sum(
#                                 CASE
#                                     WHEN ((v_budget_lines.budget_line_type)::text = 'unit'::text) THEN v_budget_lines.actual_amount
#                                     ELSE (0)::numeric
#                                 END) AS act_qty,
#                             sum(
#                                 CASE
#                                     WHEN ((v_budget_lines.budget_line_type)::text = 'amount_labour'::text) THEN v_budget_lines.actual_amount
#                                     ELSE (0)::numeric
#                                 END) AS act_tenaga,
#                             sum(
#                                 CASE
#                                     WHEN ((v_budget_lines.budget_line_type)::text = 'amount_material'::text) THEN v_budget_lines.actual_amount
#                                     ELSE (0)::numeric
#                                 END) AS act_material,
#                             sum(
#                                 CASE
#                                     WHEN ((v_budget_lines.budget_line_type)::text = 'amount_other'::text) THEN v_budget_lines.actual_amount
#                                     ELSE (0)::numeric
#                                 END) AS act_lain,
#                              sum(
#                                 CASE
#                                     WHEN ((v_budget_lines.budget_line_type)::text = 'unit'::text) THEN v_budget_lines.varian_amount
#                                     ELSE (0)::numeric
#                                 END) AS var_qty,
#                             sum(
#                                 CASE
#                                     WHEN ((v_budget_lines.budget_line_type)::text = 'amount_labour'::text) THEN v_budget_lines.varian_amount
#                                     ELSE (0)::numeric
#                                 END) AS var_tenaga,
#                             sum(
#                                 CASE
#                                     WHEN ((v_budget_lines.budget_line_type)::text = 'amount_material'::text) THEN v_budget_lines.varian_amount
#                                     ELSE (0)::numeric
#                                 END) AS var_material,
#                             sum(
#                                 CASE
#                                     WHEN ((v_budget_lines.budget_line_type)::text = 'amount_other'::text) THEN v_budget_lines.varian_amount
#                                     ELSE (0)::numeric
#                                 END) AS var_lain
#                            FROM (
#                                   select 
#                                         budget_line.crossovered_budget_id,
#                                         budget_line.budget_line_type,
#                                         budget_line.general_budget_id,
#                                         budget_line.date_from,
#                                         budget_line.date_to,
#                                         budget_line.planned_amount,
#                                         (case when budget_line.actual_amount is null then 0.0 else budget_line.actual_amount end) actual_amount,
#                                         budget_line.planned_amount - (case when budget_line.actual_amount is null then 0.0 else budget_line.actual_amount end) varian_amount
#                                   from (
#                                       select 
#                                         cbl.budget_line_type,
#                                         cbl.crossovered_budget_id,
#                                         cbl.general_budget_id,
#                                         cbl.planned_amount,
#                                         cbl.date_from,
#                                         cbl.date_to,
#                                         (
#                                             SELECT 
#                                                 case when cbl.budget_line_type = 'unit' then
#                                                     SUM(unit_amount) 
#                                                 else
#                                                     SUM(amount)
#                                                 end
#                                             FROM 
#                                                 account_analytic_line 
#                                             WHERE 
#                                                 account_id=cbl.analytic_account_id 
#                                                 AND (date between cbl.date_from AND cbl.date_to) 
#                                                 AND general_account_id in (
#                                                     select account_id from account_budget_rel where budget_id = cbl.general_budget_id 
#                                                 )
#                                         ) actual_amount
#                                     from 
#                                         crossovered_budget_lines cbl
#                                 )budget_line    
#                              )as v_budget_lines
#                         GROUP BY 
#                             v_budget_lines.crossovered_budget_id,
#                             v_budget_lines.general_budget_id,
#                             v_budget_lines.date_from,
#                             v_budget_lines.date_to
#                         ) cbl inner join crossovered_budget cb
#                         on cbl.crossovered_budget_id = cb.id;
#                    """)
    
    def init(self, cr):
        drop_view_if_exists(cr, 'v_budget_lines_pivot')
        cr.execute("""
                    create or replace view v_budget_lines_pivot
                    as
                        with date_range_budget as (
                            select 
                                row_number() over(order by date_from) rownum, 
                                date_from, 
                                date_to 
                            from 
                                crossovered_budget_lines 
                            group by 
                                date_from, date_to
                        )
                        select 
                            row_number() over() id,
                            cb.analytic_account_id,
                            date_part('year', cb.date_from) as budget_year,
                            ''||date_part('year', cb.date_from) as budget_year_str,
                            cb.date_from as budget_date_from,
                            cbl.crossovered_budget_id,
                            cbl.general_budget_id,
                            cbl.date_from,
                            cbl.date_to,
                            cbl.qty,
                            round((cbl.tenaga/1000000)::numeric,2) tenaga,
                            round((cbl.material/1000000)::numeric,2) material,
                            round((cbl.lain/1000000)::numeric,2) lain,
                            cbl.act_qty,
                            round((cbl.act_tenaga/1000000)::numeric,2) act_tenaga,
                            round((cbl.act_material/1000000)::numeric,2) act_material,
                            round((cbl.act_lain/1000000)::numeric,2) act_lain,
                            cbl.var_qty,
                            round((cbl.var_tenaga/1000000)::numeric,2) var_tenaga,
                            round((cbl.var_material/1000000)::numeric,2) var_material,
                            round((cbl.var_lain/1000000)::numeric,2) var_lain,
                            round(((cbl.tenaga + cbl.material + cbl.lain)/1000000)::numeric,2) total_money_planned, 
                            round(((cbl.act_tenaga + cbl.act_material + cbl.act_lain)/1000000)::numeric,2) total_money_actual,
                            round(((case when cbl.qty = 0  then 0 else (cbl.tenaga + cbl.material + cbl.lain)/cbl.qty end)/1000000)::numeric,2) money_per_ha_planned,
                            round(((case when cbl.act_qty = 0  then 0 else (cbl.act_tenaga + cbl.act_material + cbl.act_lain)/cbl.act_qty end)/1000000)::numeric,2) money_per_ha_actual,
                            case when cbl.qty = 0 or cbl.act_qty = 0 then 0.0 else to_char((cbl.act_qty/cbl.qty)*100,'FM999999999.00')::float end achievement_percentage_qty,
                            case when cbl.tenaga = 0 or cbl.act_tenaga = 0.0 then 0 else to_char((cbl.act_tenaga/cbl.tenaga)*100,'FM999999999.00')::float end achievement_percentage_tenaga,
                            case when cbl.material = 0 or cbl.act_material = 0.0 then 0 else to_char((cbl.act_material/cbl.material)*100,'FM999999999.00')::float end achievement_percentage_material,
                            case when cbl.lain = 0 or cbl.act_lain = 0.0 then 0 else to_char((cbl.act_lain/cbl.lain)*100,'FM999999999.00')::float end achievement_percentage_lain
                        from 
                        (
                        SELECT 
                            v_budget_lines.crossovered_budget_id,
                            v_budget_lines.general_budget_id,
                            v_budget_lines.date_from,
                            v_budget_lines.date_to,
                            sum(
                                CASE
                                    WHEN ((v_budget_lines.budget_line_type)::text = 'unit'::text) THEN v_budget_lines.planned_amount
                                    ELSE (0)::numeric
                                END) AS qty,
                            sum(
                                CASE
                                    WHEN ((v_budget_lines.budget_line_type)::text = 'amount_labour'::text) THEN v_budget_lines.planned_amount
                                    ELSE (0)::numeric
                                END) AS tenaga,
                            sum(
                                CASE
                                    WHEN ((v_budget_lines.budget_line_type)::text = 'amount_material'::text) THEN v_budget_lines.planned_amount
                                    ELSE (0)::numeric
                                END) AS material,
                            sum(
                                CASE
                                    WHEN ((v_budget_lines.budget_line_type)::text = 'amount_other'::text) THEN v_budget_lines.planned_amount
                                    ELSE (0)::numeric
                                END) AS lain,
                             sum(
                                CASE
                                    WHEN ((v_budget_lines.budget_line_type)::text = 'unit'::text) THEN v_budget_lines.actual_amount
                                    ELSE (0)::numeric
                                END) AS act_qty,
                            sum(
                                CASE
                                    WHEN ((v_budget_lines.budget_line_type)::text = 'amount_labour'::text) THEN v_budget_lines.actual_amount
                                    ELSE (0)::numeric
                                END) AS act_tenaga,
                            sum(
                                CASE
                                    WHEN ((v_budget_lines.budget_line_type)::text = 'amount_material'::text) THEN v_budget_lines.actual_amount
                                    ELSE (0)::numeric
                                END) AS act_material,
                            sum(
                                CASE
                                    WHEN ((v_budget_lines.budget_line_type)::text = 'amount_other'::text) THEN v_budget_lines.actual_amount
                                    ELSE (0)::numeric
                                END) AS act_lain,
                             sum(
                                CASE
                                    WHEN ((v_budget_lines.budget_line_type)::text = 'unit'::text) THEN v_budget_lines.varian_amount
                                    ELSE (0)::numeric
                                END) AS var_qty,
                            sum(
                                CASE
                                    WHEN ((v_budget_lines.budget_line_type)::text = 'amount_labour'::text) THEN v_budget_lines.varian_amount
                                    ELSE (0)::numeric
                                END) AS var_tenaga,
                            sum(
                                CASE
                                    WHEN ((v_budget_lines.budget_line_type)::text = 'amount_material'::text) THEN v_budget_lines.varian_amount
                                    ELSE (0)::numeric
                                END) AS var_material,
                            sum(
                                CASE
                                    WHEN ((v_budget_lines.budget_line_type)::text = 'amount_other'::text) THEN v_budget_lines.varian_amount
                                    ELSE (0)::numeric
                                END) AS var_lain
                           FROM (
                                   select 
                                    cbl.crossovered_budget_id,
                                    cbl.analytic_account_id, 
                                    cbl.general_budget_id, 
                                    cbl.date_from, 
                                    cbl.date_to, 
                                    cbl.budget_line_type,
                                    cbl.planned_amount,
                                    (case when cbl.budget_line_type = 'unit' then
                                        coalesce(aal.unit_amount,0.0) 
                                    else
                                        coalesce(aal.amount,0.0)*-1
                                    end) actual_amount,
                                    cbl.planned_amount - (case when cbl.budget_line_type = 'unit' then
                                        coalesce(aal.unit_amount,0.0) 
                                    else
                                        coalesce(aal.amount,0.0)*-1
                                    end) varian_amount
                                from
                                    (
                                        select 
                                            cbl.crossovered_budget_id,
                                            cbl.analytic_account_id, 
                                            cbl.general_budget_id, 
                                            cbl.date_from, 
                                            cbl.date_to, 
                                            cbl.budget_line_type,
                                            cbl.planned_amount,
                                            dbr.rownum
                                        from 
                                            crossovered_budget_lines cbl inner join date_range_budget dbr
                                            on cbl.date_from = dbr.date_from and cbl.date_to = dbr.date_to
                                    )cbl left join
                                    (
                                        select 
                                            account_id,
                                            rownum,
                                            budget_id,
                                            SUM(unit_amount) unit_amount,     
                                            SUM(amount)*1 amount 
                                        from 
                                            (
                                            select 
                                                aal.account_id,
                                                aal.general_account_id,
                                                aal.date,
                                                aal.unit_amount,
                                                aal.amount,
                                                abr.budget_id
                                            from 
                                                account_analytic_line aal full outer join
                                                account_budget_rel abr
                                                on aal.general_account_id = abr.account_id
                                                where abr.budget_id is not null
                                            )aal left join date_range_budget drb
                                            on aal.date between drb.date_from and drb.date_to
                                        group by
                                            account_id,
                                            rownum,
                                            budget_id
                                    )aal
                                    on 
                                        cbl.analytic_account_id = aal.account_id and
                                        cbl.general_budget_id = aal.budget_id and
                                        cbl.rownum = aal.rownum
                             )as v_budget_lines
                        GROUP BY 
                            v_budget_lines.crossovered_budget_id,
                            v_budget_lines.general_budget_id,
                            v_budget_lines.date_from,
                            v_budget_lines.date_to
                        ) cbl inner join crossovered_budget cb
                        on cbl.crossovered_budget_id = cb.id;
                   """)
    
    @api.multi
    def open_form_budget(self):
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'crossovered.budget',
            'view_mode': 'form',
            'res_id': self.general_budget_id.id,
            'target' : 'new',
        }