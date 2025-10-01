from odoo import fields, models, api
import json
from lxml.objectify import fromstring
import base64
from datetime import datetime, timedelta
from odoo.tools import float_round
from odoo.exceptions import UserError, ValidationError
import time
import re
from random import choice, randint
from io import BytesIO, StringIO
from xml.dom import minidom
import qrcode
from num2words import num2words
from MqttLibPy.client import MqttClient
import logging
import re
import json
import xml.etree.ElementTree as ET
from lxml import objectify, etree
import requests
import yaml
_logger = logging.getLogger(__name__)
import hashlib
import pandas as pd
import io
class AccountMoveDO(models.Model):
    _inherit = "account.move"


    l10n_xma_file_name = fields.Char(string="Nombre XML", copy=False)

    l10n_xma_encf = fields.Char(string="eNCF", copy=False)

    l10n_xma_track_id = fields.Char(string="Track ID", copy=False)

    l10n_xma_date_modify = fields.Date(string="Fecha de modificacion", copy=False)

    l10n_xma_modify_code = fields.Selection(
        [
            ('1', 'Anula el NCF modificado'),
            ('2', 'Corrige Texto del Comprobante Fiscal modificado'),
            ('3', 'Corrige montos del NCF modificado'),
            ('4', 'Reemplazo NCF emitido en contingencia'),
            ('5', 'Referencia Factura Consumo Electrónica'),
        ], string="Codigo de Modificacion", copy=False
    )
    amount_total_itbis = fields.Float(string="Total ITBIS", copy=False)
    amount_total_do = fields.Float(string="Total DO", copy=False)
    l10n_xma_require_resume = fields.Boolean(string="Requiere Resumen", default=False)
    url_odoo = fields.Char(string="URL")
    l10n_xma_secure_code = fields.Char(string="codigo", copy=False)
    l10n_xma_seller_id = fields.Many2one('l10n_xma.seller.zone', string="Zona vendedor")
    l10n_xma_route_id = fields.Many2one('l10n_xma.route.zone', string="Ruta Vendedor")

    l10n_xma_shipping_date = fields.Date(string="Fecha Embarque")
    l10n_xma_shipping_number = fields.Char(string="Numero de Embarque")
    l10n_xma_container_number = fields.Char(string="Numero Contenedor")

    l10n_xma_driver = fields.Char(string="Conductor")
    l10n_xma_document_transport = fields.Char(string="Documento de Transporte")
    l10n_xma_ficha = fields.Char(string="Ficha")
    l10n_xma_license_plate = fields.Char(string="Placa")
    l10n_xma_transport_route = fields.Char(string="Ruta de Transporte")
    l10n_xma_transport_zone = fields.Char(string="Zona de Transporte")
    l10n_xma_albara_number = fields.Char(string="Numero de Albaran")

    payment_form_ids = fields.One2many('type.payments.lines', 'move_id', string="Formas de Pago", copy=True)

    l10n_xma_weight_gross = fields.Float(string="Peso Bruto")
    l10n_xma_weight_net = fields.Float(string="Peso Neto")
    l10n_xma_uom_weight_gross = fields.Many2one('uom.uom', string="Unidad de peso Bruto")
    l10n_xma_uom_weight_net = fields.Many2one('uom.uom', string="Unidad de peso Neto")
    l10n_xma_qty_bulto = fields.Float(string="Cantitdad Bulto")
    l10n_xma_uni_bulto = fields.Many2one('uom.uom', string="Unidad Bulto")
    l10n_xma_vol_bulto = fields.Float(string="Volumen Bulto")
    l10n_xma_uni_vol = fields.Many2one('uom.uom', string="Unidad Volumen")

    l10n_xma_name_port_embarque = fields.Char(string="Puerto de Embarque")
    l10n_xma_condiciones_entrega = fields.Char(string="Condiciones de Entrega")
    l10n_xma_total_fob = fields.Float(string="TotalFob")
    l10n_xma_seguro = fields.Float(string="Seguro")
    l10n_xma_flete = fields.Float(string="Flete")
    l10n_xma_otros_gastos = fields.Float(string="Otros Gastos")

    l10n_xma_total_cif = fields.Float(string="TotalCif")
    l10n_xma_regiment_aduanero = fields.Char(string="RegimenAduanero")
    l10n_xma_nombre_puerto_salida = fields.Char(string="NombrePuertoSalida")
    l10n_xma_nombre_puerto_desembarque = fields.Char(string="NombrePuertoDesembarque")
    l10n_xma_via_transporte = fields.Char(string="ViaTransporte")
    l10n_xma_pais_origen = fields.Many2one('res.country',string="PaisOrigen")
    l10n_xma_dir_dest = fields.Char(string="DireccionDestino")
    l10n_xma_pais_dest = fields.Many2one('res.country',string=" PaisDestino")
    
    l10n_xma_json = fields.Text(string="JSON")
    l10n_xma_json_bol = fields.Boolean(string="JSON BOL")



    #importador de CVS 
    l10n_xma_import_id = fields.Many2one('l10n_xma.import.csv', string="CVS ID")

    def get_mx_current_datetime_do_all(self, date):
        return fields.Datetime.context_timestamp(
            self.with_context(tz='America/Santo_Domingo'), date)

    def send_xml_to_api(self):
        return {
            'name': "Enviar XML",
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'l10n_xma.send.xml.do',
            'view_id': self.env.ref('l10n_xma_einvoice.view_wizard_xml_send_form').id,
            'target': 'new'
        }

    def send_xml_to_api_ac(self):
        return {
            'name': "Enviar XML",
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'l10n_xma.send.xml.ac',
            'view_id': self.env.ref('l10n_xma_einvoice.view_wizard_xml_send_form_ac').id,
            'target': 'new'
        }

    def get_xml_data_to_format_ac_re(self, xml):
        for rec in self:
            bxml = base64.decodebytes(xml)
            cert = str(self.company_id.xma_key_p12).replace("b'","").replace("'","")
            entorno = self.company_id.l10n_xma_type_env_do
            cert =  f'{cert}'

            cert_bytes = base64.b64decode(cert)
            cert_hash = hashlib.sha256(cert_bytes).hexdigest()
            password =  self.company_id.xma_key_p12_password
            headers = {
                'Accept': 'application/json',
                'cert':cert,
                'password': password,
            }
            url_acuse = "https://dominicana.xmarts.online/fe/Recepcion/api/ecf"
            url = "https://api.xmarts.com/api/dominicana/sign"
            params = {"isSeed": False, "totalBytes": len(bxml), "sha256": cert_hash, "password": password}
            result = requests.post(url, data=bxml, params=params).text
            root = ET.fromstring(bxml.decode('utf-8'))
            rnc_comprador = root.find('.//RNCComprador').text
            encf = root.find('.//eNCF').text
            xml_name = str(rnc_comprador + encf + ".xml")
            files = {
                "xml_file": (xml_name, result, "text/xml"),
            }
            response = requests.post(url_acuse, headers=headers, files=files)
            content_disposition = response.headers['Content-Disposition']
            if "filename=" in content_disposition:
                filename = content_disposition.split("filename=")[-1].strip().strip('"')
            return {"xml": response.text, 'xml_name': filename}


        # self.get_xml_data_to_format_ap_co(self.l10n_xma_invoice_cfdi)
    def get_xml_data_to_format_ap_co(self, xml):
        for rec in self:
            bxml = base64.decodebytes(xml)
            root = ET.fromstring(bxml.decode('utf-8'))
            version = root.find('.//Version').text
            ernc_emisor = root.find('.//RNCComprador').text
            rnc_comprador = root.find('.//RNCEmisor').text
            encf = root.find('.//eNCF').text
            monto_total = root.find('.//MontoTotal').text
            fecha_emision = root.find('.//FechaEmision').text
        fecha_hora_acr = self.get_mx_current_datetime_do_all(datetime.now())
        fecha_hora_acr =  fecha_hora_acr.strftime('%d-%m-%Y %H:%M:%S')
        data = {
            "DetalleAprobacionComercial": {
                "Version": version,
                "RNCEmisor": ernc_emisor,
                "eNCF": encf,
                "FechaEmision":fecha_emision,
                "MontoTotal": '%.2f' % float(monto_total),
                "RNCComprador": rnc_comprador,
                "Estado":1,
                "FechaHoraAprobacionComercial": "11-04-2025 16:43:33",
                }
            }

        # Convert JSON to XML
        xml = self.convert_json_to_xml(data)

        dom = minidom.parseString(xml)
        pretty_xml = dom.toprettyxml()
        headers = {
            'Accept': 'application/json',
        }
        url = "https://api.xmarts.com/api/dominicana/sign"
        cert = str(self.company_id.xma_key_p12).replace("b'","").replace("'","")
        entorno = self.company_id.l10n_xma_type_env_do
        cert =  f'{cert}'
        password =  self.company_id.xma_key_p12_password
        cert_bytes = base64.b64decode(cert)
        cert_hash = hashlib.sha256(cert_bytes).hexdigest()
        params = {"isSeed": False, "totalBytes": len(pretty_xml), "sha256": cert_hash, "password": password}
        result = requests.post(url, data=pretty_xml, params=params).text
        sign_xml = minidom.parseString(result)
        sign_xml = sign_xml.toprettyxml()
        # sign_xml = BytesIO(sign_xml.encode('utf-8'))
        xml_name = str(rnc_comprador + encf + ".xml")
        files = {
            "xml_file": (xml_name, sign_xml, "text/xml"),
        }
        url_xma = "https://dominicana.xmarts.online/fe/AprobacionComercial/api/ecf"
        response = requests.post(url_xma, headers=headers, files=files)
        return {"xml": sign_xml, "response": response.text, 'xml_name': xml_name}
    def convert_json_to_xml(self, json_data):
        xml_data = ET.Element('ACECF', {
        "xmlns:xsi": "http://www.w3.org/2001/XMLSchema-instance",
        "xmlns:xsd": "http://www.w3.org/2001/XMLSchema"
    })
        self._json_to_xml(json_data, xml_data)
        xml_string = ET.tostring(xml_data, encoding='utf-8', method='xml')
        return xml_string.decode('utf-8')

    def _json_to_xml(self,json_data, parent):
        if isinstance(json_data, dict):
            for key, value in json_data.items():
                if isinstance(value, dict):
                    element = ET.SubElement(parent, key)
                    self._json_to_xml(value, element)
                elif isinstance(value, list):
                    for item in value:
                        element = ET.SubElement(parent, key)
                        self._json_to_xml(item, element)
                else:
                    element = ET.SubElement(parent, key)
                    element.text = str(value)
        elif isinstance(json_data, list):
            for item in json_data:
                self._json_to_xml(item, parent)
        else:
            parent.text = str(json_data)
    def generate_name_XML_do(self):
        for rec in self:
            """EJEMPLO 132324277 E31 0000001010 
                RUC + Codigo de Tipo de Comprobante + consecutivo rellenado por 0 hasta llegar a 10
            """
            ruc = rec.company_id.partner_id.vat
            serie = rec.l10n_latam_document_type_id.doc_code_prefix
            consecutivo = rec.l10n_latam_document_type_id.l10n_xma_current_number
            com_consecutivo = str(consecutivo).zfill(10)
            rec.l10n_xma_file_name = str(ruc) +str(serie) + str(com_consecutivo)
            rec.l10n_xma_encf = str(serie) + str(com_consecutivo)
        
    
    def replace_special_characters(self, secure_code):
        special_characters = {
            " ": "%20",
            "!": "%21",
            "#": "%23",
            "$": "%24",
            "&": "%26",
            "'": "%27",
            "(": "%28",
            ")": "%29",
            "*": "%2A",
            "+": "%2B",
            ",": "%2C",
            "/": "%2F",
            ":": "%3A",
            ";": "%3B"
        }
        for key, value in special_characters.items():
            secure_code = secure_code.replace(key, value)
        return secure_code
    @api.model
    def edi_get_xml_etree_do(self, py_xml=None):
        for rec in self:
            if rec.l10n_xma_invoice_cfdi:
                # time_invoice = self.get_mx_current_datetime_do()
                current_dt = datetime.now()
                date_time = fields.Datetime.context_timestamp(self.with_context(tz=self.env.user.tz), current_dt)
                # invoice_date = date_time.strftime('%Y-%m-%dT%H:%M:%S')
                self.l10n_xma_date_post = current_dt
                time_invoice = date_time
                secure_code = rec.replace_special_characters(rec.l10n_xma_secure_code)
                entorno = rec.company_id.l10n_xma_type_env_do
                if rec.l10n_latam_document_type_id.code == '32' and rec.l10n_xma_require_resume == True:
                    url = "https://fc.dgii.gov.do/%s/consultatimbrefc?rncemisor=%s&encf=%s&montototal=%s&codigoseguridad=%s" % (entorno, rec.company_id.vat, rec.l10n_xma_encf, round(rec.amount_total, 2), secure_code)
                    return url
                elif rec.l10n_latam_document_type_id.code == '32' and rec.l10n_xma_require_resume == False:
                    url = "https://ecf.dgii.gov.do/%s/consultatimbre?rncemisor=%s&rnccomprador=%s&encf=%s&fechaemision=%s&montototal=%s&fechafirma=%s&codigoseguridad=%s" % (entorno, rec.company_id.vat, rec.partner_id.vat, rec.l10n_xma_encf, rec.invoice_date.strftime('%d-%m-%Y'), round(rec.amount_total_do, 2), time_invoice.strftime('%d-%m-%Y %H:%M:%S'), secure_code)
                    return url
                elif rec.l10n_latam_document_type_id.code == '43':
                    url = "https://ecf.dgii.gov.do/%s/consultatimbre?rncemisor=%s&encf=%s&fechaemision=%s&montototal=%s&fechafirma=%s&codigoseguridad=%s" % (entorno, rec.company_id.vat, rec.l10n_xma_encf, rec.invoice_date.strftime('%d-%m-%Y'), round(rec.amount_total_do, 2), time_invoice.strftime('%d-%m-%Y %H:%M:%S'), secure_code)
                elif rec.l10n_latam_document_type_id.code in ('31','33','34','41','44','45','46','47'):
                    url = "https://ecf.dgii.gov.do/%s/consultatimbre?rncemisor=%s&rnccomprador=%s&encf=%s&fechaemision=%s&montototal=%s&fechafirma=%s&codigoseguridad=%s" % (entorno, rec.company_id.vat, rec.partner_id.vat, rec.l10n_xma_encf, rec.invoice_date.strftime('%d-%m-%Y'), round(rec.amount_total_do, 2), time_invoice.strftime('%d-%m-%Y %H:%M:%S'), secure_code)
                return url
    def get_date_do_utc(self):
        # time_invoice = self.get_mx_current_datetime_do()
        current_dt = datetime.now()
        date_time = fields.Datetime.context_timestamp(self.with_context(tz=self.env.user.tz), current_dt)
        self.l10n_xma_date_post = current_dt
        time_invoice = date_time
        date =  time_invoice.strftime('%d-%m-%Y %H:%M:%S')
        return date

    def aument_seq_number(self):
        for rec in self:
            rec.l10n_latam_document_type_id.l10n_xma_current_number + 1
    def another_currency_converter(self, amount , tax_type_code):
        for rec in self:
            amount = float(amount)
            if tax_type_code != False:
                if amount > 0:
                    id_moneda = self.env['res.currency'].search([
                        ('name', '=', rec.currency_id.name)
                    ])
                    ti_cambio = self.env['res.currency.rate'].search([
                        ('currency_id', '=', id_moneda.id)
                    ], order= "id desc", limit=1)
                    tipo_cambio = ti_cambio.inverse_company_rate
                    monto_usd = amount
                    tax = 0.0

                    if tax_type_code == '1':
                        tax = float(0.18)
                    if tax_type_code == '2':
                        tax = float(0.16)
                    if tax_type_code == '3':
                        return round(amount * tipo_cambio ,2)
                    if tax_type_code in ('0', '4'):
                        t1 = round(float(monto_usd) * 1, 2)
                        t2 = t1 * tipo_cambio
                        total = round(t2 / 1, 2)
                        return total
                    t1 = round(float(monto_usd) * tax, 2)
                    t2 = t1 * tipo_cambio
                    total = round(t2 / tax, 2)
                    # _logger.info(f" \n Cantitdad que llege {amount} \n Cantidad que retorna {total}")
                    return total
                else:
                    return 0
    def dividir_con_cero(self, a, b):
        if b == 0:
            return a  # devuelve el monto original si el cambio es cero
        return round(a / b, 2)
    def generate_json_l10n_do(self):
        for rec in self:
            # time_invoice = self.get_mx_current_datetime_do()
            current_dt = datetime.now()
            date_time = fields.Datetime.context_timestamp(self.with_context(tz=self.env.user.tz), current_dt)
            rec.l10n_xma_date_post = current_dt - timedelta(minutes=10)
            time_invoice = current_dt - timedelta(minutes=10)
            # rec.generate_name_XML_do()
            IndicadorBienoServicio = 0
            
            DatosItem = []
            DescuentoORecargo = []
            line = 1
            line_dis = 1
            MontoGravadoI1 = 0
            ITBIS1 = 0
            TotalITBIS = 0
            TotalITBIS1 = 0
            MontoGravadoI2 = 0
            TotalITBIS2 = 0
            MontoGravadoI3 = 0
            ITBIS3 = 0
            TotalITBISRetenido = 0
            TotalISRRetencion = 0
            with_retencion = 0
            MontoNoFacturable = 0
            cambio = 0
            if rec.currency_id.name != 'DOP':
                
                id_moneda = self.env['res.currency'].search([
                    ('name', '=', rec.currency_id.name)
                ])
                ti_cambio = self.env['res.currency.rate'].search([
                    ('currency_id', '=', id_moneda.id)
                ], order= "id desc", limit=1)
                cambio = ti_cambio.inverse_company_rate
            if rec.move_type == 'out_invoice' :
                for ite in rec.line_ids:
                    if ite.tax_tag_ids and ite.credit > 0:
                        for tag in ite.tax_tag_ids:
                            if tag.l10n_xma_tax_type_id.code in ['1','2','3']:                            
                                TotalITBIS +=  ite.credit
                            if tag.l10n_xma_tax_type_id.code in ['1']:
                                MontoGravadoI1 += ite.credit
                                ITBIS1 += 1
                                TotalITBIS1 += ite.credit
                            if tag.l10n_xma_tax_type_id.code in ['2']:
                                MontoGravadoI2 += ite.credit
                                TotalITBIS2 += ite.credit
                                
                            if rec.l10n_latam_document_type_id.code in ('31','33', '34', '41', '47') and tag.l10n_xma_tax_type_id.code in ['6']:
                                TotalITBISRetenido +=  ite.credit
                                with_retencion += 1
                                
                            if rec.l10n_latam_document_type_id.code in ('31','33', '34', '41', '47') and tag.l10n_xma_tax_type_id.code in ['5']:
                                TotalISRRetencion +=  ite.credit
                                with_retencion += 1
                    else:
                        for tag in ite.tax_tag_ids:
                            if rec.l10n_latam_document_type_id.code in ('31','33', '34', '41', '47') and tag.l10n_xma_tax_type_id.code in ['6']:
                                TotalITBISRetenido +=  ite.debit
                                with_retencion += 1
                                
                            if rec.l10n_latam_document_type_id.code in ('31','33', '34', '41', '47') and tag.l10n_xma_tax_type_id.code in ['5']:
                                TotalISRRetencion +=  ite.debit
                                with_retencion += 1
            if rec.move_type == 'in_invoice' and rec.l10n_latam_document_type_id.code in ('41','47'):
                for ite in rec.line_ids:
                    if ite.tax_tag_ids and ite.debit > 0:
                        for tag in ite.tax_tag_ids:
                            if tag.l10n_xma_tax_type_id.code in ['1','2','3']:                            
                                TotalITBIS +=  ite.debit
                            if tag.l10n_xma_tax_type_id.code in ['1']:
                                MontoGravadoI1 += ite.debit
                                ITBIS1 += 1
                                TotalITBIS1 += ite.debit
                            
                            if tag.l10n_xma_tax_type_id.code in ['2']:
                                MontoGravadoI2 += ite.debit
                                TotalITBIS2 += ite.debit
                                
                            if rec.l10n_latam_document_type_id.code in ('31','33', '34', '41', '47') and tag.l10n_xma_tax_type_id.code in ['6']:
                                TotalITBISRetenido +=  ite.debit
                                with_retencion += 1
                                
                            if rec.l10n_latam_document_type_id.code in ('31','33', '34', '41', '47') and tag.l10n_xma_tax_type_id.code in ['5']:
                                TotalISRRetencion +=  ite.debit
                                with_retencion += 1
                    else:
                        for tag in ite.tax_tag_ids:
                            if rec.l10n_latam_document_type_id.code in ('31','33', '34', '41', '47') and tag.l10n_xma_tax_type_id.code in ['6']:
                                TotalITBISRetenido +=  ite.credit
                                with_retencion += 1
                                
                            if rec.l10n_latam_document_type_id.code in ('31','33', '34', '41', '47') and tag.l10n_xma_tax_type_id.code in ['5']:
                                TotalISRRetencion +=  ite.credit
                                with_retencion += 1
            elif rec.move_type == 'out_refund':
                for ite in rec.line_ids:
                    if ite.tax_tag_ids and ite.debit > 0:
                        for tag in ite.tax_tag_ids:
                            if tag.l10n_xma_tax_type_id.code in ['1','2','3']:                            
                                TotalITBIS +=  ite.debit
                            if tag.l10n_xma_tax_type_id.code in ['1']:
                                MontoGravadoI1 += ite.debit
                                ITBIS1 += 1
                                TotalITBIS1 += ite.debit
                            if tag.l10n_xma_tax_type_id.code in ['2']:
                                MontoGravadoI2 += ite.debit
                                TotalITBIS2 += ite.debit
                                

                    else:
                        for tag in ite.tax_tag_ids:
                            if rec.l10n_latam_document_type_id.code in ('31','33', '34', '41', '47') and tag.l10n_xma_tax_type_id.code in ['6']:
                                TotalITBISRetenido +=  ite.credit
                                with_retencion += 1
                                
                            if rec.l10n_latam_document_type_id.code in ('31','33', '34', '41', '47') and tag.l10n_xma_tax_type_id.code in ['5']:
                                TotalISRRetencion +=  ite.credit
                                with_retencion += 1
            total_recargo = 0
            total_descuento = 0
            descuento = 0
            sale = self.env['sale.order'].search([('name', '=', rec.invoice_origin)], limit=1)

            for lines in self.invoice_line_ids:
                if lines.display_type == 'product':
                    for ite in rec.line_ids:                
                        if ite.product_id.type == 'consu' or lines.product_id.type == 'product':
                            IndicadorBienoServicio = 1
                        else:
                            IndicadorBienoServicio = 2
                        if lines.discount < 0 or lines.l10n_xma_discount < 0:
                            total_recargo = 0
                            total_descuento = 0
                            descuento = 0
                            descuento = lines.discount * (lines.quantity * lines.price_unit) / 100
                            total_recargo = descuento * -1
                            #_logger.info(f"Recargo Product:{lines.name}, \n qty: {lines.quantity}, \n price: {lines.price_unit}, \n descuento: {total_descuento}, \n recargo {total_recargo}")
                        elif lines.discount > 0 or lines.l10n_xma_discount > 0:
                            total_recargo = 0
                            total_descuento = 0
                            descuento = 0
                            descuento = lines.discount * (lines.quantity * lines.price_unit) / 100
                            total_descuento = descuento
                            #_logger.info(f"Descuento Product:{lines.name}, \n qty: {lines.quantity}, \n price: {lines.price_unit}, \n descuento: {total_descuento}, \n recargo {total_recargo}")
                    # _logger.info(f"Product:{lines.name}, \n qty: {lines.quantity}, \n price: {lines.price_unit}, \n descuento: {total_descuento}, \n recargo {total_recargo}")

                    subtotal_itbis_retenido = 0
                    subtotal_isr_retenido = 0

                    
                    for tax in lines.tax_ids:
                        if tax.l10n_xma_tax_type_id.code == '6' and rec.move_type == 'out_invoice':
                            subtotal_itbis_retenido += ((lines.price_subtotal * tax.amount) / 100) *-1
                            #_logger.info(f"===== out_invoice====={subtotal_itbis_retenido}" )
                            
                        elif tax.l10n_xma_tax_type_id.code == '6' and rec.move_type == 'in_invoice':
                            subtotal_itbis_retenido += ((lines.price_subtotal * tax.amount) / 100) *-1
                            #_logger.info(f"===== out_invoice====={subtotal_itbis_retenido}" )
                        if tax.l10n_xma_tax_type_id.code == '5' and rec.move_type == 'out_invoice':
                            subtotal_isr_retenido +=  ((lines.price_subtotal * tax.amount) / 100) *-1
                            #_logger.info(f"===== out_invoice====={subtotal_isr_retenido}" )
                        elif tax.l10n_xma_tax_type_id.code == '5' and rec.move_type == 'in_invoice':
                            subtotal_isr_retenido +=  ((lines.price_subtotal * tax.amount) / 100) *-1
                            #_logger.info(f"===== out_invoice====={subtotal_isr_retenido}" )

                    if lines.discount > 0 or lines.discount < 0 and lines.product_id.l10n_xma_isdiscount == False:
                        date_exp = ''
                        date_fab = ''
                        if sale:
                            picking = self.env['stock.picking'].search([('sale_id', '=', sale.id)])
                            for ml in picking.move_line_ids_without_package:
                                if ml.product_id.id == lines.product_id.id:
                                    date_exp = ml.lot_id.expiration_date
                                    date_fab = ml.lot_id.l10n_xma_fab_date
                        if date_fab:
                            date_fab = date_fab.strftime('%d-%m-%Y')
                        if date_exp:
                            date_exp = date_exp.strftime('%d-%m-%Y')
                        monto_recargo = descuento * -1
                        tbcode = {
                                    'CodigosItem': {
                                        "TipoCodigo": 'Interna',
                                        "CodigoItem": lines.product_id.default_code,
                                    }
                                }
                        mto_it = '%.2f' % float(((lines.price_unit * lines.quantity) - total_descuento) + (total_recargo))
                        DatosItem.append({
                            "Item": {
                                    "NumeroLinea": line,
                                    "TablaCodigosItem": tbcode if lines.product_id.default_code else {},
                                    "IndicadorFacturacion": lines.l10n_xma_tax_type_id.code,
                                    "Retencion":{
                                        "IndicadorAgenteRetencionoPercepcion": 1,
                                        "MontoITBISRetenido": '%.2f' % float(subtotal_itbis_retenido),
                                        "MontoISRRetenido": '%.2f' % float(subtotal_isr_retenido),
                                    },
                                    "NombreItem": lines.product_id.name,
                                    "IndicadorBienoServicio": IndicadorBienoServicio,
                                    "DescripcionItem": lines.name,
                                    "CantidadItem": '%.2f' % float(lines.quantity),
                                    "UnidadMedida": int(lines.product_uom_id.l10n_xma_uomcode_id.code),
                                    "FechaElaboracion": date_fab,
                                    "FechaVencimientoItem": date_exp,
                                    "PrecioUnitarioItem": '%.4f' % float(lines.price_unit)  if rec.currency_id.name == 'DOP' else rec.another_currency_converter('%.4f' % float(lines.price_unit), lines.l10n_xma_tax_type_id.code), # precio_item_om,
                                    "DescuentoMonto": '%.2f' % float(total_descuento)  if rec.currency_id.name == 'DOP' else rec.another_currency_converter('%.2f' % float(total_descuento), lines.l10n_xma_tax_type_id.code), # total_descuento_om,                                
                                    "TablaSubDescuento": {
                                        "SubDescuento": {
                                            "TipoSubDescuento": '%' if lines.l10n_xma_discount == 0 else '$',
                                            "SubDescuentoPorcentaje": '%.2f' % float(lines.discount) ,
                                            "MontoSubDescuento":'%.2f' % float(total_descuento)  if rec.currency_id.name == 'DOP' else rec.another_currency_converter('%.2f' % float(total_descuento), lines.l10n_xma_tax_type_id.code), # total_descuento_om,
                                        }
                                    },
                                    "RecargoMonto": '%.2f' % float(total_recargo) if rec.currency_id.name == 'DOP' else rec.another_currency_converter('%.2f' % float(total_recargo), lines.l10n_xma_tax_type_id.code), # tota_mto_recargo_om,
                                    "TablaSubRecargo":{
                                        "SubRecargo":{
                                            "TipoSubRecargo": '%' if lines.l10n_xma_discount == 0 else '$',
                                            "SubRecargoPorcentaje": '%.2f' % float(lines.discount * -1),
                                            "MontoSubRecargo":  '%.2f' % float(total_recargo) if rec.currency_id.name == 'DOP' else rec.another_currency_converter('%.2f' % float(total_recargo), lines.l10n_xma_tax_type_id.code), # tota_mto_recargo_om,
                                        }
                                    },
                                    "OtraMonedaDetalle":{
                                        "PrecioOtraMoneda": '%.4f' % float(lines.price_unit),
                                        "DescuentoOtraMoneda": '%.2f' % float(total_descuento),
                                        "RecargoOtraMoneda": '%.2f' % float(total_recargo),
                                        "MontoItemOtraMoneda": mto_it
                                    },
                                    "MontoItem": mto_it if rec.currency_id.name == 'DOP' else rec.another_currency_converter(mto_it, lines.l10n_xma_tax_type_id.code) # monto_item_om,
                                }
                        })
                        if not date_fab:
                            DatosItem[-1]['Item'].pop('FechaElaboracion')
                        if not date_exp:
                            DatosItem[-1]['Item'].pop('FechaVencimientoItem')
                        if subtotal_isr_retenido == 0:
                            DatosItem[-1]['Item']['Retencion'].pop('MontoISRRetenido')
                        if subtotal_itbis_retenido == 0:
                            DatosItem[-1]['Item']['Retencion'].pop('MontoITBISRetenido')
                        if not lines.product_id.default_code:
                            DatosItem[-1]['Item'].pop('TablaCodigosItem')
                        line += 1
                        if lines.l10n_xma_discount != 0:
                            DatosItem[-1]['Item']['TablaSubDescuento']['SubDescuento'].pop('SubDescuentoPorcentaje', None)
                            DatosItem[-1]['Item']['TablaSubRecargo']['SubRecargo'].pop('SubRecargoPorcentaje', None)
                        if lines.discount < 0 or lines.l10n_xma_discount < 0:
                            DatosItem[-1]['Item'].pop('TablaSubDescuento')
                            DatosItem[-1]['Item'].pop('DescuentoMonto')
                        else:
                            DatosItem[-1]['Item'].pop('TablaSubRecargo')
                            DatosItem[-1]['Item'].pop('RecargoMonto')
                        if rec.currency_id.name == 'DOP':
                            DatosItem[-1]['Item'].pop('OtraMonedaDetalle')
                    #_logger.info(f"descuento------------\n {descuento} \n dsedcuento -----------------")
                    if lines.discount == 0 and lines.product_id.l10n_xma_isdiscount == False:
                        date_exp = ''
                        date_fab = ''
                        if sale:
                            picking = self.env['stock.picking'].search([('sale_id', '=', sale.id)])
                            for ml in picking.move_line_ids_without_package:
                                if ml.product_id.id == lines.product_id.id:
                                    date_exp = ml.lot_id.expiration_date
                                    date_fab = ml.lot_id.l10n_xma_fab_date
                        if date_fab:
                            date_fab = date_fab.strftime('%d-%m-%Y')
                        if date_exp:
                            date_exp = date_exp.strftime('%d-%m-%Y')
                        tbcode = {
                                'CodigosItem': {
                                    "TipoCodigo": 'Interna',
                                    "CodigoItem": lines.product_id.default_code,
                                }
                            }
                        mto_item = '%.2f' % float(lines.price_unit * lines.quantity)
                        DatosItem.append({
                            "Item": {
                                    "NumeroLinea": line,
                                    "TablaCodigosItem": tbcode if lines.product_id.default_code else {},
                                    "IndicadorFacturacion": lines.l10n_xma_tax_type_id.code,
                                    "Retencion":{
                                        "IndicadorAgenteRetencionoPercepcion": 1,
                                        "MontoITBISRetenido": '%.2f' % float(subtotal_itbis_retenido),
                                        "MontoISRRetenido": '%.2f' % float(subtotal_isr_retenido),
                                    },
                                    "NombreItem": lines.product_id.name,
                                    "IndicadorBienoServicio": IndicadorBienoServicio,
                                    "DescripcionItem": lines.name,
                                    "CantidadItem": '%.2f' % float(lines.quantity),
                                    "UnidadMedida": int(lines.product_uom_id.l10n_xma_uomcode_id.code),
                                    "FechaElaboracion": date_fab,
                                    "FechaVencimientoItem": date_exp,                            
                                    "PrecioUnitarioItem": '%.4f' % float(lines.price_unit) if rec.currency_id.name == 'DOP' else rec.another_currency_converter('%.4f' % float(lines.price_unit), lines.l10n_xma_tax_type_id.code),
                                    "OtraMonedaDetalle":{
                                        "PrecioOtraMoneda": '%.4f' % float(lines.price_unit),
                                        "MontoItemOtraMoneda": mto_item
                                    },
                                    "MontoItem": mto_item if rec.currency_id.name == 'DOP' else rec.another_currency_converter(mto_item, lines.l10n_xma_tax_type_id.code),
                                }
                        })
                        if rec.currency_id.name == 'DOP':
                            DatosItem[-1]['Item'].pop('OtraMonedaDetalle')
                        if not date_fab:
                            DatosItem[-1]['Item'].pop('FechaElaboracion')
                        if not date_exp:
                            DatosItem[-1]['Item'].pop('FechaVencimientoItem')
                        if subtotal_isr_retenido == 0:
                            DatosItem[-1]['Item']['Retencion'].pop('MontoISRRetenido')
                        if subtotal_itbis_retenido == 0:
                            DatosItem[-1]['Item']['Retencion'].pop('MontoITBISRetenido')
                        if not lines.product_id.default_code:
                            DatosItem[-1]['Item'].pop('TablaCodigosItem')
                        line += 1
                    if lines.l10n_xma_tax_type_id.code == '0':
                        MontoNoFacturable += lines.price_subtotal
                
                for lines_dor in self.invoice_line_ids:
                    if lines_dor.product_id.l10n_xma_isdiscount == True:
                        DescuentoORecargo.append({
                            "DescuentoORecargo": {
                                "NumeroLinea": line_dis,
                                "TipoAjuste": lines_dor.product_id.l10n_xma_type_discount,
                                # "IndicadorNorma1007": 1,
                                "DescripcionDescuentooRecargo": lines_dor.name,
                                "TipoValor": '$',
                                # "ValorDescuentooRecargo": '',
                                "MontoDescuentooRecargo": '%.2f' % float(lines_dor.price_unit),
                                # "MontoDescuentooRecargoOtraMoneda": '',
                                "IndicadorFacturacionDescuentooRecargo": lines_dor.l10n_xma_tax_type_id.code,
                            }
                        })
                        line_dis += 1
                

                _logger.info(f"MontoGravadoI1: {MontoGravadoI1}, \n ITBIS1: {ITBIS1}, \n TotalITBIS: {TotalITBIS}, \n TotalITBIS1: {TotalITBIS1}, \n MontoGravadoI2: {MontoGravadoI2}, \n TotalITBIS2: {TotalITBIS2}, \n MontoGravadoI3: {MontoGravadoI3}, \n ITBIS3: {ITBIS3}, \n TotalITBISRetenido: {TotalITBISRetenido}, \n TotalISRRetencion: {TotalISRRetencion}, \n with_retencion: {with_retencion}, \n MontoNoFacturable: {MontoNoFacturable}")
                Monto_Exento = 0
                mtogravadoi3 = 0
                count_not_tax = 0
                count_itbs3 = 0
                count_excento = 0
                indicador_facturacion = 0
                
                _logger.info(f"Monto_Exento: {Monto_Exento}, \n mtogravadoi3: {mtogravadoi3}, \n count_not_tax: {count_not_tax}, \n count_itbs3: {count_itbs3}, \n count_excento: {count_excento}, \n indicador_facturacion: {indicador_facturacion}\n")
                for lines_p in rec.invoice_line_ids:

                    if not lines_p.tax_ids:
                        count_not_tax +=1
                    else:
                        for tax in lines_p.tax_ids:
                            if tax.price_include == True:
                                indicador_facturacion += 1
                            if tax.l10n_xma_tax_type_id.code == '3':
                                count_itbs3 += 1
                                mtogravadoi3 += lines_p.price_subtotal
                            if tax.l10n_xma_tax_type_id.code == '4':
                                _logger.info(f"Monto_Exento {Monto_Exento}")
                                Monto_Exento += lines_p.price_subtotal
                                count_excento += 1
                _logger.info(f"Monto_Exento {Monto_Exento}")
                if rec.currency_id.name != 'DOP':
                    mtogravadoi3 = mtogravadoi3 * cambio
                    Monto_Exento = Monto_Exento * cambio
                MontosGravados = (MontoGravadoI1 /.18) + (MontoGravadoI2 / .16) + (mtogravadoi3 / 1)
                MontoGravadoTotal = MontosGravados # - Monto_Exento - MontoNoFacturable
                MontoTotal = MontosGravados + TotalITBIS - MontoNoFacturable + Monto_Exento
                rec.amount_total_itbis = TotalITBIS
                rec.amount_total_do = MontoTotal


                _logger.info(f"CAMPOS FINALESSSSSSSSSSSSSSSSSSSSSSSSS \n MontosGravados: {MontosGravados}, \n MontoGravadoTotal: {MontoGravadoTotal}, \n MontoTotal: {MontoTotal}, \n TotalITBIS: {TotalITBIS}, \n MontoNoFacturable: {MontoNoFacturable}, \n Monto_Exento: {Monto_Exento}")

                MontoImpuestoAdicionalOtraMoneda = 0
                TipoImpuestoOtraMoneda = 0
                MontoImpuestoSelectivoConsumoEspecificoOtraMoneda = 0
                MontoImpuestoSelectivoConsumoAdvaloremOtraMoneda = 0
                OtrosImpuestosAdicionalesOtraMoneda = 0

                

                MontoGravado1OtraMoneda = rec.dividir_con_cero(MontoGravadoI1 / .18, cambio)
                MontoGravado2OtraMoneda = rec.dividir_con_cero(MontoGravadoI2 / .16, cambio)
                MontoGravado3OtraMoneda = rec.dividir_con_cero(mtogravadoi3, cambio)
                MontoGravadoTotalOtraMoneda = rec.dividir_con_cero(MontoGravadoTotal, cambio)
                MontoExentoOtraMoneda = rec.dividir_con_cero(Monto_Exento, cambio)
                TotalITBIS1OtraMoneda = rec.dividir_con_cero(TotalITBIS1, cambio)
                TotalITBIS2OtraMoneda = rec.dividir_con_cero(TotalITBIS2, cambio)
                TotalITBIS3OtraMoneda = 0
                TotalITBISOtraMoneda = rec.dividir_con_cero(TotalITBIS, cambio)
                MontoTotalOtraMoneda = rec.dividir_con_cero(MontoTotal, cambio)




                actividad_economica = self.env['l10n_xma.economic_activity'].search([('res_company', '=', rec.company_id.id)], limit=1)
                
                principal_contact = self.env['res.partner'].search([
                    ('l10n_xma_is_principal_contact', '=', True),
                    ('parent_id', '=', rec.partner_id.id)
                ], limit=1)
                formas_pago = []
                for payments in rec.payment_form_ids:
                    formas_pago.append({
                        "FormaDePago":{
                            "FormaPago": int(payments.payment_id.code),
                            "MontoPago": '%.2f' % float(payments.payment_amount)
                        }
                    })
            json_m = {
                    "ECF": {
                        "Encabezado": {
                            "Version": "1.0",
                            "IdDoc": {
                                "TipoeCF": rec.l10n_latam_document_type_id.code,
                                "eNCF": rec.l10n_xma_encf,
                                "IndicadorNotaCredito": 0,
                                "FechaVencimientoSecuencia": rec.l10n_latam_document_type_id.l10n_xma_date_end.strftime('%d-%m-%Y'),
                                "IndicadorMontoGravado": 1 if indicador_facturacion > 0 else 0,
                                "TipoIngresos": rec.l10n_xma_use_document_id.code,
                                "TipoPago": rec.l10n_xma_payment_type_id.code,
                                "FechaLimitePago": rec.invoice_date_due.strftime('%d-%m-%Y') if rec.invoice_date_due else {},
                                "TablaFormasPago":formas_pago,
                            },
                            "Emisor": {
                                "RNCEmisor": rec.company_id.vat,
                                "RazonSocialEmisor": rec.company_id.name,
                                "NombreComercial": rec.company_id.partner_id.commercial_partner_id.name,
                                "DireccionEmisor": rec.company_id.street,
                                "Municipio": rec.company_id.partner_id.l10n_xma_municipality_id.code,
                                "Provincia": rec.company_id.partner_id.state_id.l10n_xma_statecode,
                                "TablaTelefonoEmisor": {
                                    "TelefonoEmisor": rec.company_id.phone.replace('+1 ', '')
                                },
                                "CorreoEmisor": rec.company_id.email,
                                "WebSite" : rec.company_id.website if rec.company_id.website else {},
                                "ActividadEconomica": actividad_economica.code,
                                "CodigoVendedor": rec.invoice_user_id.ref if rec.invoice_user_id.ref else {},
                                "NumeroFacturaInterna": rec.name,
                                "NumeroPedidoInterno": sale.id,
                                "ZonaVenta": rec.l10n_xma_seller_id.code,
                                "RutaVenta": rec.l10n_xma_route_id.code,
                                "FechaEmision": rec.invoice_date.strftime('%d-%m-%Y'),
                            },
                            "Comprador": {
                                "RNCComprador": rec.partner_id.vat,
                                "IdentificadorExtranjero": rec.partner_id.vat,
                                "RazonSocialComprador": rec.partner_id.name,
                                "ContactoComprador": principal_contact.name, # no 43, 47
                                "CorreoComprador": principal_contact.email, # no 43, 47
                                "DireccionComprador": rec.partner_id.street, # no 43, 47
                                "MunicipioComprador": rec.partner_id.l10n_xma_municipality_id.code, # no 43, 47
                                "ProvinciaComprador": rec.partner_id.state_id.l10n_xma_statecode, # no 43, 47
                                "PaisComprador": rec.partner_id.country_id.code, #solo lleva el 46
                                "FechaEntrega":sale.commitment_date.strftime('%d-%m-%Y') if sale.commitment_date else {}, # no 41,47, 
                                "ContactoEntrega": principal_contact.name, # no 41,47,
                                "DireccionEntrega": sale.partner_shipping_id.street if sale else {}, # no 41,47,
                                "TelefonoAdicional":principal_contact.mobile.replace('+1 ', '') if principal_contact.mobile else '', # no 41,47,
                                "FechaOrdenCompra": sale.date_order.strftime('%d-%m-%Y') if sale.date_order else {}, # no 41,,47,
                                "NumeroOrdenCompra": sale.name if sale else {}, # no 41,47,
                                "CodigoInternoComprador": rec.partner_id.ref
                            },
                            "InformacionesAdicionales":{
                                "FechaEmbarque": rec.l10n_xma_shipping_date.strftime('%d-%m-%Y') if rec.l10n_xma_shipping_date else {},
                                "NumeroEmbarque": rec.l10n_xma_shipping_number if rec.l10n_xma_shipping_number else {},
                                "NumeroContenedor": rec.l10n_xma_container_number if rec.l10n_xma_container_number else {},
                                "NombrePuertoEmbarque": rec.l10n_xma_name_port_embarque,
                                "CondicionesEntrega": rec.l10n_xma_condiciones_entrega,
                                "TotalFob": '%.2f' % float(rec.l10n_xma_total_fob),
                                "Seguro": rec.l10n_xma_seguro,
                                "Flete": rec.l10n_xma_flete,
                                "OtrosGastos": rec.l10n_xma_otros_gastos,
                                "TotalCif":rec.l10n_xma_total_cif,
                                "RegimenAduanero":rec.l10n_xma_regiment_aduanero,
                                "NombrePuertoSalida":rec.l10n_xma_nombre_puerto_salida,
                                "NombrePuertoDesembarque":rec.l10n_xma_nombre_puerto_desembarque,
                                "PesoBruto": '%.2f' % float(rec.l10n_xma_weight_gross),
                                "PesoNeto": '%.2f' % float(rec.l10n_xma_weight_net),
                                "UnidadPesoBruto": rec.l10n_xma_uom_weight_gross.l10n_xma_uomcode_id.code,
                                "UnidadPesoNeto": rec.l10n_xma_uom_weight_net.l10n_xma_uomcode_id.code,
                                "CantidadBulto":  '%.2f' % float(rec.l10n_xma_qty_bulto),
                                "UnidadBulto": rec.l10n_xma_uni_bulto.l10n_xma_uomcode_id.code,
                                "VolumenBulto":  '%.2f' % float(rec.l10n_xma_vol_bulto),
                                "UnidadVolumen": rec.l10n_xma_uni_vol.l10n_xma_uomcode_id.code,
                            },
                            "Transporte":{
                                "ViaTransporte":rec.l10n_xma_via_transporte,
                                "PaisOrigen":rec.l10n_xma_pais_origen.name,
                                "DireccionDestino":rec.l10n_xma_dir_dest,
                                "PaisDestino":rec.l10n_xma_pais_dest.name,
                                "Conductor":rec.l10n_xma_driver,
                                "DocumentoTransporte":rec.l10n_xma_document_transport,
                                "Ficha":rec.l10n_xma_ficha,
                                "Placa":rec.l10n_xma_license_plate,
                                "RutaTransporte":rec.l10n_xma_transport_route,
                                "ZonaTransporte":rec.l10n_xma_transport_zone,
                                "NumeroAlbaran":rec.l10n_xma_albara_number,

                            },
                            "Totales": {
                                "MontoGravadoTotal": '%.2f' % float(MontoGravadoTotal),
                                "MontoGravadoI1": '%.2f' % float(MontoGravadoI1 / .18),
                                "MontoGravadoI2": '%.2f' % float(MontoGravadoI2 / .16),
                                "MontoGravadoI3": '%.2f' % float(mtogravadoi3 / 1),
                                "MontoExento": '%.2f' % float(Monto_Exento),    
                                "ITBIS1": '18' if MontoGravadoI1 > 0 else {},
                                "ITBIS2": '16' if MontoGravadoI2 > 0 else {},
                                "ITBIS3": '0' if MontoGravadoI3 == 0 else {},
                                "TotalITBIS": '%.2f' % float(TotalITBIS),
                                "TotalITBIS1": '%.2f' % float(MontoGravadoI1),
                                "TotalITBIS2": '%.2f' % float(MontoGravadoI2),
                                "TotalITBIS3": '%.2f' % float(0),
                                "MontoTotal": '%.2f' % float(MontoTotal),
                                "MontoNoFacturable": '%.2f' % float(MontoNoFacturable),
                                "MontoPeriodo": '%.2f' % float(MontoTotal + MontoNoFacturable),
                                "ValorPagar" : '%.2f' % float(MontoTotal),
                                "TotalITBISRetenido": '%.2f' % float(TotalITBISRetenido) if TotalITBISRetenido > 0 else {},
                                "TotalISRRetencion": '%.2f' % float(TotalISRRetencion) if TotalISRRetencion > 0 else {},
                            },
                            "OtraMoneda": {
                                "TipoMoneda": rec.currency_id.name,
                                "TipoCambio": '%.2f' % float(cambio),
                                "MontoGravadoTotalOtraMoneda": '%.2f' % float(MontoGravadoTotalOtraMoneda),
                                "MontoGravado1OtraMoneda": '%.2f' % float(MontoGravado1OtraMoneda),
                                "MontoGravado2OtraMoneda": '%.2f' % float(MontoGravado2OtraMoneda),
                                "MontoGravado3OtraMoneda": '%.2f' % float(MontoGravado3OtraMoneda),
                                "MontoExentoOtraMoneda": '%.2f' % float(MontoExentoOtraMoneda),
                                "TotalITBISOtraMoneda": '%.2f' % float(TotalITBISOtraMoneda),
                                "TotalITBIS1OtraMoneda": '%.2f' % float(TotalITBIS1OtraMoneda),
                                "TotalITBIS2OtraMoneda": '%.2f' % float(TotalITBIS2OtraMoneda),
                                "TotalITBIS3OtraMoneda": '%.2f' % float(TotalITBIS3OtraMoneda),
                                "MontoTotalOtraMoneda": '%.2f' % float(MontoTotalOtraMoneda),
                            }                                                     
                        },
                        "DetallesItems": DatosItem,
                        "DescuentosORecargos": DescuentoORecargo if DescuentoORecargo else {},
                        "InformacionReferencia":{
                            "NCFModificado":rec.l10n_xma_origin,
                            # "RNCOtroContribuyente": '',
                            "FechaNCFModificado": rec.l10n_xma_date_modify.strftime('%d-%m-%Y') if rec.l10n_latam_document_type_id.code in ('33','34') else {},
                            "CodigoModificacion": int(rec.l10n_xma_modify_code),
                            # "RazonModificacion": '',
                        },
                        "FechaHoraFirma": time_invoice.strftime('%d-%m-%Y %H:%M:%S')
                }
            }
            if TotalITBIS1 == 0 and TotalITBIS2 == 0 and count_itbs3 == 0:
                json_m['ECF']['Encabezado']['OtraMoneda'].pop('TotalITBISOtraMoneda', None)
            if MontoGravadoTotalOtraMoneda == 0:
                json_m['ECF']['Encabezado']['OtraMoneda'].pop('MontoGravadoTotalOtraMoneda', None)
            if not rec.company_id.phone:
                json_m['ECF']['Encabezado']['Emisor'].pop("TablaTelefonoEmisor", None)
            if not principal_contact.mobile:
                json_m['ECF']['Encabezado']['Comprador'].pop("TelefonoAdicional", None)
            if not rec.partner_id.ref: 
                json_m['ECF']['Encabezado']['Comprador'].pop('CodigoInternoComprador', None)

            if not actividad_economica:
                json_m['ECF']['Encabezado']['Emisor'].pop('ActividadEconomica', None)
            if not rec.l10n_xma_name_port_embarque:
                json_m['ECF']['Encabezado']['InformacionesAdicionales'].pop('NombrePuertoEmbarque', None)
            if not rec.l10n_xma_condiciones_entrega:
                json_m['ECF']['Encabezado']['InformacionesAdicionales'].pop('CondicionesEntrega', None)
            if not rec.l10n_xma_total_fob:
                json_m['ECF']['Encabezado']['InformacionesAdicionales'].pop('TotalFob', None)
            if not rec.l10n_xma_seguro:
                json_m['ECF']['Encabezado']['InformacionesAdicionales'].pop('Seguro', None)
            if not rec.l10n_xma_flete:
                json_m['ECF']['Encabezado']['InformacionesAdicionales'].pop('Flete', None)
            if not rec.l10n_xma_otros_gastos:
                json_m['ECF']['Encabezado']['InformacionesAdicionales'].pop('OtrosGastos', None)
            if not rec.l10n_xma_total_cif:
                json_m['ECF']['Encabezado']['InformacionesAdicionales'].pop('TotalCif', None)
            if not rec.l10n_xma_regiment_aduanero:
                json_m['ECF']['Encabezado']['InformacionesAdicionales'].pop('RegimenAduanero', None)
            if not rec.l10n_xma_nombre_puerto_salida:
                json_m['ECF']['Encabezado']['InformacionesAdicionales'].pop('NombrePuertoSalida', None)
            if not rec.l10n_xma_nombre_puerto_desembarque:
                json_m['ECF']['Encabezado']['InformacionesAdicionales'].pop('NombrePuertoDesembarque', None)
            if not rec.l10n_xma_via_transporte:
                json_m['ECF']['Encabezado']['Transporte'].pop('ViaTransporte', None)
            if not rec.l10n_xma_pais_origen:
                json_m['ECF']['Encabezado']['Transporte'].pop('PaisOrigen', None)
            if not rec.l10n_xma_dir_dest:
                json_m['ECF']['Encabezado']['Transporte'].pop('DireccionDestino', None)
            if not rec.l10n_xma_pais_dest:
                json_m['ECF']['Encabezado']['Transporte'].pop('PaisDestino', None)
            if TotalITBIS ==0 and TotalITBIS1 == 0 and TotalITBIS2 == 0 and count_itbs3 == 0:
                json_m['ECF']['Encabezado']['Totales'].pop('TotalITBIS', None)
            if not rec.l10n_xma_driver:
                json_m['ECF']['Encabezado']['Transporte'].pop('Conductor', None)
            if not rec.l10n_xma_document_transport:
                json_m['ECF']['Encabezado']['Transporte'].pop('DocumentoTransporte', None)
            if not rec.l10n_xma_ficha:
                json_m['ECF']['Encabezado']['Transporte'].pop('Ficha', None)
            if not rec.l10n_xma_license_plate:
                json_m['ECF']['Encabezado']['Transporte'].pop('Placa', None)
            if not rec.l10n_xma_transport_route:
                json_m['ECF']['Encabezado']['Transporte'].pop('RutaTransporte', None)
            if not rec.l10n_xma_transport_zone:
                json_m['ECF']['Encabezado']['Transporte'].pop('ZonaTransporte', None)
            if not rec.l10n_xma_albara_number:
                json_m['ECF']['Encabezado']['Transporte'].pop('NumeroAlbaran', None)
            
            if not rec.l10n_xma_driver and not rec.l10n_xma_document_transport \
                    and not rec.l10n_xma_ficha and not rec.l10n_xma_license_plate \
                    and not rec.l10n_xma_transport_route and not rec.l10n_xma_transport_zone and  not rec.l10n_xma_albara_number:
                json_m['ECF']['Encabezado'].pop('Transporte', None)
            if not DescuentoORecargo: 
                json_m['ECF'].pop('DescuentosORecargos', None)
            if MontoGravadoTotal <= 0:
                json_m['ECF']['Encabezado']['Totales'].pop('MontoGravadoTotal', None)
                json_m['ECF']['Encabezado']['IdDoc'].pop('IndicadorMontoGravado')
            if not sale:
                json_m['ECF']['Encabezado']['Comprador'].pop('FechaEntrega', None)
                json_m['ECF']['Encabezado']['Comprador'].pop('DireccionEntrega', None)
                json_m['ECF']['Encabezado']['Comprador'].pop('FechaOrdenCompra', None)
                json_m['ECF']['Encabezado']['Comprador'].pop('NumeroOrdenCompra', None)
                json_m['ECF']['Encabezado']['Comprador'].pop('ContactoEntrega', None)
                json_m['ECF']['Encabezado']['Emisor'].pop('NumeroPedidoInterno', None)
            if not formas_pago:
                json_m['ECF']['Encabezado']['IdDoc'].pop('TablaFormasPago')
                json_m['ECF']['Encabezado']['Totales'].pop('MontoPeriodo', None)
                json_m['ECF']['Encabezado']['Totales'].pop('ValorPagar', None)
            if not rec.invoice_user_id.ref:
                json_m['ECF']['Encabezado']['Emisor'].pop('CodigoVendedor', None)
            if not rec.l10n_xma_seller_id.code:
                json_m['ECF']['Encabezado']['Emisor'].pop('ZonaVenta', None)
            if not rec.l10n_xma_route_id.code:
                json_m['ECF']['Encabezado']['Emisor'].pop('RutaVenta', None)
            if not principal_contact:
                json_m['ECF']['Encabezado']['Comprador'].pop('ContactoComprador', None)
                json_m['ECF']['Encabezado']['Comprador'].pop('CorreoComprador', None)
                json_m['ECF']['Encabezado']['Comprador'].pop('ContactoEntrega', None)
                json_m['ECF']['Encabezado']['Comprador'].pop('TelefonoAdicional', None)
            if not rec.partner_id.street:
                json_m['ECF']['Encabezado']['Comprador'].pop('DireccionComprador', None)
            if not rec.partner_id.l10n_xma_municipality_id.code:
                json_m['ECF']['Encabezado']['Comprador'].pop('MunicipioComprador', None)
            if not rec.partner_id.state_id.code:
                json_m['ECF']['Encabezado']['Comprador'].pop('ProvinciaComprador', None)
            if rec.partner_id.country_id.code != 'DO':
                json_m['ECF']['Encabezado']['Comprador'].pop('ProvinciaComprador', None)

            if not sale.commitment_date:
                json_m['ECF']['Encabezado']['Comprador'].pop('FechaEntrega', None)
            if not sale.partner_shipping_id.street:
                json_m['ECF']['Encabezado']['Comprador'].pop('DireccionEntrega', None)
            if not sale.date_order:
                json_m['ECF']['Encabezado']['Comprador'].pop('FechaOrdenCompra', None)
            if not sale.name:
                json_m['ECF']['Encabezado']['Comprador'].pop('NumeroOrdenCompra', None)
            if count_not_tax == len(rec.invoice_line_ids):
                json_m['ECF']['Encabezado']['Totales'].pop('MontoGravadoTotal', None)
            if count_itbs3 == 0:
                json_m['ECF']['Encabezado']['Totales'].pop('MontoGravadoI3', None)
                json_m['ECF']['Encabezado']['Totales'].pop('ITBIS3', None)
                json_m['ECF']['Encabezado']['Totales'].pop('TotalITBIS3', None)

            if MontoNoFacturable == 0:
                json_m['ECF']['Encabezado']['Totales'].pop('MontoNoFacturable', None)
            if rec.l10n_latam_document_type_id.code not in ('33','34'):
                json_m['ECF'].pop('InformacionReferencia')
            if MontoGravadoI1 == 0:
                json_m['ECF']['Encabezado']['Totales'].pop('MontoGravadoI1')
                json_m['ECF']['Encabezado']['Totales'].pop('ITBIS1')
                json_m['ECF']['Encabezado']['Totales'].pop('TotalITBIS1')
            if  MontoGravado1OtraMoneda == 0:
                json_m['ECF']['Encabezado']['OtraMoneda'].pop('MontoGravado1OtraMoneda', None)
                json_m['ECF']['Encabezado']['OtraMoneda'].pop('TotalITBIS1OtraMoneda', None)

            if MontoGravadoI2 == 0:
                json_m['ECF']['Encabezado']['Totales'].pop('MontoGravadoI2')    
                json_m['ECF']['Encabezado']['Totales'].pop('ITBIS2')
                json_m['ECF']['Encabezado']['Totales'].pop('TotalITBIS2')
            if MontoGravado2OtraMoneda == 0:
                json_m['ECF']['Encabezado']['OtraMoneda'].pop('MontoGravado2OtraMoneda', None)
                json_m['ECF']['Encabezado']['OtraMoneda'].pop('TotalITBIS2OtraMoneda', None)
            if count_itbs3 == 0:
                json_m['ECF']['Encabezado']['OtraMoneda'].pop('MontoGravado3OtraMoneda', None)
                json_m['ECF']['Encabezado']['OtraMoneda'].pop('TotalITBIS3OtraMoneda', None)

            if TotalITBISRetenido == 0:
                json_m['ECF']['Encabezado']['Totales'].pop('TotalITBISRetenido')
            if TotalISRRetencion == 0:
                json_m['ECF']['Encabezado']['Totales'].pop('TotalISRRetencion') 
            if with_retencion == 0:
                for lines in json_m['ECF']['DetallesItems']:
                    lines['Item'].pop('Retencion')
            if rec.move_type != 'out_refund':
                json_m['ECF']['Encabezado']['IdDoc'].pop('IndicadorNotaCredito')
            if rec.l10n_latam_document_type_id.code in ('32','34'):
                json_m['ECF']['Encabezado']['IdDoc'].pop('FechaVencimientoSecuencia')
            if rec.l10n_latam_document_type_id.code in ('41','47'):
                json_m['ECF']['Encabezado']['IdDoc'].pop('TipoIngresos')
                json_m['ECF']['Encabezado']['Emisor'].pop('CodigoVendedor', None)
                json_m['ECF']['Encabezado']['Emisor'].pop('ZonaVenta', None)
                json_m['ECF']['Encabezado']['Emisor'].pop('RutaVenta', None)
                # json_m['ECF']['Encabezado']['Comprador'].pop('', None)
                
            if rec.l10n_latam_document_type_id.code not in ('46','47') and rec.partner_id.country_id == rec.company_id.country_id:
                json_m['ECF']['Encabezado']['Comprador'].pop('IdentificadorExtranjero', None)
                
            elif rec.l10n_latam_document_type_id.code == '32' and  rec.partner_id.country_id != rec.company_id.country_id:
                json_m['ECF']['Encabezado']['Comprador'].pop('RNCComprador', None)
            else:
                json_m['ECF']['Encabezado']['Comprador'].pop('RNCComprador', None)
            if rec.l10n_latam_document_type_id.code != '46':
                json_m['ECF']['Encabezado']['Comprador'].pop('PaisComprador', None)
            if rec.l10n_latam_document_type_id.code == '43':
                json_m['ECF']['Encabezado']['IdDoc'].pop('TipoIngresos')
                json_m['ECF']['Encabezado']['Totales'].pop('MontoGravadoI1', None)
                json_m['ECF']['Encabezado']['Totales'].pop('MontoGravadoTotal', None)
                json_m['ECF']['Encabezado']['Totales'].pop('ITBIS1', None)
                json_m['ECF']['Encabezado']['Totales'].pop('TotalITBIS1', None)
                json_m['ECF']['Encabezado']['Totales'].pop('MontoGravadoI2', None)    
                json_m['ECF']['Encabezado']['Totales'].pop('ITBIS2', None)
                json_m['ECF']['Encabezado']['Totales'].pop('TotalITBIS2', None)
                json_m['ECF']['Encabezado']['Totales'].pop('TotalITBISRetenido', None)
                json_m['ECF']['Encabezado']['Totales'].pop('TotalISRRetencion', None)
                json_m['ECF']['Encabezado']['IdDoc'].pop('IndicadorMontoGravado', None)
                json_m['ECF']['Encabezado']['Totales'].pop('MontoGravadoI3', None)
                json_m['ECF']['Encabezado']['Totales'].pop('ITBIS3', None)
                for lines in json_m['ECF']['DetallesItems']:
                    lines['Item'].pop('Retencion', None)
                json_m['ECF']['Encabezado']['Emisor'].pop('CodigoVendedor', None)
                json_m['ECF']['Encabezado']['Emisor'].pop('ZonaVenta', None)
                json_m['ECF']['Encabezado']['Emisor'].pop('RutaVenta', None)
                json_m['ECF']['Encabezado']['Comprador'].pop('CodigoInternoComprador', None)
                json_m['ECF']['Encabezado']['InformacionesAdicionales'].pop('FechaEmbarque', None)
                json_m['ECF']['Encabezado']['InformacionesAdicionales'].pop('NumeroEmbarque', None)
                json_m['ECF']['Encabezado']['InformacionesAdicionales'].pop('NumeroContenedor', None)
                json_m['ECF']['Encabezado']['Comprador'].pop('ContactoComprador', None)
                json_m['ECF']['Encabezado']['Comprador'].pop('CorreoComprador', None)
                json_m['ECF']['Encabezado']['Comprador'].pop('DireccionComprador', None)
                json_m['ECF']['Encabezado']['Comprador'].pop('MunicipioComprador', None)
                json_m['ECF']['Encabezado']['Comprador'].pop('ProvinciaComprador', None)
                json_m['ECF']['Encabezado']['Comprador'].pop('FechaEntrega', None)
                json_m['ECF']['Encabezado']['Comprador'].pop('ContactoEntrega', None)
                json_m['ECF']['Encabezado']['Comprador'].pop('DireccionEntrega', None)
                json_m['ECF']['Encabezado']['Comprador'].pop('TelefonoAdicional', None)
                json_m['ECF']['Encabezado']['Comprador'].pop('FechaOrdenCompra', None)
                json_m['ECF']['Encabezado']['Comprador'].pop('NumeroOrdenCompra', None)
                json_m['ECF']['Encabezado'].pop('Comprador', None)
            if rec.l10n_latam_document_type_id.code == '44':
                json_m['ECF']['Encabezado']['Totales'].pop('MontoGravadoI1', None)
                json_m['ECF']['Encabezado']['Totales'].pop('MontoGravadoTotal', None)
                json_m['ECF']['Encabezado']['Totales'].pop('ITBIS1', None)
                json_m['ECF']['Encabezado']['Totales'].pop('TotalITBIS1', None)
                json_m['ECF']['Encabezado']['Totales'].pop('MontoGravadoI2', None)    
                json_m['ECF']['Encabezado']['Totales'].pop('ITBIS2', None)
                json_m['ECF']['Encabezado']['Totales'].pop('TotalITBIS2', None)
                json_m['ECF']['Encabezado']['Totales'].pop('TotalITBISRetenido', None)
                json_m['ECF']['Encabezado']['Totales'].pop('TotalISRRetencion', None)
                json_m['ECF']['Encabezado']['IdDoc'].pop('IndicadorMontoGravado', None)
                json_m['ECF']['Encabezado']['Totales'].pop('MontoGravadoI3', None)
                json_m['ECF']['Encabezado']['Totales'].pop('ITBIS3', None)
            if rec.l10n_latam_document_type_id.code != '46' and rec.l10n_xma_condiciones_entrega:
                json_m['ECF']['Encabezado']['InformacionesAdicionales'].pop('CondicionesEntrega', None)
            if rec.l10n_latam_document_type_id.code == '46':
                json_m['ECF']['Encabezado']['IdDoc'].pop('IndicadorMontoGravado', None)
                json_m['ECF']['Encabezado']['Totales'].pop('MontoGravadoI1', None)
                json_m['ECF']['Encabezado']['Totales'].pop('MontoGravadoI2', None) 
                json_m['ECF']['Encabezado']['Totales'].pop('ITBIS1', None)    
                json_m['ECF']['Encabezado']['Totales'].pop('ITBIS2', None)
                json_m['ECF']['Encabezado']['Totales'].pop('TotalITBIS1', None)
                json_m['ECF']['Encabezado']['Totales'].pop('TotalITBIS2', None)
                json_m['ECF']['Encabezado']['Totales'].pop('TotalITBISRetenido', None)
                json_m['ECF']['Encabezado']['Totales'].pop('TotalISRRetencion', None)
                json_m['ECF']['Encabezado']['Totales'].pop('MontoExento', None)
            if rec.l10n_latam_document_type_id.code == '47':
                json_m['ECF']['Encabezado']['IdDoc'].pop('IndicadorMontoGravado', None)
                json_m['ECF']['Encabezado']['Totales'].pop('MontoGravadoTotal', None)
                json_m['ECF']['Encabezado']['Totales'].pop('MontoGravadoI1', None)
                json_m['ECF']['Encabezado']['Totales'].pop('MontoGravadoI2', None) 

                json_m['ECF']['Encabezado']['Totales'].pop('TotalITBIS', None)
                json_m['ECF']['Encabezado']['Totales'].pop('ITBIS1', None)    
                json_m['ECF']['Encabezado']['Totales'].pop('ITBIS2', None)
                json_m['ECF']['Encabezado']['Totales'].pop('TotalITBIS1', None)
                json_m['ECF']['Encabezado']['Totales'].pop('TotalITBIS2', None)
                json_m['ECF']['Encabezado']['Totales'].pop('TotalITBISRetenido', None)
                # json_m['ECF']['Encabezado']['Totales'].pop('MontoExento', None)
                json_m['ECF']['Encabezado']['Totales'].pop('MontoGravadoI3', None)
                json_m['ECF']['Encabezado']['Totales'].pop('ITBIS3', None)
                json_m['ECF']['Encabezado']['Comprador'].pop('CodigoInternoComprador', None)
                json_m['ECF']['Encabezado']['InformacionesAdicionales'].pop('FechaEmbarque', None)
                json_m['ECF']['Encabezado']['InformacionesAdicionales'].pop('NumeroEmbarque', None)
                json_m['ECF']['Encabezado']['InformacionesAdicionales'].pop('NumeroContenedor', None)
                json_m['ECF']['Encabezado']['Comprador'].pop('ContactoComprador', None)
                json_m['ECF']['Encabezado']['Comprador'].pop('CorreoComprador', None)
                json_m['ECF']['Encabezado']['Comprador'].pop('DireccionComprador', None)
                json_m['ECF']['Encabezado']['Comprador'].pop('MunicipioComprador', None)
                json_m['ECF']['Encabezado']['Comprador'].pop('ProvinciaComprador', None)
                json_m['ECF']['Encabezado']['Comprador'].pop('FechaEntrega', None)
                json_m['ECF']['Encabezado']['Comprador'].pop('ContactoEntrega', None)
                json_m['ECF']['Encabezado']['Comprador'].pop('DireccionEntrega', None)
                json_m['ECF']['Encabezado']['Comprador'].pop('TelefonoAdicional', None)
                json_m['ECF']['Encabezado']['Comprador'].pop('FechaOrdenCompra', None)
                json_m['ECF']['Encabezado']['Comprador'].pop('NumeroOrdenCompra', None)
            # if rec.l10n_latam_document_type_id.code == '32':
            #     # json_m['ECF']['Encabezado']['IdDoc'].pop('IndicadorMontoGravado', None)
            #     json_m['ECF']['Encabezado']['Totales'].pop('MontoExento', None)
            if Monto_Exento == 0:
                json_m['ECF']['Encabezado']['Totales'].pop('MontoExento', None)
            if MontoExentoOtraMoneda == 0:
                json_m['ECF']['Encabezado']['OtraMoneda'].pop('MontoExentoOtraMoneda', None)
            # if rec.l10n_latam_document_type_id.code == '33':
            #     json_m['ECF']['Encabezado']['Totales'].pop('MontoExento', None)
            if rec.l10n_latam_document_type_id.code == '41':
                if Monto_Exento == 0:
                    json_m['ECF']['Encabezado']['Totales'].pop('MontoExento', None)
                json_m['ECF']['Encabezado']['Comprador'].pop('FechaEntrega', None)
                json_m['ECF']['Encabezado']['Comprador'].pop('ContactoEntrega', None)
                json_m['ECF']['Encabezado']['Comprador'].pop('DireccionEntrega', None)
                json_m['ECF']['Encabezado']['Comprador'].pop('TelefonoAdicional', None)
                json_m['ECF']['Encabezado']['Comprador'].pop('FechaOrdenCompra', None)
                json_m['ECF']['Encabezado']['Comprador'].pop('NumeroOrdenCompra', None)
            if rec.l10n_xma_payment_type_id.code != '2':
                json_m['ECF']['Encabezado']['IdDoc'].pop('FechaLimitePago', None)

            if count_excento == 0:
                json_m['ECF']['Encabezado']['Totales'].pop('MontoExento', None)
            if not rec.l10n_xma_shipping_date:
                json_m['ECF']['Encabezado']['InformacionesAdicionales'].pop('FechaEmbarque', None)
            if not rec.l10n_xma_shipping_number:
                json_m['ECF']['Encabezado']['InformacionesAdicionales'].pop('NumeroEmbarque', None)
            if not rec.l10n_xma_container_number:
                json_m['ECF']['Encabezado']['InformacionesAdicionales'].pop('NumeroContenedor', None)

            if not rec.l10n_xma_weight_gross:
                json_m['ECF']['Encabezado']['InformacionesAdicionales'].pop('PesoBruto', None)
            if not rec.l10n_xma_weight_net:
                json_m['ECF']['Encabezado']['InformacionesAdicionales'].pop('PesoNeto', None)
            if not rec.l10n_xma_uom_weight_gross:
                json_m['ECF']['Encabezado']['InformacionesAdicionales'].pop('UnidadPesoBruto', None)
            if not rec.l10n_xma_uom_weight_net:
                json_m['ECF']['Encabezado']['InformacionesAdicionales'].pop('UnidadPesoNeto', None)
            if not  rec.l10n_xma_qty_bulto:
                json_m['ECF']['Encabezado']['InformacionesAdicionales'].pop('CantidadBulto', None)
            if not rec.l10n_xma_uni_bulto:
                json_m['ECF']['Encabezado']['InformacionesAdicionales'].pop('UnidadBulto', None)
            if not rec.l10n_xma_vol_bulto:
                json_m['ECF']['Encabezado']['InformacionesAdicionales'].pop('VolumenBulto', None)
            if not rec.l10n_xma_uni_vol:
                json_m['ECF']['Encabezado']['InformacionesAdicionales'].pop('UnidadVolumen', None)
            if not rec.l10n_xma_shipping_date and not rec.l10n_xma_shipping_number \
                    and not rec.l10n_xma_weight_gross and not rec.l10n_xma_weight_net \
                    and not rec.l10n_xma_container_number and not rec.l10n_xma_uom_weight_gross \
                    and not rec.l10n_xma_uom_weight_net and not rec.l10n_xma_qty_bulto \
                    and not rec.l10n_xma_uni_bulto and not rec.l10n_xma_vol_bulto and not rec.l10n_xma_uni_vol:
                json_m['ECF']['Encabezado'].pop('InformacionesAdicionales')
            if rec.currency_id.name == 'DOP':
                json_m['ECF']['Encabezado'].pop('OtraMoneda', None)
            json_m = rec.delete_none_or_false(json_m)
            
            _logger.info(f"json final:{ str(json_m)}")
            
            
            # json_32 = {
            #     "ECF": {
            #         "Encabezado": {
            #             "Version": "1.0",
            #             "IdDoc": {
            #                 "TipoeCF": "32",
            #                 "eNCF": "E320000006015",
            #                 "FechaVencimientoSecuencia": "31-12-2025",
            #                 "IndicadorMontoGravado": "0",
            #                 "TipoIngresos": "01",
            #                 "TipoPago": "1"
            #             },
            #             "Emisor": {
            #                 "RNCEmisor": "132324277",
            #                 "RazonSocialEmisor": "XMARTS DEL CARIBE SRL",
            #                 "NombreComercial": "XMARTS DEL CARIBE",
            #                 "DireccionEmisor": "CALLE B, NO. 27, MOISES",
            #                 "Municipio": "320101",
            #                 "Provincia": "320000",
            #                 "CorreoEmisor": "info@xmarts.com",
            #                 "FechaEmision": "25-12-2024"
            #             },
            #             "Comprador": {
            #                 "RNCComprador": "132109122",
            #                 "RazonSocialComprador": "ALANUBE SOLUCIONES SRL",
            #                 "DireccionComprador": "Plaza Hache, C/ Luis Lembert esq. Dr. Heriberto Pieter, Ensanche Naco",
            #                 "MunicipioComprador": "010101",
            #                 "ProvinciaComprador": "010000"
            #             },
            #             "Totales": {
            #                 "MontoGravadoTotal": "500",
            #                 "MontoGravadoI1": "500",
            #                 "ITBIS1": "18",
            #                 "TotalITBIS": "90.00",
            #                 "TotalITBIS1": "90.00",
            #                 "MontoTotal": "590.00"
            #             }
            #         },
            #         "DetallesItems": {
            #             "Item": {
            #                 "NumeroLinea": "1",
            #                 "IndicadorFacturacion": "1",
            #                 "NombreItem": "Teclado Inalambrico USB - Modelo XYZ",
            #                 "IndicadorBienoServicio": "1",
            #                 "DescripcionItem": "Teclado Inalambrico USB - Modelo XYZ",
            #                 "CantidadItem": "1.00",
            #                 "PrecioUnitarioItem": "500",
            #                 "MontoItem": "500"
            #             }
            #         },
            #         "FechaHoraFirma": "17-02-2025 10:00:00"
            #     }
            # }
            json32_res = {}
            if rec.l10n_latam_document_type_id.code == '32':
                if self.l10n_xma_json_bol == True:
                    json_m = yaml.load(self.l10n_xma_json)['data']
                else:
                    json_m = json_m

                json32_res = {
                    "RFCE": {
                        "Encabezado": {
                        "Version": "1.0",
                        "IdDoc": {
                            "TipoeCF": "32",
                            "eNCF": json_m['ECF']['Encabezado']['IdDoc']['eNCF'],
                            "TipoIngresos": json_m['ECF']['Encabezado']['IdDoc']['TipoIngresos'],
                            "TipoPago": json_m['ECF']['Encabezado']['IdDoc']['TipoPago']
                        },
                        "Emisor": {
                            "RNCEmisor": json_m['ECF']['Encabezado']['Emisor']['RNCEmisor'],
                            "RazonSocialEmisor": json_m['ECF']['Encabezado']['Emisor']['RazonSocialEmisor'],
                            "FechaEmision": json_m['ECF']['Encabezado']['Emisor']['FechaEmision']
                        },
                        "Comprador": {
                            "RNCComprador": json_m['ECF']['Encabezado']['Comprador']['RNCComprador'] if 'RNCComprador' in json_m['ECF']['Encabezado']['Comprador'] else '' ,
                            "IdentificadorExtranjero": json_m['ECF']['Encabezado']['Comprador']['IdentificadorExtranjero'] if 'IdentificadorExtranjero' in json_m['ECF']['Encabezado']['Comprador'] else '',
                            "RazonSocialComprador": json_m['ECF']['Encabezado']['Comprador']['RazonSocialComprador']
                        },
                        "Totales": {
                            "MontoGravadoTotal": json_m['ECF']['Encabezado']['Totales']['MontoGravadoTotal'] if 'MontoGravadoTotal' in json_m['ECF']['Encabezado']['Totales'] else '',
                            "MontoGravadoI1": json_m['ECF']['Encabezado']['Totales']['MontoGravadoI1'] if 'MontoGravadoI1' in json_m['ECF']['Encabezado']['Totales'] else '',
                            "MontoGravadoI2": json_m['ECF']['Encabezado']['Totales']['MontoGravadoI2'] if 'MontoGravadoI2' in json_m['ECF']['Encabezado']['Totales'] else '',
                            "MontoGravadoI3": json_m['ECF']['Encabezado']['Totales']['MontoGravadoI3'] if 'MontoGravadoI3' in json_m['ECF']['Encabezado']['Totales'] else '',
                            "TotalITBIS": json_m['ECF']['Encabezado']['Totales']['TotalITBIS'] if 'TotalITBIS' in json_m['ECF']['Encabezado']['Totales'] else '',
                            "TotalITBIS1": json_m['ECF']['Encabezado']['Totales']['TotalITBIS1'] if 'TotalITBIS1' in json_m['ECF']['Encabezado']['Totales'] else '',
                            "TotalITBIS2": json_m['ECF']['Encabezado']['Totales']['TotalITBIS2'] if 'TotalITBIS2' in json_m['ECF']['Encabezado']['Totales'] else '',
                            "TotalITBIS3": json_m['ECF']['Encabezado']['Totales']['TotalITBIS3'] if 'TotalITBIS3' in json_m['ECF']['Encabezado']['Totales'] else '',
                            "MontoTotal": json_m['ECF']['Encabezado']['Totales']['MontoTotal'] if 'MontoTotal' in json_m['ECF']['Encabezado']['Totales'] else '',
                        },
                        "CodigoSeguridadeCF": json_m['ECF']['Encabezado']['IdDoc']['CodigoSeguridadeeCF'] if 'CodigoSeguridadeeCF' in json_m['ECF']['Encabezado']['IdDoc'] else '',
                        },
                        
                    }
                    }
                if MontoGravadoI1 == 0:
                    json32_res['RFCE']['Encabezado']['Totales'].pop('MontoGravadoI1')
                    json32_res['RFCE']['Encabezado']['Totales'].pop('TotalITBIS1')
                if MontoGravadoI2 == 0:
                    json32_res['RFCE']['Encabezado']['Totales'].pop('MontoGravadoI2')
                    json32_res['RFCE']['Encabezado']['Totales'].pop('TotalITBIS2')
                if count_itbs3 == 0:
                    json32_res['RFCE']['Encabezado']['Totales'].pop('MontoGravadoI3')
                    json32_res['RFCE']['Encabezado']['Totales'].pop('TotalITBIS3')

            flag = False
            if self.l10n_latam_document_type_id.code != '32':
                flag = False
            else:
                if self.amount_total_do < 250000 and self.l10n_xma_require_resume == True:
                    flag = True
                elif self.amount_total_do < 250000 and self.l10n_xma_require_resume == False:
                    flag = False



            # if rec.l10n_latam_document_type_id.code != '32':
            #     json32_res = {}
            json_m = self.clean_json_accents(json_m)
            json32_res = self.clean_json_accents(json32_res)
            _logger.info(f"\n\nJSON LIMPIO:     {json32_res}\n\n")
            # _logger.info(f"\n\nJSON LIMPIO:     {self.limpiar_diccionario(json_m)}\n\n")
            cert = str(self.company_id.xma_key_p12).replace("b'","").replace("'","")
            entorno = self.company_id.l10n_xma_type_env_do
            json_complete = {
                "id":self.id,
                "uuid_client":self.company_id.uuid_client,
                "data":json_m,
                "data_resume":json32_res,
                "rfc":self.company_id.vat,
                "prod": 'NO' if self.company_id.l10n_xma_test else 'SI',
                "type": 'FD',
                "pac_invoice": self.company_id.l10n_xma_type_pac,
                "cert": f'{cert}',
                "password": self.company_id.xma_key_p12_password,
                "type_env": entorno,
                "is_conditional_doc": flag,
                "total": self.amount_total_do,
            }
            print(f"\n\nJSON RES:     {json32_res}")
            print(f"\n\nJSON RES LIMPIO:     {self.limpiar_diccionario(json32_res)}\n\n")
            print(json_complete)
            return json_m,json_complete
            
            
    def remove_accents(self, text):
        if not isinstance(text, str):
            return text
            
        replacements = {
            'á': 'a', 'à': 'a', 'ã': 'a', 'â': 'a', 'ä': 'a',
            'é': 'e', 'è': 'e', 'ê': 'e', 'ë': 'e',
            'í': 'i', 'ì': 'i', 'î': 'i', 'ï': 'i',
            'ó': 'o', 'ò': 'o', 'õ': 'o', 'ô': 'o', 'ö': 'o',
            'ú': 'u', 'ù': 'u', 'û': 'u', 'ü': 'u',
            'ý': 'y', 'ÿ': 'y',
            'ñ': 'n',
            'Á': 'A', 'À': 'A', 'Ã': 'A', 'Â': 'A', 'Ä': 'A',
            'É': 'E', 'È': 'E', 'Ê': 'E', 'Ë': 'E',
            'Í': 'I', 'Ì': 'I', 'Î': 'I', 'Ï': 'I',
            'Ó': 'O', 'Ò': 'O', 'Õ': 'O', 'Ô': 'O', 'Ö': 'O',
            'Ú': 'U', 'Ù': 'U', 'Û': 'U', 'Ü': 'U',
            'Ý': 'Y',
            'Ñ': 'N'
        }
        
        for a, n in replacements.items():
            text = text.replace(a, n)
        return text

    def clean_json_accents(self, data):
        if isinstance(data, dict):
            return {k: self.clean_json_accents(v) for k, v in data.items()}
        elif isinstance(data, list):
            return [self.clean_json_accents(item) for item in data]
        elif isinstance(data, str):
            return self.remove_accents(data)
        else:
            return data

            
    def limpiar_diccionario(self, diccionario):
        if not isinstance(diccionario, dict):
            return diccionario

        def esta_vacio(valor):
            if valor is None:
                return True
            if isinstance(valor, str) and not valor.strip():
                return True
            if isinstance(valor, (list, dict)) and not valor:
                return True
            return False

        resultado = {}
        for key, value in diccionario.items():
            # Mantener CodigoSeguridadeCF sin importar su valor
            if key == 'CodigoSeguridadeCF':
                resultado[key] = value
                continue
                
            # Si es un diccionario anidado
            if isinstance(value, dict):
                valor_limpio = self.limpiar_diccionario(value)
                if not esta_vacio(valor_limpio):
                    resultado[key] = valor_limpio
            # Si es una lista
            elif isinstance(value, list):
                if value:  # Si la lista no está vacía
                    resultado[key] = value
            # Otros tipos de valores
            elif not esta_vacio(value):
                resultado[key] = value

        return resultado




    
    def send_to_matrix_json_do(self):
        for rec in self:
            
            def convert_json_to_xml(json_data):
                xml_data = ET.Element('root')
                _json_to_xml(json_data, xml_data)
                xml_string = ET.tostring(xml_data, encoding='utf-8', method='xml')
                return xml_string.decode('utf-8')

            def _json_to_xml(json_data, parent):
                if isinstance(json_data, dict):
                    for key, value in json_data.items():
                        if isinstance(value, dict):
                            element = ET.SubElement(parent, key)
                            _json_to_xml(value, element)
                        elif isinstance(value, list):
                            for item in value:
                                element = ET.SubElement(parent, key)
                                _json_to_xml(item, element)
                        else:
                            element = ET.SubElement(parent, key)
                            element.text = str(value)
                elif isinstance(json_data, list):
                    for item in json_data:
                        _json_to_xml(item, parent)
                else:
                    parent.text = str(json_data)
            json_m,xml_json_do = rec.generate_json_l10n_do()
            xml = convert_json_to_xml(json_m)
            _logger.info(f"\n json NORMAL: {xml_json_do} \n json manual {rec.l10n_xma_json} \n  {type(rec.l10n_xma_json)}")
            xml_json = ''
            if rec.l10n_xma_json_bol == True:
                xml_json = {"DO": yaml.load(rec.l10n_xma_json)}
            else:
                xml_json = {"DO": xml_json_do}
            company = rec.get_company()
            uuid = company.company_name
            rfc = rec.company_id.partner_id.vat
            country = rec.company_id.partner_id.country_id.code.lower()
            version = self.env['ir.module.module'].search([('name', '=', 'xma_core')]).latest_version
            xml_json = {"from":uuid, "data":xml_json, "file_name": rec.l10n_xma_file_name, "TipoeCF": int(rec.l10n_latam_document_type_id.code), "odoo_version": str(version)}
            # _logger.info(f"JSON DO: {xml_json}")
            mqtt_client = MqttClient("api.xmarts.com", 1883, prefix=f"uuid/{uuid}/rfc/{rfc}/country/{country}/", encryption_key=company.key)
            # xml_json = json.dumps(xml_json)
            # print("send_to_matrix_json_do",xml_json)
            _logger.info(f"uuid/{uuid}/rfc/{rfc}/country/{country}/stamp")
            mqtt_client.send_message_serialized(
                [xml_json],
                f"uuid/{uuid}/rfc/{rfc}/country/{country}/stamp", 
                valid_json=True, 
                secure=True
            )

    def l10n_xma_consult_track_id(self):
        cert = str(self.company_id.xma_key_p12).replace("b'","").replace("'","")
        entorno = self.company_id.l10n_xma_type_env_do
        xml_json = {
            'id': self.id,
            'rfc': self.company_id.partner_id.vat,
            'track_id': self.l10n_xma_track_id,
            "cert": f'{cert}',
            "password": self.company_id.xma_key_p12_password,
            "type_env":entorno,
        }

        company = self.get_company()
        uuid = company.company_name
        rfc = self.company_id.partner_id.vat
        country = self.company_id.partner_id.country_id.code.lower()
        version = self.env['ir.module.module'].search([('name', '=', 'xma_core')]).latest_version
        xml_json = {"from":uuid, "data":xml_json, "odoo_version": str(version)}
        mqtt_client = MqttClient("api.xmarts.com", 1883, prefix=f"uuid/{uuid}/rfc/{rfc}/country/{country}/", encryption_key=company.key)
        # xml_json = json.dumps(xml_json)
        _logger.info(f"uuid/{uuid}/rfc/{rfc}/country/{country}/consult")
        mqtt_client.send_message_serialized(
            [xml_json],
            f"uuid/{uuid}/rfc/{rfc}/country/{country}/consult", 
            valid_json=True, 
            secure=True
        )
    
    def l10n_xma_micro_ping(self):
        xml_json = {
            'id': self.id,
        }
        company = self.get_company()
        uuid = company.company_name
        rfc = self.company_id.partner_id.vat
        country = self.company_id.partner_id.country_id.code.lower()
        mqtt_client = MqttClient("api.xmarts.com", 1883, prefix=f"uuid/{uuid}/rfc/{rfc}/country/{country}/", encryption_key=company.key)
        _logger.info(f"uuid/{uuid}/rfc/{rfc}/country/{country}/ping")
        mqtt_client.send_message_serialized(
            [xml_json],
            f"uuid/{uuid}/rfc/{rfc}/country/{country}/ping", 
            valid_json=True, 
            secure=True
        )
        # pong = mqtt_client.send_message_serialized(
        #     [xml_json],
        #     f"uuid/{uuid}/rfc/{rfc}/country/{country}/ping", 
        #     valid_json=True, 
        #     secure=True
        # )
        # for rc in pong:
        #     if rc != 0:
        #         print("PELIGRO ", rc)
        #         mqtt_client.client.loop_stop()
        #         mqtt_client.client.disconnect()
        #         time.sleep(2)
        #         xml_json = {
        #             'id': self.id,
        #         }
        #         company = self.get_company()
        #         uuid = company.company_name
        #         rfc = self.company_id.partner_id.vat
        #         country = self.company_id.partner_id.country_id.code.lower()
        #         mqtt_client = MqttClient("api.xmarts.com", 1883, prefix=f"uuid/{uuid}/rfc/{rfc}/country/{country}/", encryption_key=company.key)
        #         _logger.info(f"uuid/{uuid}/rfc/{rfc}/country/{country}/ping")
        #         pong = mqtt_client.send_message_serialized(
        #             [xml_json],
        #             f"uuid/{uuid}/rfc/{rfc}/country/{country}/ping", 
        #             valid_json=True, 
        #             secure=True
        #         )
        #         _logger.info(f"Reconectando {rc}---{country}--{xml_json}")

