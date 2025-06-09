from django.test import TestCase, override_settings
from django.conf import settings
from api.utils import generate_verification_code

class UtilsTests(TestCase):

    def test_generate_verification_code_default_length(self):
        # Test with default length (VERIFICATION_CODE_LENGTH from settings or 6)
        # Ensure settings has VERIFICATION_CODE_LENGTH or it defaults to 6
        expected_length = getattr(settings, 'VERIFICATION_CODE_LENGTH', 6)
        code = generate_verification_code()
        self.assertEqual(len(code), expected_length)
        self.assertTrue(code.isdigit())

    @override_settings(VERIFICATION_CODE_LENGTH=8)
    def test_generate_verification_code_custom_length_from_settings(self):
        # Test when VERIFICATION_CODE_LENGTH is set in settings
        code = generate_verification_code()
        self.assertEqual(len(code), 8)
        self.assertTrue(code.isdigit())

    def test_generate_verification_code_explicit_length_parameter(self):
        # Test with explicit length parameter overriding settings
        custom_length = 10
        code = generate_verification_code(length=custom_length)
        self.assertEqual(len(code), custom_length)
        self.assertTrue(code.isdigit())

    @override_settings(VERIFICATION_CODE_LENGTH=4)
    def test_generate_verification_code_explicit_length_overrides_settings_length(self):
        # Explicit length parameter should take precedence over VERIFICATION_CODE_LENGTH
        explicit_len = 5
        code = generate_verification_code(length=explicit_len)
        self.assertEqual(len(code), explicit_len)
        self.assertTrue(code.isdigit())

        # Ensure that if not passed, it uses the settings one
        code_settings = generate_verification_code()
        self.assertEqual(len(code_settings), 4)
        self.assertTrue(code_settings.isdigit())

    def test_generate_verification_code_zero_length(self):
        code = generate_verification_code(length=0)
        self.assertEqual(len(code), 0)
        self.assertEqual(code, "")

    def test_generate_verification_code_is_random(self):
        # Generate a few codes and check they are different
        codes = set()
        for _ in range(100): # Generate 100 codes
            codes.add(generate_verification_code())
        # It's statistically highly improbable that all 100 6-digit codes would be the same,
        # or even that there would be fewer than, say, 90 unique codes.
        # A simpler check is just that not all are identical, but this is stronger.
        self.assertTrue(len(codes) > 95, "Generated codes should be mostly unique")
