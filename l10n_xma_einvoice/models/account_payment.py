
import logging
from lxml.objectify import fromstring
from math import copysign
from odoo.tools import float_round
from odoo.tools.float_utils import float_repr
from odoo import fields, models, api, _, tools
from odoo.tools.float_utils import float_round, float_is_zero
from odoo.exceptions import UserError, ValidationError
from odoo.tools import DEFAULT_SERVER_TIME_FORMAT, DEFAULT_SERVER_DATETIME_FORMAT
import re
from collections import defaultdict
from datetime import datetime
import base64
from lxml import etree
import json
import time
from uuid import uuid4
from MqttLibPy.client import MqttClient
from MqttLibPy.serializer import Serializer

_logger = logging.getLogger(__name__)
EQUIVALENCIADR_PRECISION_DIGITS = 6
TAX_TYPE_CODE_XMA = {'ISR': '001', 'IVA': '002', 'IEPS': '003'}
XMA_CODE_TO_TAX_TYPE = {v: k for k, v in TAX_TYPE_CODE_XMA.items()}


url_xmarts = 'http://159.203.170.13:8069'  # rec.company_id.edi_url_bd
db_xmarts = 'server'  # rec.company_id.edi_name_bd
# url_xmarts = 'http://localhost:8014'  # rec.company_id.edi_url_bd
# db_xmarts = 'cfdi4_s2'  # rec.company_id.edi_name_bd

def create_list_html(array):
    if not array:
        return ''
    msg = ''
    for item in array:
        msg += '<li>' + item + '</li>'
    return '<ul>' + msg + '</ul>'


