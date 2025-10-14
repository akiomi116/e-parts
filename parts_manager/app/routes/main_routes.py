from flask import Blueprint

main_bp = Blueprint('main', __name__)

@main_bp.route('/')
def index():
    return '<h1>電子部品管理システム</h1><p><a href="/parts/">部品一覧</a></p><p><a href="/tags/">タグ一覧</a></p><p><a href="/labels/select">ラベル印刷</a></p>'
