# -*- coding: utf-8 -*-
from odoo import api, fields, models, _, Command
from collections import defaultdict
from odoo.tools import frozendict, groupby, split_every

import math

class AccountTax(models.Model):
    _inherit = "account.tax"

    country_id = fields.Many2one(
        'res.country',
        related="company_id.country_id",
    )

    l10n_xma_tax_factor_type_id = fields.Many2one(
        'l10n_xma.tax_factor_type'
    )
    
    l10n_xma_edi_tax_type_id = fields.Many2one(
        'l10n_xma.tax_type'
    )

    l10n_xma_tax_type_id = fields.Many2one(
        'l10n_xma.tax_type'
    )
    
    l10n_xma_is_special_tax = fields.Boolean(
        string='Es impuesto especial',
    )
    
    
    l10n_xma_base_tax = fields.Selection(
        [
            ('100', '100'),
            ('50', '50'),
            ('30', '30'),
            ('0', '0')
        ], default='0', 
        string='Tax Base'
    )
    
    def _convert_to_tax_base_line_dict(
            self, base_line,
            partner=None, currency=None, product=None, taxes=None, price_unit=None, quantity=None,
            discount=None, account=None, analytic_distribution=None, price_subtotal=None,
            is_refund=False, rate=None,
            handle_price_include=True,
            extra_context=None,
    ):
        return {
            'record': base_line,
            'partner': partner or self.env['res.partner'],
            'currency': currency or self.env['res.currency'],
            'product': product or self.env['product.product'],
            'taxes': taxes or self.env['account.tax'],
            'price_unit': price_unit or 0.0,
            'quantity': quantity or 0.0,
            'discount': discount or 0.0,
            'account': account or self.env['account.account'],
            'analytic_distribution': analytic_distribution,
            'price_subtotal': price_subtotal or 0.0,
            'is_refund': is_refund,
            'rate': rate or 1.0,
            'handle_price_include': handle_price_include,
            'extra_context': extra_context or {},
        }
        
    def _compute_taxes_for_single_line(self, base_line, handle_price_include=True, include_caba_tags=False, early_pay_discount_computation=None, early_pay_discount_percentage=None):
        print(f"base_line:::::::::::  {base_line['taxes']._origin}")
        orig_price_unit_after_discount = base_line['price_unit'] * (1 - (base_line['discount'] / 100.0))
        price_unit_after_discount = orig_price_unit_after_discount
        taxes = base_line['taxes']._origin
        currency = base_line['currency'] or self.env.company.currency_id
        rate = base_line['rate']

        if early_pay_discount_computation in ('included', 'excluded'):
            remaining_part_to_consider = (100 - early_pay_discount_percentage) / 100.0
            price_unit_after_discount = remaining_part_to_consider * price_unit_after_discount

        if taxes:
            print(f"SI HAY TAXESSSSSSSSSSSSSSSSSSSSSSS")
            taxes_res = taxes.with_context(**base_line['extra_context']).compute_all(
                price_unit_after_discount,
                currency=currency,
                quantity=base_line['quantity'],
                product=base_line['product'],
                partner=base_line['partner'],
                is_refund=base_line['is_refund'],
                handle_price_include=base_line['handle_price_include'],
                include_caba_tags=include_caba_tags,
            )
            print(f"taxes_res------------------- {taxes_res}")
            to_update_vals = {
                'tax_tag_ids': [Command.set(taxes_res['base_tags'])],
                'price_subtotal': taxes_res['total_excluded'],
                'price_total': taxes_res['total_included'],
            }

            if early_pay_discount_computation == 'excluded':
                new_taxes_res = taxes.with_context(**base_line['extra_context']).compute_all(
                    orig_price_unit_after_discount,
                    currency=currency,
                    quantity=base_line['quantity'],
                    product=base_line['product'],
                    partner=base_line['partner'],
                    is_refund=base_line['is_refund'],
                    handle_price_include=base_line['handle_price_include'],
                    include_caba_tags=include_caba_tags,
                )
                for tax_res, new_taxes_res in zip(taxes_res['taxes'], new_taxes_res['taxes']):
                    delta_tax = new_taxes_res['amount'] - tax_res['amount']
                    tax_res['amount'] += delta_tax
                    to_update_vals['price_total'] += delta_tax

            tax_values_list = []
            for tax_res in taxes_res['taxes']:
                tax_amount = tax_res['amount'] / rate
                if self.company_id.tax_calculation_rounding_method == 'round_per_line':
                    tax_amount = currency.round(tax_amount)
                tax_rep = self.env['account.tax.repartition.line'].browse(tax_res['tax_repartition_line_id'])
                tax_values_list.append({
                    **tax_res,
                    'tax_repartition_line': tax_rep,
                    'base_amount_currency': tax_res['base'],
                    'base_amount': currency.round(tax_res['base'] / rate),
                    'tax_amount_currency': tax_res['amount'],
                    'tax_amount': tax_amount,
                })

        else:
            price_subtotal = currency.round(price_unit_after_discount * base_line['quantity'])
            to_update_vals = {
                'tax_tag_ids': [Command.clear()],
                'price_subtotal': price_subtotal,
                'price_total': price_subtotal,
            }
            tax_values_list = []
        print(f"to_update_vals, tax_values_list ------------------------ {to_update_vals, tax_values_list}")
        return to_update_vals, tax_values_list
    
    def _aggregate_taxes(self, to_process, filter_tax_values_to_apply=None, grouping_key_generator=None, distribute_total_on_line=True):

        def default_grouping_key_generator(base_line, tax_values):
            return {'tax': tax_values['tax_repartition_line'].tax_id}

        global_tax_details = {
            'to_process': to_process,
            'base_amount_currency': 0.0,
            'base_amount': 0.0,
            'tax_amount_currency': 0.0,
            'tax_amount': 0.0,
            'tax_details': defaultdict(lambda: {
                'base_amount_currency': 0.0,
                'base_amount': 0.0,
                'tax_amount_currency': 0.0,
                'tax_amount': 0.0,
                'group_tax_details': [],
                'records': set(),
            }),
            'tax_details_per_record': defaultdict(lambda: {
                'base_amount_currency': 0.0,
                'base_amount': 0.0,
                'tax_amount_currency': 0.0,
                'tax_amount': 0.0,
                'tax_details': defaultdict(lambda: {
                    'base_amount_currency': 0.0,
                    'base_amount': 0.0,
                    'tax_amount_currency': 0.0,
                    'tax_amount': 0.0,
                    'group_tax_details': [],
                    'records': set(),
                }),
            }),
        }

        def add_tax_values(record, results, grouping_key, serialized_grouping_key, tax_values):
            # Add to global results.
            results['tax_amount_currency'] += tax_values['tax_amount_currency']
            results['tax_amount'] += tax_values['tax_amount']

            # Add to tax details.
            if serialized_grouping_key not in results['tax_details']:
                tax_details = results['tax_details'][serialized_grouping_key]
                tax_details.update(grouping_key)
                tax_details['base_amount_currency'] = tax_values['base_amount_currency']
                tax_details['base_amount'] = tax_values['base_amount']
                tax_details['records'].add(record)
            else:
                tax_details = results['tax_details'][serialized_grouping_key]
                if record not in tax_details['records']:
                    tax_details['base_amount_currency'] += tax_values['base_amount_currency']
                    tax_details['base_amount'] += tax_values['base_amount']
                    tax_details['records'].add(record)
            tax_details['tax_amount_currency'] += tax_values['tax_amount_currency']
            tax_details['tax_amount'] += tax_values['tax_amount']
            tax_details['group_tax_details'].append(tax_values)

        if self.env.company.tax_calculation_rounding_method == 'round_globally' and distribute_total_on_line:
            # Aggregate all amounts according the tax lines grouping key.
            comp_currency = self.env.company.currency_id
            amount_per_tax_repartition_line_id = defaultdict(lambda: {
                'tax_amount': 0.0,
                'tax_amount_currency': 0.0,
                'tax_values_list': [],
            })
            for base_line, to_update_vals, tax_values_list in to_process:
                currency = base_line['currency'] or comp_currency
                for tax_values in tax_values_list:
                    grouping_key = frozendict(self._get_generation_dict_from_base_line(base_line, tax_values))
                    total_amounts = amount_per_tax_repartition_line_id[grouping_key]
                    total_amounts['tax_amount_currency'] += tax_values['tax_amount_currency']
                    total_amounts['tax_amount'] += tax_values['tax_amount']
                    total_amounts['tax_values_list'].append(tax_values)

            # Round them like what the creation of tax lines would do.
            for key, values in amount_per_tax_repartition_line_id.items():
                currency = self.env['res.currency'].browse(key['currency_id']) or comp_currency
                values['tax_amount_rounded'] = comp_currency.round(values['tax_amount'])
                values['tax_amount_currency_rounded'] = currency.round(values['tax_amount_currency'])

            # Dispatch the amount accross the tax values.
            for key, values in amount_per_tax_repartition_line_id.items():
                foreign_currency = self.env['res.currency'].browse(key['currency_id']) or comp_currency
                for currency, amount_field in ((comp_currency, 'tax_amount'), (foreign_currency, 'tax_amount_currency')):
                    raw_value = values[amount_field]
                    rounded_value = values[f'{amount_field}_rounded']
                    diff = rounded_value - raw_value
                    abs_diff = abs(diff)
                    diff_sign = -1 if diff < 0 else 1
                    tax_values_list = values['tax_values_list']
                    nb_error = math.ceil(abs_diff / currency.rounding)
                    nb_cents_per_tax_values = math.floor(nb_error / len(tax_values_list))
                    nb_extra_cent = nb_error % len(tax_values_list)

                    for tax_values in tax_values_list:
                        if not abs_diff:
                            break

                        nb_amount_curr_cent = nb_cents_per_tax_values
                        if nb_extra_cent:
                            nb_amount_curr_cent += 1
                            nb_extra_cent -= 1

                        # We can have more than one cent to distribute on a single tax_values.
                        abs_delta_to_add = min(abs_diff, currency.rounding * nb_amount_curr_cent)
                        tax_values[amount_field] += diff_sign * abs_delta_to_add
                        abs_diff -= abs_delta_to_add

        grouping_key_generator = grouping_key_generator or default_grouping_key_generator

        for base_line, to_update_vals, tax_values_list in to_process:
            record = base_line['record']

            # Add to global tax amounts.
            global_tax_details['base_amount_currency'] += to_update_vals['price_subtotal']

            currency = base_line['currency'] or self.env.company.currency_id
            base_amount = currency.round(to_update_vals['price_subtotal'] / base_line['rate'])
            global_tax_details['base_amount'] += base_amount

            for tax_values in tax_values_list:
                if filter_tax_values_to_apply and not filter_tax_values_to_apply(base_line, tax_values):
                    continue

                grouping_key = grouping_key_generator(base_line, tax_values)
                serialized_grouping_key = frozendict(grouping_key)

                # Add to invoice line global tax amounts.
                if serialized_grouping_key not in global_tax_details['tax_details_per_record'][record]:
                    record_global_tax_details = global_tax_details['tax_details_per_record'][record]
                    record_global_tax_details['base_amount_currency'] = to_update_vals['price_subtotal']
                    record_global_tax_details['base_amount'] = base_amount
                else:
                    record_global_tax_details = global_tax_details['tax_details_per_record'][record]

                add_tax_values(record, global_tax_details, grouping_key, serialized_grouping_key, tax_values)
                add_tax_values(record, record_global_tax_details, grouping_key, serialized_grouping_key, tax_values)

        return global_tax_details 
    
    def _get_generation_dict_from_base_line(self, line_vals, tax_vals, force_caba_exigibility=False):
        tax_repartition_line = tax_vals['tax_repartition_line']
        tax_account = tax_repartition_line._get_aml_target_tax_account(force_caba_exigibility=force_caba_exigibility) or line_vals['account']
        return {
            'account_id': tax_account.id,
            'currency_id': line_vals['currency'].id,
            'partner_id': line_vals['partner'].id,
            'tax_repartition_line_id': tax_repartition_line.id,
            'tax_ids': [Command.set(tax_vals['tax_ids'])],
            'tax_tag_ids': [Command.set(tax_vals['tag_ids'])],
            'tax_id': tax_vals['group'].id if tax_vals['group'] else tax_vals['id'],
            'analytic_distribution': line_vals['analytic_distribution'] if tax_vals['analytic'] else {},
            '_extra_grouping_key_': line_vals.get('extra_context', {}).get('_extra_grouping_key_'),
        }