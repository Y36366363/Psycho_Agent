import io
import http.client
import unittest
import urllib.error
from unittest.mock import patch
from typing import Any

from psycho_agent.config import ProviderSettings
from psycho_agent.providers import ModelError, UrllibJsonTransport, _verified_ssl_context, create_model


class FakeTransport:
    def __init__(self, response: dict[str, Any]) -> None:
        self.response = response
        self.calls: list[dict[str, Any]] = []

    def post(
        self,
        url: str,
        *,
        headers: dict[str, str],
        payload: dict[str, Any],
        timeout: float,
    ) -> dict[str, Any]:
        self.calls.append(
            {"url": url, "headers": headers, "payload": payload, "timeout": timeout}
        )
        return self.response


class ProviderAdapterTests(unittest.TestCase):
    def test_openai_responses_payload_and_parser(self) -> None:
        transport = FakeTransport(
            {"output": [{"content": [{"type": "output_text", "text": "自然回应"}]}]}
        )
        model = create_model(
            ProviderSettings("openai", "openai-secret", "test-gpt"), transport
        )
        self.assertEqual(model.complete("system", "user"), "自然回应")
        call = transport.calls[0]
        self.assertEqual(call["url"], "https://api.openai.com/v1/responses")
        self.assertEqual(call["payload"]["instructions"], "system")
        self.assertEqual(call["headers"]["Authorization"], "Bearer openai-secret")

    def test_deepseek_chat_payload_and_parser(self) -> None:
        transport = FakeTransport({"choices": [{"message": {"content": "一起梳理"}}]})
        model = create_model(
            ProviderSettings("deepseek", "deepseek-secret", "deepseek-chat"), transport
        )
        self.assertEqual(model.complete("system", "user"), "一起梳理")
        call = transport.calls[0]
        self.assertIn("api.deepseek.com", call["url"])
        self.assertEqual(call["payload"]["messages"][1]["content"], "user")

    def test_gemini_generate_content_payload_and_parser(self) -> None:
        transport = FakeTransport(
            {"candidates": [{"content": {"parts": [{"text": "先慢一点"}]}}]}
        )
        model = create_model(
            ProviderSettings("gemini", "gemini-secret", "gemini-test"), transport
        )
        self.assertEqual(model.complete("system", "user"), "先慢一点")
        call = transport.calls[0]
        self.assertIn("gemini-test:generateContent", call["url"])
        self.assertEqual(call["headers"]["x-goog-api-key"], "gemini-secret")

    def test_missing_output_raises_safe_error(self) -> None:
        model = create_model(
            ProviderSettings("openai", "secret-that-must-not-leak", "test"),
            FakeTransport({"output": []}),
        )
        with self.assertRaises(ModelError) as context:
            model.complete("system", "user")
        self.assertNotIn("secret-that-must-not-leak", str(context.exception))

    def test_http_error_body_is_never_exposed(self) -> None:
        error = urllib.error.HTTPError(
            "https://example.invalid",
            401,
            "Unauthorized",
            {},
            io.BytesIO(b'key fragment: sensitive-secret'),
        )
        with patch("urllib.request.urlopen", side_effect=error):
            with self.assertRaises(ModelError) as context:
                UrllibJsonTransport().post(
                    "https://example.invalid",
                    headers={},
                    payload={},
                    timeout=1,
                )
        self.assertIn("Authentication failed", str(context.exception))
        self.assertNotIn("sensitive-secret", str(context.exception))

    def test_ssl_context_uses_system_bundle_when_python_has_none(self) -> None:
        paths = type("Paths", (), {"cafile": None})()
        sentinel = object()
        with (
            patch("psycho_agent.providers.ssl.get_default_verify_paths", return_value=paths),
            patch("psycho_agent.providers.Path.is_file", return_value=True),
            patch("psycho_agent.providers.ssl.create_default_context", return_value=sentinel) as create,
        ):
            context = _verified_ssl_context()
        self.assertIs(context, sentinel)
        create.assert_called_once_with(cafile="/etc/ssl/cert.pem")

    def test_transient_network_error_is_retried(self) -> None:
        class Response:
            def __enter__(self):
                return self

            def __exit__(self, *args):
                return False

            def read(self) -> bytes:
                return b'{"ok": true}'

        transient = urllib.error.URLError("temporary tunnel failure")
        with (
            patch("urllib.request.urlopen", side_effect=[transient, Response()]) as opened,
            patch("psycho_agent.providers.time.sleep"),
        ):
            result = UrllibJsonTransport().post(
                "https://example.invalid",
                headers={},
                payload={},
                timeout=1,
            )
        self.assertEqual(result, {"ok": True})
        self.assertEqual(opened.call_count, 2)

    def test_remote_disconnect_is_retried(self) -> None:
        class Response:
            def __enter__(self):
                return self

            def __exit__(self, *args):
                return False

            def read(self) -> bytes:
                return b'{"recovered": true}'

        with (
            patch(
                "urllib.request.urlopen",
                side_effect=[http.client.RemoteDisconnected("closed"), Response()],
            ) as opened,
            patch("psycho_agent.providers.time.sleep"),
        ):
            result = UrllibJsonTransport().post(
                "https://example.invalid",
                headers={},
                payload={},
                timeout=1,
            )
        self.assertEqual(result, {"recovered": True})
        self.assertEqual(opened.call_count, 2)


if __name__ == "__main__":
    unittest.main()
