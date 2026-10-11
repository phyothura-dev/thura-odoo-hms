from odoo import api, fields, models


class HotelService(models.Model):
    _name = 'hotel.service'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = 'Hotel Extra Service & Product Catalog'
    _order = 'name'

    name = fields.Char(string='Service Name', required=True, tracking=True)

    currency_id = fields.Many2one(
        'res.currency',
        string='Currency',
        default=lambda self: self.env.company.currency_id
    )

    list_price = fields.Monetary(
        string='Price',
        currency_field='currency_id',
        default=0.0,
        required=True,
        tracking=True
    )

    active = fields.Boolean(string='Active', default=True)
    note = fields.Text(string='Description / Notes')
