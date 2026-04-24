from flask import redirect, url_for
from flask_login import login_required, current_user
from . import bp

@bp.route('/')
def index():
    from flask_login import logout_user, current_user
    if current_user.is_authenticated:
        logout_user()
    return redirect(url_for('auth.login'))
