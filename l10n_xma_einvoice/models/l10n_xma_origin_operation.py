# -*- coding: utf-8 -*-
from odoo import fields, models


class l10n_xma_origin_operation(models.Model):
    _name = "l10n_xma.origin_operation"
    
    code = fields.Char()
    name = fields.Char()
    comments = fields.Text()
    country_id = fields.Many2one('res.country')
    active = fields.Boolean(default=True)
    