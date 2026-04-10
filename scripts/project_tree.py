#!/usr/bin/env python3
"""
Proje Dosya Yapısı Görselleştirici
Bu script, karmaşık proje yapılarını tree formatında gösterir
ve isteğe bağlı olarak HTML veya Markdown formatında kaydeder.
"""

import os
import argparse
from pathlib import Path
import json


class ProjectTreeVisualizer:
    def __init__(self, root_path, ignore_patterns=None, max_depth=None):
        self.root_path = Path(root_path)
        self.ignore_patterns = ignore_patterns or [
            '.git', '__pycache__', 'node_modules', '.idea',
            '.vscode', '*.pyc', '.DS_Store', 'venv', 'env',
            '.pytest_cache', '.mypy_cache', 'dist', 'build'
        ]
        self.max_depth = max_depth
        self.file_count = 0
        self.dir_count = 0

    def should_ignore(self, path):
        """Dosya/klasörün göz ardı edilip edilmeyeceğini kontrol et"""
        name = path.name
        for pattern in self.ignore_patterns:
            if pattern.startswith('*'):
                if name.endswith(pattern[1:]):
                    return True
            elif name == pattern:
                return True
        return False

    def generate_tree(self, directory=None, prefix="", depth=0):
        """Tree yapısını string olarak generate et"""
        if self.max_depth and depth > self.max_depth:
            return ""

        if directory is None:
            directory = self.root_path

        tree_str = ""

        try:
            items = list(directory.iterdir())
            # Önce klasörler, sonra dosyalar olacak şekilde sırala
            items.sort(key=lambda x: (not x.is_dir(), x.name.lower()))

            # Göz ardı edilmeyecek öğeleri filtrele
            items = [item for item in items if not self.should_ignore(item)]

            for i, item in enumerate(items):
                is_last = i == len(items) - 1
                connector = "└── " if is_last else "├── "

                if item.is_dir():
                    self.dir_count += 1
                    tree_str += f"{prefix}{connector}📁 {item.name}/\n"

                    if is_last:
                        extension = "    "
                    else:
                        extension = "│   "

                    tree_str += self.generate_tree(
                        item, prefix + extension, depth + 1
                    )
                else:
                    self.file_count += 1
                    # Dosya uzantısına göre emoji ekle
                    file_icon = self.get_file_icon(item.name)
                    tree_str += f"{prefix}{connector}{file_icon} {item.name}\n"

        except PermissionError:
            tree_str += f"{prefix}[Permission Error]\n"

        return tree_str

    def get_file_icon(self, filename):
        """Dosya tipine göre emoji döndür"""
        extension_icons = {
            '.py': '🐍',
            '.js': '📜',
            '.jsx': '⚛️',
            '.ts': '📘',
            '.tsx': '⚛️',
            '.html': '🌐',
            '.css': '🎨',
            '.scss': '🎨',
            '.json': '📋',
            '.xml': '📄',
            '.md': '📝',
            '.txt': '📄',
            '.pdf': '📕',
            '.jpg': '🖼️',
            '.jpeg': '🖼️',
            '.png': '🖼️',
            '.gif': '🖼️',
            '.svg': '🖼️',
            '.mp4': '🎥',
            '.mp3': '🎵',
            '.zip': '📦',
            '.rar': '📦',
            '.tar': '📦',
            '.gz': '📦',
            '.sql': '🗃️',
            '.db': '🗃️',
            '.exe': '⚙️',
            '.sh': '📜',
            '.bat': '📜',
            '.yml': '⚙️',
            '.yaml': '⚙️',
            '.env': '🔐',
            '.gitignore': '🚫',
            'Dockerfile': '🐳',
            '.dockerignore': '🐳',
        }

        # Önce tam dosya adını kontrol et
        if filename in extension_icons:
            return extension_icons[filename]

        # Sonra uzantıyı kontrol et
        ext = Path(filename).suffix.lower()
        return extension_icons.get(ext, '📄')

    def save_as_html(self, tree_content, output_file="project_structure.html"):
        """Tree yapısını HTML olarak kaydet"""
        html_content = f"""
<!DOCTYPE html>
<html lang="tr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Proje Yapısı - {self.root_path.name}</title>
    <style>
        body {{
            font-family: 'Courier New', monospace;
            background-color: #1e1e1e;
            color: #d4d4d4;
            padding: 20px;
        }}
        .container {{
            max-width: 1200px;
            margin: 0 auto;
            background-color: #252526;
            padding: 30px;
            border-radius: 10px;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.3);
        }}
        h1 {{
            color: #61dafb;
            border-bottom: 2px solid #61dafb;
            padding-bottom: 10px;
        }}
        .stats {{
            background-color: #1e1e1e;
            padding: 15px;
            border-radius: 5px;
            margin: 20px 0;
        }}
        .stats span {{
            margin-right: 20px;
            color: #98c379;
        }}
        pre {{
            white-space: pre;
            overflow-x: auto;
            line-height: 1.6;
            font-size: 14px;
        }}
        .tree {{
            background-color: #1e1e1e;
            padding: 20px;
            border-radius: 5px;
            overflow-x: auto;
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>📁 Proje Yapısı: {self.root_path.name}</h1>
        <div class="stats">
            <span>📁 Klasör Sayısı: {self.dir_count}</span>
            <span>📄 Dosya Sayısı: {self.file_count}</span>
            <span>📊 Toplam: {self.dir_count + self.file_count}</span>
        </div>
        <div class="tree">
            <pre>{tree_content}</pre>
        </div>
    </div>
</body>
</html>
"""
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(html_content)
        print(f"✅ HTML file created: {output_file}")

    def save_as_markdown(self, tree_content, output_file="project_structure.md"):
        """Tree yapısını Markdown olarak kaydet"""
        md_content = f"""# 📁 Proje Yapısı: {self.root_path.name}

## 📊 İstatistikler
- **Klasör Sayısı:** {self.dir_count}
- **Dosya Sayısı:** {self.file_count}
- **Toplam:** {self.dir_count + self.file_count}

## 🌳 Dosya Ağacı

```
{tree_content}
```

---
*Bu dosya otomatik olarak oluşturulmuştur.*
"""
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(md_content)
        print(f"✅ Markdown file created: {output_file}")

    def save_as_json(self, output_file="project_structure.json"):
        """Proje yapısını JSON olarak kaydet"""

        def build_dict(directory):
            result = {
                "name": directory.name,
                "type": "directory",
                "children": []
            }

            try:
                for item in sorted(directory.iterdir(), key=lambda x: (not x.is_dir(), x.name.lower())):
                    if self.should_ignore(item):
                        continue

                    if item.is_dir():
                        result["children"].append(build_dict(item))
                    else:
                        result["children"].append({
                            "name": item.name,
                            "type": "file",
                            "size": item.stat().st_size
                        })
            except PermissionError:
                result["error"] = "Permission denied"

            return result

        structure = build_dict(self.root_path)

        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(structure, f, indent=2, ensure_ascii=False)
        print(f"✅ JSON file created: {output_file}")

    def print_tree(self):
        """Tree yapısını konsola yazdır"""
        print(f"\n{'=' * 60}")
        print(f"📁 Proje: {self.root_path.name}")
        print(f"📍 Konum: {self.root_path.absolute()}")
        print(f"{'=' * 60}\n")

        tree_content = self.generate_tree()
        print(tree_content)

        print(f"\n{'=' * 60}")
        print(f"📊 İstatistikler:")
        print(f"  📁 Toplam klasör: {self.dir_count}")
        print(f"  📄 Toplam dosya: {self.file_count}")
        print(f"  📊 Genel toplam: {self.dir_count + self.file_count}")
        print(f"{'=' * 60}\n")

        return tree_content


