# -*- coding: utf-8 -*-
from odoo import http
from odoo.http import request

class ProjectPitchDeck(http.Controller):

    @http.route('/quan_ly_du_an/pitch_deck/<int:project_id>', type='http', auth='user', website=True)
    def render_pitch_deck(self, project_id, **kw):
        project = request.env['quan_ly.du_an'].sudo().browse(project_id)
        if not project.exists():
            return request.not_found()

        # Render the template with the robust Reveal.js logic
        values = {
            'project': project,
        }
        return request.render('quan_ly_du_an.pitch_deck_template', values)
