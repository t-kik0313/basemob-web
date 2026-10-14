"""ブラウザ描画用の Nunjucks テンプレートを JSON にまとめる。"""

import json
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parents[1]


def build():
    folder = BASE_DIR / "client" / "views"
    sources = {
        str(path.relative_to(folder)): path.read_text(encoding="utf-8")
        for path in sorted(folder.rglob("*.njk"))
    }
    output = BASE_DIR / "static" / "app" / "views.json"
    output.write_text(json.dumps(sources, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return output


if __name__ == "__main__":
    print(build())
