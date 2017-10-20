# -*- coding: utf-8 -*-

from openerp import models, api, fields, _
from datetime import datetime
from openerp.exceptions import UserError, ValidationError
from openerp.tools import DEFAULT_SERVER_DATE_FORMAT as DF


class Rainfall(models.Model):
    _name = 'estate_rainfall.rainfall'
    _description = 'Rainfall'
    _order = 'date desc, date_year asc, date_month asc, block_id asc, time_start asc'

    def _default_date(self):
        today = datetime.today().strftime(DF)
        return today

    name = fields.Char('Name', compute='_compute_name', store=True)
    date = fields.Date('Date', default=_default_date, required=True,
                       help='Date used to define next upkeep activity on that day.')
    date_month = fields.Integer('Date Month', compute='_compute_month', store=True,
                             help='Help to compare rainfall by month.')
    date_year = fields.Integer('Date Year', compute='_compute_year', store=True,
                            help='Help to compare rainfall by month.')
    # day = fields.Integer('Rainfall Day', default=0, compute='_compute_day', store=True, group_operator="sum",
    day = fields.Float('Rainfall Day', default=0, group_operator="sum",
                         help='Morning observation, minimum 1 minute duration and 1 mm volume.\n' \
                              'Evening observation, minimum 1 minute duration and 1 mm volume. Change morning observation to 0.')
    duration = fields.Float('Duration (minutes)', default=0.0, compute='_compute_duration', store=True,
                            help='1 minute rainfall duration required to set 1 rainfall day.')
    observation = fields.Selection([('morning', 'Morning'),
                                    ('evening', 'Evening')], 'Observation Period',
                                   help='Use time start and end to defined observation period')
    period = fields.Selection([('day', 'Daily'),
                               ('week', 'Weekly'),
                               ('month', 'Monthly')], default='day',
                              help='Period of observation. It use to set rainfall data weekly or monthly.')
    time_start = fields.Float('Time Start', required=True,
                              help='Define observation period for time start based configuration.')
    time_end = fields.Float('Time End', required=True,
                            help='Define observation period for time end based configuration.')
    volume = fields.Float('Volume (mm)', default=0, required=True, group_operator="sum",
                            help='1 mm rainfall volume required to set 1 rainfall day.')
    block_id = fields.Many2one('estate.block.template', 'Block Location',
                               domain=[('estate_location', '=', True)],
                               help='Define observation location')

    @api.one
    @api.depends('date')
    def _compute_name(self):
        self.name = self.date

    @api.model
    def _morning_day(self, rainfall):
        """ Cannot update morning observation while creating evening one."""
        morning_rainfall_id = self.env['estate_rainfall.rainfall'].browse(rainfall)
        res = morning_rainfall_id.write({'day': 0})
        return res

    @api.one
    @api.depends('date')
    def _compute_month(self):
        date = datetime.strptime(self.date, DF)
        res = date.month
        self.date_month = res
        return res

    @api.one
    @api.depends('date')
    def _compute_year(self):
        date = datetime.strptime(self.date, DF)
        res = date.year
        self.date_year = res
        return res

    @api.depends('time_start', 'time_end')
    def _compute_duration(self):
        """ Get duration between start and end. Record saved in float."""
        for record in self:
            if record.time_end > record.time_start:
                res = record.time_end - record.time_start
            else:
                res = record.time_start - record.time_end
            record.duration = res
        return res

    @api.one
    def _compute_day(self):
        if self.volume > 0 and self.duration > 0.0:
            self.day = 1
        return True

    @api.constrains('volume')
    def _check_volume(self):
        if self.volume == 0:
            err_msg = _('You should update rainfall volume.')
            raise ValidationError(err_msg)

    @api.constrains('time_start', 'time_end')
    def _check_time(self):
        if (not 0.0 <= self.time_start <= 24.0) or (not 0.0 <= self.time_end <= 24.0):
            err_msg = _('Use 24:00 time value.')
            raise ValidationError(err_msg)

    @api.onchange('time_start', 'time_end')
    def _onchange_time(self):
        """ Automatically define observation based on time start and end"""

        observation = ['morning', 'evening']
        res = ''

        # Observation method depends on configuration
        # TODO use self._config()
        config_id = self.env['estate.config.settings'].search([], order='id desc', limit=1)
        start = config_id.default_time_start
        end = config_id.default_time_end
        overnight = config_id.default_time_overnight
        observation_method = config_id.default_observation_method


        # define single hour to decide morning/evening
        hour = 0.0
        if observation_method == 'start':
            hour = self.time_start
        elif observation_method == 'end':
            hour = self.time_end

        if overnight:
            if end <= hour < start:
                res = observation[1]
            else:
                res = observation[0]
        else:
            if start <= hour < end:
                res = observation[1]
            else:
                res = observation[0]

        self.observation = res

        return res

    @api.one
    @api.onchange('volume')
    def _onchange_volume(self):
        if self.volume > 0 and self.duration > 0.0:
            self.day = 1
        return True


    @api.model
    def read_group(self, domain, fields, groupby, offset=0, limit=None, orderby=False, lazy=True):
        """ Update aggregate number"""

        obj = self.env['estate_rainfall.rainfall']

        if 'time_start' in fields:
            fields.remove('time_start')

        if 'time_end' in fields:
            fields.remove('time_end')

        res = super(Rainfall, self).read_group(domain, fields, groupby, offset=offset, limit=limit, orderby=orderby, lazy=lazy)

        # show average per month at total
        if 'date:year' in groupby and 'date_month' not in groupby:
            year_domain = res[0].get('__domain', domain)
            month_ids = list(set(obj.search(year_domain, order='date_month asc').mapped('date_month')))

            year_res = []

            for month in month_ids:
                domain_month = []
                domain_month.append(('date_month', '=', month))
                domain_month.extend(year_domain)

                monthly_rainfall_ids = obj.search(domain_month)

                monthly_volume = sum(r.volume for r in monthly_rainfall_ids)
                monthly_day = sum(r.day for r in monthly_rainfall_ids)

                # count 1 for empty location
                undefined_location = 1 if monthly_rainfall_ids.filtered(lambda r: not r.block_id) else 0

                monthly_location = len(set(monthly_rainfall_ids.mapped('block_id'))) + undefined_location

                month_res = {
                    'month': month,
                    'day': monthly_day/float(monthly_location),
                    'volume': monthly_volume/float(monthly_location)
                }

                year_res.append(month_res)

            res[0]['day'] = sum(r['day'] for r in year_res)
            res[0]['volume'] = sum(r['volume'] for r in year_res)

        # show average per month (not sum)
        if 'date_month' in groupby:
            for line in res:
                rainfall_ids = obj.search(line.get('__domain', domain))

                total_volume = sum(r.volume for r in rainfall_ids)
                total_day = sum(r.day for r in rainfall_ids)

                # count 1 for empty location
                undefined_location = 1 if rainfall_ids.filtered(lambda r: not r.block_id) else 0

                total_location = len(rainfall_ids.mapped('block_id')) + undefined_location

                print 'read_group: average/month have %s location' % rainfall_ids

                line['day'] = total_day/float(total_location)
                line['volume'] = total_volume/float(total_location)

                print ' read_group %s ' % line


        return res

    @api.model
    def create(self, vals):
        """ Limit single morning/evening observation data in a day."""

        rainfall_obj = self.env['estate_rainfall.rainfall']

        domain = [('date', '=', vals['date'])]

        # support multi location
        if vals.has_key('block_id'):
            domain.append(('block_id', '=', vals['block_id']))

        rainfall_ids = rainfall_obj.search(domain)

        if vals['observation'] in rainfall_ids.mapped('observation'):
            err_msg = _('There are %s observation at %s already.') % (vals['observation'], vals['date'])
            raise ValidationError(err_msg)
        else:
            if 'morning' in rainfall_ids.mapped('observation'):
                self._morning_day(rainfall_ids[0].id)
            res = super(Rainfall, self).create(vals)

        return res

    @api.multi
    def write(self, vals):
        """ Update record did not check duplicate observation."""
        # odoo edit mode only include modified field in vals
        vals['date'] = self.date

        domain = [('id', 'not in', self.ids), ('date', '=', vals['date'])]

        # support multi location
        if self.block_id:
            domain.append(('block_id', '=', self.block_id.id))

        # check duplicate observation in a single day
        if vals.has_key('observation'):
            rainfall_obj = self.env['estate_rainfall.rainfall']
            rainfall_ids = rainfall_obj.search(domain)

            if vals['observation'] in rainfall_ids.mapped('observation'):
                err_msg = _('There are %s observation at %s already.') % (vals['observation'], vals['date'])
                raise ValidationError(err_msg)

        res = super(Rainfall, self).write(vals)

        return res

    @api.model
    def _config(self):
        # Observation method depends on configuration
        config_id = self.env['estate.config.settings'].search([], order='id desc', limit=1)
        start = config_id.default_time_start
        end = config_id.default_time_end
        overnight = config_id.default_time_overnight
        method = config_id.default_observation_method
        res = {
            'start': start,
            'end': end,
            'overnight': overnight,
            'method': method
        }

        if not res:
            raise ValueError('No rainfall configuration.')

        return res