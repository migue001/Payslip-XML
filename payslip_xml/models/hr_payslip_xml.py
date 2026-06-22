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
        
        return cfdi_values
    