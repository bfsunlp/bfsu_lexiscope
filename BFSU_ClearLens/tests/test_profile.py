from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from clearlens.models import LLMRule, RegexRule
from clearlens.profile import load_profile, save_profile


class ProfileTests(unittest.TestCase):
    def test_profile_round_trip_excludes_all_api_keys(self) -> None:
        settings = {
            "language": "zh_sim",
            "local_cleaning": {"remove_emoji": True},
            "ai": {
                "provider": "deepseek",
                "openai_api_key": "openai-secret",
                "deepseek_api_key": "deepseek-secret",
                "nested": {"other_api_key": "nested-secret"},
            },
            "regex_enabled_keys": ["custom-one"],
        }
        rule = RegexRule(
            key="custom-one",
            name="Custom one",
            pattern=r"foo+",
            replacement="bar",
            enabled=True,
            custom=True,
        )
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "profile.json"
            llm_rule = LLMRule(key="llm-one", name="Remove footer", instruction="Remove repeated footer lines.")
            save_profile(path, settings, [rule], [llm_rule])
            raw = path.read_text(encoding="utf-8")
            self.assertNotIn("openai-secret", raw)
            self.assertNotIn("deepseek-secret", raw)
            self.assertNotIn("nested-secret", raw)
            payload = json.loads(raw)
            self.assertNotIn("openai_api_key", payload["settings"]["ai"])

            loaded_settings, loaded_rules, loaded_llm_rules = load_profile(path)
            self.assertTrue(loaded_settings["local_cleaning"]["remove_emoji"])
            self.assertEqual(loaded_settings["ai"]["provider"], "deepseek")
            self.assertEqual(loaded_settings["ai"]["openai_api_key"], "")
            self.assertEqual(len(loaded_rules), 1)
            self.assertEqual(loaded_rules[0].pattern, r"foo+")
            self.assertTrue(loaded_rules[0].custom)
            self.assertEqual(len(loaded_llm_rules), 1)
            self.assertEqual(loaded_llm_rules[0].instruction, "Remove repeated footer lines.")


if __name__ == "__main__":
    unittest.main()
