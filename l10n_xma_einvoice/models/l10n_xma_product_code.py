# -*- coding: utf-8 -*-
from odoo import fields, models


class L10nXmaProductcode(models.Model):
    _name = "l10n_xma.productcode"
    _rec_names_search = ['code','name']


    active = fields.Boolean(default=True)
    sequence = fields.Integer(
        default=10,help='To set in which order show the documents type taking into account the most'
        ' commonly used first')
    country_id = fields.Many2one(
        'res.country', index=True, help='Country in which this document is valid')
    name = fields.Char(required=True, help='Use document name')
    code = fields.Char(help='Code used by different localizations')
    comments = fields.Char(
       string='comments'
    )
    date_since = fields.Date(
        string="Valido desde"
    )
    danger_material = fields.Char(
        string="Material Peligroso"
    )
    is_hazaudous_material = fields.Selection(
        [('si', "Si"),("noo", "No (opcional)"),("no", "No")],
        string="Es Material Peligroso"
    )

    countrys_ids = fields.Many2many(
        'res.country', index=True, help='Country in which this document is valid')
    
    type = fields.Selection(selection=[('P','Product'),('S','Service')])
    
    def name_get(self):
        # OVERRIDE 
        return [(tipo.id, "%s %s" % (tipo.code, tipo.name or '')) for tipo in self]