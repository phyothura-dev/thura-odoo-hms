import math
from datetime import timedelta
from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class HotelBooking(models.Model):
    _name = 'hotel.booking'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = 'Hotel Booking'
    _order = 'id desc'

    name = fields.Char(
        string='Booking Reference',
        required=True,
        readonly=True,
        copy=False,
        tracking=True
    )
    guest_id = fields.Many2one('hotel.guest', string='Guest', required=True, tracking=True)
    room_id = fields.Many2one('hotel.room', string='Room', required=True, tracking=True)

    booking_type = fields.Selection([
        ('nightly', 'Nightly / Daily'),
        ('hourly', 'Hourly'),
    ], string='Booking Type', default='nightly', required=True, tracking=True)

    checkin_date = fields.Datetime(
        string='Check-in Date & Time',
        required=True,
        default=fields.Datetime.now,
        tracking=True
    )
    checkout_date = fields.Datetime(
        string='Check-out Date & Time',
        required=True,
        default=lambda self: fields.Datetime.now() + timedelta(days=1),
        tracking=True
    )

    currency_id = fields.Many2one(
        'res.currency',
        related='room_id.currency_id',
        string='Currency',
        store=True,
        readonly=True
    )

    duration = fields.Float(
        string='Duration',
        compute='_compute_booking_pricing',
        store=True,
        help="Duration in Days (Nightly) or Hours (Hourly)"
    )

    rate_plan_id = fields.Many2one(
        'hotel.rate.plan',
        string='Applied Rate Plan',
        compute='_compute_booking_pricing',
        store=True,
        readonly=True,
        help="Highest priority rate plan automatically applied matching booking dates."
    )

    promo_code_id = fields.Many2one(
        'hotel.promo.code',
        string='Promo Code',
        tracking=True,
        help="Exclusive promo code discount (cannot be combined with Rate Plan)."
    )

    unit_price = fields.Monetary(
        string='Unit Price',
        currency_field='currency_id',
        compute='_compute_booking_pricing',
        store=True
    )

    discount_amount = fields.Monetary(
        string='Discount Amount',
        currency_field='currency_id',
        compute='_compute_booking_pricing',
        store=True
    )

    total_amount = fields.Monetary(
        string='Total Amount',
        currency_field='currency_id',
        compute='_compute_booking_pricing',
        store=True,
        tracking=True
    )

    state = fields.Selection([
        ('draft', 'Draft'),
        ('checked_in', 'Checked-In'),
        ('checked_out', 'Checked-Out'),
        ('cancelled', 'Cancelled'),
    ], string='Status', default='draft', required=True, tracking=True)

    is_overdue = fields.Boolean(
        string='Is Overdue',
        compute='_compute_is_overdue',
        search='_search_is_overdue'
    )

    note = fields.Text(string='Booking Notes')

    # ─────────────────────────────────────────
    # Billing Integration
    # ─────────────────────────────────────────

    bill_ids = fields.One2many('hotel.bill', 'booking_id', string='Bills')
    bill_count = fields.Integer(
        string='Bill Count',
        compute='_compute_bill_count'
    )

    @api.depends('bill_ids')
    def _compute_bill_count(self):
        for rec in self:
            rec.bill_count = len(rec.bill_ids)

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            vals['name'] = self.env['ir.sequence'].next_by_code('hotel.booking')

        return super().create(vals_list)

    @api.depends('booking_type', 'checkin_date', 'checkout_date', 'room_id', 'room_id.price', 'room_id.hourly_rate', 'promo_code_id')
    def _compute_booking_pricing(self):
        for rec in self:
            if not rec.checkin_date or not rec.checkout_date or rec.checkout_date <= rec.checkin_date:
                rec.duration = 0.0
                rec.unit_price = 0.0
                rec.discount_amount = 0.0
                rec.total_amount = 0.0
                rec.rate_plan_id = False
                continue

            diff_seconds = (rec.checkout_date - rec.checkin_date).total_seconds()

            if rec.booking_type == 'hourly':
                rec.duration = max(1.0, math.ceil(diff_seconds / 3600.0))
                base_price = rec.room_id.hourly_rate if rec.room_id else 0.0
            else:
                rec.duration = max(1.0, math.ceil(diff_seconds / 86400.0))
                base_price = rec.room_id.price if rec.room_id else 0.0

            # ─────────────────────────────────────────
            # Rule 1 & Rule 2: Single Priority Rate Plan OR Exclusive Promo Code
            # ─────────────────────────────────────────
            applied_rate_plan = False
            computed_unit_price = base_price
            discount = 0.0

            # EXCLUSIVE RULE: If Promo Code is selected, skip Rate Plan!
            if rec.promo_code_id:
                applied_rate_plan = False
                computed_unit_price = base_price
                subtotal = rec.duration * computed_unit_price

                # Check promo code validity
                promo = rec.promo_code_id
                today = fields.Date.context_today(rec)
                if promo.active and promo.valid_from <= today <= promo.valid_to:
                    if promo.discount_type == 'percentage':
                        discount = subtotal * (promo.discount_value / 100.0)
                    else:
                        discount = min(subtotal, promo.discount_value)
            else:
                # SINGLE RATE PLAN RULE: Search matching active rate plans & pick highest priority
                checkin_dt_date = rec.checkin_date.date()
                domain = [
                    ('active', '=', True),
                    ('date_start', '<=', checkin_dt_date),
                    ('date_end', '>=', checkin_dt_date),
                    '|',
                    ('applied_on', '=', 'all'),
                    '&',
                    ('applied_on', '=', 'room_type'),
                    ('room_type', '=', rec.room_id.room_type if rec.room_id else False)
                ]
                matching_plans = self.env['hotel.rate.plan'].search(domain, order='priority desc, id desc', limit=1)

                if matching_plans:
                    applied_rate_plan = matching_plans[0]
                    if applied_rate_plan.computation_type == 'fixed':
                        computed_unit_price = applied_rate_plan.amount
                    elif applied_rate_plan.computation_type == 'percentage_increase':
                        computed_unit_price = base_price * (1.0 + (applied_rate_plan.amount / 100.0))
                    elif applied_rate_plan.computation_type == 'percentage_discount':
                        computed_unit_price = base_price * (1.0 - (applied_rate_plan.amount / 100.0))

            rec.rate_plan_id = applied_rate_plan
            rec.unit_price = computed_unit_price
            rec.discount_amount = discount
            rec.total_amount = max(0.0, (rec.duration * computed_unit_price) - discount)

    @api.depends('state', 'checkout_date')
    def _compute_is_overdue(self):
        now = fields.Datetime.now()
        for rec in self:
            rec.is_overdue = (rec.state == 'checked_in' and rec.checkout_date and now > rec.checkout_date)

    def _search_is_overdue(self, operator, value):
        now = fields.Datetime.now()
        if (operator == '=' and value) or (operator == '!=' and not value):
            return [('state', '=', 'checked_in'), ('checkout_date', '<', now)]
        else:
            return ['|', ('state', '!=', 'checked_in'), ('checkout_date', '>=', now)]

    @api.constrains('checkin_date', 'checkout_date')
    def _check_dates(self):
        for rec in self:
            if rec.checkin_date and rec.checkout_date and rec.checkout_date <= rec.checkin_date:
                raise ValidationError(_("Check-out Date & Time must be strictly after Check-in Date & Time."))

    @api.constrains('booking_type', 'checkin_date', 'checkout_date', 'room_id')
    def _check_min_hourly_duration(self):
        for rec in self:
            if rec.booking_type == 'hourly' and rec.checkin_date and rec.checkout_date and rec.room_id:
                diff_hours = (rec.checkout_date - rec.checkin_date).total_seconds() / 3600.0
                if rec.room_id.min_hourly_hours and diff_hours < rec.room_id.min_hourly_hours:
                    raise ValidationError(_(
                        "Hourly booking for room '%s' requires a minimum duration of %s hours."
                    ) % (rec.room_id.name, rec.room_id.min_hourly_hours))

    def action_check_in(self):
        for rec in self:
            rec.state = 'checked_in'
            if rec.room_id and rec.room_id.status == 'available':
                rec.room_id.status = 'occupied'
            else:
                raise ValidationError(_("Cannot check in this room. This room was already occupied."))

    def action_check_out(self):
        for rec in self:
            rec.state = 'checked_out'
            if rec.room_id:
                rec.room_id.status = 'available'
                rec.room_id.housekeeping_status = 'dirty'
                self.env['hotel.housekeeping.task'].create({
                    'room_id': rec.room_id.id,
                    'cleaning_type': 'checkout',
                    'priority': '2',
                    'notes': _('Automatic checkout cleaning task for %s (Guest: %s)') % (rec.name, rec.guest_id.name),
                })

    # ─────────────────────────────────────────
    # Billing Actions
    # ─────────────────────────────────────────

    def action_create_bill(self):
        self.ensure_one()
        if self.bill_count > 0:
            return self.action_view_bills()

        # Track promo code usage if redeemed
        if self.promo_code_id:
            self.promo_code_id.sudo().write({'use_count': self.promo_code_id.use_count + 1})

        # Auto-populate room charge line from booking data
        bill = self.env['hotel.bill'].create({
            'booking_id': self.id,
            'line_ids': [(0, 0, {
                'name': 'Room Charge - %s (%s)' % (
                    self.room_id.name,
                    dict(self._fields['booking_type'].selection).get(self.booking_type, '')
                ),
                'quantity': self.duration,
                'unit_price': self.unit_price,
            })],
        })

        return {
            'type': 'ir.actions.act_window',
            'name': 'Hotel Bill',
            'res_model': 'hotel.bill',
            'res_id': bill.id,
            'view_mode': 'form',
            'target': 'current',
        }

    def action_view_bills(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Booking Bills',
            'res_model': 'hotel.bill',
            'view_mode': 'list,form',
            'domain': [('booking_id', '=', self.id)],
            'context': {'default_booking_id': self.id},
        }

    def action_cancel(self):
        for rec in self:
            rec.state = 'cancelled'
            if rec.room_id:
                rec.room_id.status = 'available'