class SingnPayment(models.Model):
    _inherit = "account.payment"

    country_id = fields.Many2one(
        'res.country',
        related="company_id.country_id",
    )

    """FIELDS GUATEMALA"""
    l10n_xma_payment_item_ids = fields.One2many("l10n_xma.payment.item","payment_id")
    l10n_latam_document_type_id = fields.Many2one(
        'l10n_latam.document.type', string='Document Type', readonly=False, auto_join=True, index='btree_not_null', compute=False, store=True)
    l10n_xma_phrase_ids = fields.Many2many('l10n_xma.fel_phrase', string='Frases')
    l10n_xma_einvoice_serie = fields.Char(string="Serie DTE", copy=False)
    l10n_xma_einvoice_numero = fields.Char(string="Numero Autorizacion", copy=False)
    l10n_xma_einvoice_status = fields.Selection(string="Estado Factura", copy=False, selection=[("signed","Firmada"),("failed","Fallida"),("canceled","Cancelada")])
    l10n_xma_cancel_motive = fields.Char(string='Motivo Cancelacion', copy=False)
    """FIELDS GUATEMALA"""

    # -- Fields to Loca MX --

    l10n_xma_payment_cfdi = fields.Binary(
        string = 'Cfdi content', copy = False, readonly = True,
        help = 'The cfdi xml content encoded in base64.')
    l10n_xma_payment_cfdi_name = fields.Char(
        string = 'CFDI name',
        copy = False,
        readonly = True,
        help = 'The attachment name of the CFDI.')

    l10n_xma_payment_type_id = fields.Many2one(
        'l10n_xma.payment_type',
        string='Metodo de Pago'
    )

    l10n_xma_payment_form_id = fields.Many2one(
        'xma_payment.form',
        string="Forma de pago"
    )
    l10n_xma_uuid_invoice = fields.Char(
        string="Folio Fiscal" , copy=False
    )

    force_pue = fields.Boolean(
        string = 'Force PUE',
    )

    l10n_xma_use_document_id = fields.Many2one(
        'l10n_xma.use.document',
        string='Use Document'
    ) 

    l10n_xma_timbre = fields.Boolean(default=False, copy=False)
    

    l10n_xma_cadena_original = fields.Char(string="Cadena Original", copy=False)

    l10n_xma_uuid_invoice = fields.Char(string="Folio Fiscal" , copy=False)

    l10n_xma_post_time = fields.Datetime(string="Fecha de Timbrado", copy=False)

    # -- Fields to Loca MX --
    
    """METODOS GUATEMALA"""
    def button_send_json_gtm(self):
        for rec in self:
            # self.move_id.send_json_gtm(self.l10n_xma_payment_item_ids, payment=rec)
            if rec.l10n_xma_einvoice_status != 'signed':
                rec.move_id.send_json_gtm(rec.l10n_xma_payment_item_ids, payment=rec)
                time.sleep(1)
                # self.refresh_account_move_xma()
                return True
            else:
                raise ValidationError(_('Error de timbrado: Esta factura ya esta timbrada.'))
            
    def button_cancel_json_gtm(self):
        for rec in self:
            if not rec.l10n_xma_cancel_motive:
                raise ValidationError(_('Error de Cancelacion:\nDebe llenar primero el campo de motivo de cancelacion.'))
            if rec.l10n_xma_einvoice_status == 'signed':
                rec.move_id.cancel_json_gtm(payment=rec)
                time.sleep(1)
                # rec.refresh_account_move_xma()
                return True
            else:
                raise ValidationError(_('Error de Cancelacion:\nEsta factura no ha sido timbrada aun.'))
    """METODOS GUATEMALA"""

    # -- Metodos Loca MX --

    def l10n_xma_consulted_xml_view(self):
        self.l10n_xma_consulted_xml(self.l10n_xma_uuid_invoice, self.id, self.company_id.vat, self)

    def l10n_xma_consulted_xml(self, folio, id_registro, rfc, registro):
        xml_json = {
            'folio': folio,
            'id_factura': id_registro,
            'rfc': rfc
        }
        company = registro.get_company()
        uuid = company.company_name
        rfc = registro.company_id.partner_id.vat
        country = registro.company_id.partner_id.country_id.code.lower()
        _logger.info(f"uuid/{uuid}/rfc/{rfc}/country/{country}/consult")
        xml_json = {"from":uuid, "data":xml_json}
        mqtt_client = MqttClient("api.xmarts.com", 1883, prefix=f"uuid/{uuid}/rfc/{rfc}/country/{country}/", encryption_key=company.key)
        # xml_json = json.dumps(xml_json)
        print(xml_json)
        mqtt_client.send_message_serialized(
            [xml_json],
            f"uuid/{uuid}/rfc/{rfc}/country/{country}/consult", 
            valid_json=True, 
            secure=True
        )
    def _get_l10n_xma_signed_edi_document(self):
        return self.l10n_xma_payment_cfdi
    
    def l10n_mx_edi_decode_cfdi(self, cfdi_data=None):
        ''' Helper to extract relevant data from the CFDI to be used, for example, when printing the invoice.
        :param cfdi_data:   The optional cfdi data.
        :return:            A python dictionary.
        '''
        self.ensure_one()

        def get_node(cfdi_node, attribute, namespaces):
            if hasattr(cfdi_node, 'Complemento'):
                node = cfdi_node.Complemento.xpath(attribute, namespaces=namespaces)
                return node[0] if node else None
            else:
                return None

        def get_cadena(cfdi_node, template):
            if cfdi_node is None:
                return None
            cadena_root = etree.parse(tools.file_open(template))
            return str(etree.XSLT(cadena_root)(cfdi_node))

        def is_purchase_move(move):
            return move.move_type in move.get_purchase_types() \
                    or move.payment_id.reconciled_bill_ids

        # Find a signed cfdi.

        signed_edi = self._get_l10n_xma_signed_edi_document()

        if signed_edi:
            cfdi_data = base64.decodebytes(signed_edi)

        cfdi_node = fromstring(cfdi_data)
        emisor_node = cfdi_node.Emisor
        receptor_node = cfdi_node.Receptor


        tfd_node = get_node(
            cfdi_node,
            'tfd:TimbreFiscalDigital[1]',
            {'tfd': 'http://www.sat.gob.mx/TimbreFiscalDigital'},
        )

        vals = {
            'uuid': ({} if tfd_node is None else tfd_node).get('UUID'),
            'supplier_rfc': emisor_node.get('Rfc', emisor_node.get('rfc')),
            'customer_rfc': receptor_node.get('Rfc', receptor_node.get('rfc')),
            'amount_total': cfdi_node.get('Total', cfdi_node.get('total')),
            'cfdi_node': cfdi_node,
            'usage': receptor_node.get('UsoCFDI'),
            'payment_method': cfdi_node.get('formaDePago', cfdi_node.get('MetodoPago')), 
            'bank_account': cfdi_node.get('NumCtaPago'),
            'sello': cfdi_node.get('sello', cfdi_node.get('Sello', 'No identificado')),
            'sello_sat': tfd_node is not None and tfd_node.get('selloSAT', tfd_node.get('SelloSAT', 'No identificado')),
            'cadena': self.l10n_xma_cadena_original,
            'certificate_number': cfdi_node.get('noCertificado', cfdi_node.get('NoCertificado')),
            'certificate_sat_number': tfd_node is not None and tfd_node.get('NoCertificadoSAT'),
            'expedition': cfdi_node.get('LugarExpedicion'),
            'fiscal_regime': emisor_node.get('RegimenFiscal', ''),
            'emission_date_str': cfdi_node.get('fecha', cfdi_node.get('Fecha', '')).replace('T', ' '),
            'stamp_date': tfd_node is not None and tfd_node.get('FechaTimbrado', '').replace('T', ' '),
        }
        return vals
    def get_company(self):
        company_id = self.env['res.company'].sudo().search([("company_name", "!=", "")], limit=1)
        if not company_id:
            company_id = self.env['res.company'].search([], limit=1)

        return company_id

    def send_to_matrix_json(self):
        xml_json_mx = self.get_json_payment()
        payment_json = {
            "id":self.id,
            "uuid_client":self.company_id.uuid_client,
            "data":xml_json_mx,
            "rfc":self.company_id.vat,
            "prod": 'NO' if self.company_id.l10n_xma_test else 'SI',
            "type": 'P',
            "pac_invoice": self.company_id.l10n_xma_type_pac,
        }
        xml_json = {"MX_payment": payment_json}
        company = self.get_company()
        uuid = company.company_name
        rfc = self.company_id.partner_id.vat
        country = self.company_id.partner_id.country_id.code.lower()
        xml_json = {"from":uuid, "data":xml_json}
        _logger.info("company " + str(company.name) + " Company name " + str(company.company_name) + " KEY " + str(company.key))
        mqtt_client = MqttClient("api.xmarts.com", 1883, prefix=f"uuid/{uuid}/rfc/{rfc}/country/{country}/", encryption_key=company.key)
        print(xml_json)

        mqtt_client.send_message_serialized(
            [xml_json],
            f"uuid/{uuid}/rfc/{rfc}/country/{country}/stamp", 
            valid_json=True, 
            secure=True
        )
        count = 0
        while count <= 3:
            print(count)
            self.refresh_account_move_xma()
            time.sleep(1)
            print("Se Ejecuto!!!")
            count += 1
    
    def refresh_account_move_xma(self):
        return {
            'name': _("Pagos"),
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'res_model': 'account.payment',
            'domain': [('id', '=', self.id)],
            'target': 'current',
            'res_id': self.id,
        }


    @api.model
    def _l10n_mx_edi_xmarts_info(self):
        url = 'http://ws.facturacionmexico.com.mx/pac/?wsdl'
        return {
            'url': url,
            'multi': False,  # TODO: implement multi
            'username': 'EKU9003173C9' if self.company_id.edi_test_pac == True else self.company_id.edi_user_pac,
            'password': 'EKU9003173C9' if self.company_id.edi_test_pac == True else self.company_id.edi_pass_pac,
            'production': 'NO' if self.company_id.edi_test_pac == True else 'SI',
        }

    # def edi_cancel_cfdi(self):
    #     for rec in self:
    #         _logger.info("xma_log------------------------------edi_cancel_cfdi------------------------")
    #         if not rec.edi_cfdi_cancel_type_id:
    #             raise UserError("Es necesario establecer un motivo de cancelación.")
    #         try:
    #             user_data = rec._l10n_mx_edi_xmarts_info()
    #             url = url_xmarts
    #             db = db_xmarts
    #             username = rec.company_id.edi_user_bd  # user_xmarts
    #             password = rec.company_id.edi_passw_bd  # password_xmarts
    #             common = xmlrpc.client.ServerProxy(
    #                 '{}/xmlrpc/2/common'.format(url))
    #             uid = common.authenticate(db, username, password, {})
    #             models = xmlrpc.client.ServerProxy(
    #                 '{}/xmlrpc/2/object'.format(url))
    #             response = {}
    #             model_name = 'sign.account.move'
    #             json_data = {
    #                 'uuid': rec.edi_payment_cfdi_uuid.lower(),
    #                 'rfc': rec.company_id.vat,
    #                 'default_code': rec.edi_cfdi_cancel_type_id.default_code,
    #                 'replace_uuid': rec.edi_replace_uuid or '',
    #             }
    #             response = models.execute_kw(
    #                 db, uid, password, model_name, 'request_cancel_invoice', [False, json_data, user_data['username'], user_data['password'], user_data['production'], rec.edi_cfdi, 'F'])
    #             rec._edi_post_cancel_process(
    #                 response['cancelled'], response['code'], response['msg'])
    #         except Exception as err:
    #             _logger.info("xma_log except err: %s", err)
    #             rec.message_post(body=_(
    #                 """<p>La conexion falló.</p><p><ul>%s</ul></p>""" % err))

    #         self.edi_update_sat_status()
            # if self.edi_payment_sat_status in ['not_found', 'cancelled']:
            #     self.edi_payment_pac_status = 'cancelled'

    def _l10n_mx_xma_get_40_values(self, move):
        print("_l10n_mx_xma_get_40_values", move.name)
        customer = move.partner_id if move.partner_id.type == 'invoice' else move.partner_id.commercial_partner_id
        print(customer.name, customer.l10n_xma_taxpayer_type_id.code)
        vals = {
            'fiscal_regime': customer.l10n_xma_taxpayer_type_id.code,
            'tax_objected': move._l10n_xma_get_tax_objected()
        }
        if customer.country_code not in [False, 'MX'] and not vals['fiscal_regime']:
            vals['fiscal_regime'] = '616'
        print('111111111111111111111', vals)
        return vals
    def get_mx_current_datetime_payment(self):
        tz = 'America/Mexico_City' or 'UTC'
        return fields.Datetime.context_timestamp(
            self.with_context(tz=tz), self.l10n_xma_post_time)
    
    def _l10n_mx_xma_get_invoice_cfdi_values(self, invoice):
        print("=-------------------------_l10n_mx_xma_get_invoice_cfdi_values-------------------------------=", invoice)
        ''' Doesn't check if the config is correct so you need to call _l10n_mx_edi_check_config first.

        :param invoice:
        :return:
        ''' 
        cfdi_date = self.get_mx_current_datetime_payment()
        cfdi_date = cfdi_date.strftime('%Y-%m-%dT%H:%M:%S')
        print('JOTASON', cfdi_date)
        cfdi_values = {
            **invoice._prepare_edi_vals_to_export(),
            **self._l10n_xma_get_common_cfdi_values(invoice, invoice),
            'document_type': 'I' if invoice.move_type == 'out_invoice' else 'E',
            'currency_name': invoice.currency_id.name,
            'payment_method_code': (invoice.l10n_xma_payment_form.code or '').replace('NA', '99'),
            'payment_policy': invoice.l10n_xma_payment_form.name,
            'cfdi_date': cfdi_date,
            # 'l10n_mx_edi_external_trade_type': '01', # CFDI 4.0
        }
        cfdi_values.update(self._l10n_mx_xma_get_40_values(invoice))

        # ==== Invoice Values ====
        if invoice.currency_id.name == 'MXN':
            cfdi_values['currency_conversion_rate'] = None
        else:  # assumes that invoice.company_id.country_id.code == 'MX', as checked in '_is_required_for_invoice'
            cfdi_values['currency_conversion_rate'] = abs(invoice.amount_total_signed) / abs(invoice.amount_total) if invoice.amount_total else 1.0

        if invoice.partner_bank_id:
            digits = [s for s in invoice.partner_bank_id.acc_number if s.isdigit()]
            acc_4number = ''.join(digits)[-4:]
            cfdi_values['account_4num'] = acc_4number if len(acc_4number) == 4 else None
        else:
            cfdi_values['account_4num'] = None

        if cfdi_values['customer'].country_id.code  != 'MEX' and cfdi_values['customer_rfc'] not in ('XEXX010101000', 'XAXX010101000'):
            cfdi_values['customer_fiscal_residence'] = cfdi_values['customer'].country_id.code 
        else:
            cfdi_values['customer_fiscal_residence'] = None

        # ==== Tax details ====

        def get_tax_cfdi_name(tax_detail_vals):
            tags = set()
            for detail in tax_detail_vals['group_tax_details']:
                for tag in self.env['account.tax.repartition.line'].search([('id', '=', detail['tax_repartition_line'].id)]).tax_id:
                    tags.add(tag)
            tags = list(tags)
            if len(tags) == 1:
                return {'ISR': '001', 'IVA': '002', 'IEPS': '003'}.get(tags[0].l10n_xma_tax_type_id.name)
            elif tags.l10n_xma_tax_factor_type_id.code == 'Exento':
                return '002'
            else:
                return None

        def filter_void_tax_line(inv_line):
            return inv_line.discount != 100.0

        def filter_tax_transferred(base_line, tax_values):
            tax = tax_values['tax_repartition_line'].tax_id
            return tax.amount >= 0.0

        def filter_tax_withholding(base_line, tax_values):
            tax = tax_values['tax_repartition_line'].tax_id
            return tax.amount < 0.0

        tax_details_transferred = invoice._prepare_xma_tax_details(filter_to_apply=filter_tax_transferred, filter_invl_to_apply=filter_void_tax_line,  grouping_key_generator=None)
        for tax_detail_transferred in (list(tax_details_transferred['tax_details_per_record'].values())
                                       + [tax_details_transferred]):
            for tax_detail_vals in tax_detail_transferred['tax_details'].values():
                tax = tax_detail_vals['tax']
                if tax.l10n_xma_tax_factor_type_id.code == 'Tasa':
                    tax_detail_vals['tax_rate_transferred'] = tax.amount / 100.0
                elif tax.l10n_xma_tax_factor_type_id.code == 'Cuota':
                    tax_detail_vals['tax_rate_transferred'] = tax_detail_vals['tax_amount_currency'] / tax_detail_vals['base_amount_currency']
                else:
                    tax_detail_vals['tax_rate_transferred'] = None

        tax_details_withholding = invoice._prepare_xma_tax_details(filter_to_apply=filter_tax_withholding, filter_invl_to_apply=filter_void_tax_line,  grouping_key_generator=None)
        for tax_detail_withholding in (list(tax_details_withholding['tax_details_per_record'].values())
                                       + [tax_details_withholding]):
            for tax_detail_vals in tax_detail_withholding['tax_details'].values():
                tax = tax_detail_vals['tax']
                if tax.l10n_xma_tax_factor_type_id.code == 'Tasa':
                    tax_detail_vals['tax_rate_withholding'] = - tax.amount / 100.0
                elif tax.l10n_xma_tax_factor_type_id.code == 'Cuota':
                    tax_detail_vals['tax_rate_withholding'] = - tax_detail_vals['tax_amount_currency'] / tax_detail_vals['base_amount_currency']
                else:
                    tax_detail_vals['tax_rate_withholding'] = None

        cfdi_values.update({
            'get_tax_cfdi_name': get_tax_cfdi_name,
            'tax_details_transferred': tax_details_transferred,
            'tax_details_withholding': tax_details_withholding,
        })

        cfdi_values.update({
            'has_tax_details_transferred_no_exento': any(x['tax'].l10n_xma_tax_factor_type_id.code != 'Exento' for x in cfdi_values['tax_details_transferred']['tax_details'].values()),
            'has_tax_details_withholding_no_exento': any(x['tax'].l10n_xma_tax_factor_type_id.code != 'Exento' for x in cfdi_values['tax_details_withholding']['tax_details'].values()),
        })

        if not invoice._l10n_mx_edi_is_managing_invoice_negative_lines_allowed():
            return cfdi_values


        # ==== Distribute negative lines ====

        def is_discount_line(line):
            return line.price_subtotal < 0.0

        def is_candidate(discount_line, other_line):
            discount_taxes = discount_line.tax_ids.flatten_taxes_hierarchy()
            other_line_taxes = other_line.tax_ids.flatten_taxes_hierarchy()
            return set(discount_taxes.ids) == set(other_line_taxes.ids)

        def put_discount_on(cfdi_values, discount_vals, other_line_vals):
            discount_line = discount_vals['line']
            other_line = other_line_vals['line']

            # Update price_discount.

            remaining_discount = discount_vals['price_discount'] - discount_vals['price_subtotal_before_discount']
            remaining_price_subtotal = other_line_vals['price_subtotal_before_discount'] - other_line_vals['price_discount']
            discount_to_allow = min(remaining_discount, remaining_price_subtotal)

            other_line_vals['price_discount'] += discount_to_allow
            discount_vals['price_discount'] -= discount_to_allow

            # Update taxes.

            for tax_key in ('tax_details_transferred', 'tax_details_withholding'):
                discount_line_tax_details = cfdi_values[tax_key]['tax_details_per_record'][discount_line]['tax_details']
                other_line_tax_details = cfdi_values[tax_key]['tax_details_per_record'][other_line]['tax_details']
                for k, tax_values in discount_line_tax_details.items():
                    if discount_line.currency_id.is_zero(tax_values['base_amount_currency']):
                        continue

                    other_tax_values = other_line_tax_details[k]
                    tax_amount_to_allow = copysign(
                        min(abs(tax_values['tax_amount_currency']), abs(other_tax_values['tax_amount_currency'])),
                        other_tax_values['tax_amount_currency'],
                    )
                    other_tax_values['tax_amount_currency'] -= tax_amount_to_allow
                    tax_values['tax_amount_currency'] += tax_amount_to_allow
                    base_amount_to_allow = copysign(
                        min(abs(tax_values['base_amount_currency']), abs(other_tax_values['base_amount_currency'])),
                        other_tax_values['base_amount_currency'],
                    )
                    other_tax_values['base_amount_currency'] -= base_amount_to_allow
                    tax_values['base_amount_currency'] += base_amount_to_allow

            return discount_line.currency_id.is_zero(remaining_discount - discount_to_allow)

        for line_vals in cfdi_values['invoice_line_vals_list']:
            line = line_vals['line']

            if not is_discount_line(line):
                continue

            # Search for lines on which distribute the global discount.
            candidate_vals_list = [x for x in cfdi_values['invoice_line_vals_list']
                                   if not is_discount_line(x['line']) and is_candidate(line, x['line'])]

            # Put the discount on the biggest lines first.
            candidate_vals_list = sorted(candidate_vals_list, key=lambda x: x['line'].price_subtotal, reverse=True)
            for candidate_vals in candidate_vals_list:
                if put_discount_on(cfdi_values, line_vals, candidate_vals):
                    break

        # ==== Remove discount lines ====

        cfdi_values['invoice_line_vals_list'] = [x for x in cfdi_values['invoice_line_vals_list']
                                                 if not is_discount_line(x['line'])]

        # ==== Remove taxes for zero lines ====

        for line_vals in cfdi_values['invoice_line_vals_list']:
            line = line_vals['line']

            if line.currency_id.is_zero(line_vals['price_subtotal_before_discount'] - line_vals['price_discount']):
                for tax_key in ('tax_details_transferred', 'tax_details_withholding'):
                    cfdi_values[tax_key]['tax_details_per_record'].pop(line, None)

        # Recompute Totals since lines changed.
        cfdi_values.update({
            'total_price_subtotal_before_discount': sum(x['price_subtotal_before_discount'] for x in cfdi_values['invoice_line_vals_list']),
            'total_price_discount': sum(x['price_discount'] for x in cfdi_values['invoice_line_vals_list']),
        })

        return cfdi_values

    @api.model
    def _l10n_xma_get_serie_and_folio(self, move):
        name_numbers = list(re.finditer(r'\d+', move.name))
        serie_number = move.name[:name_numbers[-1].start()]
        folio_number = name_numbers[-1].group().lstrip('0')
        print(f"||||||||||||||||||| serie_number {serie_number}")
        print(f"||||||||||||||||||| folio_number {folio_number}")
        return {
            'serie_number': serie_number,
            'folio_number': folio_number,
        }

    def _l10n_xma_get_common_cfdi_values(self, move, invoice):
        ''' Generic values to generate a cfdi for a journal entry.
        :param move:    The account.move record to which generate the CFDI.
        :return:        A python dictionary.
        '''

        def _format_string_cfdi(text, size=100):
            """Replace from text received the characters that are not found in the
            regex. This regex is taken from SAT documentation
            https://goo.gl/C9sKH6
            text: Text to remove extra characters
            size: Cut the string in size len
            Ex. 'Product ABC (small size)' - 'Product ABC small size'"""
            if not text:
                return None
            text = text.replace('|', ' ')
            return text.strip()[:size]

        def _format_float_cfdi(amount, precision):
            if amount is None or amount is False:
                return None
            # Avoid things like -0.0, see: https://stackoverflow.com/a/11010869
            return '%.*f' % (precision, amount if not float_is_zero(amount, precision_digits=precision) else 0.0)

        company = invoice.company_id
        # certificate = company.l10n_mx_edi_certificate_ids.sudo()._get_valid_certificate()
        currency_precision = invoice.currency_id.l10n_xma_decimal_number

        customer = invoice.partner_id if invoice.partner_id.type == 'invoice' else invoice.partner_id.commercial_partner_id
        supplier = invoice.company_id.partner_id.commercial_partner_id

        if not customer:
            customer_rfc = False
        elif customer.country_id and customer.country_id.code != 'MX':
            customer_rfc = 'XEXX010101000'
        elif customer.vat:
            customer_rfc = customer.vat.strip()
        elif customer.country_id.code in (False, 'MX'):
            customer_rfc = 'XAXX010101000'
        else:
            customer_rfc = 'XEXX010101000'

        if invoice.l10n_xma_origin:
            origin_type, origin_uuids = invoice._l10n_xma_read_cfdi_origin(invoice.l10n_xma_origin)
        else:
            origin_type = None
            origin_uuids = []

        return {
            **self._l10n_xma_get_serie_and_folio(invoice),
            # 'certificate': certificate,
            # 'certificate_number': certificate.serial_number,
            # 'certificate_key': certificate.sudo()._get_data()[0].decode('utf-8'),
            'record': invoice,
            'supplier': supplier,
            'customer': customer,
            'customer_rfc': customer_rfc,
            'issued_address': invoice._get_l10n_xma_issued_address(),
            'currency_precision': currency_precision,
            'origin_type': origin_type,
            'origin_uuids': origin_uuids,
            'format_string': _format_string_cfdi,
            'format_float': _format_float_cfdi,
        }

    def _l10n_mx_xma_get_payment_cfdi_values(self, invoice_id, move):
        print(f"MOVES invoice_id, move {invoice_id, move}")
        def get_tax_cfdi_name(env, tax_detail_vals):
            tags = set()
            for detail in tax_detail_vals['group_tax_details']:
                for tag in env['account.tax.repartition.line'].search([('id', '=', detail['tax_repartition_line'].id)]).tax_id:
                    tags.add(tag)
            tags = list(tags)
            if len(tags) == 1:
                return {'ISR': '001', 'IVA': '002', 'IEPS': '003'}.get(tags[0].l10n_xma_tax_type_id.name)
            elif tags.l10n_xma_tax_factor_type_id.code == 'Exento':
                return '002'
            else:
                return None
        
        def divide_tax_details(env, invoice, tax_details, amount_paid):
            percentage_paid = amount_paid / invoice.amount_total
            precision = invoice.currency_id.decimal_places
            for detail in tax_details['tax_details'].values():
                tax = detail['tax']
                tax_amount = abs(tax.amount) / 100.0 if tax.amount_type != 'fixed' else abs(detail['tax_amount_currency'] / detail['base_amount_currency'])
                base_val_proportion = float_round(detail['base_amount_currency'] * percentage_paid, precision)
                tax_val_proportion = float_round(base_val_proportion * tax_amount, precision)
                detail.update({
                    'base_val_prop_amt_curr': base_val_proportion,
                    'tax_val_prop_amt_curr': tax_val_proportion if tax.l10n_xma_tax_factor_type_id.code != 'Exento' else False,
                    'tax_class': get_tax_cfdi_name(env, detail),
                    'tax_amount': tax_amount,
                })
            return tax_details

        if self.move_id == move:
            _liquidity_line, counterpart_lines, _writeoff_lines = self._seek_for_lines()
            currency = counterpart_lines.currency_id
            total_amount_currency = abs(sum(counterpart_lines.mapped('amount_currency')))
            total_amount = abs(sum(counterpart_lines.mapped('balance')))
        else:
            counterpart_vals = move.statement_line_id._prepare_move_line_default_vals()[1]
            currency = self.env['res.currency'].browse(counterpart_vals['currency_id'])
            total_amount_currency = abs(counterpart_vals['amount_currency'])
            total_amount = abs(counterpart_vals['debit'] - counterpart_vals['credit'])

        # === Decode the reconciliation to extract invoice data ===
        pay_rec_lines = move.line_ids.filtered(lambda line: line.account_type in ('asset_receivable', 'liability_payable'))
        exchange_move_x_invoice = {}
        reconciliation_vals = defaultdict(lambda: {
            'amount_currency': 0.0,
            'balance': 0.0,
            'exchange_balance': 0.0,
        })
        for match_field in ('credit', 'debit'):

            # Peek the partials linked to exchange difference first in order to separate them from the partials
            # linked to invoices.
            for partial in pay_rec_lines[f'matched_{match_field}_ids'].sorted(lambda x: not x.exchange_move_id):
                counterpart_move = partial[f'{match_field}_move_id'].move_id
                if counterpart_move.l10n_xma_cfdi_request:
                    # Invoice.

                    # Gather all exchange moves.
                    if partial.exchange_move_id:
                        exchange_move_x_invoice[partial.exchange_move_id] = counterpart_move

                    invoice_vals = reconciliation_vals[counterpart_move]
                    invoice_vals['amount_currency'] += partial[f'{match_field}_amount_currency']
                    invoice_vals['balance'] += partial.amount
                elif counterpart_move in exchange_move_x_invoice:
                    # Exchange difference.
                    invoice_vals = reconciliation_vals[exchange_move_x_invoice[counterpart_move]]
                    invoice_vals['exchange_balance'] += partial.amount

        # === Create the list of invoice data ===
        invoice_vals_list = []
        for invoice, invoice_vals in reconciliation_vals.items():

            # Compute 'number_of_payments' & add amounts from exchange difference.
            payment_ids = set()
            inv_pay_rec_lines = invoice.line_ids.filtered(lambda line: line.account_type in ('asset_receivable', 'liability_payable'))
            for field in ('debit', 'credit'):
                for partial in inv_pay_rec_lines[f'matched_{field}_ids']:
                    counterpart_move = partial[f'{field}_move_id'].move_id

                    if counterpart_move.payment_ids or counterpart_move.statement_line_id:
                        payment_ids.add(counterpart_move.id)
            number_of_payments = len(payment_ids)

            if invoice.currency_id == currency:
                # Same currency
                invoice_exchange_rate = None
            elif currency == move.company_currency_id:
                # Payment expressed in MXN but the invoice is expressed in another currency.
                # The payment has been reconciled using the currency of the invoice, not the MXN.
                # Then, we retrieve the rate from amounts gathered from the reconciliation using the balance of the
                # exchange difference line allowing to switch from the "invoice rate" to the "payment rate".
                invoice_exchange_rate = float_round(
                    invoice_vals['amount_currency'] / (invoice_vals['balance'] + invoice_vals['exchange_balance']),
                    precision_digits=EQUIVALENCIADR_PRECISION_DIGITS,
                    rounding_method='UP',
                )
            else:
                # Multi-currency
                invoice_exchange_rate = float_round(
                    invoice_vals['amount_currency'] / invoice_vals['balance'],
                    precision_digits=6,
                    rounding_method='UP',
                )

            print("# for CFDI 4.0", invoice_id.name)
            cfdi_values = self._l10n_mx_xma_get_invoice_cfdi_values(invoice)
            tax_details_transferred = divide_tax_details(self.env, invoice, cfdi_values['tax_details_transferred'],
                                                         invoice_vals['amount_currency'])
            tax_details_withholding = divide_tax_details(self.env, invoice, cfdi_values['tax_details_withholding'],
                                                         invoice_vals['amount_currency'])

            invoice_vals_list.append({
                'invoice': invoice,
                'exchange_rate': invoice_exchange_rate,
                'payment_policy': invoice.l10n_xma_payment_type_id.code,
                'number_of_payments': number_of_payments,
                'amount_paid': invoice_vals['amount_currency'],
                'amount_before_paid': invoice.amount_residual + invoice_vals['amount_currency'],
                'tax_details_transferred': tax_details_transferred,
                'tax_details_withholding': tax_details_withholding,
                'equivalenciadr_precision_digits': EQUIVALENCIADR_PRECISION_DIGITS,
                **self._l10n_xma_get_serie_and_folio(invoice),
            })

        if currency == move.company_currency_id:
            # Same currency
            payment_exchange_rate = None
        else:
            # Multi-currency
            payment_exchange_rate = float_round(
                total_amount / total_amount_currency,
                precision_digits=6,
                rounding_method='UP',
            )

        payment_method_code = move.l10n_xma_payment_form.code
        is_payment_code_emitter_ok = payment_method_code in ('02', '03', '04', '05', '06', '28', '29', '99')
        is_payment_code_receiver_ok = payment_method_code in ('02', '03', '04', '05', '28', '29', '99')
        is_payment_code_bank_ok = payment_method_code in ('02', '03', '04', '28', '29', '99')

        bank_accounts = move.partner_id.commercial_partner_id.bank_ids.filtered(lambda x: x.company_id.id in (False, move.company_id.id))

        partner_bank = bank_accounts[:1].bank_id
        if partner_bank.country and partner_bank.country.code != 'MX':
            partner_bank_vat = 'XEXX010101000'
        else:  # if no partner_bank (e.g. cash payment), partner_bank_vat is not set.
            partner_bank_vat = partner_bank.l10n_xma_vat

        payment_account_ord = re.sub(r'\s+', '', bank_accounts[:1].acc_number or '') or None
        payment_account_receiver = re.sub(r'\s+', '', move.journal_id.bank_account_id.acc_number or '') or None

        # CFDI 4.0: prepare the tax summaries
        rate_payment_curr_mxn_40 = payment_exchange_rate or 1
        mxn_currency = self.env["res.currency"].search([('name', '=', 'MXN')], limit=1)
        total_taxes_paid = {}
        total_taxes_withheld = {
            '001': {'amount_curr': 0.0, 'amount_mxn': 0.0},
            '002': {'amount_curr': 0.0, 'amount_mxn': 0.0},
            '003': {'amount_curr': 0.0, 'amount_mxn': 0.0},
            None: {'amount_curr': 0.0, 'amount_mxn': 0.0},
        }
        for inv_vals in invoice_vals_list:
            wht_detail = list(inv_vals['tax_details_withholding']['tax_details'].values())
            print('tax_details_withholding00000000000000000', wht_detail)
            trf_detail = list(inv_vals['tax_details_transferred']['tax_details'].values())
            print("tax_details_transferredllllllllllllllllll", trf_detail)
            for detail in wht_detail + trf_detail:
                tax = detail['tax']
                tax_class = detail['tax_class']
                key = (float_round(tax.amount / 100, 6), tax.l10n_xma_tax_factor_type_id.code, tax_class)
                base_val_pay_curr = detail['base_val_prop_amt_curr'] / (inv_vals['exchange_rate'] or 1.0)
                tax_val_pay_curr = detail['tax_val_prop_amt_curr'] / (inv_vals['exchange_rate'] or 1.0)
                if key in total_taxes_paid:
                    total_taxes_paid[key]['base_value'] += base_val_pay_curr
                    total_taxes_paid[key]['tax_value'] += tax_val_pay_curr
                elif tax.amount >= 0:
                    total_taxes_paid[key] = {
                        'base_value': base_val_pay_curr,
                        'tax_value': tax_val_pay_curr,
                        'tax_amount': float_round(detail['tax_amount'], 6),
                        'tax_type': tax.l10n_xma_tax_factor_type_id.code,
                        'tax_class': tax_class,
                        'tax_spec': 'W' if tax.amount < 0 else 'T',
                    }
                else:
                    total_taxes_withheld[tax_class]['amount_curr'] += tax_val_pay_curr

        # CFDI 4.0: rounding needs to be done after all DRs are added
        # We round up for the currency rate and down for the tax values because we lost a lot of time to find out
        # that Finkok only accepts it this way.  The other PACs accept either way and are reasonable.
        for v in total_taxes_paid.values():
            v['base_value'] = float_round(v['base_value'], move.currency_id.l10n_xma_decimal_number, rounding_method='DOWN')
            v['tax_value'] = float_round(v['tax_value'], move.currency_id.l10n_xma_decimal_number, rounding_method='DOWN')
            v['base_value_mxn'] = float_round(v['base_value'] * rate_payment_curr_mxn_40, mxn_currency.l10n_xma_decimal_number)
            v['tax_value_mxn'] = float_round(v['tax_value'] * rate_payment_curr_mxn_40, mxn_currency.l10n_xma_decimal_number)
        for v in total_taxes_withheld.values():
            v['amount_curr'] = float_round(v['amount_curr'], move.currency_id.l10n_xma_decimal_number, rounding_method='DOWN')
            v['amount_mxn'] = float_round(v['amount_curr'] * rate_payment_curr_mxn_40, mxn_currency.l10n_xma_decimal_number)
        cfdi_date = self.get_mx_current_datetime_payment()
        cfdi_date = cfdi_date.strftime('%Y-%m-%dT%H:%M:%S')
        print('JOTASON', cfdi_date)
        cfdi_values = {
            **self._l10n_xma_get_common_cfdi_values(move, invoice_id),
            'invoice_vals_list': invoice_vals_list,
            'currency': currency,
            'amount': total_amount_currency,
            'amount_mxn': float_round(total_amount_currency * rate_payment_curr_mxn_40, mxn_currency.l10n_xma_decimal_number),
            'rate_payment_curr_mxn': payment_exchange_rate,
            'rate_payment_curr_mxn_40': rate_payment_curr_mxn_40,
            'emitter_vat_ord': is_payment_code_emitter_ok and partner_bank_vat,
            'bank_vat_ord': is_payment_code_bank_ok and partner_bank.name,
            'payment_account_ord': is_payment_code_emitter_ok and payment_account_ord,
            'receiver_vat_ord': is_payment_code_receiver_ok and move.journal_id.bank_account_id.bank_id.l10n_xma_vat,
            'payment_account_receiver': is_payment_code_receiver_ok and payment_account_receiver,
            'cfdi_date': cfdi_date,
            'tax_summary': total_taxes_paid,
            'withholding_summary': total_taxes_withheld,
        }
        print(cfdi_values)
        cfdi_payment_datetime = datetime.combine(fields.Datetime.from_string(self.date), datetime.strptime('12:00:00', '%H:%M:%S').time())
        cfdi_values['cfdi_payment_date'] = cfdi_payment_datetime.strftime('%Y-%m-%dT%H:%M:%S')
        if cfdi_values['customer'].country_id.code != 'MEX':
            cfdi_values['customer_fiscal_residence'] = cfdi_values['customer'].country_id.code
        else:
            cfdi_values['customer_fiscal_residence'] = None
        print(f"CFDI VALUES ||||||||||||||||||||||||||||||\n{cfdi_values}\n|||||||||||||||||||||||||||")
        return cfdi_values

    __check_cfdi_partner_name_re = re.compile(u'''([A-Z]|[a-z]|[0-9]|.| |Ñ|ñ|!|"|%|&|'|´|-|:|;|>|=|<|@|_|,|\{|\}|`|~|á|é|í|ó|ú|Á|É|Í|Ó|Ú|ü|Ü)''')
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
        for char in SingnPayment.__check_cfdi_partner_name_re.sub('', text):
            text = text.replace(char, ' ')
        return text.strip()[:size]
    def get_json_payment(self):
        _logger.info("xma_log------------------------------get_edi_json------------------------")
        for rec in self:
            print(rec.reconciled_invoice_ids[0].name) 
            cfdi_values = self._l10n_mx_xma_get_payment_cfdi_values(rec.reconciled_invoice_ids[0], rec.move_id)
            print("cfdi_values", cfdi_values, '||||||||||||||||||||||||||||||||||||||||||')
            format_string = cfdi_values.get('format_string')
            format_float = cfdi_values.get('format_float')
            tax_objected = cfdi_values.get('tax_objected') if  cfdi_values.get('tax_objected') != None else rec.reconciled_invoice_ids[0]._l10n_xma_get_tax_objected()
            print("tax_objected", tax_objected)
            pago20_totales = {
                "MontoTotalPagos": format_float(cfdi_values.get('amount_mxn'), 2)
            }
            if tax_objected == '02':
                TotalTrasladosBaseIVA0 = format_float(cfdi_values.get('tax_summary')[(0.0, 'Tasa', '002')]['base_value_mxn'], 2) if (0.0, 'Tasa', '002') in cfdi_values.get('tax_summary') else False
                TotalTrasladosImpuestoIVA0 = format_float(cfdi_values.get('tax_summary')[(0.0, 'Tasa', '002')]['tax_value_mxn'], 2) if (0.0, 'Tasa', '002') in cfdi_values.get('tax_summary') else False
                TotalTrasladosBaseIVAExento = format_float(cfdi_values.get('tax_summary')[(0.0, 'Exento', '002')]['base_value_mxn'], 2) if (0.0, 'Exento', '002') in cfdi_values.get('tax_summary') else False
                TotalTrasladosBaseIVA8 = format_float(cfdi_values.get('tax_summary')[(0.08, 'Tasa', '002')]['base_value_mxn'], 2) if (0.08, 'Tasa', '002') in cfdi_values.get('tax_summary') else False
                TotalTrasladosImpuestoIVA8 = format_float(cfdi_values.get('tax_summary')[(0.08, 'Tasa', '002')]['tax_value_mxn'], 2) if (0.08, 'Tasa', '002') in cfdi_values.get('tax_summary') else False
                TotalTrasladosBaseIVA16 = format_float(cfdi_values.get('tax_summary')[(0.16, 'Tasa', '002')]['base_value_mxn'], 2) if (0.16, 'Tasa', '002') in cfdi_values.get('tax_summary') else False
                TotalTrasladosImpuestoIVA16 = format_float(cfdi_values.get('tax_summary')[(0.16, 'Tasa', '002')]['tax_value_mxn'], 2) if (0.16, 'Tasa', '002') in cfdi_values.get('tax_summary') else False
                TotalRetencionesISR = format_float(cfdi_values.get('withholding_summary')['001']['amount_mxn'], 2) if cfdi_values.get('withholding_summary')['001']['amount_mxn'] else False
                TotalRetencionesIVA = format_float(cfdi_values.get('withholding_summary')['002']['amount_mxn'], 2) if cfdi_values.get('withholding_summary')['002']['amount_mxn'] else False
                TotalRetencionesIEPS = format_float(cfdi_values.get('withholding_summary')['003']['amount_mxn'], 2) if cfdi_values.get('withholding_summary')['003']['amount_mxn'] else False

                if TotalTrasladosBaseIVA0:
                    pago20_totales['TotalTrasladosBaseIVA0'] = TotalTrasladosBaseIVA0
                if TotalTrasladosImpuestoIVA0:
                    pago20_totales['TotalTrasladosImpuestoIVA0'] = TotalTrasladosImpuestoIVA0
                if TotalTrasladosBaseIVAExento:
                    pago20_totales['TotalTrasladosBaseIVAExento'] = TotalTrasladosBaseIVAExento
                if TotalTrasladosBaseIVA8:
                    pago20_totales['TotalTrasladosBaseIVA8'] = TotalTrasladosBaseIVA8
                if TotalTrasladosImpuestoIVA8:
                    pago20_totales['TotalTrasladosImpuestoIVA8'] = TotalTrasladosImpuestoIVA8
                if TotalTrasladosBaseIVA16:
                    pago20_totales['TotalTrasladosBaseIVA16'] = TotalTrasladosBaseIVA16
                if TotalTrasladosImpuestoIVA16:
                    pago20_totales['TotalTrasladosImpuestoIVA16'] = TotalTrasladosImpuestoIVA16
                if TotalRetencionesISR:
                    pago20_totales['TotalRetencionesISR'] = TotalRetencionesISR
                if TotalRetencionesIVA:
                    pago20_totales['TotalRetencionesIVA'] = TotalRetencionesIVA
                if TotalRetencionesIEPS:
                    pago20_totales['TotalRetencionesIEPS'] = TotalRetencionesIEPS

            anex2_list_json = []
            for invoice_vals in cfdi_values.get('invoice_vals_list'):
                _logger.info("xma_log invoice_valssssssssssssssssssssssssss %s", invoice_vals)
                invoice = invoice_vals['invoice']
                invoice_tax_objected = invoice._l10n_xma_get_tax_objected()
                print("_l10n_xma_get_tax_objected====================================", invoice_tax_objected)
                pago20_docto_relacionado = {
                    "IdDocumento": invoice.l10n_xma_uuid_invoice,
                    "Serie": format_string(invoice_vals['serie_number'], 25),
                    "Folio": format_string(invoice_vals['folio_number'], 40),
                    "MonedaDR": invoice.currency_id.name,
                    "NumParcialidad": invoice_vals['number_of_payments'],
                    "ImpSaldoAnt": format_float(invoice_vals['amount_before_paid'], invoice.currency_id.l10n_xma_decimal_number),
                    "ImpPagado": format_float(invoice_vals['amount_paid'], invoice.currency_id.l10n_xma_decimal_number),
                    "ImpSaldoInsoluto": format_float(invoice_vals['amount_before_paid'] - invoice_vals['amount_paid'], invoice.currency_id.l10n_xma_decimal_number),
                    "ObjetoImpDR": invoice_tax_objected,
                    "EquivalenciaDR": format_float(invoice_vals['exchange_rate'], 6) if invoice_vals['exchange_rate'] else '1',
                }
                # if pago20_docto_relacionado and invoice_vals['exchange_rate']:
                #     pago20_docto_relacionado['EquivalenciaDR'] = format_float(invoice_vals['exchange_rate'], 6)

                impuestos_dr = {}
                if invoice_tax_objected == '02':
                    tax_detail_withholding = invoice_vals['tax_details_withholding']['tax_details']
                    tax_detail_transferred = invoice_vals['tax_details_transferred']['tax_details']
                    retenciones_dr = []
                    traslados_dr = []

                    if tax_detail_withholding:
                        for wh_tax_detail in tax_detail_withholding.values():
                            tax = wh_tax_detail['tax']
                            values = {
                                "pago20:RetencionDR": {
                                    "BaseDR": format_float(wh_tax_detail['base_val_prop_amt_curr'], invoice.currency_id.decimal_places),
                                    "ImpuestoDR": wh_tax_detail['tax_class'],
                                    "TipoFactorDR": tax.l10n_xma_tax_factor_type_id.code,
                                    "TasaOCuotaDR": format_float(wh_tax_detail['tax_amount'], 6) if tax.l10n_xma_tax_factor_type_id.code != 'Exento' else False,
                                    "ImporteDR": format_float(wh_tax_detail['tax_val_prop_amt_curr'], invoice.currency_id.decimal_places),
                                }
                            }
                            retenciones_dr.append(values)
                    if tax_detail_transferred:
                        for tax_detail in tax_detail_transferred.values():
                            tax = tax_detail['tax']
                            values = {
                                "pago20:TrasladoDR": {
                                    "BaseDR": format_float(tax_detail['base_val_prop_amt_curr'], invoice.currency_id.decimal_places),
                                    "ImpuestoDR": tax_detail['tax_class'],
                                    "TipoFactorDR": tax.l10n_xma_tax_factor_type_id.code,
                                    "TasaOCuotaDR": format_float(tax_detail['tax_amount'], 6) if tax.l10n_xma_tax_factor_type_id.code != 'Exento' else False,
                                    "ImporteDR": format_float(tax_detail['tax_val_prop_amt_curr'], invoice.currency_id.decimal_places),
                                }
                            }
                            traslados_dr.append(values)
                    if retenciones_dr:
                        impuestos_dr['pago20:RetencionesDR'] = retenciones_dr
                    if traslados_dr:
                        impuestos_dr['pago20:TrasladosDR'] = traslados_dr
                if impuestos_dr:
                    pago20_docto_relacionado['pago20:ImpuestosDR'] = impuestos_dr
                anex2_list_json.append(pago20_docto_relacionado)

            impuestos_p = {}
            if tax_objected == '02':
                retenciones_p = []
                traslados_p = []
                if sum([tax['amount_curr'] for tax in cfdi_values.get('withholding_summary').values()]):
                    for tax_class in cfdi_values.get('withholding_summary').keys():
                        if cfdi_values.get('withholding_summary')[tax_class] and cfdi_values.get('withholding_summary')[tax_class]['amount_curr']:
                            withholding_summary = cfdi_values.get('withholding_summary')
                            values = {
                                "pago20:RetencionP": {
                                    "ImpuestoP": tax_class,
                                    "ImporteP": format_float(withholding_summary[tax_class]['amount_curr'], rec.currency_id.decimal_places),
                                }
                            }
                            retenciones_p.append(values)
                for item in cfdi_values.get('tax_summary').values():
                    if item['tax_spec'] == 'T':
                        print("--------------------------------------------item['base_value']", item['base_value'])
                        values = {
                            "pago20:TrasladoP": {
                                "BaseP": format_float(item['base_value'], rec.currency_id.decimal_places),
                                "ImpuestoP": item['tax_class'],
                                "TipoFactorP": item['tax_type'],
                                "TasaOCuotaP": format_float(item['tax_amount'], 6) if item['tax_type'] != 'Exento' else False,
                                "ImporteP": format_float(item['tax_value'], rec.currency_id.decimal_places) if item['tax_type'] != 'Exento' else False,
                            }
                        }
                        traslados_p.append(values)
                if retenciones_p:
                    impuestos_p['pago20:RetencionesP'] = retenciones_p
                if traslados_p:
                    impuestos_p['pago20:TrasladosP'] = traslados_p

            pago20_pago = {
                "FechaPago": cfdi_values.get('cfdi_payment_date'),
                "FormaDePagoP": rec.l10n_xma_payment_form_id.code,
                "MonedaP": self.currency_id.name,
                "TipoCambioP": format_float(cfdi_values.get('rate_payment_curr_mxn_40'), 6) if cfdi_values.get('rate_payment_curr_mxn_40') != 1 else '1',
                "Monto": format_float(rec.amount, rec.currency_id.decimal_places),
                "NumOperacion": format_string(rec.memo, 100),
            }
            if cfdi_values.get('emitter_vat_ord'):
                pago20_pago['RfcEmisorCtaOrd'] = cfdi_values.get('emitter_vat_ord')
            if cfdi_values.get('bank_vat_ord'):
                pago20_pago['NomBancoOrdExt'] = cfdi_values.get('bank_vat_ord')
            if cfdi_values.get('payment_account_ord'):
                pago20_pago['CtaOrdenante'] = cfdi_values.get('payment_account_ord')
            if cfdi_values.get('receiver_vat_ord'):
                pago20_pago['RfcEmisorCtaBen'] = cfdi_values.get('receiver_vat_ord')
            if cfdi_values.get('payment_account_receiver'):
                pago20_pago['CtaBeneficiario'] = cfdi_values.get('payment_account_receiver')

            # for item in anex2_list_json:
            #     pago20_pago['pago20:DoctoRelacionado'] = item

            if anex2_list_json:
                pago20_pago['pago20:DoctoRelacionado'] = anex2_list_json
            if impuestos_p:
                pago20_pago['pago20:ImpuestosP'] = impuestos_p

            uuids = []
            tipo_relacion = ''
            if cfdi_values.get('origin_uuids'):
                tipo_relacion = cfdi_values.get('origin_type')
                for uuid in cfdi_values.get('origin_uuids'):
                    uuids.append({'UUID': uuid})
            name_numbers = list(re.finditer(r'\d+', self.name))
            folio =  name_numbers[-1].group().lstrip('0'),
            serie = self.name[:name_numbers[-1].start()],
            print(f"/////////////////////////////////////////// folio serie {folio[0]} {serie[0]}")
            cfdi_date = self.get_mx_current_datetime_payment()
            cfdi_date = cfdi_date.strftime('%Y-%m-%dT%H:%M:%S')
            xml_json = {
                "xsi:schemaLocation": "http://www.sat.gob.mx/cfd/4 http://www.sat.gob.mx/sitio_internet/cfd/4/cfdv40.xsd http://www.sat.gob.mx/Pagos20 http://www.sat.gob.mx/sitio_internet/cfd/Pagos/Pagos20.xsd",
                "xmlns:cfdi": "http://www.sat.gob.mx/cfd/4",
                "xmlns:xsi": "http://www.w3.org/2001/XMLSchema-instance",
                "xmlns:pago20": "http://www.sat.gob.mx/Pagos20",
                "Version": "4.0",
                "Fecha": cfdi_date,
                "Folio": folio[0], #format_string(cfdi_values.get('folio_number'), 40),
                "Serie": serie[0], #format_string(cfdi_values.get('serie_number'), 25),
                "Sello": "",
                "NoCertificado": "",  # certificate_id.serial_number,
                "Certificado": "",  # certificate_id.sudo().get_data()[0],
                "SubTotal": 0,
                "Moneda": "XXX",
                "Total": 0,
                "TipoDeComprobante": "P",
                "Exportacion": "01",
                "LugarExpedicion": cfdi_values.get('issued_address').zip or cfdi_values.get('supplier').zip,
                # 'cfdi:CfdiRelacionados': {
                #     "TipoRelacion": tipo_relacion if rec.edi_cfdi_origin else '',
                #     'cfdi:CfdiRelacionado': uuids
                # } if rec.edi_cfdi_origin else [],
                "cfdi:Emisor": {
                    "Rfc": self._get_string_cfdi_partner_name(self.company_id.vat.replace('&', '&amp;').replace('"', '&quot;').replace('<', '&lt;').replace('>', '&gt;'), 254),
                    "Nombre": self._get_string_cfdi_partner_name(cfdi_values.get('supplier').name.replace('&', '&amp;').replace('"', '&quot;').replace('<', '&lt;').replace('>', '&gt;'), 254)  ,#format_string(cfdi_values.get('supplier').name, 40),
                    "RegimenFiscal": rec.company_id.partner_id.l10n_xma_taxpayer_type_id.code,
                },
                "cfdi:Receptor": {
                    "Rfc": self._get_string_cfdi_partner_name(cfdi_values.get('customer_rfc').replace('&', '&amp;').replace('"', '&quot;').replace('<', '&lt;').replace('>', '&gt;'), 254),  #'XME100323J17', # if rec.company_id.edi_test_pac else cfdi_values.get('customer_rfc'),
                    "Nombre": self._get_string_cfdi_partner_name(cfdi_values.get('customer').commercial_partner_id.name.replace('&', '&amp;').replace('"', '&quot;').replace('<', '&lt;').replace('>', '&gt;'), 254),#format_string(cfdi_values.get('customer').commercial_partner_id.name, 254).upper(), 
                    "RegimenFiscalReceptor": format_string(cfdi_values.get('customer').commercial_partner_id.l10n_xma_taxpayer_type_id.code),
                    "DomicilioFiscalReceptor": cfdi_values.get('customer').zip if cfdi_values.get('customer').country_id.code == 'MX' else  cfdi_values.get('supplier').zip,
                    "UsoCFDI": "CP01",
                },
                "cfdi:Conceptos": {
                    "cfdi:Concepto": {
                        "ClaveProdServ": "84111506",
                        "Cantidad": "1",
                        "ClaveUnidad": "ACT",
                        "Descripcion": "Pago",
                        "ValorUnitario": "0",
                        "Importe": "0",
                        "ObjetoImp": "01",
                    }
                },
                "cfdi:Complemento": {
                    "pago20:Pagos": {
                        "Version": "2.0",
                        "pago20:Totales": pago20_totales,
                        "pago20:Pago": pago20_pago,
                    }
                }
            }
            return xml_json
    
    def format_float(amount, precision=2):
        ''' Helper to format monetary amount as a string with 2 decimal places. '''
        if amount is None or amount is False:
            return None
        return '%.*f' % (precision, amount)
    # -- Metodos Loca MX --
    def ensure_uuid_exists(self, company_id):
        if company_id.client_uuid == "":
            uuid = str(uuid4())
            company_id.write({"client_uuid": uuid})
            self.env.cr.commit()
            return uuid
        else:
            return company_id.client_uuid


