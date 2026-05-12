from flask import redirect, url_for, session
from flask_login import login_required, logout_user, current_user
from ... import db
from . import bp

@bp.route('/logout')
@login_required
def logout():
    # Clear token from db
    current_user.session_token = None
    db.session.commit()
    logout_user()
    session.clear()
    return redirect(url_for('auth.login'))