class TypePaymentsLines(models.Model):
    _name = 'type.payments.lines'


    payment_id = fields.Many2one('xma_payment.form', string="Forma de Pago")
    move_id = fields.Many2one('account.move')
    payment_amount = fields.Float(string="Monto del pago")

class ImportCSVDO(models.Model):
    _name = 'l10n_xma.import.csv'

    name = fields.Char( string="Name", default="New")

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', 'New') == 'New':
                vals['name'] = self.env['ir.sequence'].next_by_code(
                    'l10n_xma.import.csv') or 'New'
        return super(ImportCSVDO, self).create(vals_list)

    l10n_xma_file = fields.Binary(
        string="Archivo CSV",
    )

    company_id = fields.Many2one(
        'res.company',
        compute="get_country_id_from_company",
        string="Company",
    )

    account_move_count_out_invoice= fields.Integer(
        compute="get_account_move_count_out_invoice",
        string="count inv"
    )

    account_move_count_out_refund = fields.Integer(
        compute="get_account_move_count_out_refund",
        string="count inv"
    )

    account_move_count_in_invoice = fields.Integer(
        compute="get_account_move_count_in_invoice",
        string="count inv"
    )
    def get_account_move_count_out_invoice(self):
        account_move = self.env['account.move'].search([('l10n_xma_import_id', '=', self.id), ('move_type', '=', 'out_invoice')])
        self.account_move_count_out_invoice = len(account_move)
    
    def action_account_move_entry_out_invoice(self):
        view_id = self.env.ref('account.view_out_invoice_tree').id
        form = self.env.ref('account.view_move_form').id
        return { 
            'name': "Facturas",
            'type': 'ir.actions.act_window',
            'view_type': 'tree,form',
            'res_model': 'account.move',
            'domain': [('l10n_xma_import_id', '=', self.id), ('move_type', '=', 'out_invoice')],
            'views': [(view_id, 'tree'), (form, 'form')],
            'target': 'current'
        }
    
    def get_account_move_count_out_refund(self):
        account_move = self.env['account.move'].search([('l10n_xma_import_id', '=', self.id), ('move_type', '=', 'out_refund')])
        self.account_move_count_out_refund = len(account_move)
    
    def action_account_move_entry_out_refund(self):
        view_id = self.env.ref('account.view_out_credit_note_tree').id
        form = self.env.ref('account.view_move_form').id
        return { 
            'name': "Facturas",
            'type': 'ir.actions.act_window',
            'view_type': 'tree,form',
            'res_model': 'account.move',
            'domain': [('l10n_xma_import_id', '=', self.id), ('move_type', '=', 'out_refund')],
            'views': [(view_id, 'tree'), (form, 'form')],
            'target': 'current'
        }
    
    def get_account_move_count_in_invoice(self):
        account_move = self.env['account.move'].search([('l10n_xma_import_id', '=', self.id), ('move_type', '=', 'in_invoice')])
        self.account_move_count_in_invoice = len(account_move)
    
    def action_account_move_entry_in_invoice(self):
        view_id = self.env.ref('account.view_in_invoice_bill_tree').id
        form = self.env.ref('account.view_move_form').id
        return { 
            'name': "Facturas",
            'type': 'ir.actions.act_window',
            'view_type': 'tree,form',
            'res_model': 'account.move',
            'domain': [('l10n_xma_import_id', '=', self.id), ('move_type', '=', 'in_invoice')],
            'views': [(view_id, 'tree'), (form, 'form')],
            'target': 'current'
        }

    @api.model
    def get_country_id_from_company(self):
        for rec in self:
            rec.company_id = self.env.company.id
    
    def get_mx_current_datetime_do_all(self, date):
        return fields.Datetime.context_timestamp(
            self.with_context(tz='America/Santo_Domingo'), date)
    def delete_none_or_false(self, _dict):
        if isinstance(_dict, dict):
            for key, value in list(_dict.items()):
                if isinstance(value, (list, dict, tuple, set)):
                    _dict[key] = self.delete_none_or_false(value)
                elif value is False or key is False or value is None or key is None:
                    del _dict[key]

        elif isinstance(_dict, (list, set, tuple)):
            _dict = type(_dict)(self.delete_none_or_false(item) for item in _dict if item is not False)

        return _dict
    def eliminar_claves_vacias(self, data):
        if isinstance(data, dict):
            for clave, valor in list(data.items()):
                if isinstance(valor, list) and not valor:
                    data.pop(clave)
                elif isinstance(valor, dict):
                    self.eliminar_claves_vacias(valor)
                    if not valor:
                        data.pop(clave)
        return data     
    def limpiar_diccionario(self, data):
        if isinstance(data, dict):
            for clave, valor in list(data.items()):
                if isinstance(valor, list) and not valor:
                    data.pop(clave)
                elif isinstance(valor, dict):
                    self.limpiar_diccionario(valor)
                    if not valor:
                        data.pop(clave)
                elif valor is None or valor == {}:
                    data.pop(clave)
        return data      
    def import_csv(self):
        if not self.l10n_xma_file:
            return
        fileb64 = base64.b64decode(self.l10n_xma_file)
        file_data = io.StringIO(fileb64.decode('utf-8'))
        df = pd.read_csv(file_data)
        data = df.to_dict(orient='records')

        data = [{k.strip(): v for k, v in row.items() if v != '#e'} for row in data]
        for data_original in data:
            # if data_original.get('ENCF') == 'E310000000006':
            time_invoice = self.get_mx_current_datetime_do_all(datetime.now())
            impuestos_adicionales_t = []
            iat = 1
            while True:
                tipo_impuesto_t = data_original.get(f'TipoImpuesto[{iat}]', 0)
                if not tipo_impuesto_t:
                    break
                ampuestoadicional = {
                    "ImpuestoAdicional":{
                        "TipoImpuesto": tipo_impuesto_t,
                        "TasaImpuestoAdicional": data_original.get(f'TasaImpuestoAdicional[{iat}]', 0),
                        "MontoImpuestoSelectivoConsumoEspecifico": data_original.get(f'MontoImpuestoSelectivoConsumoEspecifico[{iat}]', 0.0),
                        "MontoImpuestoSelectivoConsumoAdvalorem": data_original.get(f'MontoImpuestoSelectivoConsumoAdvalorem[{iat}]', 0.0),
                        "OtrosImpuestosAdicionales": data_original.get(f'OtrosImpuestosAdicionales[{iat}]', 0.0),
                    }
                }
                if data_original.get(f'TasaImpuestoAdicional[{iat}]', 0.0) == 0.0:
                    ampuestoadicional['ImpuestoAdicional'].pop('TasaImpuestoAdicional', None)
                if data_original.get(f'MontoImpuestoSelectivoConsumoEspecifico[{iat}]', 0.0) == 0.0:
                    ampuestoadicional['ImpuestoAdicional'].pop('MontoImpuestoSelectivoConsumoEspecifico', None)
                if data_original.get(f'MontoImpuestoSelectivoConsumoAdvalorem[{iat}]', 0.0) == 0.0:
                    ampuestoadicional['ImpuestoAdicional'].pop('MontoImpuestoSelectivoConsumoAdvalorem', None)
                if data_original.get(f'OtrosImpuestosAdicionales[{iat}]', 0.0) == 0.0:
                    ampuestoadicional['ImpuestoAdicional'].pop('OtrosImpuestosAdicionales', None)

                impuestos_adicionales_t.append(ampuestoadicional)
                iat+=1
            name_xml = str(data_original.get('RNCEmisor', False)) + data_original.get('ENCF', False)
            data_transformada = {
                "ECF": {
                    "Encabezado": {
                        "Version": str(data_original.get('Version', False)),
                        "IdDoc": {
                            "TipoeCF": str(data_original.get('TipoeCF', False)),
                            "eNCF": data_original.get('ENCF', False),
                            "IndicadorNotaCredito": int(data_original.get('IndicadorNotaCredito', 0)) if data_original.get('IndicadorNotaCredito') else False,
                            "FechaVencimientoSecuencia": data_original.get('FechaVencimientoSecuencia', False),                
                            "IndicadorMontoGravado": data_original.get('IndicadorMontoGravado', False),
                            "TipoIngresos": data_original.get('TipoIngresos', False),
                            "TipoPago": data_original.get('TipoPago', False),
                            "FechaLimitePago": data_original.get('FechaLimitePago', False),
                            "TerminoPago": data_original.get('TerminoPago', False),
                            "TablaFormasPago": [{
                                "FormaDePago": {
                                    "FormaPago": int(data_original.get('FormaPago[1]', False)),
                                    "MontoPago": '%.2f' % float(data_original.get('MontoPago[1]', 0.0)),
                                }
                            }] if data_original.get('FormaPago[1]', False) else [],
                            "TipoCuentaPago": str(data_original.get('TipoCuentaPago', False)) if data_original.get('TipoCuentaPago') else None,
                            "NumeroCuentaPago": str(data_original.get('NumeroCuentaPago', False)) if data_original.get('NumeroCuentaPago') else None,
                            "BancoPago": str(data_original.get('BancoPago', False)) if data_original.get('BancoPago') else None,
                        },
                        "Emisor": {
                            "RNCEmisor": str(data_original.get('RNCEmisor', False)) if data_original.get('RNCEmisor') else None,
                            "RazonSocialEmisor": data_original.get('RazonSocialEmisor', False) if data_original.get('RazonSocialEmisor') else None,
                            "NombreComercial": data_original.get('NombreComercial', False) if data_original.get('NombreComercial') else None,
                            "DireccionEmisor": data_original.get('DireccionEmisor', False) if data_original.get('DireccionEmisor') else None,
                            "Municipio": str(data_original.get('Municipio', False)).zfill(6) if data_original.get('Municipio') else None,
                            "Provincia": str(data_original.get('Provincia', False)).zfill(6) if data_original.get('Provincia') else None,
                            "TablaTelefonoEmisor": [
                                {"TelefonoEmisor": data_original.get('TelefonoEmisor[1]', False)},
                                {"TelefonoEmisor": data_original.get('TelefonoEmisor[2]', False)}
                            ] if data_original.get('TelefonoEmisor[1]', False) or data_original.get('TelefonoEmisor[2]', False) else [],
                            "CorreoEmisor": data_original.get('CorreoEmisor', False) if data_original.get('CorreoEmisor') else None,
                            "WebSite": data_original.get('WebSite', False) if data_original.get('WebSite') else None,
                            "CodigoVendedor": data_original.get('CodigoVendedor', False) if data_original.get('CodigoVendedor') else None,
                            "NumeroFacturaInterna": data_original.get('NumeroFacturaInterna', False) if data_original.get('NumeroFacturaInterna') else None,
                            "NumeroPedidoInterno": int(data_original.get('NumeroPedidoInterno', False)) if data_original.get('NumeroPedidoInterno') else None,
                            "ZonaVenta": data_original.get('ZonaVenta', False) if data_original.get('ZonaVenta') else None,
                            "FechaEmision": data_original.get('FechaEmision', False) if data_original.get('FechaEmision') else None
                        },
                        "Comprador": {
                            "RNCComprador": data_original.get('RNCComprador', False) if data_original.get('RNCComprador') else None,
                            "IdentificadorExtranjero": data_original.get('IdentificadorExtranjero', False) if data_original.get('IdentificadorExtranjero') else None,
                            "RazonSocialComprador": data_original.get('RazonSocialComprador', False) if data_original.get('RazonSocialComprador') else None,
                            "ContactoComprador": data_original.get('ContactoComprador', False) if data_original.get('ContactoComprador') else None,
                            "CorreoComprador": data_original.get('CorreoComprador', False) if data_original.get('CorreoComprador') else None,
                            "DireccionComprador": data_original.get('DireccionComprador', False) if data_original.get('DireccionComprador') else None,
                            "MunicipioComprador": str(data_original.get('MunicipioComprador', False)).zfill(6) if data_original.get('MunicipioComprador') else None,
                            "ProvinciaComprador": str(data_original.get('ProvinciaComprador', False)).zfill(6) if data_original.get('ProvinciaComprador') else None,
                            "FechaEntrega": data_original.get('FechaEntrega', False) if data_original.get('FechaEntrega') else None,
                            "ContactoEntrega": data_original.get('ContactoEntrega', False) if data_original.get('ContactoEntrega') else None,
                            "DireccionEntrega": data_original.get('DireccionEntrega', False) if data_original.get('DireccionEntrega') else None,
                            "TelefonoAdicional": data_original.get('TelefonoAdicional', False) if data_original.get('TelefonoAdicional') else None,
                            "FechaOrdenCompra": data_original.get('FechaOrdenCompra', False) if data_original.get('FechaOrdenCompra') else None,
                            "NumeroOrdenCompra": data_original.get('NumeroOrdenCompra', False) if data_original.get('NumeroOrdenCompra') else None,
                            "CodigoInternoComprador": data_original.get('CodigoInternoComprador', False) if data_original.get('CodigoInternoComprador') else None
                        },
                        "InformacionesAdicionales": {
                            "FechaEmbarque": data_original.get('FechaEmbarque', False) if data_original.get('FechaEmbarque') else None,
                            "NumeroEmbarque": data_original.get('NumeroEmbarque', False) if data_original.get('NumeroEmbarque') else None,
                            "NumeroContenedor": data_original.get('NumeroContenedor') if data_original.get('NumeroContenedor') else None,
                            "NumeroReferencia": data_original.get('NumeroReferencia', False) if data_original.get('NumeroReferencia') else None,
                            "NombrePuertoEmbarque": data_original.get('NombrePuertoEmbarque', False) if data_original.get('NombrePuertoEmbarque') else None,
                            "CondicionesEntrega": data_original.get('CondicionesEntrega', False) if data_original.get('CondicionesEntrega') else None,
                            "TotalFob": '%.2f' % float(data_original.get('TotalFob', 0.0)) if data_original.get('TotalFob') else None,
                            "Seguro": '%.2f' % float(data_original.get('Seguro', 0.0)) if data_original.get('Seguro') else None,
                            "Flete": '%.2f' % float(data_original.get('Flete', 0.0)) if data_original.get('Flete') else None,
                            "TotalCif": '%.2f' % float(data_original.get('TotalCif', 0.0)) if data_original.get('TotalCif') else None,
                            "RegimenAduanero": data_original.get('RegimenAduanero', False) if data_original.get('RegimenAduanero') else None,
                            "NombrePuertoSalida": data_original.get('NombrePuertoSalida', False) if data_original.get('NombrePuertoSalida') else None,
                            "NombrePuertoDesembarque": data_original.get('NombrePuertoDesembarque', False) if data_original.get('NombrePuertoDesembarque') else None,
                            "PesoBruto": '%.2f' % float(data_original.get('PesoBruto', 0.0)) if data_original.get('PesoBruto') else None,
                            "PesoNeto": '%.2f' % float(data_original.get('PesoNeto', 0.0)) if data_original.get('PesoNeto') else None,
                            "UnidadPesoBruto": int(data_original.get('UnidadPesoBruto', 0)) if data_original.get('UnidadPesoBruto') else None,
                            "UnidadPesoNeto": int(data_original.get('UnidadPesoNeto', 0)) if data_original.get('UnidadPesoNeto') else None,
                            "CantidadBulto": '%.2f' % float(data_original.get('CantidadBulto', 0.0)) if data_original.get('CantidadBulto') else None,
                            "UnidadBulto": int(data_original.get('UnidadBulto', 0)) if data_original.get('UnidadBulto') else None,
                            "VolumenBulto": int (float(data_original.get('VolumenBulto', 0.00))) if data_original.get('VolumenBulto') else None,
                            "UnidadVolumen": int(data_original.get('UnidadVolumen', 0)) if data_original.get('UnidadVolumen') else None,
                        },
                        "Transporte": {
                            "ViaTransporte": data_original.get('ViaTransporte', False) if data_original.get('ViaTransporte') else None,
                            "PaisOrigen": data_original.get('PaisOrigen', False) if data_original.get('PaisOrigen') else None,
                            "DireccionDestino": data_original.get('DireccionDestino', False) if data_original.get('DireccionDestino') else None,
                            "PaisDestino": data_original.get('PaisDestino', False) if data_original.get('PaisDestino') else None,
                            "NumeroAlbaran": data_original.get('NumeroAlbaran', False) if data_original.get('NumeroAlbaran') else None,
                        },
                        "Totales": {
                            "MontoGravadoTotal": data_original.get('MontoGravadoTotal', False) if data_original.get('MontoGravadoTotal') else None,
                            "MontoGravadoI1": data_original.get('MontoGravadoI1', False) if data_original.get('MontoGravadoI1') else None,
                            "MontoGravadoI2": data_original.get('MontoGravadoI2', False) if data_original.get('MontoGravadoI2') else None,
                            "MontoGravadoI3": data_original.get('MontoGravadoI3', False) if data_original.get('MontoGravadoI3') else None,
                            "MontoExento": data_original.get('MontoExento', False) if data_original.get('MontoExento') else None,
                            "ITBIS1": data_original.get('ITBIS1', False) if data_original.get('ITBIS1') else None,
                            "ITBIS2": data_original.get('ITBIS2', False) if data_original.get('ITBIS2') else None,
                            "ITBIS3": data_original.get('ITBIS3', False) if data_original.get('ITBIS3') else None,
                            "TotalITBIS": '%.2f' % float(data_original.get('TotalITBIS', 0.00)) if data_original.get('TotalITBIS') else None,
                            "TotalITBIS1": '%.2f' % float(data_original.get('TotalITBIS1', 0.00)) if data_original.get('TotalITBIS1') else None,
                            "TotalITBIS2": '%.2f' % float(data_original.get('TotalITBIS2', 0.00)) if data_original.get('TotalITBIS2') else None,
                            "TotalITBIS3": '%.2f' % float(data_original.get('TotalITBIS3', 0.00)) if data_original.get('TotalITBIS3') else None,
                            "MontoImpuestoAdicional": '%.2f' % float(data_original.get('MontoImpuestoAdicional', 0.0)) if data_original.get('MontoImpuestoAdicional') else None,
                            "ImpuestosAdicionales": impuestos_adicionales_t if impuestos_adicionales_t else None,
                            "MontoTotal": '%.2f' % float(data_original.get('MontoTotal', 0.00)),
                            "MontoNoFacturable": '%.2f' % float(data_original.get('MontoNoFacturable', False)) if data_original.get('MontoNoFacturable') else None,
                            "MontoPeriodo": '%.2f' % float(data_original.get('MontoPeriodo', False)) if data_original.get('MontoPeriodo') else None,
                            "ValorPagar": '%.2f' % float(data_original.get('ValorPagar', False)) if data_original.get('ValorPagar') else None,
                            "TotalITBISRetenido": '%.2f' % float(data_original.get('TotalITBISRetenido', False)) if data_original.get('TotalITBISRetenido') else None,
                            "TotalISRRetencion": '%.2f' % float(data_original.get('TotalISRRetencion', False)) if data_original.get('TotalISRRetencion') else None,
                        }
                    },
                    "DetallesItems": [],
                    "DescuentosORecargos": [],
                    "InformacionReferencia": {
                        "NCFModificado": data_original.get('NCFModificado', False) if data_original.get('NCFModificado') else None,
                        "FechaNCFModificado": data_original.get('FechaNCFModificado', False) if data_original.get('FechaNCFModificado') else None,
                        "CodigoModificacion": data_original.get('CodigoModificacion', False) if data_original.get('CodigoModificacion') else None,
                        "RazonModificacion": data_original.get('RazonModificacion', False) if data_original.get('RazonModificacion') else None,
                    },
                    "FechaHoraFirma": time_invoice.strftime('%d-%m-%Y %H:%M:%S')
                },
            }
            if not data_original.get('IdentificadorExtranjero', False):
                data_transformada["ECF"]["Encabezado"]["Comprador"].pop("IdentificadorExtranjero", None)
            if not data_original.get('FechaEntrega', False) or data_original.get('FechaEntrega', False) == False:
                data_transformada["ECF"]["Encabezado"]["Comprador"].pop("FechaEntrega", None)
            if not data_original.get('DireccionEntrega', False) or data_original.get('DireccionEntrega', False) == False:
                data_transformada["ECF"]["Encabezado"]["Comprador"].pop("DireccionEntrega", None)
            if not data_original.get('TelefonoAdicional', False) or data_original.get('TelefonoAdicional', False) == False:
                data_transformada["ECF"]["Encabezado"]["Comprador"].pop("TelefonoAdicional", None)
            if data_original.get('TerminoPago', False) == False:
                data_transformada["ECF"]["Encabezado"]["IdDoc"].pop("TerminoPago", None)
            if not data_original.get('TipoCuentaPago'):
                data_transformada["ECF"]["Encabezado"]["IdDoc"].pop("TipoCuentaPago", None)
            if not data_original.get('NumeroCuentaPago'):
                data_transformada["ECF"]["Encabezado"]["IdDoc"].pop("NumeroCuentaPago", None)
            if not data_original.get('BancoPago'):
                data_transformada["ECF"]["Encabezado"]["IdDoc"].pop("BancoPago", None)
            if data_transformada.get('TipoeCF', False) == '43':
                data_transformada['ECF']['Encabezado'].pop('Comprador', None)

            if not data_original.get('NumeroPedidoInterno'):
                data_transformada["ECF"]["Encabezado"]["Emisor"].pop("NumeroPedidoInterno", None)
            if not impuestos_adicionales_t:
                data_transformada["ECF"]["Encabezado"]["Totales"].pop('ImpuestosAdicionales')
            try:
                monto_pago = float(data_original.get('MontoPago[1]', 0.0))
            except ValueError:
                monto_pago = 0.0
            if monto_pago == 0.0:
                data_transformada["ECF"]["Encabezado"]["IdDoc"].pop("TablaFormasPago")
            
            # if data_transformada.get('TipoeCF', False) not in ('33','34'):
            #     data_transformada["ECF"].pop('InformacionReferencia')
            
            # if  float(data_original.get('MontoGravadoTotal', False)) == 0.0:
            #     data_transformada["ECF"]["Encabezado"]["Totales"].pop('MontoGravadoTotal')
            # if float(data_original.get('MontoGravadoI1', False)) == 0.0:
            #     data_transformada["ECF"]["Encabezado"]["Totales"].pop('MontoGravadoI1')
            # if float(data_original.get('MontoGravadoI2', False)) == 0.0:
            #     data_transformada["ECF"]["Encabezado"]["Totales"].pop('MontoGravadoI2')
            # if float(data_original.get('MontoGravadoI3', False)) == 0.0:
            #     data_transformada["ECF"]["Encabezado"]["Totales"].pop('MontoGravadoI3')
            # if float(data_original.get('MontoExento', False)) == 0.0:
            #     data_transformada["ECF"]["Encabezado"]["Totales"].pop('MontoExento')
            # if float(data_original.get('ITBIS1', False)) == 0.0:
            #     data_transformada["ECF"]["Encabezado"]["Totales"].pop('ITBIS1')
            # if float(data_original.get('ITBIS2', False)) == 0.0:
            #     data_transformada["ECF"]["Encabezado"]["Totales"].pop('ITBIS2')
            # if not data_original.get('TotalITBIS', False):
            #     data_transformada["ECF"]["Encabezado"]["Totales"].pop('TotalITBIS')
            # if float(data_original.get('MontoGravadoI3', False)) <= 0.0:
            #     data_transformada["ECF"]["Encabezado"]["Totales"].pop('ITBIS3')
            #     data_transformada["ECF"]["Encabezado"]["Totales"].pop('TotalITBIS3')
            # if float(data_original.get('MontoImpuestoAdicional', 0.0)) == 0.0:
            #     data_transformada["ECF"]["Encabezado"]["Totales"].pop('MontoImpuestoAdicional')
            # if float(data_original.get('TotalITBIS1', False)) == 0.0:
            #     data_transformada["ECF"]["Encabezado"]["Totales"].pop('TotalITBIS1')
            # if float(data_original.get('TotalITBIS2', False)) == 0.0:
            #     data_transformada["ECF"]["Encabezado"]["Totales"].pop('TotalITBIS2')
            # print(data_original.get('MontoTotal'), '-----------------------------------------')
            # if float(data_original.get('MontoNoFacturable', False)) == 0.0:
            #     data_transformada["ECF"]["Encabezado"]["Totales"].pop('MontoNoFacturable')
            # if float(data_original.get('MontoPeriodo', False)) == 0.0:
            #     data_transformada["ECF"]["Encabezado"]["Totales"].pop('MontoPeriodo')
            # if float(data_original.get('ValorPagar', False)) == 0.0:
            #     data_transformada["ECF"]["Encabezado"]["Totales"].pop('ValorPagar')
            # if float(data_original.get('TotalITBISRetenido', False)) == 0.0:
            #     data_transformada["ECF"]["Encabezado"]["Totales"].pop('TotalITBISRetenido')
            # if float(data_original.get('TotalISRRetencion', False)) == 0.0:
            #     data_transformada["ECF"]["Encabezado"]["Totales"].pop('TotalISRRetencion')
            if not data_original.get('MontoGravadoTotal'):
                data_transformada["ECF"]["Encabezado"]["Totales"].pop('MontoGravadoTotal', None)
            if not data_original.get('MontoGravadoI1'):
                data_transformada["ECF"]["Encabezado"]["Totales"].pop('MontoGravadoI1', None)
            if not data_original.get('MontoGravadoI2'):
                data_transformada["ECF"]["Encabezado"]["Totales"].pop('MontoGravadoI2', None)
            if not data_original.get('MontoGravadoI3'):
                data_transformada["ECF"]["Encabezado"]["Totales"].pop('MontoGravadoI3', None)
            if not data_original.get('MontoExento'):
                data_transformada["ECF"]["Encabezado"]["Totales"].pop('MontoExento', None)
            if not data_original.get('ITBIS1'):
                data_transformada["ECF"]["Encabezado"]["Totales"].pop('ITBIS1', None)
            if not data_original.get('ITBIS2'):
                data_transformada["ECF"]["Encabezado"]["Totales"].pop('ITBIS2', None)
            if not data_original.get('TotalITBIS'):
                data_transformada["ECF"]["Encabezado"]["Totales"].pop('TotalITBIS', None)
            if not data_original.get('MontoImpuestoAdicional'):
                data_transformada["ECF"]["Encabezado"]["Totales"].pop('MontoImpuestoAdicional', None)
            if not data_original.get('TotalITBIS1'):
                data_transformada["ECF"]["Encabezado"]["Totales"].pop('TotalITBIS1', None)
            if not data_original.get('TotalITBIS2'):
                data_transformada["ECF"]["Encabezado"]["Totales"].pop('TotalITBIS2', None)
            if not data_original.get('MontoNoFacturable'):
                data_transformada["ECF"]["Encabezado"]["Totales"].pop('MontoNoFacturable', None)
            if not data_original.get('MontoPeriodo'):
                data_transformada["ECF"]["Encabezado"]["Totales"].pop('MontoPeriodo', None)
            if not data_original.get('ValorPagar'):
                data_transformada["ECF"]["Encabezado"]["Totales"].pop('ValorPagar', None)
            if not data_original.get('TotalITBISRetenido'):
                data_transformada["ECF"]["Encabezado"]["Totales"].pop('TotalITBISRetenido', None)
            if not data_original.get('TotalISRRetencion'):
                data_transformada["ECF"]["Encabezado"]["Totales"].pop('TotalISRRetencion', None)

            # Casos especiales
            if not data_original.get('MontoGravadoI3'):
                data_transformada["ECF"]["Encabezado"]["Totales"].pop('ITBIS3', None)
                data_transformada["ECF"]["Encabezado"]["Totales"].pop('TotalITBIS3', None)
            
            # Items 
            for de in range(1, len(data_original) + 1):
                if f'TipoAjuste[{de}]' not in data_original:
                    continue
                lineas = {
                    "NumeroLinea": de,
                    "TipoAjuste": data_original.get(f'TipoAjuste[{de}]', False),
                    "DescripcionDescuentooRecargo": data_original.get(f'DescripcionDescuentooRecargo[{de}]', 0),
                    "TipoValor": data_original.get(f'TipoValor[{de}]', False),
                    "ValorDescuentooRecargo": data_original.get(f'ValorDescuentooRecargo[{de}]', 0.0),
                    "MontoDescuentooRecargo": data_original.get(f'MontoDescuentooRecargo[{de}]', 0),
                    "IndicadorFacturacionDescuentooRecargo": data_original.get(f'IndicadorFacturacionDescuentooRecargo[{de}]', 0),
                }
                if not data_original.get(f'ValorDescuentooRecargo[{de}]', 0.0) or data_original.get(f'ValorDescuentooRecargo[{de}]', 0.0) == 0.0:
                    lineas.pop('ValorDescuentooRecargo', None)
                data_transformada["ECF"]["DescuentosORecargos"].append({"DescuentoORecargo": lineas})
            for i in range(1, len(data_original) + 1):
                if f'MontoItem[{i}]' not in data_original:
                    continue
                subdescuentos = []
                j = 1
                while True:
                    tipo_subdescuento = data_original.get(f'TipoSubDescuento[{i}][{j}]')
                    if not tipo_subdescuento:
                        break
                    if tipo_subdescuento == '$':
                        subdescuento = {
                            "SubDescuento": {
                                "TipoSubDescuento": tipo_subdescuento,
                                "MontoSubDescuento": data_original.get(f'MontoSubDescuento[{i}][{j}]', 0),
                            }
                        }
                    else:
                        subdescuento = {
                            "SubDescuento": {
                                "TipoSubDescuento": tipo_subdescuento,
                                "SubDescuentoPorcentaje": data_original.get(f'SubDescuentoPorcentaje[{i}][{j}]', 0),
                                "MontoSubDescuento": data_original.get(f'MontoSubDescuento[{i}][{j}]', 0),
                            }
                        }
                    subdescuentos.append(subdescuento)
                    j += 1
                
                # Manejo de subrecargos
                subrecargos = []
                k = 1
                while True:
                    tipo_subrecargo = data_original.get(f'TipoSubRecargo[{i}][{k}]')
                    if not tipo_subrecargo:
                        break
                    if tipo_subrecargo == '$':
                        subrecargo = {
                            "SubRecargo": {
                                "TipoSubRecargo": tipo_subrecargo,
                                "MontoSubRecargo": data_original.get(f'MontosubRecargo[{i}][{k}]', 0.0),
                            }
                        }
                    else:
                        subrecargo = {
                            "SubRecargo": {
                                "TipoSubRecargo": tipo_subrecargo,
                                "SubRecargoPorcentaje": data_original.get(f'SubRecargoPorcentaje[{i}][{k}]', 0.0),
                                "MontosubRecargo": data_original.get(f'MontosubRecargo[{i}][{k}]', 0.0),
                            }
                        }
                    subrecargos.append(subrecargo)
                    k += 1
                
                #Manejo de Subcantidad

                subcantidad = []
                l = 1
                while True:
                    cantidad_subcantidad = data_original.get(f'Subcantidad[{i}][{l}]')
                    if not cantidad_subcantidad:
                        break
                    subcantidades = {
                        "SubcantidadItem": {
                            "Subcantidad": '%.3f' % float(cantidad_subcantidad),
                            "CodigoSubcantidad": int(data_original.get(f'CodigoSubcantidad[{i}][{l}]', 0)),
                        }
                    }
                    subcantidad.append(subcantidades)
                    l += 1
                
                tipoimpuesto = []
                im = 1
                while True:
                    tipo_impuesto = data_original.get(f'TipoImpuesto[{i}][{im}]', 0)
                    if not tipo_impuesto:
                        break
                    tipoimpuestos = {
                        "ImpuestoAdicional": {
                            "TipoImpuesto": tipo_impuesto,
                        }
                    }
                    tipoimpuesto.append(tipoimpuestos)
                    im += 1
                qty_item = 0
                if str(data_original.get('TipoeCF')) == '34':
                    qty_item = int(float(data_original.get(f'CantidadItem[{i}]', 0.0)))
                else:
                    qty_item = '%.2f' % float(data_original.get(f'CantidadItem[{i}]', 0.0))
                item = {
                    "NumeroLinea": i,
                    "IndicadorFacturacion": data_original.get(f'IndicadorFacturacion[{i}]', False),
                    "Retencion":{
                        "IndicadorAgenteRetencionoPercepcion": data_original.get(f'IndicadorAgenteRetencionoPercepcion[1]', False),
                        "MontoITBISRetenido": '%.2f' % float(data_original.get(f'MontoITBISRetenido[1]', 0.0)),
                        "MontoISRRetenido": '%.2f' % float(data_original.get(f'MontoISRRetenido[1]', 0.0)),
                    },
                    "NombreItem": data_original.get(f'NombreItem[{i}]'),
                    "IndicadorBienoServicio": int(data_original.get(f'IndicadorBienoServicio[{i}]', False)),
                    "DescripcionItem": data_original.get(f'DescripcionItem[{i}]', False),
                    "CantidadItem": qty_item,
                    "UnidadMedida": int(data_original.get(f'UnidadMedida[{i}]', 0)),
                    "CantidadReferencia": int(data_original.get(f'CantidadReferencia[{i}]', 0)),
                    "UnidadReferencia": int(data_original.get(f'UnidadReferencia[{i}]', 0)),
                    "TablaSubcantidad": subcantidad,
                    "GradosAlcohol" : '%.2f' %  float(data_original.get(f'GradosAlcohol[{i}]', 0.0)),
                    "PrecioUnitarioReferencia": '%.2f' %  float(data_original.get(f'PrecioUnitarioReferencia[{i}]', 0.0)),
                    "PrecioUnitarioItem": '%.2f' %  float(data_original.get(f'PrecioUnitarioItem[{i}]', 0.0)),
                    "DescuentoMonto": '%.2f' % float(data_original.get(f'DescuentoMonto[{i}]', 0.0)),                                
                    "TablaSubDescuento": subdescuentos,
                    "RecargoMonto": '%.2f' % float(data_original.get(f'RecargoMonto[{i}]', 0.0)),
                    "TablaSubRecargo":subrecargos,
                    "TablaImpuestoAdicional": tipoimpuesto,
                    "MontoItem": '%.2f' %  float(data_original.get(f'MontoItem[{i}]', 0.0))
                }
                if not data_original.get(f'MontoITBISRetenido[1]', False):
                    item['Retencion'].pop('MontoITBISRetenido', None)
                if not data_original.get(f'MontoISRRetenido[1]', False):
                    item['Retencion'].pop('MontoISRRetenido', None)
                if not subcantidad:
                    item.pop("TablaSubcantidad", None)
                if not tipoimpuesto:
                    item.pop("TablaImpuestoAdicional")
                # _logger.info(f" Item Descuento {float(item['DescuentoMonto'])}, \n  Item Recargo {float(item['RecargoMonto'])}, \n  MontoITBISRetenido {float(data_original.get(f'MontoITBISRetenido[1]', 0))}, \n  MontoISRRetenido {float(data_original.get(f'MontoISRRetenido[1]', 0))}")
                if float(item['DescuentoMonto']) == 0.0:
                    item.pop('DescuentoMonto')
                    item.pop('TablaSubDescuento')
                if float(item['RecargoMonto']) == 0.0:
                    item.pop('RecargoMonto')
                    item.pop('TablaSubRecargo')
                if float(data_original.get(f'MontoITBISRetenido[1]', 0)) == 0.0 and float(data_original.get(f'MontoISRRetenido[1]', 0)) == 0.0:
                    item.pop('Retencion')
                if  float(data_original.get(f'CantidadReferencia[{i}]', 0.0)) == 0.0:
                    item.pop('CantidadReferencia')
                if int(data_original.get(f'UnidadReferencia[{i}]', 0)) == 0:
                    item.pop('UnidadReferencia')
                if float(data_original.get(f'GradosAlcohol[{i}]', 0.0)) == 0.0:
                    item.pop('GradosAlcohol')
                if float(data_original.get(f'PrecioUnitarioReferencia[{i}]', 0.0)) == 0.0:
                    item.pop('PrecioUnitarioReferencia')
                data_transformada["ECF"]["DetallesItems"].append({"Item": item})
                
            
            # print(data_transformada["ECF"]["Encabezado"].get("DescuentosORecargos", False), bool(data_transformada["ECF"]["Encabezado"].get("InformacionesAdicionales")), bool(data_transformada["ECF"]["Encabezado"].get("Transporte")))
            # if data_transformada["ECF"]["Encabezado"].get("DescuentosORecargos", False) == False:
            #     data_transformada["ECF"]["Encabezado"].pop("DescuentosORecargos", None)
            # if data_transformada["ECF"]["Encabezado"].get("InformacionesAdicionales", False) == False:
            #     data_transformada["ECF"]["Encabezado"].pop("InformacionesAdicionales", None)
            # if data_transformada["ECF"]["Encabezado"].get("Transporte", False) == False:
            #     data_transformada["ECF"]["Encabezado"].pop("Transporte", None)
            data_transformada = self.eliminar_claves_vacias(data_transformada)
            data_transformada = self.limpiar_diccionario(data_transformada)
            # print("\n", data_transformada)
            # flag = False
            # if data_original.get('TipoeCF') != '32':
            #     flag = False
            # else:
            #     print("ELSE: ", float(data_original.get('MontoTotal')) )
            #     if float(data_original.get('MontoTotal')) < 250000:
            #         flag = True
            # print(data_original.get('TipoeCF'), float(data_original.get('MontoTotal')), flag)
            #     print("Generando JSON para ECF Tipo 32")
            
            json32_res = ''
            if str(data_original.get('TipoeCF')) == '32':
                json32_res = {
                    "RFCE": {
                        "Encabezado": {
                        "Version": "1.0",
                        "IdDoc": {
                            "TipoeCF": "32",
                            "eNCF": data_transformada['ECF']['Encabezado']['IdDoc']['eNCF'],
                            "TipoIngresos": data_transformada['ECF']['Encabezado']['IdDoc']['TipoIngresos'],
                            "TipoPago": data_transformada['ECF']['Encabezado']['IdDoc']['TipoPago']
                        },
                        "Emisor": {
                            "RNCEmisor": data_transformada['ECF']['Encabezado']['Emisor']['RNCEmisor'],
                            "RazonSocialEmisor": data_transformada['ECF']['Encabezado']['Emisor']['RazonSocialEmisor'],
                            "FechaEmision": data_transformada['ECF']['Encabezado']['Emisor']['FechaEmision']
                        },
                        "Comprador": {
                            "RNCComprador": data_transformada['ECF']['Encabezado']['Comprador']['RNCComprador'],
                            "IdentificadorExtranjero": data_transformada['ECF']['Encabezado']['Comprador']['IdentificadorExtranjero'] if 'IdentificadorExtranjero' in data_transformada['ECF']['Encabezado']['Comprador'] else {},
                            "RazonSocialComprador": data_transformada['ECF']['Encabezado']['Comprador']['RazonSocialComprador']
                        },
                        "Totales": {
                            "MontoGravadoTotal": data_transformada['ECF']['Encabezado']['Totales']['MontoGravadoTotal'] if 'MontoGravadoTotal' in data_transformada['ECF']['Encabezado']['Totales'] else {},
                            "MontoGravadoI1": data_transformada['ECF']['Encabezado']['Totales']['MontoGravadoI1'] if 'MontoGravadoI1' in data_transformada['ECF']['Encabezado']['Totales'] else {},
                            "MontoGravadoI2": data_transformada['ECF']['Encabezado']['Totales']['MontoGravadoI2'] if 'MontoGravadoI2' in data_transformada['ECF']['Encabezado']['Totales'] else {},
                            "MontoGravadoI3": data_transformada['ECF']['Encabezado']['Totales']['MontoGravadoI3'] if 'MontoGravadoI3' in data_transformada['ECF']['Encabezado']['Totales'] else {},
                            "TotalITBIS": data_transformada['ECF']['Encabezado']['Totales']['TotalITBIS'] if 'TotalITBIS' in data_transformada['ECF']['Encabezado']['Totales'] else {},
                            "TotalITBIS1": data_transformada['ECF']['Encabezado']['Totales']['TotalITBIS1'] if 'TotalITBIS1' in data_transformada['ECF']['Encabezado']['Totales'] else {},
                            "TotalITBIS2": data_transformada['ECF']['Encabezado']['Totales']['TotalITBIS2'] if 'TotalITBIS2' in data_transformada['ECF']['Encabezado']['Totales'] else {},
                            "TotalITBIS3": data_transformada['ECF']['Encabezado']['Totales']['TotalITBIS3'] if 'TotalITBIS3' in data_transformada['ECF']['Encabezado']['Totales'] else {},
                            "MontoTotal": data_transformada['ECF']['Encabezado']['Totales']['MontoTotal'] if 'MontoTotal' in data_transformada['ECF']['Encabezado']['Totales'] else {},
                        },
                        "CodigoSeguridadeCF": ""
                        },
                        
                    }
                }
                if not data_transformada['ECF']['Encabezado']['Totales'].get('MontoGravadoI3'):
                    json32_res['RFCE']['Encabezado']['Totales'].pop('MontoGravadoI3', None)
                    json32_res['RFCE']['Encabezado']['Totales'].pop('TotalITBIS3', None)
                if not data_transformada['ECF']['Encabezado']['Totales'].get('MontoGravadoI2'):
                    json32_res['RFCE']['Encabezado']['Totales'].pop('MontoGravadoI2', None)
                if not data_transformada['ECF']['Encabezado']['Totales'].get('MontoGravadoI1'):
                    json32_res['RFCE']['Encabezado']['Totales'].pop('MontoGravadoI1', None)
                if not data_transformada['ECF']['Encabezado']['Totales'].get('MontoGravadoTotal'):
                    json32_res['RFCE']['Encabezado']['Totales'].pop('MontoGravadoTotal', None)
                if not data_transformada['ECF']['Encabezado']['Totales'].get('TotalITBIS'):
                    json32_res['RFCE']['Encabezado']['Totales'].pop('TotalITBIS', None)
                if not data_transformada['ECF']['Encabezado']['Totales'].get('TotalITBIS1'):
                    json32_res['RFCE']['Encabezado']['Totales'].pop('TotalITBIS1', None)
                if not data_transformada['ECF']['Encabezado']['Totales'].get('TotalITBIS2'):
                    json32_res['RFCE']['Encabezado']['Totales'].pop('TotalITBIS2', None)

            json32_res = self.eliminar_claves_vacias(json32_res)
            json32_res = self.limpiar_diccionario(json32_res)

            cert = str(self.company_id.xma_key_p12).replace("b'","").replace("'","")
            entorno = self.company_id.l10n_xma_type_env_do

            

            partner_id = self.env['res.partner'].search(['|',('vat', '=', data_original.get('RNCComprador')),('vat', '!=', False)], limit=1)
            product_id = self.env['product.product'].search(['|',('name', '=', data_original.get('NombreItem[1]')), ('name', '!=', False)], limit=1)
            move_type = ''
            pront = str(data_original.get('TipoeCF', False))
            if pront in ('31', '32', '33', '44', '45', '46'):
                move_type = 'out_invoice'
            if pront == '34':
                move_type = 'out_refund'
            if pront in ('41', '43', '47'):
                move_type = 'in_invoice'
            vals = {
                'partner_id': partner_id.id,
                'move_type': move_type,
                'ref': data_original.get('ENCF', False),
                # 'l10n_mx_edi_usage': partner_id.l10n_mx_edi_usage_partner,
                'l10n_xma_file_name': name_xml,
                'l10n_xma_date_post': datetime.now(),
                # 'journal_id': 
                # 'sale_line_ids_agroup': [(4, 0, sale_lines)],
                # 'invoice_payment_term_id': partner_id.property_payment_term_id.id,
                'state': 'draft',
                'l10n_xma_import_id': self.id,
                'invoice_date': datetime.now(),
                'l10n_latam_document_type_id': self.env['l10n_latam.document.type'].search([('code', '=', data_original.get('TipoeCF', False))], limit=1).id,
                'invoice_line_ids': [
                    (0, 0, {
                        'product_id':product_id.id ,
                        'quantity': 1,
                        'price_unit': data_original.get('MontoItem[1]'),
                        'name': data_original.get('NombreItem[1]'),
                        # 'tax_ids': [(6, 0, [self.env.ref('l10n_do_itbis_18').id])],
                    }),
                ],
            }
            account_move = self.env['account.move']
            move = account_move.with_context(
                with_company=self.company_id,
                force_user_id=self.env.uid).create(vals)

            json_complete = {
                "id":move.id,
                "uuid_client": self.company_id.uuid_client,
                "data":data_transformada,
                "data_resume":json32_res,
                "rfc":self.company_id.vat,
                "prod": 'NO' if self.company_id.l10n_xma_test else 'SI',
                "type": 'FD',
                "pac_invoice": self.company_id.l10n_xma_type_pac,
                "cert": f'{cert}',
                "password": self.company_id.xma_key_p12_password,
                "type_env": entorno,
                "is_conditional_doc": False,
                "total": data_original.get('MontoTotal'),
            }

            json_without_false = self.delete_none_or_false(json_complete)
            json_without_false.update({
                'is_conditional_doc': False
            })

            json_new = json.dumps(json_without_false, indent=4)
            move.write({
                'l10n_xma_json':json_new,
                'l10n_xma_json_bol': True,
            })
            move.action_post()
            # move.send_to_matrix_json_do()