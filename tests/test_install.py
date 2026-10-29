"""Real installation behavior in disposable directories, never user skill folders."""
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
import zipfile

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("review_install", ROOT / "scripts" / "install.py")
installer = importlib.util.module_from_spec(spec)
spec.loader.exec_module(installer)


class InstallTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.base = Path(self.temp.name)
        self.source = self.base / "repository"
        self.package = self.source / "skills" / installer.SKILL
        (self.package / "references").mkdir(parents=True)
        (self.package / "SKILL.md").write_text("---\nname: daily-work-review\ndescription: Review synthetic submissions\n---\n# Skill\n", encoding="utf-8")
        (self.package / "references" / "rules.md").write_text("Read the actual work.\n", encoding="utf-8")
        self.skills = self.base / "native-skills"
        self.destination = self.skills / installer.SKILL
        self.pack()

    def tearDown(self):
        self.temp.cleanup()

    def pack(self, version="0.1.0"):
        subprocess.run([sys.executable, str(ROOT / "scripts" / "package.py"), "--source", str(self.source), "--version", version], check=True, capture_output=True)

    def read_manifest(self):
        return json.loads((self.source / "manifest.json").read_text(encoding="utf-8"))

    def write_manifest(self, manifest):
        (self.source / "manifest.json").write_text(json.dumps(manifest), encoding="utf-8")

    def test_first_install_and_check(self):
        installer.install(self.source, self.skills)
        self.assertEqual((self.destination / "SKILL.md").read_bytes(), (self.package / "SKILL.md").read_bytes())
        self.assertEqual(installer.install(self.source, self.skills, check=True), self.destination)

    def test_check_missing_does_not_create_directories(self):
        with self.assertRaises(ValueError):
            installer.install(self.source, self.skills, check=True)
        self.assertFalse(self.skills.exists())

    def test_reinstall_preserves_unmanaged_files_and_workspace_configuration(self):
        installer.install(self.source, self.skills)
        (self.destination / "personal-notes.txt").write_text("keep me", encoding="utf-8")
        config = self.base / "workspace" / ".daily-work-review" / "config.json"
        config.parent.mkdir(parents=True)
        config.write_text('{"version":1,"audit_url":"https://example.com/demo"}', encoding="utf-8")
        saved = config.read_bytes()
        installer.install(self.source, self.skills)
        self.assertEqual((self.destination / "personal-notes.txt").read_text(), "keep me")
        self.assertEqual(config.read_bytes(), saved)

    def test_update_replaces_managed_files_and_removes_obsolete_managed_file(self):
        installer.install(self.source, self.skills)
        (self.destination / "notes.txt").write_text("untouched", encoding="utf-8")
        (self.package / "references" / "rules.md").unlink()
        (self.package / "references" / "format.md").write_text("New format", encoding="utf-8")
        (self.package / "SKILL.md").write_text("Updated skill", encoding="utf-8")
        self.pack("0.2.0")
        installer.install(self.source, self.skills)
        self.assertEqual((self.destination / "SKILL.md").read_text(), "Updated skill")
        self.assertFalse((self.destination / "references" / "rules.md").exists())
        self.assertEqual((self.destination / "notes.txt").read_text(), "untouched")
        installer.install(self.source, self.skills, check=True)

    def test_modified_managed_file_is_never_overwritten(self):
        installer.install(self.source, self.skills)
        path = self.destination / "SKILL.md"
        path.write_text("my personal edits", encoding="utf-8")
        with self.assertRaises(ValueError):
            installer.install(self.source, self.skills)
        self.assertEqual(path.read_text(), "my personal edits")
        with self.assertRaises(ValueError):
            installer.install(self.source, self.skills, check=True)

    def test_new_file_collision_is_never_overwritten(self):
        installer.install(self.source, self.skills)
        path = self.destination / "references" / "new.md"
        path.write_text("personal note", encoding="utf-8")
        (self.package / "references" / "new.md").write_text("publisher update", encoding="utf-8")
        self.pack("0.2.0")
        with self.assertRaises(ValueError):
            installer.install(self.source, self.skills)
        self.assertEqual(path.read_text(), "personal note")

    def test_existing_unmanaged_installation_is_preserved(self):
        self.destination.mkdir(parents=True)
        (self.destination / "SKILL.md").write_text("manual install", encoding="utf-8")
        with self.assertRaises(ValueError):
            installer.install(self.source, self.skills)
        self.assertEqual((self.destination / "SKILL.md").read_text(), "manual install")

    def test_source_hash_mismatch_stops_before_target_creation(self):
        (self.package / "SKILL.md").write_text("changed after packaging", encoding="utf-8")
        with self.assertRaises(ValueError):
            installer.install(self.source, self.skills)
        self.assertFalse(self.skills.exists())

    def test_manifest_path_traversal_absolute_and_windows_paths_rejected(self):
        original = self.read_manifest()
        for bad in ("../outside.txt", "/outside.txt", "references/../../outside.txt", "references\\outside.txt", "C:/outside.txt", "references//rules.md", ".install-manifest.json"):
            with self.subTest(path=bad):
                manifest = json.loads(json.dumps(original))
                manifest["files"][bad] = "a" * 64
                self.write_manifest(manifest)
                with self.assertRaises(ValueError):
                    installer.install(self.source, self.skills)
                self.assertFalse(self.skills.exists())

    def test_source_and_destination_symlinks_are_rejected(self):
        source = self.package / "references" / "rules.md"
        content = source.read_bytes()
        source.unlink()
        outside = self.base / "outside.md"
        outside.write_bytes(content)
        source.symlink_to(outside)
        with self.assertRaises(ValueError):
            installer.install(self.source, self.skills)
        source.unlink()
        source.write_bytes(content)
        installer.install(self.source, self.skills)
        (self.destination / "external-link").symlink_to(outside)
        with self.assertRaises(ValueError):
            installer.install(self.source, self.skills)
        self.assertEqual(outside.read_bytes(), content)

    def test_zip_reproducible_and_contains_only_skill_root(self):
        archive = self.source / "dist" / (installer.SKILL + ".zip")
        first = archive.read_bytes()
        (self.package / ".DS_Store").write_text("ignored metadata", encoding="utf-8")
        local = self.package / ".daily-work-review"
        local.mkdir()
        (local / "config.json").write_text("private configuration", encoding="utf-8")
        self.pack()
        self.assertEqual(archive.read_bytes(), first)
        with zipfile.ZipFile(archive) as bundle:
            self.assertEqual(set(bundle.namelist()), {installer.SKILL + "/SKILL.md", installer.SKILL + "/references/rules.md"})
            self.assertIsNone(bundle.testzip())

    def test_installer_cli_check_does_not_claim_host_recognition(self):
        installer.install(self.source, self.skills)
        result = subprocess.run([sys.executable, str(ROOT / "scripts" / "install.py"), "--source", str(self.source), "--skills-dir", str(self.skills), "--check"], capture_output=True, text=True, check=True)
        self.assertIn("not host recognition", result.stdout)

    def test_packager_rejects_symlink_outputs_without_overwriting_target(self):
        archive = self.source / "dist" / (installer.SKILL + ".zip")
        archive.unlink()
        outside = self.base / "keep.txt"
        outside.write_text("keep this file", encoding="utf-8")
        archive.symlink_to(outside)
        result = subprocess.run([sys.executable, str(ROOT / "scripts" / "package.py"), "--source", str(self.source)], capture_output=True)
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(outside.read_text(), "keep this file")


if __name__ == "__main__":
    unittest.main()
