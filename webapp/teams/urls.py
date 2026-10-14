"""旧 tenant.py の処理を役割別に分割。"""
import re


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


def safe_realm(slug):
    cleaned = re.sub(r'[^A-Za-z0-9_-]', '', slug or '')
    return f'team-{cleaned}' if cleaned else 'team'
