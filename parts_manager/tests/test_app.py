
import unittest
import os
import sys
from io import BytesIO

# プロジェクトルートをパスに追加
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import create_app, db
from app.models import Part, Tag

class BasicTests(unittest.TestCase):

    def setUp(self):
        """各テストの前に実行"""
        self.app = create_app()
        self.app.config['TESTING'] = True
        self.app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
        # UPLOAD_FOLDERとQR_UPLOAD_FOLDERがテスト中に存在するようにする
        # app.root_path は parts_manager/app なので、そこからの相対パスで設定
        base_dir = os.path.dirname(self.app.root_path)
        self.app.config['UPLOAD_FOLDER'] = os.path.join(base_dir, 'static', 'images', 'test')
        self.app.config['QR_UPLOAD_FOLDER'] = os.path.join(base_dir, 'static', 'qr', 'test')
        os.makedirs(self.app.config['UPLOAD_FOLDER'], exist_ok=True)
        os.makedirs(self.app.config['QR_UPLOAD_FOLDER'], exist_ok=True)
        
        self.app_context = self.app.app_context()
        self.app_context.push()
        db.create_all()
        self.client = self.app.test_client()

    def tearDown(self):
        """各テストの後に実行"""
        db.session.remove()
        db.drop_all()
        self.app_context.pop()
        # テストで作成したディレクトリとファイルをクリーンアップ
        for folder in [self.app.config['UPLOAD_FOLDER'], self.app.config['QR_UPLOAD_FOLDER']]:
            if os.path.exists(folder):
                for f in os.listdir(folder):
                    os.remove(os.path.join(folder, f))
                os.rmdir(folder)

    def test_index_page(self):
        """トップページが正常に表示されることをテスト"""
        response = self.client.get('/', follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'\xe9\x9b\xbb\xe5\xad\x90\xe9\x83\xa8\xe5\x93\x81\xe7\xae\xa1\xe7\x90\x86\xe3\x82\xb7\xe3\x82\xb9\xe3\x83\x86\xe3\x83\xa0', response.data) # b'電子部品管理システム'

    def test_parts_list_page(self):
        """部品一覧ページが正常に表示されることをテスト"""
        response = self.client.get('/parts/', follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        # list.html のタイトルをチェック
        self.assertIn(b'\xe9\x83\xa8\xe5\x93\x81\xe4\xb8\x80\xe8\xa6\xa7', response.data) # b'部品一覧'

    def test_add_part(self):
        """新しい部品を登録できることをテスト"""
        response = self.client.post('/parts/new', data=dict(
            name='Test Resistor',
            category='Resistor',
            package='1/4W',
            quantity=100,
            location='Box A',
            note='Test note'
        ), follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Test Resistor', response.data)
        part = Part.query.filter_by(name='Test Resistor').first()
        self.assertIsNotNone(part)
        self.assertEqual(part.quantity, 100)

    def test_edit_part(self):
        """部品情報を編集できることをテスト"""
        part = Part(name='Old Name', quantity=10)
        db.session.add(part)
        db.session.commit()

        response = self.client.post(f'/parts/{part.id}/edit', data=dict(
            name='New Name',
            category='Capacitor',
            package='10uF',
            quantity=50,
            location='Box B',
            note='Updated note'
        ), follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'New Name', response.data)
        
        updated_part = Part.query.get(part.id)
        self.assertEqual(updated_part.name, 'New Name')
        self.assertEqual(updated_part.quantity, 50)

    def test_delete_part(self):
        """部品を削除できることをテスト"""
        part = Part(name='ToDelete', quantity=1)
        db.session.add(part)
        db.session.commit()

        response = self.client.post(f'/parts/{part.id}/delete', follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertNotIn(b'ToDelete', response.data)
        
        deleted_part = Part.query.get(part.id)
        self.assertIsNone(deleted_part)

    def test_add_tag(self):
        """新しいタグを登録できることをテスト"""
        tag = Tag(name='Test Tag')
        db.session.add(tag)
        db.session.commit()
        self.assertIsNotNone(Tag.query.filter_by(name='Test Tag').first())

    def test_part_with_tag(self):
        """部品にタグを関連付けられることをテスト"""
        tag = Tag(name='Important')
        db.session.add(tag)
        db.session.commit()

        self.client.post('/parts/new', data=dict(
            name='Tagged Part',
            quantity=1,
            tags=[str(tag.id)]
        ), follow_redirects=True)

        part = Part.query.filter_by(name='Tagged Part').first()
        self.assertIsNotNone(part)
        self.assertIn(tag, part.tags)

    def test_upload_csv_success(self):
        """正常なCSVファイルをアップロードして部品が登録されることをテスト"""
        csv_content = (
            b'name,category,package,quantity,location,note,tags\n'
            b'Test Part 1,Resistor,1/4W,100,Box A,Note 1,"tag1,tag2"\n'
            b'Test Part 2,Capacitor,10uF,50,Box B,Note 2,"tag2,tag3"\n'
        )
        data = {
            'csv_file': (BytesIO(csv_content), 'test.csv')
        }
        response = self.client.post('/parts/upload', data=data, content_type='multipart/form-data', follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'CSV\xe3\x83\x95\xe3\x82\xa1\xe3\x82\xa4\xe3\x83\xab\xe3\x81\x8b\xe3\x82\x89\xe9\x83\xa8\xe5\x93\x81\xe3\x81\x8c\xe4\xb8\x80\xe6\x8b\xac\xe7\x99\xbb\xe9\x8c\xb2\xe3\x81\x95\xe3\x82\x8c\xe3\x81\xbe\xe3\x81\x97\xe3\x81\x9f\xef\xbc\x81', response.data) # b'CSVファイルから部品が一括登録されました！'

        part1 = Part.query.filter_by(name='Test Part 1').first()
        self.assertIsNotNone(part1)
        self.assertEqual(part1.quantity, 100)
        self.assertEqual(len(part1.tags), 2)

        part2 = Part.query.filter_by(name='Test Part 2').first()
        self.assertIsNotNone(part2)
        self.assertEqual(part2.location, 'Box B')
        self.assertEqual(len(part2.tags), 2)

        tag2 = Tag.query.filter_by(name='tag2').first()
        self.assertIn(tag2, part1.tags)
        self.assertIn(tag2, part2.tags)

    def test_upload_csv_invalid_file_type(self):
        """許可されていないファイル形式のアップロードをテスト"""
        data = {
            'csv_file': (BytesIO(b'this is not a csv'), 'test.txt')
        }
        response = self.client.post('/parts/upload', data=data, content_type='multipart/form-data', follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'\xe8\xa8\xb1\xe5\x8f\xaf\xe3\x81\x95\xe3\x82\x8c\xe3\x81\xa6\xe3\x81\x84\xe3\x81\xaa\xe3\x81\x84\xe3\x83\x95\xe3\x82\xa1\xe3\x82\xa4\xe3\x83\xab\xe5\xbd\xa2\xe5\xbc\x8f\xe3\x81\xa7\xe3\x81\x99', response.data) # b'許可されていないファイル形式です'

    def test_upload_csv_no_file(self):
        """ファイルが選択されていない場合のアップロードをテスト"""
        response = self.client.post('/parts/upload', data={}, content_type='multipart/form-data', follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'\xe3\x83\x95\xe3\x82\xa1\xe3\x82\xa4\xe3\x83\xab\xe3\x81\x8c\xe3\x81\x82\xe3\x82\x8a\xe3\x81\xbe\xe3\x81\x9b\xe3\x82\x93', response.data) # b'ファイルがありません'

if __name__ == '__main__':
    unittest.main()
