from flask import Blueprint, render_template, request, redirect, url_for, flash
from ..models import db, Tag

tags_bp = Blueprint('tags', __name__, url_prefix='/tags')

@tags_bp.route('/', methods=['GET', 'POST'])
def tag_list():
    if request.method == 'POST':
        name = request.form.get('name')
        if name:
            # タグの重複をチェック
            existing_tag = Tag.query.filter_by(name=name).first()
            if existing_tag:
                flash('同じ名前のタグが既に存在します。', 'warning')
            else:
                new_tag = Tag(name=name)
                db.session.add(new_tag)
                db.session.commit()
                flash('新しいタグを登録しました！', 'success')
        return redirect(url_for('tags.tag_list'))

    tags = Tag.query.order_by(Tag.name).all()
    return render_template('tags/list.html', tags=tags)

@tags_bp.route('/<int:tag_id>/edit', methods=['GET', 'POST'])
def tag_edit(tag_id):
    tag = Tag.query.get_or_404(tag_id)

    if request.method == 'POST':
        name = request.form.get('name')
        if name:
            # 重複チェック（自分自身を除く）
            existing_tag = Tag.query.filter(Tag.name == name, Tag.id != tag_id).first()
            if existing_tag:
                flash('同じ名前のタグが既に存在します。', 'warning')
            else:
                tag.name = name
                db.session.commit()
                flash('タグ名を更新しました！', 'success')
                return redirect(url_for('tags.tag_list'))

    return render_template('tags/form.html', tag=tag, mode='edit')

@tags_bp.route('/<int:tag_id>/delete', methods=['POST'])
def tag_delete(tag_id):
    tag = Tag.query.get_or_404(tag_id)
    db.session.delete(tag)
    db.session.commit()
    flash('タグを削除しました。', 'success')
    return redirect(url_for('tags.tag_list'))
