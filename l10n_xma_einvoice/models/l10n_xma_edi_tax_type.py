# -*- coding: utf-8 -*-
from odoo import fields, models


class l10n_xma_edi_tax_type(models.Model):
    _name = "l10n_xma.tax_type"
    
    code = fields.Char()
    name = fields.Char()
    comments = fields.Text()
    country_id = fields.Many2one('res.country')
    
    def _get_name(self):
        name = super()._get_name()
        name = '[' + self.code + ']' + self.name
        return name

class l10n_xma_tax_factor_type(models.Model):
    _name = "l10n_xma.tax_factor_type"
    
    code = fields.Char()
    name = fields.Char()
    comments = fields.Text()
    country_id = fields.Many2one('res.country')

    # Field for PE Invoice 
    code_unece = fields.Char(string='Code Unece')

    def _get_name(self):
        name = super()._get_name()
        name = '[' + self.code + ']' + self.name
        return name