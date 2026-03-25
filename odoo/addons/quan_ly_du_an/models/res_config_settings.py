# -*- coding: utf-8 -*-
from odoo import models, fields

class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    quan_ly_groq_api_key = fields.Char(string='Groq API Key (AI Llama 3)', config_parameter='quan_ly_du_an.groq_api_key')
    quan_ly_telegram_bot_token = fields.Char(string='Telegram Bot Token', config_parameter='quan_ly_du_an.telegram_bot_token')
    quan_ly_telegram_chat_id = fields.Char(string='Telegram Chat ID', config_parameter='quan_ly_du_an.telegram_chat_id')
