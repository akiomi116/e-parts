# app/routes/parts_routes.py

import os
import time
import qrcode
import csv
from werkzeug.utils import secure_filename
from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app
from ..models import db, Part, Tag

UPLOAD_FOLDER = 'static/images'
QR_UPLOAD_FOLDER = 'static/qr'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'csv'}

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

parts_bp = Blueprint('parts', __name__, url_prefix='/parts')

@parts_bp.route('/new', methods=['GET', 'POST'])
def part_create():
    all_tags = Tag.query.order_by(Tag.name).all()
    if request.method == 'POST':
        name = request.form.get('name')
        category = request.form.get('category')
        package = request.form.get('package')
        quantity = request.form.get('quantity', 0)
        location = request.form.get('location')
        note = request.form.get('note')
        selected_tag_ids = request.form.getlist('tags')

        new_part = Part(
            name=name,
            category=category,
            package=package,
            quantity=int(quantity),
            location=location,
            note=note
        )
        
        # 画像ファイルの処理
        if 'image_file' in request.files:
            file = request.files['image_file']
            if file.filename != '' and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                # 保存パスを絶対パスで指定
                save_path = os.path.join(current_app.root_path, UPLOAD_FOLDER, filename)
                file.save(save_path)
                new_part.image_path = os.path.join(UPLOAD_FOLDER.split('/', 1)[1], filename).replace('\\', '/') # DBにはスラッシュ区切りで保存

        db.session.add(new_part) # QRコード生成のために先にコミットしてIDを取得
        db.session.commit()

        # QRコードの生成と保存
        qr_data = url_for('parts.part_detail', part_id=new_part.id, _external=True)
        qr_filename = f'part_{new_part.id}_{int(time.time())}.png'
        qr_save_path = os.path.join(current_app.root_path, QR_UPLOAD_FOLDER, qr_filename)
        
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )
        qr.add_data(qr_data)
        qr.make(fit=True)

        img = qr.make_image(fill_color="black", back_color="white")
        img.save(qr_save_path)
        new_part.qr_path = os.path.join(QR_UPLOAD_FOLDER.split('/', 1)[1], qr_filename).replace('\\', '/')

        # タグの関連付け
        for tag_id in selected_tag_ids:
            tag = Tag.query.get(tag_id)
            if tag:
                new_part.tags.append(tag)

        db.session.commit()

        flash('部品を登録しました！', 'success')
        return redirect(url_for('parts.parts_list'))

    return render_template('parts/form.html', mode='create', all_tags=all_tags)

@parts_bp.route('/')
def parts_list():
    query = Part.query.order_by(Part.created_at.desc())

    # 検索キーワードによるフィルタリング
    search_query = request.args.get('q', '')
    if search_query:
        query = query.filter(
            (Part.name.ilike(f'%{search_query}%')) |
            (Part.category.ilike(f'%{search_query}%')) |
            (Part.location.ilike(f'%{search_query}%'))
        )

    # タグによるフィルタリング
    selected_tag_ids = request.args.getlist('tags')
    if selected_tag_ids:
        # 選択されたタグIDを整数に変換
        selected_tag_ids = [int(tag_id) for tag_id in selected_tag_ids]
        # 複数のタグでフィルタリングする場合、各タグに紐づく部品をAND条件で絞り込む
        for tag_id in selected_tag_ids:
            query = query.filter(Part.tags.any(Tag.id == tag_id))

    parts = query.all()
    all_tags = Tag.query.order_by(Tag.name).all()

    return render_template('parts/list.html', parts=parts, all_tags=all_tags, selected_tag_ids=selected_tag_ids)

@parts_bp.route('/<int:part_id>/edit', methods=['GET', 'POST'])
def part_edit(part_id):
    part = Part.query.get_or_404(part_id)
    all_tags = Tag.query.order_by(Tag.name).all()

    if request.method == 'POST':
        part.name = request.form.get('name')
        part.category = request.form.get('category')
        part.package = request.form.get('package')
        part.quantity = request.form.get('quantity', type=int, default=0)
        part.location = request.form.get('location')
        part.note = request.form.get('note')
        selected_tag_ids = request.form.getlist('tags')

        # 画像ファイルの処理
        if 'image_file' in request.files:
            file = request.files['image_file']
            if file.filename != '' and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                save_path = os.path.join(current_app.root_path, UPLOAD_FOLDER, filename)
                file.save(save_path)
                part.image_path = os.path.join(UPLOAD_FOLDER.split('/', 1)[1], filename).replace('\\', '/')
            elif file.filename == '' and part.image_path: # ファイルが選択されず、既存の画像がある場合
                # 既存の画像を保持
                pass
            else: # ファイルが選択されず、既存の画像もない場合
                part.image_path = None

        # QRコードの生成と保存 (編集時)
        qr_data = url_for('parts.part_detail', part_id=part.id, _external=True)
        qr_filename = f'part_{part.id}_{int(time.time())}.png'
        qr_save_path = os.path.join(current_app.root_path, QR_UPLOAD_FOLDER, qr_filename)
        
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )
        qr.add_data(qr_data)
        qr.make(fit=True)

        img = qr.make_image(fill_color="black", back_color="white")
        img.save(qr_save_path)
        part.qr_path = os.path.join(QR_UPLOAD_FOLDER.split('/', 1)[1], qr_filename).replace('\\', '/')

        # 既存のタグ関連付けをクリアして再設定
        part.tags.clear()
        for tag_id in selected_tag_ids:
            tag = Tag.query.get(tag_id)
            if tag:
                part.tags.append(tag)

        db.session.commit()
        flash('部品情報を更新しました！', 'success')
        return redirect(url_for('parts.parts_list'))

    return render_template('parts/form.html', part=part, mode='edit', all_tags=all_tags)

