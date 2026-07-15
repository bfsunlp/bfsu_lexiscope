from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from clearlens import llm_rule_library
from clearlens.models import LLMRule


class LLMRuleLibraryTests(unittest.TestCase):
    def test_rules_are_saved_and_loaded_from_local_json(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            path = root / "llm_rules.json"
            rules = [
                LLMRule("one", "One", "Remove repeated navigation lines.", True),
                LLMRule("two", "Two", "Normalize paragraph spacing.", False),
            ]
            with patch.object(llm_rule_library, "USER_CONFIG_DIR", root), patch.object(
                llm_rule_library,
                "USER_LLM_RULES_PATH",
                path,
            ):
                llm_rule_library.save_llm_rules(rules)
                loaded = llm_rule_library.load_llm_rules()
            self.assertEqual(loaded, rules)


if __name__ == "__main__":
    unittest.main()
