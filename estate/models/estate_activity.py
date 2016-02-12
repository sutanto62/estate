# -*- coding: utf-8 -*-

from openerp import models, fields, api, osv

class Activity(models.Model):
    _name = 'estate.activity'
    _parent_store = True
    _parent_name = 'parent_id'
    _order = 'sequence'
    _rec_name = 'complete_name' # alternate display record name

    name = fields.Char("Name", required=True, help="Create unique activity name.")
    complete_name = fields.Char("Complete Name", compute="_complete_name", store=True)
    code = fields.Char("Activity Code")
    type = fields.Selection([('view', "View"),
                             ('normal', "Normal")], "Type",
                            required=True,
                            help="Select View to create group of activities.")
    # todo move to estate_account module
    # activity_income_id = fields.Many2one('account.account', "Income Account",
    #                                     help="This account will be used for invoices to value sales.")
    # activity_expense_id = fields.Many2one('account.account', "Expense Account",
    #                                     help="This account will be used for invoices to value expenses")
    comment = fields.Text("Additional Information")
    sequence = fields.Integer("Sequence", help="Keep activity in order as plantation stages.") # todo set as parent_left at create
    parent_id = fields.Many2one('estate.activity', "Parent Category", ondelete='restrict')
    parent_left = fields.Integer("Parent Left",	index=True)
    parent_right = fields.Integer("Parent Right", index=True)
    child_ids = fields.One2many('estate.activity', 'parent_id', "Child Activities")

    @api.one
    @api.depends('name', 'parent_id')
    def _complete_name(self):
        """ Forms complete name of location from parent category to child category.
        """
        if self.parent_id:
            self.complete_name = self.parent_id.complete_name + ' / ' + self.name
        else:
            self.complete_name = self.name

        return True

class Operation(models.Model):
    """Record daily field operation
    """
    _name = 'estate.operation'

    state = fields.Selection([('0', 'Draft'),
                              ('1', 'Confirmed'),
                              ('2', 'Approved')],
                             "State")