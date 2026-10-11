{
    'name': 'Hotel Management System',
    'version': '18.0.1.0.0',
    'category': 'hotel',
    'summary': 'Manage hotel operations',
    'author': 'Thura',
    'depends': ['base', 'mail'],

    'data': [
        'security/hotel_security.xml',
        'security/ir.model.access.csv',
        'data/ir_sequence_data.xml',
        'data/ir_sequence_bill.xml',
        'views/room_views.xml',
        'views/guest_views.xml',
        'views/booking_views.xml',
        'views/bill_views.xml',
        'views/service_views.xml',
        'views/housekeeping_views.xml',
        'views/rate_plan_views.xml',
        'views/menu.xml',
        'reports/reports.xml',
        'reports/bill_report_templates.xml',
    ],

    'installable': True,
    'application': True,
    'license': 'LGPL-3',
}
