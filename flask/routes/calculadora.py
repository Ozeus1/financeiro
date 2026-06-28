from flask import Blueprint, render_template
from flask_login import login_required

calculadora_bp = Blueprint('calculadora', __name__)


@calculadora_bp.route('/')
@login_required
def index():
    return render_template('calculadora/index.html')
