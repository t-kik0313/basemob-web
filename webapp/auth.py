from flask import g, redirect, request, Response
from itsdangerous import BadSignature, URLSafeTimedSerializer

from webapp.config import LOGIN_DAYS, SECRET_KEY
from webapp.tenant import all_teams, password_matches, safe_realm, team_by_id, team_by_slug

COOKIE_NAME = "team_login"
COOKIE_MAX_AGE = LOGIN_DAYS * 24 * 60 * 60


def register_auth(app):
    app.secret_key = SECRET_KEY
    serializer = URLSafeTimedSerializer(SECRET_KEY, salt="team-login")

    def cookie_team_id():
        token = request.cookies.get(COOKIE_NAME)
        if not token:
            return None
        try:
            data = serializer.loads(token, max_age=COOKIE_MAX_AGE)
        except BadSignature:
            return None
        if isinstance(data, dict):
            return data.get('team')
        return None

    def credentials():
        auth = request.authorization
        if not auth:
            return '', ''
        return auth.username or '', auth.password or ''

    def deny(slug):
        return Response(
            'このチームを開くには、チームのIDとパスワードが必要です。',
            401,
            {'WWW-Authenticate': f'Basic realm="{safe_realm(slug)}"'},
        )

    def public_schedule(path):
        path = path.rstrip('/') or '/'
        if request.method == 'GET' and path in ('/schedule', '/api/schedule', '/events', '/api/events'):
            return True
        return request.method == 'POST' and path in ('/api/schedule/poll', '/api/events')

    def send_to_team(team, path):
        g.remember_team = team['id']
        target = '/players' if path in ('', '/') else path
        if request.query_string:
            target = f"{target}?{request.query_string.decode()}"
        return redirect(f"/t/{team['slug']}{target}")

    @app.before_request
    def require_login():
        path = request.path
        if path.startswith('/static/') or path == '/favicon.ico':
            return None

        slug = request.environ.get('basemob.team_slug')
        username, password = credentials()
        if slug:
            g.team_slug = slug
            team = team_by_slug(slug)
            if team is None:
                return deny(slug)
            signed_in = cookie_team_id()
            logged_in = signed_in == team['id']
            if not logged_in and password_matches(team, username, password):
                g.remember_team = team['id']
                logged_in = True
            if logged_in:
                return None
            if public_schedule(path):
                g.public_view = True
                if path.endswith('/') and path != '/':
                    target = path.rstrip('/')
                    if request.query_string:
                        target = f"{target}?{request.query_string.decode()}"
                    return redirect(f"/t/{slug}{target}")
                return None
            return deny(slug)

        signed_in = cookie_team_id()
        if signed_in:
            team = team_by_id(signed_in)
            if team:
                return send_to_team(team, path)
        for team in all_teams():
            if password_matches(team, username, password):
                return send_to_team(team, path)
        return deny(None)

    @app.after_request
    def remember_login(response):
        team_id = getattr(g, 'remember_team', None)
        if team_id:
            response.set_cookie(
                COOKIE_NAME,
                serializer.dumps({'team': team_id}),
                max_age=COOKIE_MAX_AGE,
                httponly=True,
                samesite='Lax',
                path='/',
            )
        return response
