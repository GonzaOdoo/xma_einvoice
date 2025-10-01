from odoo import fields, models


class ResCompany(models.Model):
    _inherit = 'res.company'
    
    def _localization_use_documents(self):
        self.ensure_one()
        return True

    matrix_server = fields.Char(
        string="Servidor de Matrix",
        help="este campo es para almacenar la informacion del Servidor de Matrix"
    )

    matrix_user = fields.Char(
        string="Usuario Matrix",
        help="este campo es para almacenar la informacion del Usuario Matrix"
    )

    matrix_password = fields.Char(
        string="Password de usuario Matrix",
        help="Campo que sirve para almacenar la contrasenia para poder enviar la informacion a Matrix"
    )

    matrix_room = fields.Char(
        string="ID de la sala de Matrix",
        help="ID de la sala de Matrix"
    )

    access_token = fields.Char(
        string="Access Token",
    )

    uuid_client = fields.Char(
        string="UUID client"
    )

    l10n_xma_type_pac = fields.Selection(
        [
            ('finkok', 'Finkok'),
            ('prodigia', 'Prodigia'),
            ('solu_fa', 'Solución Factible'),
        ], string="Pac de Facturación",
    )

    l10n_xma_test = fields.Boolean(
        string="Entorno de pruebas"
    )

    l10n_xma_economic_activity_campany_id = fields.One2many(
        'l10n_xma.economic_activity',
        'res_company'
    )
    start_date_post = fields.Date(
        string="Fecha de inicio de Timbrado"
    )

    l10n_xma_integration_code = fields.Char(
        string="Codigo de integracion"
    )

    l10n_xma_access_key = fields.Char(
        string="Clave de Acesso"
    )
    
    l10n_xma_odoo_sh_environment = fields.Boolean(
        string="Entorno Entreprise"
    )

    l10n_xma_address_type_code = fields.Char()



    l10n_xma_phrase_ids = fields.Many2many('l10n_xma.fel_phrase', string='Frases')
    xma_infile_user = fields.Char(string="Usuario Infile")
    xma_api_key = fields.Char(string="Llave API") 
    xma_token_signer = fields.Char(string="Llave Firma")
    xma_api_url = fields.Char(string='URL API', default='https://certificador.feel.com.gt/fel/procesounificado/transaccion/v2/xml')
    
    xma_br_partner_key = fields.Char()
    xma_br_signature_key = fields.Char()


    l10n_xma_use_discount_for_price = fields.Boolean(
        string="Usar descuento en precio",
        readonly=False
    )