@parts_bp.route('/<int:part_id>')
def part_detail(part_id):
    part = Part.query.get_or_404(part_id)
    return render_template('parts/detail.html', part=part)

@parts_bp.route('/<int:part_id>/delete', methods=['POST'])
def part_delete(part_id):
    part = Part.query.get_or_404(part_id)
    db.session.delete(part)
    db.session.commit()
    flash('部品を削除しました。', 'success')
    return redirect(url_for('parts.parts_list'))

@parts_bp.route('/<int:part_id>/update_quantity', methods=['POST'])
def update_quantity(part_id):
    part = Part.query.get_or_404(part_id)
    
    # フォームから送信された数量を取得
    new_quantity_str = request.form.get('quantity')
    
    # 数量が空でないか、整数に変換できるかを確認
    if new_quantity_str and new_quantity_str.isdigit():
        part.quantity = int(new_quantity_str)
        db.session.commit()
        flash('在庫数を更新しました。', 'success')
    else:
        flash('無効な数量です。', 'error')
        
    return redirect(url_for('parts.part_detail', part_id=part_id))

@parts_bp.route('/upload', methods=['GET', 'POST'])
def upload_csv():
    if request.method == 'POST':
        if 'csv_file' not in request.files:
            flash('ファイルがありません', 'error')
            return redirect(request.url)
        
        file = request.files['csv_file']
        
        if file.filename == '':
            flash('ファイルが選択されていません', 'error')
            return redirect(request.url)
        
        if file and allowed_file(file.filename):
            try:
                # ストリームから直接CSVを読み込む
                csv_file = file.stream.read().decode('utf-8-sig').splitlines()
                csv_reader = csv.DictReader(csv_file)
                
                for row in csv_reader:
                    # 新しいPartオブジェクトを作成
                    new_part = Part(
                        name=row.get('name'),
                        category=row.get('category'),
                        package=row.get('package'),
                        quantity=int(row.get('quantity', 0)),
                        location=row.get('location'),
                        note=row.get('note')
                    )
                    
                    db.session.add(new_part)
                    db.session.commit() # IDを取得するためにコミット

                    # QRコードの生成
                    qr_data = url_for('parts.part_detail', part_id=new_part.id, _external=True)
                    qr_filename = f'part_{new_part.id}_{int(time.time())}.png'
                    qr_save_path = os.path.join(current_app.root_path, QR_UPLOAD_FOLDER, qr_filename)
                    
                    qr = qrcode.QRCode(version=1, error_correction=qrcode.constants.ERROR_CORRECT_L, box_size=10, border=4)
                    qr.add_data(qr_data)
                    qr.make(fit=True)
                    img = qr.make_image(fill_color="black", back_color="white")
                    img.save(qr_save_path)
                    new_part.qr_path = os.path.join(QR_UPLOAD_FOLDER.split('/', 1)[1], qr_filename).replace('\\', '/')

                    # タグの処理
                    if 'tags' in row and row['tags']:
                        tag_names = [tag.strip() for tag in row['tags'].split(',')]
                        for tag_name in tag_names:
                            if not tag_name:
                                continue
                            tag = Tag.query.filter_by(name=tag_name).first()
                            if not tag:
                                tag = Tag(name=tag_name)
                                db.session.add(tag)
                                db.session.commit() # 新しいタグを保存
                            new_part.tags.append(tag)
                
                db.session.commit()
                flash('CSVファイルから部品が一括登録されました！', 'success')
                return redirect(url_for('parts.parts_list'))

            except Exception as e:
                db.session.rollback()
                flash(f'エラーが発生しました: {e}', 'error')
                return redirect(request.url)
        else:
            flash('許可されていないファイル形式です', 'error')
            return redirect(request.url)
            
    return render_template('parts/upload.html')