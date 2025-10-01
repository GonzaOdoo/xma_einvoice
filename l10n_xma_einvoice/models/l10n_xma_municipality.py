# -*- coding: utf-8 -*-
from odoo import fields, models


class l10n_xmam_unicipality(models.Model):
    _name = "l10n_xma.municipality"
    
    code = fields.Char()
    name = fields.Char()
    comments = fields.Text()
    country_id = fields.Many2one('res.country')
    date_from = fields.Date(string="Valido desde")
    state_id = fields.Many2one(
        'res.country.state', 
        string="Estado"
    )