from odoo import fields, models, api


class ResConfigSettingsIapFirebase(models.TransientModel):
    _inherit = 'res.config.settings'

    matrix_server = fields.Char(
        string="Servidor",
        help="este campo es para almacenar la informacion del Servidor",
        related="company_id.matrix_server",
        readonly=False
    )

    matrix_user = fields.Char(
        string="Usuario",
        help="este campo es para almacenar la informacion del Usuario",
        related="company_id.matrix_user",
        readonly=False
    )

    matrix_password = fields.Char(
        string="Password de usuario",
        help="Campo que sirve para almacenar la contrasenia para poder enviar la informacion",
        related="company_id.matrix_password",
        readonly=False
    )

    matrix_room = fields.Char(
        string="ID de la sala",
        help="ID de la sala de",
        related="company_id.matrix_room",
        readonly=False
    )

    access_token = fields.Char(
        string="Access Token",
    )

    uuid_client = fields.Char(
        related='company_id.uuid_client',
        readonly=False
    )

    l10n_xma_type_pac = fields.Selection(
        [
            ('finkok', 'Finkok'),
            ('prodigia', 'Prodigia'),
            ('solu_fa', 'Solución Factible'),
        ], string="Pac de Facturación",
        related="company_id.l10n_xma_type_pac",
        readonly=False
    )
    
    l10n_xma_test = fields.Boolean(
        string="Entorno de pruebas",
        related="company_id.l10n_xma_test",
        readonly=False
    )
    l10n_xma_odoo_sh_environment = fields.Boolean(
        string="Entorno de pruebas",
        related="company_id.l10n_xma_odoo_sh_environment",
        readonly=False
    )
    
    l10n_xma_use_discount_for_price = fields.Boolean(
        string="Usar descuento en precio",
        related='company_id.l10n_xma_use_discount_for_price',
        readonly=False
    )