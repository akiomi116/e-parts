from flask import Blueprint, render_template, request
from ..models import Part

labels_bp = Blueprint('labels', __name__, url_prefix='/labels')

@labels_bp.route('/select')
def labels_select():
    parts = Part.query.order_by(Part.name).all()
    return render_template('labels/select.html', parts=parts)

@labels_bp.route('/print')
def labels_print():
    part_ids = request.args.getlist('part_ids')
    # part_ids は文字列のリストなので、整数に変換
    part_ids_int = [int(id) for id in part_ids if id.isdigit()]
    
    # 選択されたIDに基づいて部品を取得
    parts_to_print = Part.query.filter(Part.id.in_(part_ids_int)).order_by(Part.name).all()
    
    return render_template('labels/print.html', parts=parts_to_print)
