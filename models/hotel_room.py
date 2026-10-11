from odoo import fields, models, api, _

class HotelRoom(models.Model):
    _name = 'hotel.room'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = 'Hotel Room'

    name = fields.Char(string="Room Name / Number", required=True, tracking=True)
    floor = fields.Integer(string="Floor", default=1, tracking=True)
    image = fields.Image(string="Room Image", max_width=1920, max_height=1920)

    room_type = fields.Selection([
        ("single", "Single"),
        ("double", "Double"),
        ("suite", "Suite"),
        ("premium", "Premium")
    ], string="Room Type", default="single", required=True, tracking=True)

    status = fields.Selection([
        ("available", "Available"),
        ("occupied", "Occupied"),
    ], default='available', required=True, string="Status", tracking=True)

    housekeeping_status = fields.Selection([
        ('clean', 'Cleaned & Inspected'),
        ('dirty', 'Needs Cleaning (Dirty)'),
        ('cleaning', 'Cleaning In Progress'),
        ('maintenance', 'Under Maintenance')
    ], string='Housekeeping Status', default='clean', required=True, tracking=True)

    # Currency field inherited from Odoo base module (res.currency)
    currency_id = fields.Many2one(
        'res.currency',
        string='Currency',
        default=lambda self: self.env.company.currency_id
    )

    price = fields.Monetary(string="Nightly Price", currency_field="currency_id", tracking=True)
    hourly_rate = fields.Monetary(string="Hourly Rate", currency_field="currency_id", tracking=True)
    min_hourly_hours = fields.Integer(string="Min. Hourly Duration (Hours)", default=2, help="Minimum booking hours required for hourly rental")

    housekeeping_task_ids = fields.One2many('hotel.housekeeping.task', 'room_id', string='Housekeeping Tasks')
    housekeeping_task_count = fields.Integer(string='Cleaning Tasks Count', compute='_compute_housekeeping_counts')

    maintenance_request_ids = fields.One2many('hotel.maintenance.request', 'room_id', string='Maintenance Requests')
    maintenance_request_count = fields.Integer(string='Maintenance Count', compute='_compute_housekeeping_counts')

    @api.depends('housekeeping_task_ids', 'maintenance_request_ids')
    def _compute_housekeeping_counts(self):
        for room in self:
            room.housekeeping_task_count = len(room.housekeeping_task_ids)
            room.maintenance_request_count = len(room.maintenance_request_ids)

    def action_set_available(self):
        for record in self:
            record.status = 'available'

    def action_set_occupied(self):
        for record in self:
            record.status = 'occupied'

    def action_mark_dirty(self):
        for record in self:
            record.housekeeping_status = 'dirty'

    def action_mark_clean(self):
        for record in self:
            record.housekeeping_status = 'clean'

    def action_view_housekeeping_tasks(self):
        self.ensure_one()
        return {
            'name': _('Housekeeping Tasks'),
            'type': 'ir.actions.act_window',
            'res_model': 'hotel.housekeeping.task',
            'view_mode': 'kanban,list,form',
            'domain': [('room_id', '=', self.id)],
            'context': {'default_room_id': self.id},
        }

    def action_view_maintenance_requests(self):
        self.ensure_one()
        return {
            'name': _('Maintenance Requests'),
            'type': 'ir.actions.act_window',
            'res_model': 'hotel.maintenance.request',
            'view_mode': 'kanban,list,form',
            'domain': [('room_id', '=', self.id)],
            'context': {'default_room_id': self.id},
        }
