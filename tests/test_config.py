import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from psycho_agent.config import ConfigurationError, ProviderSettings, load_dotenv


class ConfigurationTests(unittest.TestCase):
    def test_dotenv_loads_without_overwriting_existing_value(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / ".env"
            path.write_text("OPENAI_API_KEY='from-file'\nNEW_VALUE=hello\n", encoding="utf-8")
            with patch.dict(os.environ, {"OPENAI_API_KEY": "already-set"}, clear=True):
                self.assertTrue(load_dotenv(path))
                self.assertEqual(os.environ["OPENAI_API_KEY"], "already-set")
                self.assertEqual(os.environ["NEW_VALUE"], "hello")

    def test_chatgpt_alias_uses_openai_configuration(self) -> None:
        with patch.dict(os.environ, {"CHATGPT_API_KEY": "secret"}, clear=True):
            settings = ProviderSettings.from_env("chatgpt")
        self.assertEqual(settings.provider, "openai")
        self.assertEqual(settings.api_key, "secret")

    def test_missing_key_has_actionable_error(self) -> None:
        with patch.dict(os.environ, {}, clear=True):
            with self.assertRaises(ConfigurationError) as context:
                ProviderSettings.from_env("gemini")
        self.assertIn("GEMINI_API_KEY", str(context.exception))

    def test_example_placeholder_is_rejected_before_network_use(self) -> None:
        with patch.dict(os.environ, {"DEEPSEEK_API_KEY": "your_deepseek_api_key"}, clear=True):
            with self.assertRaises(ConfigurationError) as context:
                ProviderSettings.from_env("deepseek")
        self.assertIn("placeholder", str(context.exception))


if __name__ == "__main__":
    unittest.main()
