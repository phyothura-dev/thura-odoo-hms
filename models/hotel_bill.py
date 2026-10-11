from odoo import api, fields, models, _
from odoo.api import ondelete
from odoo.exceptions import ValidationError


class HotelBillLine(models.Model):
    _name = 'hotel.bill.line'
    _description = 'Hotel Bill Line Item'

    bill_id = fields.Many2one(
        'hotel.bill',
        string='Bill',
        required=True,
        ondelete='cascade',
    )

    service_id = fields.Many2one('hotel.service', string='Service')
    name = fields.Char(string='Description', required=True)

    quantity = fields.Float(string='Quantity', default=1.0)
    unit_price = fields.Monetary(
        string='Unit Price',
        currency_field='currency_id'
    )
    amount = fields.Monetary(
        string='Amount',
        currency_field='currency_id',
        compute='_compute_amount',
        store=True
    )
    currency_id = fields.Many2one(
        'res.currency',
        related='bill_id.currency_id',
        store=True,
        readonly=True
    )

    @api.onchange('service_id')
    def _onchange_service_id(self):
        if self.service_id:
            self.name = self.service_id.name
            self.unit_price = self.service_id.list_price

    @api.depends('quantity', 'unit_price')
    def _compute_amount(self):
        for line in self:
            line.amount = line.quantity * line.unit_price


class HotelBill(models.Model):
    _name = 'hotel.bill'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = 'Hotel Bill / Invoice'
    _order = 'id desc'

    name = fields.Char(
        string='Bill Reference',
        required=True,
        readonly=True,
        copy=False,
        default='New',
        tracking=True
    )

    booking_id = fields.Many2one(
        'hotel.booking',
        string='Booking',
        required=True,
        ondelete='restrict',
        tracking=True
    )

    # Related fields auto-filled from booking
    guest_id = fields.Many2one(
        'hotel.guest',
        related='booking_id.guest_id',
        string='Guest',
        store=True,
        readonly=True
    )
    room_id = fields.Many2one(
        'hotel.room',
        related='booking_id.room_id',
        string='Room',
        store=False,
        readonly=True
    )
    currency_id = fields.Many2one(
        'res.currency',
        related='booking_id.currency_id',
        string='Currency',
        store=True,
        readonly=True
    )

    bill_date = fields.Date(
        string='Bill Date',
        default=fields.Date.today,
        required=True,
        tracking=True
    )

    # Bill Line Items
    line_ids = fields.One2many(
        'hotel.bill.line',
        'bill_id',
        string='Charge Items'
    )

    # Computed Totals
    subtotal_amount = fields.Monetary(
        string='Subtotal',
        currency_field='currency_id',
        compute='_compute_totals',
        store=True
    )
    tax_percent = fields.Float(
        string='Tax (%)',
        default=0.0,
        tracking=True
    )
    tax_amount = fields.Monetary(
        string='Tax Amount',
        currency_field='currency_id',
        compute='_compute_totals',
        store=True
    )
    total_amount = fields.Monetary(
        string='Total Amount',
        currency_field='currency_id',
        compute='_compute_totals',
        store=True,
        tracking=True
    )

    # Payment Info
    state = fields.Selection([
        ('draft', 'Draft'),
        ('confirmed', 'Confirmed'),
        ('paid', 'Paid'),
        ('cancelled', 'Cancelled'),
    ], string='Status', default='draft', required=True, tracking=True)

    payment_method = fields.Selection([
        ('cash', 'Cash'),
        ('card', 'Credit / Debit Card'),
        ('bank_transfer', 'Bank Transfer'),
        ('other', 'Other'),
    ], string='Payment Method', tracking=True)

    payment_date = fields.Date(
        string='Payment Date',
        tracking=True
    )

    note = fields.Text(string='Notes')

    # ─────────────────────────────────────────
    # Sequence Auto-generation
    # ─────────────────────────────────────────

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', 'New') == 'New':
                vals['name'] = self.env['ir.sequence'].next_by_code('hotel.bill') or 'New'
        return super().create(vals_list)

    # ─────────────────────────────────────────
    # Computed Fields
    # ─────────────────────────────────────────

    @api.depends('line_ids.amount', 'tax_percent')
    def _compute_totals(self):
        for rec in self:
            subtotal = sum(line.amount for line in rec.line_ids)
            tax = subtotal * (rec.tax_percent / 100.0)
            rec.subtotal_amount = subtotal
            rec.tax_amount = tax
            rec.total_amount = subtotal + tax

    # ─────────────────────────────────────────
    # Workflow Actions
    # ─────────────────────────────────────────

    def action_confirm(self):
        for rec in self:
            if not rec.line_ids:
                raise ValidationError(_("Cannot confirm a bill with no charge items. Please add at least one line."))
            rec.state = 'confirmed'

    def action_register_payment(self):
        for rec in self:
            if not rec.payment_method:
                raise ValidationError(_("Please select a Payment Method before registering payment."))
            rec.payment_date = fields.Date.today()
            rec.state = 'paid'

    def action_reset_draft(self):
        for rec in self:
            if rec.state == 'cancelled':
                rec.state = 'draft'

    # ─────────────────────────────────────────
    # Constraints
    # ─────────────────────────────────────────

    @api.constrains('tax_percent')
    def _check_tax_percent(self):
        for rec in self:
            if rec.tax_percent < 0 or rec.tax_percent > 100:
                raise ValidationError(_("Tax percentage must be between 0 and 100."))
