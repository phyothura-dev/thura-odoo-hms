# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError

class HotelRatePlan(models.Model):
    _name = 'hotel.rate.plan'
    _description = 'Hotel Seasonal & Dynamic Rate Plan'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'priority desc, id desc'

    name = fields.Char(string='Rate Plan Name', required=True, tracking=True)
    priority = fields.Integer(string='Priority Sequence', default=10, help="Higher priority rate plans take precedence when date ranges overlap.", tracking=True)

    date_start = fields.Date(string='Start Date', required=True, default=fields.Date.context_today, tracking=True)
    date_end = fields.Date(string='End Date', required=True, tracking=True)

    applied_on = fields.Selection([
        ('all', 'All Rooms'),
        ('room_type', 'Specific Room Type')
    ], string='Applies To', default='all', required=True, tracking=True)

    room_type = fields.Selection([
        ("single", "Single"),
        ("double", "Double"),
        ("suite", "Suite"),
        ("premium", "Premium")
    ], string="Room Type", help="Applies only if Applied On is set to Specific Room Type")

    computation_type = fields.Selection([
        ('fixed', 'Fixed Price Override'),
        ('percentage_increase', 'Percentage Increase (+)'),
        ('percentage_discount', 'Percentage Discount (-)')
    ], string='Price Computation', default='percentage_increase', required=True, tracking=True)

    amount = fields.Float(string='Adjustment Amount / Rate (%)', required=True, tracking=True, help="Fixed price in currency or percentage value (e.g. 20 for 20%)")

    active = fields.Boolean(string='Active', default=True, tracking=True)
    notes = fields.Text(string='Description / Conditions')

    @api.constrains('date_start', 'date_end')
    def _check_dates(self):
        for rec in self:
            if rec.date_start and rec.date_end and rec.date_end < rec.date_start:
                raise ValidationError(_("End Date must be on or after Start Date."))

    @api.constrains('computation_type', 'amount')
    def _check_amount(self):
        for rec in self:
            if rec.computation_type in ('percentage_increase', 'percentage_discount') and (rec.amount < 0 or rec.amount > 100):
                raise ValidationError(_("Percentage adjustment rate must be between 0% and 100%."))
            if rec.computation_type == 'fixed' and rec.amount < 0:
                raise ValidationError(_("Fixed price amount cannot be negative."))


class HotelPromoCode(models.Model):
    _name = 'hotel.promo.code'
    _description = 'Hotel Promo Code & Special Discount'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'id desc'

    name = fields.Char(string='Promotion Name', required=True, tracking=True)
    code = fields.Char(string='Promo Code', required=True, tracking=True)

    discount_type = fields.Selection([
        ('percentage', 'Percentage Discount (%)'),
        ('fixed_amount', 'Fixed Amount Discount')
    ], string='Discount Type', default='percentage', required=True, tracking=True)

    discount_value = fields.Float(string='Discount Value', required=True, tracking=True)

    valid_from = fields.Date(string='Valid From', required=True, default=fields.Date.context_today)
    valid_to = fields.Date(string='Valid To', required=True)

    max_uses = fields.Integer(string='Max Total Uses', default=100, help="Maximum number of times this promo code can be redeemed.")
    use_count = fields.Integer(string='Times Used', default=0, readonly=True)

    active = fields.Boolean(string='Active', default=True, tracking=True)
    notes = fields.Text(string='Terms & Conditions')

    @api.constrains('code')
    def _check_unique_code(self):
        for rec in self:
            if rec.code:
                rec.code = rec.code.upper().strip()
                duplicate = self.search([('code', '=', rec.code), ('id', '!=', rec.id)], limit=1)
                if duplicate:
                    raise ValidationError(_("Promo Code '%s' already exists! Please use a unique code.") % rec.code)

    @api.constrains('valid_from', 'valid_to')
    def _check_promo_dates(self):
        for rec in self:
            if rec.valid_from and rec.valid_to and rec.valid_to < rec.valid_from:
                raise ValidationError(_("Valid To date must be on or after Valid From date."))
