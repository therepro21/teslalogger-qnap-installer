import json
import pathlib
import unittest


ROOT = pathlib.Path(__file__).resolve().parents[1]


class ProjectContractTests(unittest.TestCase):
    def test_qnap_template_has_both_architectures_and_persistent_manager_volumes(self):
        templates = json.loads((ROOT / "qnap-template.json").read_text())["templates"]
        self.assertEqual({item["platform"] for item in templates}, {"linux/amd64", "linux/arm64"})
        for item in templates:
            mounts = {(entry.get("container"), entry.get("volume")) for entry in item["volumes"]}
            self.assertIn(("/manager-data", "teslalogger_qnap_manager_data"), mounts)
            self.assertIn(("/backups", "teslalogger_qnap_backups"), mounts)
            self.assertFalse(item["privileged"])

    def test_all_stack_data_volumes_are_external_and_named(self):
        compose = (ROOT / "compose.yaml").read_text()
        expected = [
            "teslalogger_qnap_mysql", "teslalogger_qnap_data", "teslalogger_qnap_app_backup",
            "teslalogger_qnap_invoices", "teslalogger_qnap_grafana",
            "teslalogger_qnap_grafana_dashboards", "teslalogger_qnap_grafana_plugins",
            "teslalogger_qnap_sqlschema", "teslalogger_qnap_tmp",
        ]
        self.assertEqual(compose.count("external: true"), len(expected))
        for volume in expected:
            self.assertIn(f"name: {volume}", compose)

    def test_update_backs_up_before_pull(self):
        source = (ROOT / "qnap_manager.py").read_text()
        function = source[source.index("def update_stack"):source.index("def uninstall")]
        self.assertLess(function.index('backup_stack("before-update")'), function.index('compose("pull"'))

    def test_destructive_uninstall_requires_exact_confirmation(self):
        source = (ROOT / "qnap_manager.py").read_text()
        self.assertIn('form.get("delete_confirmation") != "ALLE DATEN LOESCHEN"', source)


if __name__ == "__main__":
    unittest.main()
