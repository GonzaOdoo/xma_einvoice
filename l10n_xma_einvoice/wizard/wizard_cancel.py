# -*- coding: utf-8 -*-
import logging
import re
from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
from MqttLibPy.client import MqttClient

_logger = logging.getLogger(__name__)


class WizardCancel(models.TransientModel):
    _name = 'wizard.cancel'
    _description = "Cancelacion"

    __check_cfdi_partner_name_re = re.compile(r'''([A-Z]|[a-z]|[0-9]|.| |Ñ|ñ|!|"|%|&|'|´|-|:|;|>|=|<|@|_|,|\{|\}|`|~|á|é|í|ó|ú|Á|É|Í|Ó|Ú|ü|Ü)''')


    @staticmethod
    def _get_string_cfdi_partner_name(text, size=100):
        """Replace from text received the characters that are not found in the
        regex. This regex is taken from SAT documentation
        https://goo.gl/C9sKH6
        text: Text to remove extra characters
        size: Cut the string in size len
        Ex. 'Product ABC (small size)' - 'Product ABC small size'
        This version adds the dot symbol as an allowed character.
        """
        if not text:
            return None
        for char in WizardCancel.__check_cfdi_partner_name_re.sub('', text):
            text = text.replace(char, ' ')
        return text.strip()[:size]

    def _get_default_account(self):
        if not self._context.get('active_model'):
            return
        orders = self.env['account.move'].browse(self._context['active_ids'])
        return orders and orders[0].id

    account_id = fields.Many2one('account.move', default=_get_default_account)

    name = fields.Char(related="account_id.name")

    l10n_xma_uuid_invoice = fields.Char(string="Folio Fiscal" , copy=False, related="account_id.l10n_xma_uuid_invoice")

    l10n_xma_uuid_related = fields.Char(string="Documento relacionado" , copy=False)

    l10n_xma_reason_cancellation = fields.Selection(
        selection=[
            ('01', "01 - Comprobantes emitidos con errores con relación."),
            ('02', "02 - Comprobante emitido con errores sin relación  "),
            ('03', "03 - No se llevó a cabo la operación"),
            ('04', "04 -Operación nominativa relacionada en la factura global"),
        ],
        string="Motivo de cancelacion",)
    
    def get_company(self):
        company_id = self.env['res.company'].sudo().search([("company_name", "!=", "")], limit=1)
        if not company_id:
            company_id = self.env['res.company'].search([], limit=1)
        _logger.info(company_id)
        return company_id

    def action_cancel(self):
        _logger.info('action_cancel')
        for rec in self:
            id = rec.account_id.id
            company = rec.get_company()
            xml_uuid = rec.l10n_xma_uuid_invoice
            rfcReceptor = rec._get_string_cfdi_partner_name(rec.account_id.partner_id.vat.replace('&', '&amp;').replace('"', '&quot;').replace('<', '&lt;').replace('>', '&gt;'), 254) 
            emisor = self._get_string_cfdi_partner_name(rec.account_id.company_id.vat.replace('&', '&amp;').replace('"', '&quot;').replace('<', '&lt;').replace('>', '&gt;'), 254)
            monto =  rec.account_id.amount_total
            motivo = rec.l10n_xma_reason_cancellation
            uuid_replace = rec.l10n_xma_uuid_related        

            # tu envias a este topico  prodigia_cancel y recibes por  prodigia_canceled
            uuid = company.company_name
            rfc = rec.account_id.partner_id.vat
            country = rec.account_id.partner_id.country_id.code.lower()
            _logger.info(f"uuid/{uuid}/rfc/{rfc}/country/{country}/prodigia_cancel")
            mqtt_client = MqttClient("api.xmarts.com", 1883, prefix=f"uuid/{uuid}/rfc/{rfc}/country/{country}/", encryption_key=company.key)
            xml_json = {
                    "from": uuid,
                    "data": {
                        'id': id,
                        'uuid': uuid,
                        'folio_fiscal': xml_uuid,
                        'rfc': rfc,
                        'rfcReceptor': rfcReceptor,
                        'emisor': emisor,
                        'monto': monto,
                        'motivo': motivo,
                        'uuid_replace': uuid_replace,
                    }
                }
            print(xml_json)
            mqtt_client.send_message_serialized(
                [xml_json],
                f"uuid/{uuid}/rfc/{rfc}/country/{country}/prodigia_cancel", 
                valid_json=True, 
                secure=True
            )
