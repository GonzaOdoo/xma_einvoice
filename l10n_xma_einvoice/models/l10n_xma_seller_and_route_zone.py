from odoo import fields, models, api, _

class L10nXmaSellerZone(models.Model):
    _name = 'l10n_xma.seller.zone'

    code = fields.Char(string='Código')
    name = fields.Char(string='Nombre')



class L10nXmaRouteZone(models.Model):
    _name = 'l10n_xma.route.zone'

    code = fields.Char(string='Código')
    name = fields.Char(string='Nombre')