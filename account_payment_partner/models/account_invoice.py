# -*- coding: utf-8 -*-
# © 2014-2016 Akretion - Alexis de Lattre <alexis.delattre@akretion.com>
# © 2014 Serv. Tecnol. Avanzados - Pedro M. Baeza
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from openerp import models, fields, api


class AccountInvoice(models.Model):
    _inherit = 'account.invoice'

    payment_mode_id = fields.Many2one(
        comodel_name='account.payment.mode', string="Payment Mode",
        ondelete='restrict',
        readonly=True, states={'draft': [('readonly', False)]})

    @api.onchange('partner_id', 'company_id', 'type')
    def _onchange_partner_id(self):
        super(AccountInvoice, self)._onchange_partner_id()
        if self.partner_id and self.type:
            if self.type == 'in_invoice':
                self.payment_mode_id =\
                    self.partner_id.supplier_payment_mode_id
            elif self.type == 'out_invoice':
                payment_mode = self.partner_id.customer_payment_mode_id
                self.payment_mode_id = payment_mode
                if payment_mode and payment_mode.bank_account_link == 'fixed':
                    self.partner_bank_id = payment_mode.fixed_journal_id.\
                        bank_account_id
        else:
            self.payment_mode_id = False

    @api.model
    def line_get_convert(self, line, part):
        """Copy payment mode from invoice to account move line"""
        res = super(AccountInvoice, self).line_get_convert(line, part)
        if line.get('type') == 'dest' and line.get('invoice_id'):
            invoice = self.browse(line['invoice_id'])
            res['payment_mode_id'] = invoice.payment_mode_id.id or False
        return res

    # I think copying payment mode from invoice to refund by default
    # is a good idea because the most common way of "paying" a refund is to
    # deduct it on the payment of the next invoice (and OCA/bank-payment
    # allows to have negative payment lines since March 2016)
    @api.model
    def _prepare_refund(
            self, invoice, date_invoice=None, date=None, description=None,
            journal_id=None):
        vals = super(AccountInvoice, self)._prepare_refund(
            invoice, date_invoice=date_invoice, date=date,
            description=description, journal_id=journal_id)
        vals['payment_mode_id'] = invoice.payment_mode_id.id
        if invoice.type == 'in_invoice':
            vals['partner_bank_id'] = invoice.partner_bank_id.id
        return vals
