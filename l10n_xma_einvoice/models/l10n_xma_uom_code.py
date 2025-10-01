# -*- coding: utf-8 -*-
from odoo import fields, models


class L10nXmaUomcode(models.Model):
    _name = "l10n_xma.uomcode"
    
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
    date_since = fields.Date()