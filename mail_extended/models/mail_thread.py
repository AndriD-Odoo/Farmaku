import logging
import threading

from odoo import _, api, exceptions, fields, models, tools, registry, SUPERUSER_ID

from odoo.tools.misc import clean_context, split_every

_logger = logging.getLogger(__name__)


class MailThread(models.AbstractModel):
    _inherit = 'mail.thread'

    def _notify_record_by_email(self, message, recipients_data, msg_vals=False,
                                model_description=False, mail_auto_delete=True, check_existing=False,
                                force_send=True, send_after_commit=True,
                                **kwargs):
        """ Method to send email linked to notified messages.

        :param message: mail.message record to notify;
        :param recipients_data: see ``_notify_thread``;
        :param msg_vals: see ``_notify_thread``;

        :param model_description: model description used in email notification process
          (computed if not given);
        :param mail_auto_delete: delete notification emails once sent;
        :param check_existing: check for existing notifications to update based on
          mailed recipient, otherwise create new notifications;

        :param force_send: send emails directly instead of using queue;
        :param send_after_commit: if force_send, tells whether to send emails after
          the transaction has been committed using a post-commit hook;
        """
        partners_data = [r for r in recipients_data['partners'] if r['notif'] == 'email']
        if not partners_data:
            return True

        model = msg_vals.get('model') if msg_vals else message.model
        model_name = model_description or (self._fallback_lang().env['ir.model']._get(model).display_name if model else False) # one query for display name
        recipients_groups_data = self._notify_classify_recipients(partners_data, model_name, msg_vals=msg_vals)

        if not recipients_groups_data:
            return True
        force_send = self.env.context.get('mail_notify_force_send', force_send)

        template_values = self._notify_prepare_template_context(message, msg_vals, model_description=model_description) # 10 queries

        email_layout_xmlid = msg_vals.get('email_layout_xmlid') if msg_vals else message.email_layout_xmlid
        template_xmlid = email_layout_xmlid if email_layout_xmlid else 'mail.message_notification_email'
        try:
            base_template = self.env.ref(template_xmlid, raise_if_not_found=True).with_context(lang=template_values['lang']) # 1 query
        except ValueError:
            _logger.warning('QWeb template %s not found when sending notification emails. Sending without layouting.' % (template_xmlid))
            base_template = False

        mail_subject = message.subject or (message.record_name and 'Re: %s' % message.record_name) # in cache, no queries
        # Replace new lines by spaces to conform to email headers requirements
        mail_subject = ' '.join((mail_subject or '').splitlines())
        # compute references: set references to the parent and add current message just to
        # have a fallback in case replies mess with Messsage-Id in the In-Reply-To (e.g. amazon
        # SES SMTP may replace Message-Id and In-Reply-To refers an internal ID not stored in Odoo)
        message_sudo = message.sudo()
        if message_sudo.parent_id:
            references = f'{message_sudo.parent_id.message_id} {message_sudo.message_id}'
        else:
            references = message_sudo.message_id
        # prepare notification mail values
        base_mail_values = {
            'mail_message_id': message.id,
            'mail_server_id': message.mail_server_id.id, # 2 query, check acces + read, may be useless, Falsy, when will it be used?
            'auto_delete': mail_auto_delete,
            # due to ir.rule, user have no right to access parent message if message is not published
            'references': references,
            'subject': mail_subject,
        }
        base_mail_values = self._notify_by_email_add_values(base_mail_values)

        # Clean the context to get rid of residual default_* keys that could cause issues during
        # the mail.mail creation.
        # Example: 'default_state' would refer to the default state of a previously created record
        # from another model that in turns triggers an assignation notification that ends up here.
        # This will lead to a traceback when trying to create a mail.mail with this state value that
        # doesn't exist.
        SafeMail = self.env['mail.mail'].sudo().with_context(clean_context(self._context))
        SafeNotification = self.env['mail.notification'].sudo().with_context(clean_context(self._context))
        emails = self.env['mail.mail'].sudo()

        # loop on groups (customer, portal, user,  ... + model specific like group_sale_salesman)
        notif_create_values = []
        recipients_max = 50
        email_to = []
        recipient_ids = []
        recipients_group_data = []
        for recipients_group_data in recipients_groups_data:
            # generate notification email content
            recipients_group_data = recipients_group_data
        for partner_id in message.partner_ids:
            if partner_id.email and partner_id.email not in kwargs.get('email_cc', {}):
                email_to.append(partner_id.email)
                recipient_ids.append(partner_id.id)
        if not email_to and kwargs.get('email_cc'):
            email_cc_list = kwargs.get('email_cc').split(',')
            email_to.append(email_cc_list[0]) # trigger
        render_values = {**template_values, **recipients_group_data}
        # {company, is_discussion, lang, message, model_description, record, record_name, signature, subtype, tracking_values, website_url}
        # {actions, button_access, has_button_access, recipients}

        if base_template:
            mail_body = base_template._render(render_values, engine='ir.qweb', minimal_qcontext=True)
        else:
            mail_body = message.body
        mail_body = self.env['mail.render.mixin']._replace_local_links(mail_body)

        # create email
        create_values = {
            'body_html': mail_body,
            'subject': mail_subject,
            'email_to': ', '.join(email_to),
            # 'recipient_ids': [(4, pid) for pid in recipient_ids],
        }
        if kwargs.get('email_cc'):
            create_values['email_cc'] = kwargs['email_cc']
        create_values.update(base_mail_values)  # mail_message_id, mail_server_id, auto_delete, references, headers
        email = SafeMail.create(create_values)

        if email and recipient_ids:
            tocreate_recipient_ids = list(recipient_ids)
            if check_existing:
                existing_notifications = self.env['mail.notification'].sudo().search([
                    ('mail_message_id', '=', message.id),
                    ('notification_type', '=', 'email'),
                    ('res_partner_id', 'in', tocreate_recipient_ids)
                ])
                if existing_notifications:
                    tocreate_recipient_ids = [rid for rid in recipient_ids if rid not in existing_notifications.mapped('res_partner_id.id')]
                    existing_notifications.write({
                        'notification_status': 'ready',
                        'mail_id': email.id,
                    })
            notif_create_values += [{
                'mail_message_id': message.id,
                'res_partner_id': recipient_id,
                'notification_type': 'email',
                'mail_id': email.id,
                'is_read': True,  # discard Inbox notification
                'notification_status': 'ready',
            } for recipient_id in tocreate_recipient_ids]
        emails |= email

        if notif_create_values:
            SafeNotification.create(notif_create_values)

        # NOTE:
        #   1. for more than 50 followers, use the queue system
        #   2. do not send emails immediately if the registry is not loaded,
        #      to prevent sending email during a simple update of the database
        #      using the command-line.
        test_mode = getattr(threading.currentThread(), 'testing', False)
        if force_send and len(emails) < recipients_max and (not self.pool._init or test_mode):
            # unless asked specifically, send emails after the transaction to
            # avoid side effects due to emails being sent while the transaction fails
            if not test_mode and send_after_commit:
                email_ids = emails.ids
                dbname = self.env.cr.dbname
                _context = self._context

                @self.env.cr.postcommit.add
                def send_notifications():
                    db_registry = registry(dbname)
                    with api.Environment.manage(), db_registry.cursor() as cr:
                        env = api.Environment(cr, SUPERUSER_ID, _context)
                        env['mail.mail'].browse(email_ids).send()
            else:
                emails.send()

        return True
