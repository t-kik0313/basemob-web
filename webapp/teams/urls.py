"""旧 tenant.py の処理を役割別に分割。"""
import re
from flask import url_for
from webapp.teams.context import current_slug, current_team


class TeamPrefix:
    def __init__(self, app):
        self.app = app

    def __call__(self, environ, start_response):
        path = environ.get('PATH_INFO', '') or '/'
        parts = path.split('/')
        if len(parts) >= 3 and parts[1] == 't' and parts[2]:
            environ['basemob.team_slug'] = parts[2]
            rest = '/' + '/'.join(parts[3:])
            environ['PATH_INFO'] = rest if rest != '/' else '/'
        return self.app(environ, start_response)



def install_team_urls(app):
    app.wsgi_app = TeamPrefix(app.wsgi_app)

    def team_url_for(endpoint, **values):
        external = values.get('_external') or values.get('_scheme')
        url = url_for(endpoint, **values)
        if external or endpoint == 'static' or not url.startswith('/') or url.startswith('/static') or url.startswith('/t/'):
            return url
        slug = current_slug()
        if not slug:
            return url
        return f'/t/{slug}{url}'

    app.jinja_env.globals['url_for'] = team_url_for

    @app.context_processor
    def inject_team():
        team = current_team()
        if not team:
            return {
                'team_name': '',
                'team_id': '',
                'schedule_api': '/api/schedule',
                'abilities_api': '/api/update_abilities',
                'score_entry_url': 'https://basemob-207a2.web.app/app.html',
            }
        slug = team['slug']
        return {
            'team_name': team['name'],
            'team_id': team['id'],
            'schedule_api': f'/t/{slug}/api/schedule',
            'abilities_api': f'/t/{slug}/api/update_abilities',
            'score_entry_url': f"https://basemob-207a2.web.app/app.html?team={team['id']}",
        }



def safe_realm(slug):
    cleaned = re.sub(r'[^A-Za-z0-9_-]', '', slug or '')
    return f'team-{cleaned}' if cleaned else 'team'
