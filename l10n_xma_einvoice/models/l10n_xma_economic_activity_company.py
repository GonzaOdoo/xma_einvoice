# -*- coding: utf-8 -*-
from odoo import fields, models


class L10nXmaEcoActComp(models.Model):
    _name = "l10n_xma.economic_activity_company"
    
    l10n_xma_economic_activity_id = fields.Many2one('l10n_xma.economic_activity')    
    company_id = fields.Many2one('res.company')    