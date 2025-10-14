import os

# 作成するフォルダ・ファイル構成を定義
structure = {
    "app": {
        "__init__.py": "",
        "models.py": "",
        "routes": {
            "__init__.py": "",
            "parts_routes.py": "",
            "tags_routes.py": "",
            "labels_routes.py": ""
        },
        "templates": {
            "base.html": "",
            "parts": {},
            "tags": {},
            "labels": {}
        },
        "static": {
            "images": {},
            "qr": {}
        }
    },
    "instance": {
        "parts.db": ""
    },
    "run.py": "",
    "config.py": "",
    "requirements.txt": ""
}

def create_structure(base_path, structure):
    for name, content in structure.items():
        path = os.path.join(base_path, name)
        if isinstance(content, dict):
            os.makedirs(path, exist_ok=True)
            create_structure(path, content)
        else:
            with open(path, "w", encoding="utf-8") as f:
                f.write(content)

if __name__ == "__main__":
    project_root = os.path.abspath("parts_manager")
    os.makedirs(project_root, exist_ok=True)
    create_structure(project_root, structure)
    print(f"✅ プロジェクト構成を {project_root} に作成しました。")
