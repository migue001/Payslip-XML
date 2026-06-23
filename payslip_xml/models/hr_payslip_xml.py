from collections import defaultdict
from dateutil.relativedelta import relativedelta
from markupsafe import Markup
from werkzeug.urls import url_quote_plus
import logging

from odoo import api, fields, models
from odoo.addons.base.models.ir_qweb import keep_query
from odoo.addons.l10n_mx_edi.models.l10n_mx_edi_document import CFDI_DATE_FORMAT
from odoo.exceptions import ValidationError

_logger = logging.getLogger(__name__)

class Hrpayslip(models.Model):
    _inherit = 'hr.payslip'

    def _l10n_mx_edi_add_payslip_cfdi_values(self, cfdi_values=None):
        cfdi_values = super()._l10n_mx_edi_add_payslip_cfdi_values(cfdi_values)

        rules_amount = {
            line.salary_rule_id: abs(line.total)
            for line in self.line_ids
        }

        integrated_daily_wage_rule = self.env.ref(
            '__custom__sdi.sdi_custom',
            raise_if_not_found=False
        )

        integrated_daily_wage = (
            rules_amount[integrated_daily_wage_rule]
            if integrated_daily_wage_rule and integrated_daily_wage_rule in rules_amount
            else 0
        )

        cfdi_values['nomina_receptor']['salario_diario_integrado'] = integrated_daily_wage
        cfdi_values['nomina_receptor']['salario_base_cot_apor'] = integrated_daily_wage
        cfdi_values['nomina_receptor']['fecha_inicio_rel_laboral'] = self.employee_id.x_studio_fecha_ingreso.isoformat()
        cfdi_values['nomina_receptor']['antigüedad'] = f'P{(self.date_to - self.employee_id.x_studio_fecha_ingreso).days // 7}W'


        # ==========================
        # Subsidio vs ISR
        # ==========================

        subsidy_amount = 0.0

        # Buscar OtroPago 002
        for other_payment in cfdi_values.get('otro_pago_list', []):
            if other_payment.get('tipo_otro_pago') == '002':

                subsidy_amount = float(
                    other_payment.get('subsidio_causado')
                    or other_payment.get('importe')
                    or 0.0
                )

                # Dejar Importe="0.00"
                other_payment['importe'] = 0.0
                break

        if subsidy_amount:

            # Restar subsidio al ISR retenido
            for deduction in cfdi_values.get('deduccion_list', []):
                if deduction.get('tipo_deduccion') == '002':
                    deduction['importe'] = round(
                        max(float(deduction.get('importe', 0.0)) - subsidy_amount, 0.0),
                        2
                    )
                    break

            # ==========================
            # Recalcular deducciones
            # ==========================

            total_taxes_withheld = sum(
                float(d.get('importe', 0.0))
                for d in cfdi_values.get('deduccion_list', [])
                if d.get('tipo_deduccion') == '002'
            )

            total_other_deductions = sum(
                float(d.get('importe', 0.0))
                for d in cfdi_values.get('deduccion_list', [])
                if d.get('tipo_deduccion') != '002'
            )

            total_deductions = (
                total_taxes_withheld
                + total_other_deductions
            )

            cfdi_values['nomina_deducciones']['total_impuestos_retenidos'] = round(
                total_taxes_withheld, 2
            )

            cfdi_values['nomina_deducciones']['total_otras_deducciones'] = round(
                total_other_deductions, 2
            )

            cfdi_values['nomina']['total_deducciones'] = round(
                total_deductions, 2
            )

            # ==========================
            # Recalcular Otros Pagos
            # ==========================

            total_other_payments = sum(
                float(op.get('importe', 0.0))
                for op in cfdi_values.get('otro_pago_list', [])
            )

            cfdi_values['nomina']['total_otros_pagos'] = round(
                total_other_payments, 2
            )

            # ==========================
            # Recalcular CFDI
            # ==========================

            total_perceptions = float(
                cfdi_values['nomina'].get('total_percepciones', 0.0)
            )

            subtotal = round(
                total_perceptions + total_other_payments,
                2
            )

            cfdi_values['subtotal'] = subtotal

            cfdi_values['concepto']['valor_unitario'] = subtotal
            cfdi_values['concepto']['importe'] = subtotal

            cfdi_values['descuento'] = round(
                total_deductions,
                2
            )

            cfdi_values['concepto']['descuento'] = round(
                total_deductions,
                2
            )

            cfdi_values['total'] = round(
                subtotal - total_deductions,
                2
            )
        
        return cfdi_values
    