def main():
    parser = argparse.ArgumentParser(
        description='Proje dosya yapısını görselleştirir'
    )
    parser.add_argument(
        'path',
        nargs='?',
        default='.',
        help='Görselleştirilecek dizin yolu (varsayılan: mevcut dizin)'
    )
    parser.add_argument(
        '--max-depth',
        type=int,
        help='Maksimum derinlik seviyesi'
    )
    parser.add_argument(
        '--ignore',
        nargs='+',
        help='Göz ardı edilecek dosya/klasör isimleri'
    )
    parser.add_argument(
        '--html',
        action='store_true',
        help='Save as HTML file'
    )
    parser.add_argument(
        '--markdown',
        action='store_true',
        help='Save as Markdown file'
    )
    parser.add_argument(
        '--json',
        action='store_true',
        help='Save as JSON file'
    )
    parser.add_argument(
        '--all-formats',
        action='store_true',
        help='Tüm formatlarda kaydet (HTML, Markdown, JSON)'
    )

    args = parser.parse_args()

    # Dizin kontrolü
    if not Path(args.path).exists():
        print(f"❌ Error: '{args.path}' directory not found!")
        return

    if not Path(args.path).is_dir():
        print(f"❌ Error: '{args.path}' is not a directory!")
        return

    # Visualizer oluştur
    ignore_patterns = args.ignore if args.ignore else None
    visualizer = ProjectTreeVisualizer(
        args.path,
        ignore_patterns=ignore_patterns,
        max_depth=args.max_depth
    )

    # Tree'yi oluştur ve göster
    tree_content = visualizer.print_tree()

    # Dosya kaydetme seçenekleri
    if args.all_formats:
        visualizer.save_as_html(tree_content)
        visualizer.save_as_markdown(tree_content)
        visualizer.save_as_json()
    else:
        if args.html:
            visualizer.save_as_html(tree_content)
        if args.markdown:
            visualizer.save_as_markdown(tree_content)
        if args.json:
            visualizer.save_as_json()


if __name__ == "__main__":
    main()