# -*- coding: utf-8 -*-

from odoo import models, fields, api, _

class HotelHousekeepingTask(models.Model):
    _name = 'hotel.housekeeping.task'
    _description = 'Hotel Housekeeping Task'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'scheduled_date desc, priority desc, id desc'

    name = fields.Char(string='Task Reference', required=True, copy=False, default=lambda self: _('New'))
    room_id = fields.Many2one('hotel.room', string='Room', required=True, tracking=True)
    assigned_to_id = fields.Many2one('res.users', string='Assigned Housekeeper', tracking=True)

    cleaning_type = fields.Selection([
        ('routine', 'Routine Clean'),
        ('checkout', 'Checkout Deep Clean'),
        ('inspection', 'Inspection Only'),
        ('deep_clean', 'Deep Sanitization')
    ], string='Cleaning Type', default='checkout', required=True)

    priority = fields.Selection([
        ('0', 'Low'),
        ('1', 'Normal'),
        ('2', 'High'),
        ('3', 'Urgent')
    ], string='Priority', default='1')

    scheduled_date = fields.Date(string='Scheduled Date', default=fields.Date.context_today, required=True)
    completed_date = fields.Datetime(string='Completed Date', readonly=True)

    state = fields.Selection([
        ('draft', 'Draft'),
        ('in_progress', 'In Progress'),
        ('done', 'Completed'),
        ('cancelled', 'Cancelled')
    ], string='Status', default='draft', required=True, tracking=True)

    notes = fields.Text(string='Notes / Checklist')

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', _('New')) == _('New'):
                vals['name'] = self.env['ir.sequence'].next_by_code('hotel.housekeeping.task') or _('New')
        return super(HotelHousekeepingTask, self).create(vals_list)

    def action_start_cleaning(self):
        self.ensure_one()
        self.write({'state': 'in_progress'})
        if self.room_id:
            self.room_id.write({'housekeeping_status': 'cleaning'})

    def action_complete_cleaning(self):
        self.ensure_one()
        self.write({
            'state': 'done',
            'completed_date': fields.Datetime.now()
        })
        if self.room_id:
            self.room_id.write({'housekeeping_status': 'clean'})

    def action_cancel(self):
        self.ensure_one()
        self.write({'state': 'cancelled'})


class HotelMaintenanceRequest(models.Model):
    _name = 'hotel.maintenance.request'
    _description = 'Hotel Room Maintenance Request'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'request_date desc, priority desc, id desc'

    name = fields.Char(string='Maintenance Title', required=True, tracking=True)
    code = fields.Char(string='Request Code', required=True, copy=False, default=lambda self: _('New'))
    room_id = fields.Many2one('hotel.room', string='Room', required=True, tracking=True)
    reported_by_id = fields.Many2one('res.users', string='Reported By', default=lambda self: self.env.user)
    assigned_to_id = fields.Many2one('res.users', string='Technician / Staff', tracking=True)

    category = fields.Selection([
        ('ac', 'Air Conditioning & HVAC'),
        ('plumbing', 'Plumbing & Water'),
        ('electrical', 'Electrical & Lighting'),
        ('furniture', 'Furniture & Fixtures'),
        ('tv_internet', 'TV & Internet'),
        ('other', 'Other Issue')
    ], string='Issue Category', default='other', required=True)

    priority = fields.Selection([
        ('0', 'Low'),
        ('1', 'Normal'),
        ('2', 'High'),
        ('3', 'Urgent')
    ], string='Priority', default='1')

    request_date = fields.Date(string='Request Date', default=fields.Date.context_today, required=True)
    resolved_date = fields.Datetime(string='Resolved Date', readonly=True)

    state = fields.Selection([
        ('draft', 'Reported'),
        ('in_progress', 'Under Repair'),
        ('resolved', 'Resolved'),
        ('cancelled', 'Cancelled')
    ], string='Status', default='draft', required=True, tracking=True)

    description = fields.Text(string='Issue Description')

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('code', _('New')) == _('New'):
                vals['code'] = self.env['ir.sequence'].next_by_code('hotel.maintenance.request') or _('New')
        return super(HotelMaintenanceRequest, self).create(vals_list)

    def action_start_repair(self):
        self.ensure_one()
        self.write({'state': 'in_progress'})
        if self.room_id:
            self.room_id.write({'housekeeping_status': 'maintenance'})

    def action_resolve_repair(self):
        self.ensure_one()
        self.write({
            'state': 'resolved',
            'resolved_date': fields.Datetime.now()
        })
        if self.room_id:
            self.room_id.write({'housekeeping_status': 'dirty'})

    def action_cancel(self):
        self.ensure_one()
        self.write({'state': 'cancelled'})
