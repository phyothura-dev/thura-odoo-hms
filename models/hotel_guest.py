from odoo import api, fields, models

class HotelGuest(models.Model):
    _name = 'hotel.guest'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = 'Hotel Guest Profile'

    name = fields.Char(string="Guest Name", required=True, tracking=True)
    phone = fields.Char(string="Phone Number", required=True, tracking=True)
    gender = fields.Selection([
        ('male', 'Male'),
        ('female', 'Female'),
        ('other', 'Other'),
    ], string="Gender", default='male')
    national_id = fields.Char(string="National ID / Passport No.", tracking=True)
    nationality = fields.Char(string="Nationality")
    vip_type = fields.Selection([
        ('normal', 'Normal'),
        ('vip', 'VIP'),
        ('corporate', 'Corporate'),
    ], string="Guest Status", default='normal', tracking=True)

    image = fields.Image(string="Photo", max_width=1920, max_height=1920)
    note = fields.Text(string="Notes / Special Preferences")

    # ─────────────────────────────────────────
    # Folio & Billing Aggregation
    # ─────────────────────────────────────────

    currency_id = fields.Many2one(
        'res.currency',
        string='Currency',
        default=lambda self: self.env.company.currency_id
    )
    bill_ids = fields.One2many('hotel.bill', 'guest_id', string='Bills / Folios')
    bill_count = fields.Integer(
        string='Bill Count',
        compute='_compute_bill_data'
    )
    total_spent = fields.Monetary(
        string='Total Spent',
        currency_field='currency_id',
        compute='_compute_bill_data'
    )

    @api.depends('bill_ids', 'bill_ids.state', 'bill_ids.total_amount')
    def _compute_bill_data(self):
        for rec in self:
            rec.bill_count = len(rec.bill_ids)
            rec.total_spent = sum(
                bill.total_amount for bill in rec.bill_ids if bill.state in ('confirmed', 'paid')
            )

    def action_view_bills(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Guest Folios',
            'res_model': 'hotel.bill',
            'view_mode': 'list,form',
            'domain': [('guest_id', '=', self.id)],
            'context': {'default_guest_id': self.id},
        }
