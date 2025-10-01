# -*- coding: utf-8 -*-
from odoo import fields, models, api, _
import json
from lxml.objectify import fromstring
import base64
from datetime import datetime, timedelta
from odoo.tools import float_round
from odoo.exceptions import AccessDenied, UserError, ValidationError
import time
import re
from random import choice, randint
from xml.etree import ElementTree as ET
from io import BytesIO, StringIO
from xml.dom import minidom
import qrcode
from num2words import num2words
from MqttLibPy.client import MqttClient
import logging
import re
from decorator import decorator
from odoo.http import request
import zoneinfo
_logger = logging.getLogger(__name__)

class AccountMove(models.Model):
    _inherit = "account.move"
    
    
    def button_send_to_matrix_json_br(self):
        self.send_to_matrix_json_br()
        time.sleep(1)
        self.env.flush_all()
        self.refresh_account_move_xma()
        return True 
    
    def send_to_matrix_json_br(self):
        xml_json_br = False   
        print(f"CODE CODE CODE {self.l10n_latam_document_type_id.code}")
        if not self.xma_l10n_latam_document_number:
            self.xma_l10n_latam_document_number = self.l10n_latam_document_type_id.l10n_xma_current_number
            self.l10n_latam_document_type_id.l10n_xma_current_number = self.l10n_latam_document_type_id.l10n_xma_next_number
            self.l10n_latam_document_type_id.l10n_xma_next_number += 1
        if self.xma_l10n_latam_document_number and self.l10n_latam_document_type_id.l10n_xma_resequence_document:
            self.xma_l10n_latam_document_number = self.l10n_latam_document_type_id.l10n_xma_current_number
            self.l10n_latam_document_type_id.l10n_xma_current_number = self.l10n_latam_document_type_id.l10n_xma_next_number
            self.l10n_latam_document_type_id.l10n_xma_next_number += 1
        current_dt = datetime.now()
        date_time = fields.Datetime.context_timestamp(self.with_context(tz=self.env.user.tz), current_dt)
        self.l10n_xma_date_post = current_dt
        date_post_tz = fields.Datetime.context_timestamp(self.with_context(tz=self.env.user.tz), self.l10n_xma_date_post).strftime("%Y-%m-%dT%H:%M:%S")
        print(f"CURRENT DATETIME :::    {date_time} {self.l10n_xma_date_post} {date_post_tz}")
        # time_invoice = date_time
        if self.l10n_latam_document_type_id.code == 'SE':
            xml_json_br = self.generate_json_l10n_br_nfse()
        if self.l10n_latam_document_type_id.code in ['55', '65']: 
            xml_json_br = self.generate_json_l10n_br_nfe()
        if self.l10n_latam_document_type_id.code == '57':
            xml_json_br = self.generate_json_l10n_br_cte()
        json_str = json.dumps(xml_json_br, indent=4)
        print(f"JSON BRASIL \n {json_str}")
        _logger.info(f"BRASIL JSON ||||||||||||||||||||||||||||||\n{json_str}\n||||||||||||||||||||||||||||||||||||||||||||||||")
        xml_json = {"BR": xml_json_br}
        company = self.get_company()
        uuid = company.company_name
        rfc = re.sub(r'\D', '', self.company_id.partner_id.vat)
        country = self.company_id.partner_id.country_id.code.lower()
        xml_json = {"from":uuid, "data":xml_json}
        mqtt_client = MqttClient("api.xmarts.com", 1883, prefix=f"uuid/{uuid}/rfc/{rfc}/country/{country}/", encryption_key=company.key)
        mqtt_client.send_message_serialized(
            [xml_json],
            f"uuid/{uuid}/rfc/{rfc}/country/{country}/stamp", 
            valid_json=True, 
            secure=True
        )

        self.env.cr.commit()
        time.sleep(2) 
        return True
    
    def xma_get_last_atachment_xml(self, invoice_id=False):
        if invoice_id:
            adjuntos = self.env['ir.attachment'].search([
                ('res_model', '=', 'account.move'),
                ('res_id', '=', invoice_id.id),
                ('name', '=', invoice_id.name + '.xml')
            ])
            adjuntos_ordenados = adjuntos.sorted(key=lambda x: x.create_date, reverse=True)
            if adjuntos_ordenados:
                return adjuntos_ordenados[0]
            else:
                return None
        else:
            return None
        
    @api.onchange('l10n_related_move_id')
    def onchange_l10n_related_move_id(self):
        for rec in self:
            if rec.l10n_related_move_id:
                rec.l10n_xma_delivery_date = rec.l10n_related_move_id.delivery_date
        
    def generate_json_l10n_br_cte(self):
        for rec in self:
            # print(f"DATA SALE ORDER AND INVOICES: {rec.xma_get_related_sale_order()}")
            # sale_id, invoice_id = rec.xma_get_related_sale_order()
            # zona_brasil = zoneinfo.ZoneInfo("America/Sao_Paulo")
            # time_invoice = datetime.now(zona_brasil)
            # str_time = time_invoice.strftime('%Y-%m-%dT%H:%M:%S')
            move_xml = False
            bxml = False
            if rec.l10n_related_move_id:
                move_xml = rec.xma_get_last_atachment_xml(rec.l10n_related_move_id)
                bxml = base64.decodebytes(move_xml.datas)
                root = ET.fromstring(bxml.decode('utf-8'))
                
                ns = {'nfe': 'http://www.portalfiscal.inf.br/nfe'}
                serie_nf = root.find('.//nfe:serie', namespaces=ns).text
                nDoc_nf = root.find('.//nfe:nNF', namespaces=ns).text
                dEmi_nf = datetime.strptime(root.find('.//nfe:dhEmi', namespaces=ns).text, "%Y-%m-%dT%H:%M:%S%z").strftime("%Y-%m-%d")
                vBC_nf = root.find('.//nfe:total/nfe:ICMSTot/nfe:vBC', namespaces=ns).text
                vICMS_nf = root.find('.//nfe:total/nfe:ICMSTot/nfe:vICMS', namespaces=ns).text
                vBCST_nf = "" # Consultar con JP
                vST_nf = "" # Consultar con JP
                vProd_nf = root.find('.//nfe:total/nfe:ICMSTot/nfe:vProd', namespaces=ns).text
                vNF_nf = root.find('.//nfe:total/nfe:ICMSTot/nfe:vNF', namespaces=ns).text
                CFOP_nf = "" # Consultar con JP
                peso_nf = "%s" % rec.l10n_xma_weight_nfe #rec.shipping_weight
                dPrev_nf = rec.l10n_related_move_id.delivery_date.strftime("%Y-%m-%d")
                dPrev_nfe = rec.l10n_related_move_id.delivery_date.strftime("%Y-%m-%d")
                chave_nfe = root.find('.//nfe:chNFe', namespaces=ns).text
            else:
                serie_nf = rec.l10n_xma_serie_nf
                nDoc_nf = rec.l10n_xma_nDoc_nf
                dEmi_nf = rec.l10n_xma_dEmi_nf
                vBC_nf = rec.l10n_xma_vBC_nf
                vICMS_nf = rec.l10n_xma_vICMS_nf
                vBCST_nf = ""
                vST_nf = ""
                vProd_nf = rec.l10n_xma_vProd_nf
                vNF_nf = rec.l10n_xma_vNF_nf
                CFOP_nf = ""
                peso_nf = rec.l10n_xma_weight_nfe
                dPrev_nf = rec.l10n_xma_dPrev_nf
                dPrev_nfe = rec.l10n_xma_dPrev_nfe
                chave_nfe = rec.l10n_xma_chave_nfe
                
                dPrev_nf = rec.l10n_xma_delivery_date.strftime("%Y-%m-%d")
                dPrev_nfe = rec.l10n_xma_delivery_date.strftime("%Y-%m-%d")
                
            if rec.l10n_cteant_move_id:    
                xNome_docAnt = rec.l10n_xma_xNome_docAnt
                UF_docAnt = rec.l10n_xma_UF_docAnt
                IE_docAnt = rec.l10n_xma_IE_docAnt
                CPF_docAnt = rec.l10n_xma_CPF_docAnt
                CNPJ_docAnt = rec.l10n_xma_CNPJ_docAnt
                tpDoc_docAnt = rec.l10n_xma_tpDoc_docAnt
                serie_docAnt = rec.l10n_xma_serie_docAnt
                nDoc_docAnt = rec.l10n_xma_nDoc_docAnt
                dEmi_docAnt = rec.l10n_xma_dEmi_docAnt.strftime("%Y-%m-%d")
                chave_docAnt = rec.l10n_xma_chave_docAnt
            else:
                xNome_docAnt = rec.l10n_xma_xNome_docAnt
                UF_docAnt = rec.l10n_xma_UF_docAnt
                IE_docAnt = rec.l10n_xma_IE_docAnt
                CPF_docAnt = rec.l10n_xma_CPF_docAnt
                CNPJ_docAnt = rec.l10n_xma_CNPJ_docAnt
                tpDoc_docAnt = rec.l10n_xma_tpDoc_docAnt
                serie_docAnt = rec.l10n_xma_serie_docAnt
                nDoc_docAnt = rec.l10n_xma_nDoc_docAnt
                dEmi_docAnt = rec.l10n_xma_dEmi_docAnt.strftime("%Y-%m-%d")
                chave_docAnt = rec.l10n_xma_chave_docAnt
                
            ICMS = 0.0
            ICMS_r = 0.0
            ICMS_aliq = 0.0
            for line in rec.invoice_line_ids:
                for tax in line.tax_ids:
                    tax_res = tax.compute_all(line.price_subtotal, currency=line.currency_id)
                    for tax_entry in tax_res['taxes']:
                        if 'ICMS' in tax_entry['name']:
                            if float(tax_entry['amount']) > 0.0:
                                ICMS += tax_entry['amount']
                            if float(tax_entry['amount']) < 0.0:
                                ICMS_r += float(tax_entry['amount']) * -1
                            ICMS_aliq += self.env['account.tax'].search([('id','=',tax_entry['id'])], limit=1).amount
            date_post_tz = fields.Datetime.context_timestamp(self.with_context(tz=self.env.user.tz), self.l10n_xma_date_post).strftime("%Y-%m-%dT%H:%M:%S")
            json_data =  {
                "Documento": {
                    "ModeloDocumento": "Cte",
                    "versao": 4.00,
                    "ide": {
                        "cCT": 11,
                        "cUF": "%s" % rec.company_id.partner_id.l10n_xma_fiscal_unit_code,
                        "natOp": int(rec.l10n_xma_use_document_id.code),
                        "CFOP": 5352, #Revisar de donde toma este codigo
                        "mod": "57", # Modelo CTe
                        "serie": "%s" % rec.xma_l10n_document_serie,
                        "nCT": "%s" % rec.xma_l10n_latam_document_number,
                        "dhEmi": "%s" % date_post_tz,
                        "fusoHorario": "-03:00",
                        "tpImp": 1,
                        "tpEmis": "%s" % rec.l10n_xma_issuance_type_id.code,#Forma de Emissão
                        "tpAmb": 2 if rec.company_id.l10n_xma_test == True else 1,
                        "tpCTe": 0,
                        "procEmi": 0,
                        "indGlobalizado": 0,
                        "refCTE": "",
                        "cMunEnv": "%s" % rec.company_id.partner_id.l10n_xma_municipality_id.code,
                        "xMunEnv": "%s" % rec.company_id.partner_id.l10n_xma_municipality_id.name,
                        "UFEnv": "%s" % rec.company_id.partner_id.state_id.code,
                        "modal": "01",
                        "tpServ": rec.l10n_xma_tipo_servicio,
                        "cMunIni": "%s" % rec.company_id.partner_id.l10n_xma_municipality_id.code,
                        "xMunIni": "%s" % rec.company_id.partner_id.l10n_xma_municipality_id.name,
                        "UFIni": "RS",
                        "cMunFim": "%s" % rec.partner_id.l10n_xma_municipality_id.code,
                        "xMunFim": "%s" % rec.partner_id.l10n_xma_municipality_id.name,
                        "UFFim": "%s" % rec.partner_id.state_id.code,
                        "retira": 0,
                        "xDetRetira": "Retirar o pacote no local de entrega indicado", #Mensaje personalizado par el retiro o nota de entrega
                        "indIEToma": 9,
                        "dhCont": "0000-00-00T00:00:00",
                        "xJust": "",
                        "EmailArquivos": "",
                        "tomador": {
                            "toma": "4",
                            "CNPJ_toma": "", #"%s" % re.sub(r'\D', '', rec.l10n_xma_tomador_id.vat),
                            "CPF_toma": "%s" % rec.l10n_xma_tomador_id.l10n_br_cpf_code,
                            "IE_toma": "", #"%s" % (rec.partner_id.l10n_br_ie_code if rec.partner_id.l10n_br_ie_code else ""),
                            "xNome_toma": "%s" % rec.l10n_xma_tomador_id.name,
                            "xFant_toma": "%s" % rec.l10n_xma_tomador_id.commercial_name if rec.l10n_xma_tomador_id.commercial_name else rec.l10n_xma_tomador_id.name,
                            "fone_toma": "%s" % rec.l10n_xma_tomador_id.phone if rec.l10n_xma_tomador_id.phone else "",
                            "email_toma": "%s" % rec.l10n_xma_tomador_id.email if rec.l10n_xma_tomador_id.email else "",
                            "enderTomador": {
                                "xLgr_toma": "%s" % rec.l10n_xma_tomador_id.street,
                                "nro_toma": "%s" % rec.l10n_xma_tomador_id.l10n_xma_external_number if rec.l10n_xma_tomador_id.l10n_xma_external_number else "",
                                "xCpl_toma": "",
                                "xBairro_toma": "%s" % rec.l10n_xma_tomador_id.street2,
                                "cMun_toma": "%s" % rec.l10n_xma_tomador_id.l10n_xma_municipality_id.code,
                                "xMun_toma": "%s" % rec.l10n_xma_tomador_id.l10n_xma_municipality_id.name,
                                "CEP_toma": "%s" % re.sub(r'\D', '', rec.l10n_xma_tomador_id.zip),
                                "UF_toma": "%s" % rec.l10n_xma_tomador_id.state_id.code,
                                "cPais_toma": "%s" % rec.l10n_xma_tomador_id.country_id.l10n_xma_bacen_country_code,
                                "xPais_toma": "%s" % rec.l10n_xma_tomador_id.country_id.name,
                            }
                        }
                    },
                    "emit": {
                        "CNPJ_emit": "%s" % re.sub(r'\D', '', rec.company_id.partner_id.vat),
                        "IE": "%s" % (rec.company_id.l10n_br_ie_code if rec.company_id.l10n_br_ie_code else ""),
                        "IEST": "",
                        "xNome": "%s" % rec.company_id.name,
                        "xFant": "%s" % (rec.company_id.partner_id.commercial_name or rec.company_id.name),
                        "CRT": "%s" % rec.company_id.partner_id.l10n_xma_taxpayer_type_id.code,
                        "enderEmit": {
                            "xLgr": "%s" % rec.company_id.partner_id.street,
                            "nro": "%s" % rec.company_id.partner_id.l10n_xma_external_number,
                            "xCpl": "",
                            "xBairro": "%s" % rec.company_id.partner_id.street2,
                            "cMun": "%s" % rec.company_id.partner_id.l10n_xma_municipality_id.code,
                            "xMun": "%s" % rec.company_id.partner_id.l10n_xma_municipality_id.name,
                            "CEP": "%s" % re.sub(r'\D', '', rec.company_id.partner_id.zip),
                            "UF": "%s" % rec.company_id.partner_id.state_id.code,
                            "fone": "%s" % rec.company_id.partner_id.phone,
                        }
                    },
                    "rem": {
                        "CNPJ_rem": "%s" % re.sub(r'\D', '', rec.company_id.partner_id.vat),
                        "CPF_rem": "",
                        "IE_rem": "%s" % (rec.company_id.l10n_br_ie_code if rec.company_id.l10n_br_ie_code else ""),
                        "xNome_rem": "%s" % rec.company_id.name if rec.company_id.l10n_xma_test != True else "CTE EMITIDO EM AMBIENTE DE HOMOLOGACAO - SEM VALOR FISCAL", #"%s" % rec.company_id.name,
                        "xFant_rem": "%s" % (rec.company_id.partner_id.commercial_name or rec.company_id.name),
                        "fone_rem": "%s" % rec.company_id.partner_id.phone,
                        "email_rem": "%s" % rec.company_id.partner_id.email or "",
                        "enderRem": {
                            "xLgr_rem": "%s" % rec.company_id.partner_id.street,
                            "nro_rem": "%s" % rec.company_id.partner_id.l10n_xma_external_number,
                            "xCpl_rem": "",
                            "xBairro_rem": "%s" % rec.company_id.partner_id.street2,
                            "cMun_rem": "%s" % rec.company_id.partner_id.l10n_xma_municipality_id.code,
                            "xMun_rem": "%s" % rec.company_id.partner_id.l10n_xma_municipality_id.name,
                            "CEP_rem": "%s" % re.sub(r'\D', '', rec.company_id.partner_id.zip),
                            "UF_rem": "%s" % rec.company_id.partner_id.state_id.code,
                            "cPais_rem": "%s" % rec.company_id.partner_id.country_id.l10n_xma_bacen_country_code,
                            "xPais_rem": "%s" % rec.company_id.partner_id.country_id.name,
                        }
                    } if rec.l10n_xma_tipo_servicio != '3' else {},
                    "exped": {
                        "CNPJ_exp": "%s" % re.sub(r'\D', '', rec.l10n_xma_expedidor_id.vat),
                        "CPF_exp": "",
                        "IE_exp":  "%s" % (rec.l10n_xma_expedidor_id.l10n_br_ie_code if rec.l10n_xma_expedidor_id.l10n_br_ie_code else ""),
                        "xNome_exp": "%s" % rec.l10n_xma_expedidor_id.name if rec.company_id.l10n_xma_test != True else "CTE EMITIDO EM AMBIENTE DE HOMOLOGACAO - SEM VALOR FISCAL",
                        "fone_exp": "%s" % rec.l10n_xma_expedidor_id.phone,
                        "email_exp": "%s" % rec.l10n_xma_expedidor_id.email if rec.l10n_xma_expedidor_id.email else "",
                        "enderExped": {
                            "xLgr_exp": "%s" % rec.l10n_xma_expedidor_id.street,
                            "nro_exp": "%s" % rec.l10n_xma_expedidor_id.l10n_xma_external_number,
                            "xCpl_exp": "",
                            "xBairro_exp": "%s" % rec.l10n_xma_expedidor_id.street2,
                            "cMun_exp": "%s" % rec.l10n_xma_expedidor_id.l10n_xma_municipality_id.code,
                            "xMun_exp": "%s" % rec.l10n_xma_expedidor_id.l10n_xma_municipality_id.name,
                            "CEP_exp": "%s" % re.sub(r'\D', '', rec.l10n_xma_expedidor_id.zip),
                            "UF_exp": "%s" % rec.l10n_xma_expedidor_id.state_id.code,
                            "cPais_exp": "%s" % rec.l10n_xma_expedidor_id.country_id.l10n_xma_bacen_country_code,
                            "xPais_exp": "%s" % rec.l10n_xma_expedidor_id.country_id.name,
                        }
                    } if rec.l10n_xma_tipo_servicio == '3' else {},
                    "receb": {
                        "CNPJ_rec": "",
                        "CPF_rec": "%s" % rec.l10n_xma_recibidor_id.l10n_br_cpf_code,
                        "IE_rec": "",
                        "xNome_rec": "%s" % rec.l10n_xma_recibidor_id.name if rec.company_id.l10n_xma_test != True else "CTE EMITIDO EM AMBIENTE DE HOMOLOGACAO - SEM VALOR FISCAL",
                        "fone_rec": "%s" % rec.l10n_xma_recibidor_id.phone if rec.l10n_xma_recibidor_id.phone else "",
                        "email_rec": "%s" % rec.l10n_xma_recibidor_id.email if rec.l10n_xma_recibidor_id.email else "",
                        "enderReceb": {
                            "xLgr_rec": "%s" % rec.l10n_xma_recibidor_id.street,
                            "nro_rec": "%s" % rec.l10n_xma_recibidor_id.l10n_xma_external_number if rec.l10n_xma_recibidor_id.l10n_xma_external_number else "",
                            "xCpl_rec": "",
                            "xBairro_rec": "%s" % rec.l10n_xma_recibidor_id.street2,
                            "cMun_rec": "%s" % rec.l10n_xma_recibidor_id.l10n_xma_municipality_id.code,
                            "xMun_rec": "%s" % rec.l10n_xma_recibidor_id.l10n_xma_municipality_id.name,
                            "CEP_rec": "%s" % re.sub(r'\D', '', rec.l10n_xma_recibidor_id.zip),
                            "UF_rec": "%s" % rec.l10n_xma_recibidor_id.state_id.code,
                            "cPais_rec": "%s" % rec.l10n_xma_recibidor_id.country_id.l10n_xma_bacen_country_code,
                            "xPais_rec": "%s" % rec.l10n_xma_recibidor_id.country_id.name
                        }
                    } if rec.l10n_xma_tipo_servicio == '3' else {},
                    "dest": {
                        "CNPJ_dest": "", #"%s" % re.sub(r'\D', '', rec.partner_id.vat),
                        "CPF_dest": "%s" % rec.partner_id.l10n_br_cpf_code,
                        "IE_dest": "", #"%s" % (rec.partner_id.l10n_br_ie_code if rec.partner_id.l10n_br_ie_code else ""),
                        "xNome_dest": "%s" % rec.partner_id.name,
                        "fone_dest": "%s" % rec.partner_id.phone if rec.partner_id.phone else "",
                        "ISUF_dest": "",
                        "email_dest": "%s" % rec.partner_id.email if rec.partner_id.email else "",
                        "enderDest": {
                            "xLgr_dest": "%s" % rec.partner_id.street,
                            "nro_dest": "%s" % rec.partner_id.l10n_xma_external_number if rec.partner_id.l10n_xma_external_number else "",
                            "xCpl_dest": "",
                            "xBairro_dest": "%s" % rec.partner_id.street2,
                            "cMun_dest": "%s" % rec.partner_id.l10n_xma_municipality_id.code,
                            "xMun_dest": "%s" % rec.partner_id.l10n_xma_municipality_id.name,
                            "CEP_dest": "%s" % re.sub(r'\D', '', rec.partner_id.zip),
                            "UF_dest": "%s" % rec.partner_id.state_id.code,
                            "cPais_dest": "%s" % rec.partner_id.country_id.l10n_xma_bacen_country_code,
                            "xPais_dest": "%s" % rec.partner_id.country_id.name
                        }
                    },
                    "vPrest": {
                        "vTPrest": "%s" % rec.amount_total,
                        "vRec": "0.00"
                    },
                    "imp": {
                        "vTotImp": "%s" % (rec.amount_total - rec.amount_untaxed) ,
                        "vTotTrib": "0.00",
                        "infAdFisco": "Informacoes de interesse do fisco estarão escritas aqui",
                        "ICMS": {
                            "CST": "00",
                            "vBC": rec.amount_untaxed,
                            "pICMS": ICMS_aliq,
                            "vICMS": ICMS,
                            "pRedBC": 0,
                            "vBCSTRet": "0.00",
                            "vICMSSTRet": "0.00",
                            "pICMSSTRet": 0,
                            "vCred": "0.00",
                            "pRedBCOutraUF": 0,
                            "vBCOutraUF": "0.00",
                            "pICMSOutraUF": 0,
                            "vICMSOutraUF": "0.00",
                            "indSN": 1
                        },
                        "ICMSUFFim": {
                            "vBCUFFim": "0.00",
                            "pFCPUFFim": 0,
                            "pICMSUFFim": 0,
                            "pICMSInter": 0,
                            "pICMSInterPart": 0,
                            "vFCPUFFim": "0.00",
                            "vICMSUFIni": "0.00",
                            "vICMSUFFim": "0.00"
                        }
                    },
                    "infCTeNorm": {
                        "infCarga": {
                            "vMerc": "%s" % rec.l10n_xma_valor_carga,
                            "proPred": "%s" % rec.l10n_xma_prod_pred,
                            "xOutCat": "",
                            "vCargaAverb": "%s" % rec.l10n_xma_valor_carga,
                            "infQ": [{
                                    "cUnid": "01",
                                    "tpMed": "KILOGRAMAS",
                                    "qCarga": "%s" % rec.l10n_xma_weight_nfe
                                }
                            ]
                        },
                        "infDoc": [{
                                "tipoDocumento": 2,
                                "nRoma_nf": "",
                                "nPed_nf": "",
                                "mod_nf": "01",
                                "serie_nf": serie_nf,
                                "nDoc_nf": nDoc_nf,
                                "dEmi_nf": dEmi_nf,
                                "vBC_nf": vBC_nf,
                                "vICMS_nf": vICMS_nf,
                                "vBCST_nf": vBCST_nf,
                                "vST_nf": vST_nf,
                                "vProd_nf": vProd_nf,
                                "vNF_nf": vNF_nf,
                                "CFOP_nf": 0,
                                "peso_nf": peso_nf,
                                "PINSuframa_nf": "",
                                "dPrev_nf": dPrev_nf,
                                "chave_nfe": chave_nfe,
                                "PINSuframa_nfe": "",
                                "dPrev_nfe": dPrev_nfe,
                                "tpDoc_outros": "",
                                "desc_outros": "",
                                "nDoc_outros": "",
                                "dEmi_outros": "0000-00-00",
                                "vDocFisc_outros": "0.00",
                                "dPrev_outros": "0000-00-00",
                            }
                        ] if rec.l10n_xma_tipo_servicio != '3' else [],
                        "docAnt": [{
                                "xNome_docAnt": "%s" % xNome_docAnt,#"CTe99000517",
                                "UF_docAnt": "%s" % UF_docAnt,#"RS",
                                "IE_docAnt": "%s" % IE_docAnt,#"0018001360",
                                "CPF_docAnt": "%s" % CPF_docAnt,#"99999999999",
                                "CNPJ_docAnt": "%s" % CNPJ_docAnt,#"06354976000149",
                                "idDocAnt": [{
                                    "idDocAntPap": [{
                                    "tpDoc_docAnt": "%s" % tpDoc_docAnt,#"07",
                                    "serie_docAnt": "%s" % serie_docAnt,#"99",
                                    "nDoc_docAnt": "%s" % nDoc_docAnt,#"517",
                                    "dEmi_docAnt": "%s" % dEmi_docAnt,#"2025-05-14",
                                    "idDocAntEle": {
                                        "chave_docAnt": "%s" % chave_docAnt,#"43250506354976000149570990000005171000000110",
                                        }
                                    }],
                                }],
                        }],
                        "infModal": {
                            "versaoModal": 4.00,
                            "rodo": {
                                "RNTRC": "%s" % rec.l10n_xma_vehicle_licence
                            }
                        },
                    },
                }
            }
            # if not invoice_id:
            #     json_data['Documento']['infCTeNorm'].pop('infDoc')
            # print(json_data)
            json_complete = {
                "id":self.id,
                "uuid_client":self.company_id.uuid_client,
                "data":[json_data],
                "rfc":re.sub(r'\D', '', self.company_id.vat),
                "prod": 'NO' if self.company_id.l10n_xma_test else 'SI',
                "type": 'BF',
                "pac_invoice": self.company_id.l10n_xma_type_pac,
                "signature_key": self.company_id.xma_br_signature_key,
                "partner_key": self.company_id.xma_br_partner_key
            }
            return json_complete

    def generate_json_l10n_br_nfe(self):
        for move in self:

            ISS_tot = 0.0
            INSS_tot = 0.0
            ICMS_tot = 0.0
            ICMS_base = 0.0
            ISSQN_base = 0.0
            IPI_tot = 0.0
            COFINS_tot = 0.0
            sCOFINS_tot = 0.0
            IR_tot = 0.0
            ISSQN_tot = 0.0
            PIS_tot = 0.0
            sPIS_tot = 0.0
            CSLL_tot = 0.0
            IOF_tot = 0.0
            PROD_tot = 0.0
            SERV_tot = 0.0
            II_tot = 0.0
            total_products = 0.0
            have_taxes = False

            plist = []
            for l in move.invoice_line_ids:

                ISS = 0.0
                ISS_r = 0.0
                ISS_aliq = 0.0
                ISS_aliq_r = 0.0

                INSS = 0.0
                INSS_r = 0.0
                INSS_aliq = 0.0
                INSS_aliq_r = 0.0

                ICMS = 0.0
                ICMS_r = 0.0
                ICMS_aliq = 0.0
                ICMS_aliq_r = 0.0

                IPI = 0.0
                IPI_r = 0.0
                IPI_aliq = 0.0
                IPI_aliq_r = 0.0

                COFINS = 0.0
                COFINS_r = 0.0
                COFINS_aliq = 0.0
                COFINS_aliq_r = 0.0

                IR = 0.0
                IR_r = 0.0
                IR_aliq = 0.0
                IR_aliq_r = 0.0

                ISSQN = 0.0
                ISSQN_r = 0.0
                ISSQN_aliq = 0.0
                ISSQN_aliq_r = 0.0

                PIS = 0.0
                PIS_r = 0.0
                PIS_aliq = 0.0
                PIS_aliq_r = 0.0

                CSLL = 0.0
                CSLL_r = 0.0
                CSLL_aliq = 0.0
                CSLL_aliq_r = 0.0

                IOF = 0.0
                IOF_r = 0.0
                IOF_aliq = 0.0
                IOF_aliq_r = 0.0

                II = 0.0
                II_r = 0.0
                II_aliq = 0.0
                II_aliq_r = 0.0

                if l.tax_ids:
                    have_taxes = True

                for tax in l.tax_ids:
                    tax_res = tax.compute_all(l.price_subtotal, currency=l.currency_id)
                    print("TAXES TAXES TAXES TAXES TAXES ---------------------------- \n", tax_res)
                    # {'base_tags': [10], 'taxes': [{'id': 102, 'name': 'ICMS Saída Externo 7%', 'amount': 7.0, 'base': 100.0, 'sequence': 1, 'account_id': 1419, 'analytic': False, 'use_in_tax_closing': True, 'price_include': False, 'tax_exigibility': 'on_invoice', 'tax_repartition_line_id': 390, 'group': None, 'tag_ids': [12], 'tax_ids': []}], 'total_excluded': 100.0, 'total_included': 107.0, 'total_void': 100.0}
                    for tax_entry in tax_res['taxes']:
                        if 'ISS' in tax_entry['name'] and 'ISSQN' not in tax_entry['name']:
                            if float(tax_entry['amount']) > 0.0:
                                ISS += tax_entry['amount']
                                ISS_tot += tax_entry['amount']
                                ISS_aliq += self.env['account.tax'].search([('id','=',tax_entry['id'])], limit=1).amount
                            if float(tax_entry['amount']) < 0.0:
                                ISS_r += float(tax_entry['amount']) * -1
                                ISS_aliq_r += self.env['account.tax'].search([('id','=',tax_entry['id'])], limit=1).amount * -1
                        if 'INSS' in tax_entry['name']:
                            if float(tax_entry['amount']) > 0.0:
                                INSS += tax_entry['amount']
                                INSS_tot += tax_entry['amount']
                                INSS_aliq += self.env['account.tax'].search([('id','=',tax_entry['id'])], limit=1).amount
                            if float(tax_entry['amount']) < 0.0:
                                INSS_r += float(tax_entry['amount']) * -1
                                INSS_aliq_r += self.env['account.tax'].search([('id','=',tax_entry['id'])], limit=1).amount * -1
                        if 'ICMS' in tax_entry['name']:
                            if float(tax_entry['amount']) > 0.0:
                                ICMS += tax_entry['amount']
                                ICMS_tot += tax_entry['amount']
                                ICMS_aliq += self.env['account.tax'].search([('id','=',tax_entry['id'])], limit=1).amount
                            if float(tax_entry['amount']) < 0.0:
                                ICMS_r += float(tax_entry['amount']) * -1
                                ICMS_aliq_r += self.env['account.tax'].search([('id','=',tax_entry['id'])], limit=1).amount * -1
                        if 'IPI' in tax_entry['name']:
                            if float(tax_entry['amount']) > 0.0:
                                IPI += tax_entry['amount']
                                IPI_tot += tax_entry['amount']
                                IPI_aliq += self.env['account.tax'].search([('id','=',tax_entry['id'])], limit=1).amount
                            if float(tax_entry['amount']) < 0.0:
                                IPI_r += float(tax_entry['amount']) * -1
                                IPI_aliq_r += self.env['account.tax'].search([('id','=',tax_entry['id'])], limit=1).amount * -1
                        if 'COFINS' in tax_entry['name']:
                            if float(tax_entry['amount']) > 0.0:
                                COFINS += tax_entry['amount']
                                COFINS_tot += tax_entry['amount'] if l.product_id.type != 'service' else 0
                                sCOFINS_tot += tax_entry['amount'] if l.product_id.type == 'service' else 0
                                COFINS_aliq += self.env['account.tax'].search([('id','=',tax_entry['id'])], limit=1).amount
                            if float(tax_entry['amount']) < 0.0:
                                COFINS_r += float(tax_entry['amount']) * -1
                                COFINS_aliq_r += self.env['account.tax'].search([('id','=',tax_entry['id'])], limit=1).amount * -1
                        if 'IR' in tax_entry['name']:
                            if float(tax_entry['amount']) > 0.0:
                                IR += tax_entry['amount']
                                IR_tot += tax_entry['amount']
                                IR_aliq += self.env['account.tax'].search([('id','=',tax_entry['id'])], limit=1).amount
                            if float(tax_entry['amount']) < 0.0:
                                IR_r += float(tax_entry['amount']) * -1
                                IR_aliq += self.env['account.tax'].search([('id','=',tax_entry['id'])], limit=1).amount * -1
                        if 'ISSQN' in tax_entry['name']:
                            if float(tax_entry['amount']) > 0.0:
                                ISSQN += tax_entry['amount']
                                ISSQN_tot += tax_entry['amount']
                                ISSQN_aliq += self.env['account.tax'].search([('id','=',tax_entry['id'])], limit=1).amount
                            if float(tax_entry['amount']) < 0.0:
                                ISSQN_r += float(tax_entry['amount']) * -1
                                ISSQN_aliq_r += self.env['account.tax'].search([('id','=',tax_entry['id'])], limit=1).amount * -1
                        if 'PIS' in tax_entry['name']:
                            if float(tax_entry['amount']) > 0.0:
                                PIS += tax_entry['amount']
                                PIS_tot += tax_entry['amount'] if l.product_id.type != 'service' else 0
                                sPIS_tot += tax_entry['amount'] if l.product_id.type == 'service' else 0
                                PIS_aliq += self.env['account.tax'].search([('id','=',tax_entry['id'])], limit=1).amount
                            if float(tax_entry['amount']) < 0.0:
                                PIS_r += float(tax_entry['amount']) * -1
                                PIS_aliq_r += self.env['account.tax'].search([('id','=',tax_entry['id'])], limit=1).amount * -1
                        if 'CSLL' in tax_entry['name']:
                            if float(tax_entry['amount']) > 0.0:
                                CSLL += tax_entry['amount']
                                CSLL_tot += tax_entry['amount']
                                CSLL_aliq += self.env['account.tax'].search([('id','=',tax_entry['id'])], limit=1).amount
                            if float(tax_entry['amount']) < 0.0:
                                CSLL_r += float(tax_entry['amount']) * -1
                                CSLL_aliq_r += self.env['account.tax'].search([('id','=',tax_entry['id'])], limit=1).amount * -1
                        if 'IOF' in tax_entry['name']:
                            if float(tax_entry['amount']) > 0.0:
                                IOF += tax_entry['amount']
                                IOF_tot += tax_entry['amount']
                                IOF_aliq += self.env['account.tax'].search([('id','=',tax_entry['id'])], limit=1).amount
                            if float(tax_entry['amount']) < 0.0:
                                IOF_r += float(tax_entry['amount']) * -1
                                IOF_aliq_r += self.env['account.tax'].search([('id','=',tax_entry['id'])], limit=1).amount * -1

                        if 'II' in tax_entry['name']:
                            if float(tax_entry['amount']) > 0.0:
                                II += tax_entry['amount']
                                II_tot += tax_entry['amount']
                                II_aliq += self.env['account.tax'].search([('id','=',tax_entry['id'])], limit=1).amount
                            if float(tax_entry['amount']) < 0.0:
                                II_r += float(tax_entry['amount']) * -1
                                II_aliq_r += self.env['account.tax'].search([('id','=',tax_entry['id'])], limit=1).amount * -1
                
                if l.product_id.type != 'service':
                    if ICMS > 0.0 or IPI > 0 or PIS > 0 or COFINS > 0:
                        ICMS_base += l.price_subtotal
                        PROD_tot += l.quantity
                else:
                    if ISS > 0.0 or PIS > 0.0 or COFINS > 0.0:
                        ISSQN_base += l.price_subtotal
                        SERV_tot += l.quantity
                total_products += l.price_subtotal


                p = {
                    "infADProd": "",
                    "prod": {
                        "cProd": "%s" % l.product_id.default_code,
                        "cEAN": "SEM GTIN",#"%s" % l.product_id.barcode,
                        "xProd": "NOTA FISCAL EMITIDA EM AMBIENTE DE HOMOLOGACAO - SEM VALOR FISCAL" if move.company_id.l10n_xma_test == True else "%s" % l.product_id.name,
                        "NCM": "%s" % re.sub(r'\D', '',l.product_id.xma_ncm_code_id.code),
                        "EXTIPI": "",#CODIGO DE EXEPCION TIPI (AGREGAR)
                        "CFOP": "%s" % l.product_id.l10n_xma_cfop_id.code if l.product_id.l10n_xma_cfop_id else "",
                        "uCOM": "%s" % l.product_uom_id.l10n_xma_uomcode_id.code,
                        "qCOM": "%s" % l.quantity,
                        "vUnCom": "%s" % l.price_unit,
                        "vProd": "%s" % l.price_subtotal,
                        "cEANTrib": "SEM GTIN",
                        "uTrib": "%s" % l.product_uom_id.l10n_xma_uomcode_id.code,
                        "qTrib": "%s" % l.quantity,
                        "vUnTrib": "%s" % l.price_unit,
                        "vFrete": "0.00",
                        "vSeg": "0.00",
                        "vDesc": "0.00",
                        "vOutro_item": "0.00",
                        "indTot": 1,
                        "nTipoItem": "%s" % l.product_id.l10n_xma_product_type_id.code,
                        "dProd": 0,
                        "xPed_item": "",
                        "nItemPed": "",
                        "nFCI": "",
                        "nRECOPI": "",
                        "CEST": "%s" % l.product_id.xma_cest_code, #CONTROL ST enlazar a l10n_br_cest_code
                        "cBenef": "", #CONTROL ST
                        "indEscala": "", #CONTROL ST
                        "CNPJFab": "", #CONTROL ST
                        "NVEs": [],
                        "detDI": [],
                        "detExport": [],
                        "veicProd": [],
                        "med": [],
                        "arma": [],
                        "comb": [],
                        "Rastro": []
                    },
                    "imposto": {
                        "ICMS": { #REVISAR SI APLICA RETENCION
                            "orig": "%s" % l.product_id.xma_source_origin, # l10n_br_source_origin
                            "CST": "%s" % l.product_id.l10n_xma_cst_code,
                            "modBC": "0",
                            "vBC": (l.price_subtotal if move.partner_id.l10n_xma_taxpayer_type_id.code != '2' else 0) if ICMS_aliq != 0 else 0,
                            "pICMS": (ICMS_aliq if move.partner_id.l10n_xma_taxpayer_type_id.code != '2' else 0),
                            "vICMS_icms": (float(f"{ICMS:.4f}") if move.partner_id.l10n_xma_taxpayer_type_id.code != '2' else 0),
                            "modBCST": 0,
                            "pMVAST": 0,
                            "pRedBCST": 0,
                            "vBCST": "0.00",
                            "vBCSTRet": ("%s" % l.price_subtotal) if move.partner_id.l10n_xma_taxpayer_type_id.code == '2' else 0, #BASE DE LA RETENCION
                            "pICMSST": (ICMS_aliq_r if ICMS_r > 0 else ICMS_aliq) if move.partner_id.l10n_xma_taxpayer_type_id.code == '2' else 0,
                            "vICMSST_icms": "0.00",
                            "vICMSSTRet": ((float(f"{ICMS_r:.4f}")) if ICMS_r > 0 else 0) if move.partner_id.l10n_xma_taxpayer_type_id.code == '2' else 0, #VALOR DE RETENCION
                            "pRedBC": 0,
                            "motDesICMS": 0,
                            "vICMSDeson": "0.00",
                            "vICMSOp": "0.00",
                            "pDif": 0,
                            "vICMSDif": "0.00",
                            "pBCOp": 0,
                            "UFST": "",
                            "vBCSTDest": "0.00",
                            "vICMSSTDest_icms": "0.00",
                            "pCredSN": 0,
                            "vCredICMSSN": "0.00",
                            "GerarTagStRet": "",
                            "pFCP": 0,
                            "vFCP": "0.00",
                            "vBCFCP": "0.00",
                            "vBCFCPST": "0.00",
                            "pFCPST": 0,
                            "vFCPST": "0.00",
                            "pST": 0,
                            "vICMSSubstituto": "0.00",
                            "vBCFCPSTRet": "0.00",
                            "pFCPSTRet": 0,
                            "vFCPSTRet": "0.00",
                            "GerarICMSST": "",
                            "pRedBCEfet": 0,
                            "vBCEfet": "0.00",
                            "pICMSEfet": 0,
                            "vICMSEfet": "0.00"
                        },
                        "IPI": {
                            "clEnq": "",
                            "CNPJProd": "",
                            "cSelo": "",
                            "qSelo": 0,
                            "cEnq": "",
                            "CSTIPI": {
                                "CST_IPI": "%s" % l.product_id.l10n_xma_cst_ipi_code, #AGREGAR CAMPO DE OPCIONES 
                                "vBC_IPI": "%s" % l.price_subtotal if IPI_aliq != 0 else 0,
                                "qUnid_IPI": "%s" % l.quantity,
                                "vUnid_IPI": "%s" % l.price_unit,
                                "pIPI": IPI_aliq,
                                "vIPI": float(f"{IPI:.4f}")
                            }
                        } if self.l10n_latam_document_type_id.code == '55' else {},
                        "II": { #PREGUNTAR A DIEGO COMO SE APLICA ESTE IMPUESTO
                            "vBC_imp": "%s" % l.price_subtotal if (IOF != 0 or II != 0) else 0,
                            "vDespAdu": "0.00", #REVISAR COMO SE REALIZA ESTE CALCULO
                            "vII": float(f"{II:.4f}"),
                            "vIOF": float(f"{IOF:.4f}")
                        },
                        "PIS": {
                            "CST_pis": "%s" % l.product_id.l10n_xma_cst_pis_code,
                            "vBC_pis": "%s" % (l.price_subtotal if "%s" % move.partner_id.country_id.code == "BR" else "0") if PIS_aliq != 0 else 0,
                            "pPIS": (PIS_aliq) if "%s" % move.partner_id.country_id.code == "BR" else "0",
                            "vPIS": float(f"{PIS:.4f}") if "%s" % move.partner_id.country_id.code == "BR" else "0",
                            "qBCprod_pis": "0.0000",
                            "vAliqProd_pis": "0.0000"
                        },
                        "PISST": { #PREGUNTAR A DIEGO SOBRE ESTE IMPUESTO
                            "vBC_pis_ST": "%s" % (l.price_subtotal if "%s" % move.partner_id.country_id.code != "BR" else "0") if PIS_aliq != 0 else 0,
                            "pPIS_ST": (PIS_aliq) if "%s" % move.partner_id.country_id.code != "BR" else "0",
                            "qBCprod_pis_ST": "0.0000",
                            "vAliqProd_pis_ST": "0.0000",
                            "vPIS_ST": float(f"{PIS:.4f}") if "%s" % move.partner_id.country_id.code != "BR" else "0"
                        },
                        "COFINS": {
                            "CST_cofins": "%s" % l.product_id.l10n_xma_cst_cofins_code,
                            "vBC_cofins": "%s" % (l.price_subtotal if "%s" % move.partner_id.country_id.code == "BR" else "0") if COFINS_aliq != 0 else 0,
                            "pCOFINS": (COFINS_aliq) if "%s" % move.partner_id.country_id.code == "BR" else "0",
                            "vCOFINS": float(f"{COFINS:.4f}") if "%s" % move.partner_id.country_id.code == "BR" else "0",
                            "qBCProd_cofins": "0.0000",
                            "vAliqProd_cofins": "0.0000"
                        },
                        "COFINSST": { #PREGUNTAR A DIEGO SOBRE ESTE IMPUESTO
                            "vBC_cofins_ST": "%s" % (l.price_subtotal if "%s" % move.partner_id.country_id.code != "BR" else "0") if COFINS_aliq != 0 else 0,
                            "pCOFINS_cofins_ST": 0,
                            "qBCProd_cofins_ST": "0.0000",
                            "vAliqProd_cofins_ST": (COFINS_aliq) if "%s" % move.partner_id.country_id.code != "BR" else "0",
                            "vCOFINS_cofins_ST": float(f"{COFINS:.4f}") if "%s" % move.partner_id.country_id.code != "BR" else "0"
                        },
                        "ISSQN": {
                            "vBC_issqn": "%s" % l.price_subtotal if ISSQN_aliq != 0 else 0,
                            "vAliq": ISSQN_aliq,
                            "vISSQN": float(f"{ISSQN:.4f}"),
                            "cMunFg_issqn": 0,
                            "cListServ": "",
                            "cSitTrib": "",
                            "vDeducao": "0.00",
                            "vOutro_issqn": "0.00",
                            "vDescIncond": "0.00",
                            "vDescCond": "0.00",
                            "indISSRet": 0,
                            "vISSRet": "0.00",
                            "indISS": 0,
                            "cServico": "",
                            "cMun_issqn": 0,
                            "cPais_issqn": 0,
                            "nProcesso": "",
                            "indIncentivo": 0
                        },
                        "ICMSUFDest": { #ENVIAR LOS DATOS DE ICMS CUANDO NO ES CONTRIBUYENTE DE ICMS
                            "vBCUFDest": "%s" % (l.price_subtotal if move.partner_id.l10n_xma_taxpayer_type_id.code == '2' else 0) if ICMS_aliq != 0 else 0,
                            "pFCPUFDest": 0,
                            "pICMSUFDest": (ICMS_aliq) if move.partner_id.l10n_xma_taxpayer_type_id.code == '2' else 0,
                            "pICMSInter": (ICMS_aliq) if move.partner_id.l10n_xma_taxpayer_type_id.code == '2' else 0,
                            "pICMSInterPart": 0,
                            "vFCPUFDest": float(f"{ICMS:.4f}") if move.partner_id.l10n_xma_taxpayer_type_id.code == '2' else 0,
                            "vICMSUFDest": "0.00",
                            "vICMSUFRemet": "0.00",
                            "vBCFCPUFDest": "0.00"
                        }if move.partner_id.l10n_xma_taxpayer_type_id.code == '2' else []
                    },
                    "impostoDevol": {
                        "pDevol": 0,
                        "IPIDevol": {
                            "vIPIDevol": "0.00"
                        }
                    }
                }
                plist.append(p)
            #print("HORA HORA HORA :::: ", move.l10n_xma_date_post - timedelta(hours=3))
            date_post_tz = fields.Datetime.context_timestamp(self.with_context(tz=self.env.user.tz), self.l10n_xma_date_post).strftime("%Y-%m-%dT%H:%M:%S")
            json_br = [
                        {
                            "Documento": {
                                "ModeloDocumento": "NFe" if self.l10n_latam_document_type_id.code == '55' else "NFCe",
                                "Versao": 4,
                                "Parametros": {
                                    "ApelidoLogomarca": ""
                                },
                                "ide": {
                                    "cNF": "",
                                    "cUF": "%s" % move.company_id.partner_id.l10n_xma_fiscal_unit_code,#41, #CODIGO DE LA UNIDAD FISCAL (PENDIENTE DE CONSULTA)
                                    "natOp": int(move.l10n_xma_use_document_id.code),
                                    "serie": move.l10n_latam_document_type_id.l10n_xma_serie,#"%s" % move.l10n_latam_document_type_id.doc_code_prefix,
                                    "nNF": move.xma_l10n_latam_document_number,
                                    "dhEmi": "%s" % date_post_tz,
                                    "fusoHorario": "-03:00",
                                    "dhSaiEnt": "0000-00-00T00:00:00",
                                    "tpNf": 1 if move.move_type in ['out_invoice','out_refund'] else 2,#CODIGO SI ES CLIENTE ES 1 SI ES PROVVEDOR ES 0
                                    "idDest": "%s" % move.l10n_xma_destination_op, #IDENTIFICADOR DE LOCAL DE DESTINO
                                    "indFinal": int(move.l10n_xma_end_user), #PREGUNTAR A DIEGO SOBRE ESTE CAMPO, VALORES ACEPTADOS 0 Y 1
                                    "indPres": "%s" % move.l10n_xma_origin_operation_id.code,#INDICADOR DE PRESENCIA
                                    "cMunFg": "%s" % move.company_id.partner_id.l10n_xma_municipality_id.code,
                                    "tpImp": 1 if self.l10n_latam_document_type_id.code == '55' else 4,#HAY VARIOS TIPOS DE DOCUMENTO DE IMPRESION (FORMATO DE IMPRESION DANFE), CONSULTAR SI LO AGREGAREMOS
                                    "tpEmis": "%s" % move.l10n_xma_issuance_type_id.code,#Forma de Emissão
                                    "tpAmb": 2 if move.company_id.l10n_xma_test == True else 1,
                                    "xJust": "",#SOLO SE LLENA EN CODIGO DE EMISION 9
                                    "dhCont": "0000-00-00T00:00:00",
                                    "finNFe": "%s" % move.l10n_xma_nfe_purpose,
                                    "EmailArquivos": "%s" % move.company_id.partner_id.email or "",
                                    "NumeroPedido": ""
                                },
                                "emit": {
                                    "CNPJ_emit": "%s" % re.sub(r'\D', '', move.company_id.partner_id.vat),
                                    "CPF_emit": "%s" % move.company_id.partner_id.l10n_br_cpf_code,#CPF DENTRO DEL CONTACTO DE COMPANIA
                                    "xNome": "%s" % move.company_id.name,
                                    "xFant": "%s" % (move.company_id.partner_id.commercial_name or move.company_id.name),
                                    "IM": "",#"%s" % (move.company_id.l10n_br_im_code if move.company_id.l10n_br_im_code else ""),
                                    "CNAE": "",# SE LLENA CUANDO IM ESTA LLENO 
                                    "IE": "%s" % re.sub(r'\D', '',move.company_id.partner_id.l10n_br_ie_code) if move.company_id.partner_id.l10n_br_ie_code else "",
                                    "IEST": "",
                                    "CRT": "%s" % move.company_id.partner_id.l10n_xma_taxpayer_type_id.code,# Regímen Fiscal
                                    "enderEmit": {
                                        "xLgr":  "%s" % move.company_id.partner_id.street,
                                        "nro": "%s" % move.company_id.partner_id.l10n_xma_external_number,
                                        "xCpl": "",
                                        "xBairro": "%s" % move.company_id.partner_id.street2,
                                        "cMun": "%s" % move.company_id.partner_id.l10n_xma_municipality_id.code,
                                        "xMun": "%s" % move.company_id.partner_id.l10n_xma_municipality_id.name,
                                        "UF": "%s" % move.company_id.partner_id.state_id.code,
                                        "CEP": "%s" % re.sub(r'\D', '', move.company_id.partner_id.zip),
                                        "cPais": "%s" % move.company_id.partner_id.country_id.l10n_xma_bacen_country_code,# EN EL CAMPO PAIS, Código do País (BACEN)
                                        "xPais": "%s" % move.company_id.partner_id.country_id.name,#NOMBRE PAIS
                                        "fone": "%s" % move.company_id.partner_id.phone,
                                        "fax": "",
                                        "Email": "%s" % move.company_id.partner_id.email or ""
                                    }
                                },
                                "dest": {
                                    "CNPJ_dest": "%s" % re.sub(r'\D', '', move.partner_id.vat) if self.l10n_latam_document_type_id.code == '55' else "",
                                    "CPF_dest": "%s" % move.partner_id.l10n_br_cpf_code,#CPF DENTRO DEL CONTACTO DE CLIENTE
                                    "idEstrangeiro": "%s" % move.partner_id.vat if "%s" % move.partner_id.country_id.code != "BR" else "",#COLOCAR VAT DEL CONTACTO SI PAIS ES DIFERENTE DE BRASIL
                                    "xNome_dest": "%s" % move.partner_id.name,
                                    "IE_dest":  "%s" % (move.partner_id.l10n_br_ie_code if move.partner_id.l10n_br_ie_code else "") if self.l10n_latam_document_type_id.code == '55' else "",
                                    "ISUF": "%s" % move.partner_id.l10n_xma_suframa_code if move.partner_id.l10n_xma_suframa_code else "",#SUFRAMA code
                                    "indIEDest": "%s" % move.partner_id.l10n_xma_ie_indicator if self.l10n_latam_document_type_id.code == '55' else "9",#l10n_xma_ie_indicator DENTRO DE CONTACTO
                                    "IM_dest": "%s" % (move.partner_id.l10n_br_im_code if move.partner_id.l10n_br_im_code else ""),
                                    "enderDest": {
                                        "nro_dest": "%s" % move.partner_id.l10n_xma_external_number if move.partner_id.l10n_xma_external_number else "",
                                        "xCpl_dest": "",
                                        "xBairro_dest": "%s" % move.partner_id.street2,
                                        "xEmail_dest": "%s" % move.partner_id.email if move.partner_id.email else "",
                                        "xLgr_dest": "%s" % move.partner_id.street,
                                        "xPais_dest": "%s" % move.partner_id.country_id.name,#NOMBRE PAIS
                                        "cMun_dest":  "%s" % move.partner_id.l10n_xma_municipality_id.code,
                                        "xMun_dest": "%s" % move.partner_id.l10n_xma_municipality_id.name,
                                        "UF_dest": "%s" % move.partner_id.state_id.code,#CODIGO DE PROVINCIA DEL ESTADO
                                        "CEP_dest": "%s" % re.sub(r'\D', '', move.partner_id.zip),
                                        "cPais_dest": "%s" % move.partner_id.country_id.l10n_xma_bacen_country_code,
                                        "fone_dest": "%s" % move.partner_id.phone if move.partner_id.phone else "",
                                    }
                                },
                                "retirada": {
                                    "CNPJ_ret": "",
                                    "CPF_ret": "",
                                    "xNome_ret": "",
                                    "xLgr_ret": "",
                                    "nro_ret": "",
                                    "xCpl_ret": "",
                                    "xBairro_ret": "",
                                    "xMun_ret": "",
                                    "cMun_ret": 0,
                                    "UF_ret": "",
                                    "CEP_ret": 0,
                                    "cPais_ret": 0,
                                    "xPais_ret": "",
                                    "fone_ret": 0,
                                    "email_ret": "",
                                    "IE_ret": ""
                                },
                                "entrega": {
                                    "CNPJ_entr": "",
                                    "CPF_entr": "",
                                    "xLgr_entr": "",
                                    "nro_entr": "",
                                    "xCpl_entr": "",
                                    "xBairro_entr": "",
                                    "cMun_entr": 0,
                                    "xMun_entr": "",
                                    "UF_entr": "",
                                    "xNome_entr": "",
                                    "CEP_entr": 0,
                                    "cPais_entr": 0,
                                    "xPais_entr": "",
                                    "fone_entr": 0,
                                    "email_entr": "",
                                    "IE_entr": ""
                                },
                                "autXML": [],
                                "det": plist,
                                "total": {
                                    "ICMStot": {
                                        "vBC_ttlnfe": total_products if have_taxes == True else 0,
                                        "vICMS_ttlnfe":  float(f"{ICMS_tot:.4f}"),
                                        "vICMSDeson_ttlnfe": "0.00",
                                        "vBCST_ttlnfe": "0.00",
                                        "vST_ttlnfe": "0.00",
                                        "vProd_ttlnfe": (total_products),
                                        "vFrete_ttlnfe": "0.00",
                                        "vSeg_ttlnfe": "0.00",
                                        "vDesc_ttlnfe": "0.00",
                                        "vII_ttlnfe": "0.00",
                                        "vIPI_ttlnfe": "%s" % IPI_tot,
                                        "vPIS_ttlnfe": "%s" % PIS_tot,
                                        "vCOFINS_ttlnfe": "%s" % COFINS_tot,
                                        "vOutro": "0.00",
                                        "vNF": "%s" % (total_products + II_tot + IPI_tot + PIS_tot + COFINS_tot),
                                        "vTotTrib_ttlnfe": "",
                                        "vFCPUFDest_ttlnfe": "0.00",
                                        "vICMSUFDest_ttlnfe": "0.00",
                                        "vICMSUFRemet_ttlnfe": "0.00",
                                        "vFCP_ttlnfe": "0.00",
                                        "vFCPST_ttlnfe": "0.00",
                                        "vFCPSTRet_ttlnfe": "0.00",
                                        "vIPIDevol_ttlnfe": "0.00",
                                        "vAFRMM_ttlnfe": "0.00"
                                    },
                                    "ISSQNtot": {
                                        "vServ": "%s" % SERV_tot,
                                        "vBC_ttlnfe_iss": "%s" % ISSQN_base,
                                        "vISS": "%s" % ISS_tot,
                                        "vPIS_servttlnfe": "%s" % sPIS_tot,
                                        "vCOFINS_servttlnfe": "%s" % sCOFINS_tot,
                                        "dCompet": "%s" % fields.Datetime.context_timestamp(self.with_context(tz=self.env.user.tz), self.l10n_xma_date_post).strftime("%Y-%m-%d"),
                                        "vDeducao_servttlnfe": "0.00",
                                        "vOutro_servttlnfe": "0.00",
                                        "vDescIncond_servttlnfe": "0.00",
                                        "vDescCond_servttlnfe": "0.00",
                                        "vISSRet_servttlnfe": "0.00",
                                        "cRegTrib": 0
                                    },
                                    "retTrib": {
                                        "vRetPIS": "0.00",
                                        "vRetCOFINS_servttlnfe": "0.00",
                                        "vRetCSLL": "0.00",
                                        "vBCIRRF": "0.00",
                                        "vIRRF": "0.00",
                                        "vBCRetPrev": "0.00",
                                        "vRetPrev": "0.00"
                                    }
                                },
                                "transp": {
                                    "modFrete": 9,
                                } if self.l10n_latam_document_type_id.code == '65' else {},
                                "cobr": {
                                    "fat": {
                                        "nFat": "",
                                        "vOrig": "0.00",
                                        "vDesc_cob": "0.00",
                                        "vLiq": "0.00"
                                    },
                                    "dup": []
                                },
                                "pag": [
                                    {
                                        "indPag_pag": "",
                                        "tPag": "%s" % move.l10n_xma_payment_form_id.code,
                                        "vPag": "%s" % (total_products + II_tot + IPI_tot + PIS_tot + COFINS_tot),
                                        "card": {
                                            "tipoIntegracao": 0,
                                            "CNPJ_card": "",
                                            "tBand": "",
                                            "cAut": ""
                                        }
                                    }
                                ],
                                "infAdic": {
                                    "infAdFisco": "INFORMACOES DE INTERESSE DO FISCO",
                                    "infCpl": "INFORMACOES COMPLEMENTARES",
                                    "obsCont": [],
                                    "procRef": []
                                },
                                "exporta": {
                                    "UFEmbarq": "",
                                    "xLocEmbarq": "",
                                    "xLocDespacho": ""
                                },
                                "compra": {
                                    "xNEmp": "",
                                    "xPed": "",
                                    "xCont": ""
                                },
                                "cana": {
                                    "safra": "",
                                    "ref": "",
                                    "qTotMes": "0.0000000000",
                                    "qTotAnt": "0.0000000000",
                                    "qTotGer": "0.0000000000",
                                    "vFor": "0.00",
                                    "vTotDed": "0.00",
                                    "vLiqFor": "0.00",
                                    "canaDiario": [],
                                    "canaDeducoes": []
                                }
                            }
                        }
                    ]
           
            json_complete = {
                "id":self.id,
                "uuid_client":self.company_id.uuid_client,
                "data":json_br,
                "rfc":re.sub(r'\D', '', self.company_id.vat),
                "prod": 'NO' if self.company_id.l10n_xma_test else 'SI',
                "type": 'BF',
                "pac_invoice": self.company_id.l10n_xma_type_pac,
                "signature_key": self.company_id.xma_br_signature_key,
                "partner_key": self.company_id.xma_br_partner_key,
            }
            return json_complete

    def generate_json_l10n_br_nfse(self):
        for move in self:
            itemlist = []
            lservicios = []
            for line in move.invoice_line_ids:
                ISS = 0.0
                ISS_r = 0.0
                ISS_aliq = 0.0

                INSS = 0.0
                INSS_r = 0.0
                INSS_aliq = 0.0

                ICMS = 0.0
                ICMS_r = 0.0
                ICMS_aliq = 0.0

                IPI = 0.0
                IPI_r = 0.0
                IPI_aliq = 0.0

                COFINS = 0.0
                COFINS_r = 0.0
                COFINS_aliq = 0.0

                IR = 0.0
                IR_r = 0.0
                IR_aliq = 0.0

                ISSQN = 0.0
                ISSQN_r = 0.0
                ISSQN_aliq = 0.0

                PIS = 0.0
                PIS_r = 0.0
                PIS_aliq = 0.0

                CSLL = 0.0
                CSLL_r = 0.0
                CSLL_aliq = 0.0

                IOF = 0.0
                IOF_r = 0.0
                IOF_aliq = 0.0

                for tax in line.tax_ids:
                    tax_res = tax.compute_all(line.quantity * line.price_unit, currency=line.currency_id)
                    # {'base_tags': [10], 'taxes': [{'id': 102, 'name': 'ICMS Saída Externo 7%', 'amount': 7.0, 'base': 100.0, 'sequence': 1, 'account_id': 1419, 'analytic': False, 'use_in_tax_closing': True, 'price_include': False, 'tax_exigibility': 'on_invoice', 'tax_repartition_line_id': 390, 'group': None, 'tag_ids': [12], 'tax_ids': []}], 'total_excluded': 100.0, 'total_included': 107.0, 'total_void': 100.0}
                    _logger.info(f"Valor TAX Entry::::: {tax_res['taxes']}")
                    for tax_entry in tax_res['taxes']:
                        if 'ISS' in tax_entry['name'] and 'ISSQN' not in tax_entry['name']:
                            if float(tax_entry['amount']) > 0.0:
                                ISS += tax_entry['amount']
                            if float(tax_entry['amount']) < 0.0:
                                ISS_r += float(tax_entry['amount']) * -1
                            ISS_aliq += self.env['account.tax'].search([('id','=',tax_entry['id'])], limit=1).amount
                        if 'INSS' in tax_entry['name']:
                            if float(tax_entry['amount']) > 0.0:
                                INSS += tax_entry['amount']
                            if float(tax_entry['amount']) < 0.0:
                                INSS_r += float(tax_entry['amount']) * -1
                            INSS_aliq += self.env['account.tax'].search([('id','=',tax_entry['id'])], limit=1).amount
                        if 'ICMS' in tax_entry['name']:
                            if float(tax_entry['amount']) > 0.0:
                                ICMS += tax_entry['amount']
                            if float(tax_entry['amount']) < 0.0:
                                ICMS_r += float(tax_entry['amount']) * -1
                            ICMS_aliq += self.env['account.tax'].search([('id','=',tax_entry['id'])], limit=1).amount
                        if 'IPI' in tax_entry['name']:
                            if float(tax_entry['amount']) > 0.0:
                                IPI += tax_entry['amount']
                            if float(tax_entry['amount']) < 0.0:
                                IPI_r += float(tax_entry['amount']) * -1
                            IPI_aliq += self.env['account.tax'].search([('id','=',tax_entry['id'])], limit=1).amount
                        if 'COFINS' in tax_entry['name']:
                            if float(tax_entry['amount']) > 0.0:
                                COFINS += tax_entry['amount']
                            if float(tax_entry['amount']) < 0.0:
                                COFINS_r += float(tax_entry['amount']) * -1
                            COFINS_aliq += self.env['account.tax'].search([('id','=',tax_entry['id'])], limit=1).amount
                        if 'IR' in tax_entry['name']:
                            if float(tax_entry['amount']) > 0.0:
                                IR += tax_entry['amount']
                            if float(tax_entry['amount']) < 0.0:
                                IR_r += float(tax_entry['amount']) * -1
                            IR_aliq += self.env['account.tax'].search([('id','=',tax_entry['id'])], limit=1).amount
                        if 'ISSQN' in tax_entry['name']:
                            if float(tax_entry['amount']) > 0.0:
                                ISSQN += tax_entry['amount']
                            if float(tax_entry['amount']) < 0.0:
                                ISSQN_r += float(tax_entry['amount']) * -1
                            ISSQN_aliq += self.env['account.tax'].search([('id','=',tax_entry['id'])], limit=1).amount
                        if 'PIS' in tax_entry['name']:
                            if float(tax_entry['amount']) > 0.0:
                                PIS += tax_entry['amount']
                            if float(tax_entry['amount']) < 0.0:
                                PIS_r += float(tax_entry['amount']) * -1
                            PIS_aliq += self.env['account.tax'].search([('id','=',tax_entry['id'])], limit=1).amount
                        if 'CSLL' in tax_entry['name']:
                            if float(tax_entry['amount']) > 0.0:
                                CSLL += tax_entry['amount']
                            if float(tax_entry['amount']) < 0.0:
                                CSLL_r += float(tax_entry['amount']) * -1
                            CSLL_aliq += self.env['account.tax'].search([('id','=',tax_entry['id'])], limit=1).amount
                        if 'IOF' in tax_entry['name']:
                            if float(tax_entry['amount']) > 0.0:
                                IOF += tax_entry['amount']
                            if float(tax_entry['amount']) < 0.0:
                                IOF_r += float(tax_entry['amount']) * -1
                            IOF_aliq += self.env['account.tax'].search([('id','=',tax_entry['id'])], limit=1).amount
                iss_aliq_res = ISS_aliq + ISSQN_aliq
                if iss_aliq_res < 0:
                    iss_aliq_res = iss_aliq_res * -1
                if COFINS_aliq < 0:
                    COFINS_aliq = COFINS_aliq * -1
                iss_val_item = float(f"{ISS:.4f}") + float(f"{ISSQN:.4f}")
                _logger.info(f"VALOR ISS_VAL_ITEM ||||||||||||||||||||||||||||||\n{iss_val_item}\n||||||||||||||||||||||||||||||||||||||||||||||||")
                l = {
                        "ItemSeq": line.sequence, 
                        "ItemCod": "%s" % line.product_id.default_code,
                        "ItemDesc": "%s" % line.name,
                        "ItemQtde": line.quantity,
                        "ItemvUnit": line.price_unit,
                        "ItemuMed": "%s" % line.product_uom_id.l10n_xma_uomcode_id.code,
                        "ItemvlDed": 0,
                        "ItemTributavel": "",
                        "ItemcCnae": "%s" % line.l10n_xma_economic_activity_id.code,
                        "ItemTributMunicipio": "",
                        "ItemnAlvara": "",
                        "ItemvIss": iss_val_item,
                        "ItemvDesconto": 0.0,
                        "ItemAliquota": iss_aliq_res/100,
                        "ItemVlrTotal": line.quantity * line.price_unit,#move.amount_untaxed,
                        "ItemBaseCalculo": line.quantity * line.price_unit,#move.amount_untaxed,
                        "ItemvlrISSRetido": ISS_r + ISSQN_r,
                        "ItemIssRetido": 1 if (ISS_r > 0 or ISSQN_r > 0) else 2,
                        "ItemRespRetencao": 0,
                        "ItemIteListServico": "%s" % line.product_id.l10n_xma_productcode_id.code,
                        "itemCodTributNacional": "%s" % line.product_id.l10n_xma_codtributNacional_id.code,
                        "ItemExigibilidadeISS": 1,
                        "ItemcMunIncidencia": 0,
                        "ItemNumProcesso": "",
                        "ItemDedTipo": "",
                        "ItemDedCPFRef": "",
                        "ItemDedCNPJRef": "",
                        "ItemDedNFRef": 0,
                        "ItemDedvlTotRef": 0,
                        "ItemDedPer": 0,
                        # "ItemVlrLiquido": move.amount_total - (ISS_r + ISSQN_r),
                        "ItemValAliqINSS": INSS_aliq/100,
                        "ItemValINSS": float(f"{INSS:.4f}"),
                        "ItemValAliqIR": IR_aliq/100,
                        "ItemValIR": float(f"{IR:.4f}"),
                        "ItemValAliqCOFINS": COFINS_aliq/100,
                        "ItemValCOFINS": float(f"{COFINS:.4f}"),
                        "ItemValAliqCSLL": CSLL_aliq/100,
                        "ItemValCSLL": float(f"{CSLL:.4f}"),
                        "ItemValAliqPIS": PIS_aliq/100,
                        "ItemValPIS": float(f"{PIS:.4f}"),
                        "ItemRedBC": 0,
                        "ItemRedBCRetido": 0,
                        "ItemBCRetido": 0,
                        "ItemValAliqISSRetido": 0,
                        "ItemPaisImpDevido": "",
                        "ItemJustDed": "",
                        "ItemvOutrasRetencoes": 0,
                        "ItemDescIncondicionado": 0.0,
                        "ItemDescCondicionado": 0.0,
                        "ItemTotalAproxTribServ": 0

                    }
                ls = {
                    "Valores": {
                        "ValServicos": line.quantity * line.price_unit,#move.amount_untaxed,
                        "ValDeducoes": 0.00,
                        "ValPIS": float(f"{PIS_r:.4f}"),
                        "ValBCPIS": 0.00,
                        "ValCOFINS": float(f"{COFINS_r:.4f}"),
                        "ValBCCOFINS": 0.00,
                        "ValINSS": 0.00,#float(f"{INSS:.4f}"),
                        "ValBCINSS": 0.00,#,
                        "ValIR": float(f"{IR_r:.4f}"),
                        "ValBCIRRF": 0.00,
                        "ValCSLL": float(f"{CSLL_r:.4f}"),
                        "ValBCCSLL": 0.00,
                        "RespRetencao": 0.00,
                        "Tributavel": "",
                        "ValISS": iss_val_item,
                        "ISSRetido": 1 if (ISS_r > 0 or ISSQN_r > 0) else 2,
                        "ValISSRetido": ISS_r + ISSQN_r,
                        "ValTotal": line.quantity * line.price_unit,#move.amount_untaxed,
                        "ValTotalRecebido": 0,
                        "ValBaseCalculo": line.quantity * line.price_unit,#move.amount_untaxed,
                        "ValOutrasRetencoes": 0,
                        "ValAliqISS": iss_aliq_res/100,
                        "ValAliqPIS": 0.00,#PIS_aliq/100,
                        "PISRetido": 1 if PIS_r > 0 else 2,
                        "ValAliqCOFINS": 0.00,#COFINS_aliq/100,
                        "COFINSRetido": 1 if COFINS_r > 0 else 2,
                        "ValAliqIR": 0.00,#IR_aliq/100,
                        "IRRetido": 1 if IR_r > 0 else 2,
                        "ValAliqCSLL": 0.00,#CSLL_aliq/100,
                        "CSLLRetido": 1 if CSLL_r > 0 else 2,
                        "ValAliqINSS": 0.00,#INSS_aliq/100,
                        "INSSRetido": 2,#1 if INSS_r > 0 else 2,
                        "ValAliqCpp": 0,
                        "CppRetido": 0,
                        "ValCpp": 0,
                        "OutrasRetencoesRetido": 0,
                        "ValBCOutrasRetencoes": 0,
                        "ValAliqOutrasRetencoes": 0,
                        "ValAliqTotTributos": 0,
                        # "ValLiquido": move.amount_total - (ISS_r + ISSQN_r),
                        "ValDescIncond": 0.0,
                        "ValDescCond": 0.0,
                        "ValAcrescimos": 0,
                        "ValAliqISSoMunic": 0.0,
                        "InfValPIS": "",
                        "InfValCOFINS": "",
                        "ValLiqFatura": 0,
                        "ValBCISSRetido": 0,
                        "NroFatura": 0,
                        "CargaTribValor": 0,
                        "CargaTribPercentual": 0,
                        "CargaTribFonte": "",
                        "JustDed": "",
                        "ValCredito": 0,
                        "OutrosImp": 0,
                        "ValRedBC": 0,
                        "ValRetFederais": 0,
                        "ValAproxTrib": 0,
                        "NroDeducao": "0"
                    },
                    "LocalPrestacao": {
                        "SerEndTpLgr": "",
                        "SerEndLgr": "",
                        "SerEndNumero": "",
                        "SerEndComplemento": "",
                        "SerEndBairro": "",
                        "SerEndxMun": "",
                        "SerEndcMun": int("%s" % line.move_id.company_id.partner_id.l10n_xma_municipality_id.code),
                        "SerEndCep": 0,
                        "SerEndSiglaUF": ""
                    },
                    "IteListServico": "%s" % line.product_id.l10n_xma_productcode_id.code,
                    "Cnae": int("%s" % line.l10n_xma_economic_activity_id.code),
                    "fPagamento": "",
                    "tpag": 0,
                    "TributMunicipio": "",
                    "TributMunicDesc": "",
                    "Discriminacao": "%s" % line.name,
                    "cMun": int("%s" % line.move_id.company_id.partner_id.l10n_xma_municipality_id.code),
                    "SerQuantidade": 0,
                    "SerUnidade": "",
                    "SerNumAlvara": "",
                    "PaiPreServico": "",
                    # "cMunIncidencia": 0,
                    "dVencimento": "0000-00-00T00:00:00",
                    "ObsInsPagamento": "",
                    "ObrigoMunic": 0,
                    "TributacaoISS": 0,
                    "CodigoAtividadeEconomica": "",
                    "ServicoViasPublicas": 0,
                    "NumeroParcelas": 0,
                    "NroOrcamento": 0,
                    "CodigoNBS": ""
                }
                itemlist.append(l)
                lservicios = ls
            date_post_tz = fields.Datetime.context_timestamp(self.with_context(tz=self.env.user.tz), self.l10n_xma_date_post).strftime("%Y-%m-%dT%H:%M:%S")
            json_br = [{"Documento": {
                    "ModeloDocumento": "NFSe",
                    "Versao": 1.0,
                    "RPS": [
                        {
                            "RPSNumero":  move.xma_l10n_latam_document_number,
                            "RPSSerie": "%s" % move.l10n_latam_document_type_id.l10n_xma_serie,
                            "RPSTipo": 1 if move.l10n_latam_document_type_id.code == 'SE' else None,
                            "dEmis": "%s" % date_post_tz,
                            "dCompetencia": "%s" % date_post_tz,
                            "LocalPrestServ": 0,
                            "natOp": int(move.l10n_xma_use_document_id.code),
                            "Operacao": "",
                            "NumProcesso": "",
                            "RegEspTrib": move.company_id.partner_id.l10n_xma_special_regime or "",
                            "OptSN": int(move.l10n_xma_optsn),
                            "IncCult": int(move.l10n_xma_cultural_supporter),
                            "Status": 1, 
                            "cVerificaRPS": "%s" % move.company_id.partner_id.l10n_xma_rps_verification_code or "", 
                            "EmpreitadaGlobal": 0 if not move.l10n_xma_global_company else int(move.l10n_xma_global_company),
                            "tpAmb": 2 if self.company_id.l10n_xma_test == True else 1,
                            "RPSSubs": {
                                "SubsNumero": 0,
                                "SubsSerie": "",
                                "SubsTipo": 0,
                                "SubsNFSeNumero": 0,
                                "SubsDEmisNFSe": "0000-00-00T00:00:00"
                            },
                            "Prestador": {
                                "CNPJ_prest": "%s" % re.sub(r'\D', '', move.company_id.vat),
                                "xNome": "%s" % move.company_id.name,
                                "xFant": "%s" % (move.company_id.partner_id.commercial_name or move.company_id.name),
                                "IM": "%s" % (move.company_id.l10n_br_im_code if move.company_id.l10n_br_im_code else ""),
                                "IE": "%s" % (move.company_id.l10n_br_ie_code if move.company_id.l10n_br_ie_code else ""),
                                "CMC": "102748",
                                "enderPrest": {
                                    "TpEnd": "RUA", #REVISAR DE DONDE SE TOMA
                                    "xLgr": "%s" % move.company_id.street,
                                    "nro": "%s" % move.company_id.partner_id.l10n_xma_external_number,
                                    "xCpl": "", 
                                    "xBairro": "%s" % move.company_id.street2,
                                    "cMun": "%s" % move.company_id.partner_id.l10n_xma_municipality_id.code,
                                    "UF": "%s" % move.company_id.state_id.code,
                                    "CEP": "%s" % re.sub(r'\D', '', move.company_id.partner_id.zip),
                                    "fone": "%s" % move.company_id.phone,
                                    "Email": "%s" % move.company_id.email
                                }
                            },
                            
                            "ListaItens": itemlist,
                            
                            "ListaParcelas": [],

                            "Servico": lservicios,
                            "Tomador": {
                                "TomaCNPJ": "%s" % re.sub(r'\D', '', move.partner_id.vat),
                                "TomaCPF": "",
                                "TomaIE": "",
                                "TomaIM": "%s" % move.partner_id.l10n_br_im_code,
                                "TomaRazaoSocial": "%s" % move.partner_id.name,
                                "TomatpLgr": "AV",
                                "TomaEndereco": "%s" % move.partner_id.street,
                                "TomaNumero": "%s" % move.partner_id.l10n_xma_external_number if move.partner_id.l10n_xma_external_number else "",
                                "TomaComplemento": "",
                                "TomaBairro": "%s" % move.partner_id.street2,
                                "TomacMun": move.partner_id.l10n_xma_municipality_id.code,
                                "TomaxMun": "%s" % move.partner_id.l10n_xma_municipality_id.name,
                                "TomaUF": "%s" % move.partner_id.state_id.code,
                                "TomaPais": "%s" % move.partner_id.country_id.l10n_xma_bacen_country_code,
                                "TomaCEP": "%s" % re.sub(r'\D', '', move.partner_id.zip),
                                "TomaTelefone": "%s" % move.partner_id.phone if move.partner_id.phone else "",
                                "TomaTipoTelefone": "",
                                "TomaEmail": "%s" % move.partner_id.email if move.partner_id.email else "",
                                "TomaSite": "%s" % move.partner_id.website if move.partner_id.website else "",
                                "TomaIME": "",
                                "TomaSituacaoEspecial": "",
                                "DocTomadorEstrangeiro": "",
                                "TomaRegEspTrib": 0,
                                "TomaCadastroMunicipio": 0,
                                "TomaOrgaoPublico": 0
                            },
                            "IntermServico": {
                                "IntermRazaoSocial": "",
                                "IntermCNPJ": "",
                                "IntermCPF": "",
                                "IntermIM": "",
                                "IntermEmail": "",
                                "IntermEndereco": "",
                                "IntermNumero": "",
                                "IntermComplemento": "",
                                "IntermBairro": "",
                                "IntermCep": 0,
                                "IntermCmun": 0,
                                "IntermXmun": "",
                                "IntermFone": "",
                                "IntermIE": ""
                            },
                            "ConstCivil": {
                                "CodObra": "",
                                "Art": "",
                                "ObraLog": "",
                                "ObraCompl": "",
                                "ObraNumero": "",
                                "ObraBairro": "",
                                "ObraCEP": 0,
                                "ObraMun": 0,
                                "ObraUF": "",
                                "ObraPais": "",
                                "ObraCEI": "",
                                "ObraMatricula": "",
                                "ObraValRedBC": 0,
                                "ObraTipo": 0,
                                "ObraNomeFornecedor": "",
                                "ObraNumeroNF": 0,
                                "ObraDataNF": "0000-00-00T00:00:00",
                                "ObraNumEncapsulamento": "",
                                "AbatimentoMateriais": 0,
                                "ListaMaterial": []
                            },
                            "ListaDed": [],
                            "Transportadora": {
                                "TraNome": "",
                                "TraCPFCNPJ": "",
                                "TraIE": "",
                                "TraPlaca": "",
                                "TraEnd": "",
                                "TraMun": 0,
                                "TraUF": "",
                                "TraPais": "",
                                "TraTipoFrete": 0
                            },
                            "NFSOutrasinformacoes": "",
                            "RPSCanhoto": 0,
                            "Arquivo": "",
                            "ExtensaoArquivo": ""
                        }
                    ]
                }
                }]
            json_complete = {
                "id":self.id,
                "uuid_client":self.company_id.uuid_client,
                "data":json_br,
                "rfc":re.sub(r'\D', '', self.company_id.vat),
                "prod": 'NO' if self.company_id.l10n_xma_test else 'SI',
                "type": 'BF',
                "pac_invoice": self.company_id.l10n_xma_type_pac,
                "signature_key": self.company_id.xma_br_signature_key,
                "partner_key": self.company_id.xma_br_partner_key
            }
            return json_complete
        
    
    def button_send_search_json_br(self):
        self.send_to_matrix_search_json_br()
        time.sleep(2)
        self.env.flush_all()
        self.refresh_account_move_xma()
        return True 
    
    def send_to_matrix_search_json_br(self):
        xml_json_br = False   
        xml_json_br = self.send_json_search_br()
        xml_json = {"BR": xml_json_br}
        company = self.get_company()
        uuid = company.company_name
        rfc = re.sub(r'\D', '', self.company_id.partner_id.vat)
        country = self.company_id.partner_id.country_id.code.lower()
        xml_json = {"from":uuid, "data":xml_json}
        print("DATOS________________________________________\n", xml_json)
        mqtt_client = MqttClient("api.xmarts.com", 1883, prefix=f"uuid/{uuid}/rfc/{rfc}/country/{country}/", encryption_key=company.key)
        mqtt_client.send_message_serialized(
            [xml_json],
            f"uuid/{uuid}/rfc/{rfc}/country/{country}/consult", 
            valid_json=True, 
            secure=True
        )

        self.env.cr.commit()
        time.sleep(2) 
        return True
        # self.refresh_account_move_xma()
        
        
    def send_json_search_br(self):
        for rec in self:
            params = [{
                "type": "Consulta",
                "CnpjEmissor": re.sub(r'\D', '', rec.company_id.vat),
                "NumeroInicial": rec.xma_l10n_latam_document_number,
                "NumeroFinal": rec.xma_l10n_latam_document_number,
                "Serie": rec.xma_l10n_document_serie,
                "CnpjEmpresa": re.sub(r'\D', '', rec.company_id.vat),
                "tpAmb": 2 if rec.company_id.l10n_xma_test else 1,
                "dhUF": None,
                "ChaveAcesso": None,
                "DataEmissaoInicial": None,
                "DataEmissaoFinal": None,
                "DataInclusaoFinal": None,
                "DataInclusaoInicial": None,
                "StatusDocumento": None,
                "EmitidoRecebido": "E",
                "ParmTipoImpressao": "N",
                "DocumentosResumo": "N",
                "ParmAutorizadoDownload": "N",
                "ParmXMLLink": "S",
                "ParmXMLCompleto": "S",
                "ParmPDFBase64": "S",
                "ParmPDFLink": "S",
                "ParmEventos": "N",
                "ParmSituacao": "S",
                "ParmConsultarDFe": "N"
            }]
            doc_type = ""
            if self.l10n_latam_document_type_id.code == '55':
                doc_type = "nfe"
            if self.l10n_latam_document_type_id.code == 'SE':
                doc_type = "nfse"
            json_complete = {
                "id":rec.id,
                "uuid_client":rec.company_id.uuid_client,
                "data":params,
                "rfc":re.sub(r'\D', '', rec.company_id.vat),
                "prod": 'NO' if rec.company_id.l10n_xma_test else 'SI',
                "type": 'BF',
                "pac_invoice": rec.company_id.l10n_xma_type_pac,
                "signature_key": rec.company_id.xma_br_signature_key,
                "partner_key": rec.company_id.xma_br_partner_key,
                "doc_type": doc_type
            }
            return json_complete