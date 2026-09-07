from __future__ import annotations

import importlib.util
import json
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parent.parent
SCRIPT_PATH = ROOT / "scripts" / "validate_repository.py"
SPEC = importlib.util.spec_from_file_location("validate_repository", SCRIPT_PATH)
assert SPEC and SPEC.loader
validate_repository = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(validate_repository)


class SiteContractTests(unittest.TestCase):
    def test_missing_locale_key_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            self._copy_site_contract(root)
            i18n_path = root / "site" / "i18n.json"
            payload = json.loads(i18n_path.read_text(encoding="utf-8"))
            del payload["zh-CN"]["heroTitle"]
            i18n_path.write_text(
                json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
                encoding="utf-8",
            )

            errors: list[str] = []
            validate_repository.validate_site(root, errors)
            self.assertTrue(any("locale keys differ" in error for error in errors))

    def test_external_script_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            self._copy_site_contract(root)
            index_path = root / "index.html"
            index_path.write_text(
                index_path.read_text(encoding="utf-8").replace(
                    "</head>",
                    '<script src="https://example.com/runtime.js"></script></head>',
                ),
                encoding="utf-8",
            )

            errors: list[str] = []
            validate_repository.validate_site(root, errors)
            self.assertTrue(any("external script" in error for error in errors))

    @staticmethod
    def _copy_site_contract(root: Path) -> None:
        (root / ".github" / "workflows").mkdir(parents=True)
        shutil.copy2(ROOT / "index.html", root / "index.html")
        shutil.copytree(ROOT / "site", root / "site")
        shutil.copy2(
            ROOT / ".github" / "workflows" / "pages.yml",
            root / ".github" / "workflows" / "pages.yml",
        )
        shutil.copytree(ROOT / "assets", root / "assets")
        shutil.copytree(ROOT / "docs" / "assets", root / "docs" / "assets")


if __name__ == "__main__":
    unittest.main()
