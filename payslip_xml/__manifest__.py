{
    'name': 'Mexico - Payroll CFDI XML',
    'countries': ['mx'],
    'category': 'Human Resources/Payroll',
    'depends': ['l10n_mx_hr_payroll_account', 'l10n_mx_edi'],
    'auto_install': ['l10n_mx_hr_payroll_account'],
    'version': '1.0',
    'description': 'Adds CFDI to the payroll flow',
    'data': [],
    'demo': [],
    'assets': {
        'web.assets_backend': [
            'l10n_mx_hr_payroll_account_edi/static/src/**/*',
            ('remove', 'l10n_mx_hr_payroll_account_edi/static/src/scss/*.scss'),
        ],
        'web.report_assets_common': [
            'l10n_mx_hr_payroll_account_edi/static/src/scss/*.scss',
        ]
    },
    'author': 'Odoo S.A.',
    'license': 'OEEL-1',
}