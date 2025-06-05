import unittest

from src.config.config_validator import ConfigValidator

class TestConfigValidatorLanguage(unittest.TestCase):
    def test_accepts_supported_language_codes(self):
        valid_codes = [
            "pt", "pt-BR", "pt-PT", "en", "en-US", "en-GB", "es", "es-ES",
            "es-MX", "fr", "fr-FR", "de", "de-DE", "it", "it-IT", "nl",
            "ja", "ja-JP", "ko", "ko-KR", "zh", "zh-CN", "zh-TW", "ru",
        ]
        for code in valid_codes:
            with self.subTest(code=code):
                normalized = ConfigValidator.validate_language_code(code)
                self.assertEqual(normalized, code.lower())

    def test_invalid_format_raises_error(self):
        invalid_codes = ["english", "123", "en_US", "e", "en-us-extra"]
        for code in invalid_codes:
            with self.subTest(code=code):
                with self.assertRaises(ValueError):
                    ConfigValidator.validate_language_code(code)

if __name__ == "__main__":
    unittest.main()
