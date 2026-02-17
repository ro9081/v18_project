# -*- coding: utf-8 -*-
import random
import string

from odoo import models, fields, _,api
from odoo.exceptions import UserError
from odoo.exceptions import ValidationError
import requests
import json
import tempfile
import os
from odoo.modules.module import get_module_path
from cryptography.hazmat.primitives.serialization import pkcs12, Encoding, NoEncryption, PrivateFormat
from cryptography.hazmat.backends import default_backend

class AccountMove(models.Model):
    _inherit = "account.move"

    ultiqa_l10n_fj_edi_cancel_reason = fields.Selection(selection=[
        ("1", "Duplicate"),
        ("2", "Data Entry Mistake"),
        ("3", "Order Cancelled"),
        ("4", "Others"),
        ], string="Cancel reason", copy=False)
    ultiqa_l10n_fj_edi_cancel_remarks = fields.Char("Cancel remarks", copy=False)
    ultiqa_l10n_fj_edi_show_cancel = fields.Boolean(string="E-invoice(IN) is sent?")
    ultiqa_edi_document_ids = fields.One2many(
        comodel_name='account.edi.document',
        inverse_name='move_id')
    ultiqa_ref_doc_number = fields.Char(string='Ref. Document Number', copy=False)
    ultiqa_seq_proforma = fields.Char(string='Seq. Proforma', default=False, copy=False)
    def button_process_edi_web_services(self):
        self.ensure_one()
        self.action_process_edi_web_services(with_commit=False)
    def _post(self, soft=True):
        # OVERRIDE
        # Set the electronic document to be posted and post immediately for synchronous formats.
        posted = super()._post(soft=soft)

        edi_document_vals_list = []
        for move in posted:
            for edi_format in move.journal_id.edi_format_ids:
                move_applicability = edi_format._get_move_applicability(move)

                if edi_format:
                    errors = edi_format._check_move_configuration(move)
                    if errors:
                        raise UserError(_("Invalid invoice configuration:\n\n%s", '\n'.join(errors)))

                    existing_edi_document = move.edi_document_ids.filtered(lambda x: x.edi_format_id == edi_format)
                    if existing_edi_document:
                        existing_edi_document.sudo().write({
                            'state': 'to_send',
                            'attachment_id': False,
                        })
                    else:
                        edi_document_vals_list.append({
                            'edi_format_id': edi_format.id,
                            'move_id': move.id,
                            'state': 'to_send',
                        })

        self.env['account.edi.document'].create(edi_document_vals_list)
        posted.edi_document_ids._process_documents_no_web_services()
        if self.edi_document_ids:
            self.button_process_edi_web_services()
        if not self.env.context.get('skip_account_edi_cron_trigger'):
            self.env.ref('account_edi.ir_cron_edi_network')._trigger()
        return posted

    # def _compute_l10n_fj_edi_show_cancel_asc(self):
    #     pass
        # for invoice in self:
        #     invoice.l10n_in_edi_show_cancel = bool(invoice.edi_document_ids.filtered(
        #         lambda i: i.edi_format_id.code == "in_einvoice_1_03"
        #         and i.state in ("sent", "to_cancel", "cancelled")
        #     ))

    # def button_cancel_posted_moves(self):
    #     """Mark the edi.document related to this move to be canceled."""
    #     reason_and_remarks_not_set = self.env["account.move"]
    #     for move in self:
    #         send_l10n_in_edi = move.edi_document_ids.filtered(lambda doc: doc.edi_format_id.code == "in_einvoice_1_03")
    #         # check submitted E-invoice does not have reason and remarks
    #         # because it's needed to cancel E-invoice
    #         if send_l10n_in_edi and (not move.l10n_in_edi_cancel_reason or not move.l10n_in_edi_cancel_remarks):
    #             reason_and_remarks_not_set += move
    #     if reason_and_remarks_not_set:
    #         raise UserError(_(
    #             "To cancel E-invoice set cancel reason and remarks at Other info tab in invoices: \n%s",
    #             ("\n".join(reason_and_remarks_not_set.mapped("name"))),
    #         ))
    #     return super().button_cancel_posted_moves()
    def _prepare_and_process_edi_documents(self):
        """ Common helper to prepare and process EDI documents. """
        for move in self:
            edi_document_vals_list = []
            for edi_format in move.journal_id.edi_format_ids:
                existing_edi_document = move.edi_document_ids.filtered(
                    lambda x: x.edi_format_id == edi_format
                )
                if existing_edi_document:
                    existing_edi_document.sudo().write({
                        'state': 'to_send',
                        'attachment_id': False,
                    })
                else:
                    edi_document_vals_list.append({
                        'edi_format_id': edi_format.id,
                        'move_id': move.id,
                        'state': 'to_send',
                    })
            if edi_document_vals_list:
                self.env['account.edi.document'].create(edi_document_vals_list)
            move.edi_document_ids._process_documents_no_web_services()
            if move.edi_document_ids:
                move.button_process_edi_web_services()

    def action_create_invoice_from_draft(self):
        for move in self:
            if move.ultiqa_seq_proforma:
                raise ValidationError("Proforma has already been generated for this invoice.")
            move.ultiqa_seq_proforma = self.env['ir.sequence'].next_by_code('account.move.proforma')
            if move.state != 'draft':
                raise ValidationError("Proforma can only be generated in Draft stage.")
            move._prepare_and_process_edi_documents()

    def action_create_refund_from_draft(self):
        for move in self:
            if move.state != 'draft':
                raise ValidationError("Refund can only be created in Draft stage.")
            if not move.ultiqa_seq_proforma:
                raise ValidationError("Refund can only be created if Proforma is generated.")
            if move.move_type == 'out_invoice':
                move.move_type = 'out_refund'
            elif move.move_type == 'in_invoice':
                move.move_type = 'in_refund'
            else:
                raise ValidationError("Refund can only be created from Customer Invoice or Vendor Bill.")
            move._prepare_and_process_edi_documents()

    def action_copy_sale_and_refund_invoice(self):
        for move in self:
            move._prepare_and_process_edi_documents()

    def _get_l10n_in_edi_response_json(self):
        self.ensure_one()
        l10n_in_edi = self.edi_document_ids.filtered(lambda i: i.edi_format_id.code == "fj_einvoice_1_03"
            and i.state in ("sent", "to_cancel"))
        if l10n_in_edi:
            return json.loads(l10n_in_edi.sudo().attachment_id.raw.decode("utf-8"))
        else:
            return {}

    # def _can_force_cancel(self):
    #     # OVERRIDE
    #     self.ensure_one()
    #     return any(document.edi_format_id.code == 'in_einvoice_1_03' and document.state == 'to_cancel' for document in self.edi_document_ids) or super()._can_force_cancel()