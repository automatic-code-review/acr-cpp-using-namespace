import os
import tempfile
import unittest

from src import autofix as autofix_module


class TestAutofix(unittest.TestCase):
    def build_config(self):
        return {
            "regexOrder": [
                {
                    "orderType": "group",
                    "regex": [
                        r"^using std::.*;$",
                        r"^using company::.*;$",
                        r"^using project::.*;$",
                    ],
                }
            ]
        }

    def fixture_path(self, name):
        return os.path.join("tests", "fixtures", name)

    def test_autofix_mantem_arquivo_identico_em_ifdef_bug_v2(self):
        config = self.build_config()
        original_path = self.fixture_path("sample_input_ifdef_bug_v2.cpp")

        with open(original_path, "r") as data:
            original_content = data.read()

        with tempfile.TemporaryDirectory() as tmpdir:
            temp_path = os.path.join(tmpdir, "sample_input_ifdef_bug_v2.cpp")

            with open(temp_path, "w") as data:
                data.write(original_content)

            autofix_module.autofix_file(path=temp_path, config=config)

            with open(temp_path, "r") as data:
                changed_content = data.read()

        self.assertEqual(changed_content, original_content)

    def test_autofix_ordena_arquivo_desordenado(self):
        config = self.build_config()
        original_path = self.fixture_path("sample_input.cpp")
        expected_path = self.fixture_path("sample_input_ok.cpp")

        with open(original_path, "r") as data:
            original_content = data.read()

        with open(expected_path, "r") as data:
            expected_content = data.read()

        with tempfile.TemporaryDirectory() as tmpdir:
            temp_path = os.path.join(tmpdir, "sample_input.cpp")

            with open(temp_path, "w") as data:
                data.write(original_content)

            changed = autofix_module.autofix_file(path=temp_path, config=config)

            with open(temp_path, "r") as data:
                changed_content = data.read()

        self.assertTrue(changed)
        self.assertEqual(changed_content, expected_content)

    def test_autofix_nao_reescreve_arquivo_ja_ordenado(self):
        config = self.build_config()
        original_path = self.fixture_path("sample_input_ok.cpp")

        with open(original_path, "r") as data:
            original_content = data.read()

        with tempfile.TemporaryDirectory() as tmpdir:
            temp_path = os.path.join(tmpdir, "sample_input_ok.cpp")

            with open(temp_path, "w") as data:
                data.write(original_content)

            changed = autofix_module.autofix_file(path=temp_path, config=config)

            with open(temp_path, "r") as data:
                changed_content = data.read()

        self.assertFalse(changed)
        self.assertEqual(changed_content, original_content)

    def test_autofix_deve_falhar_para_extensao_invalida(self):
        config = self.build_config()

        with tempfile.TemporaryDirectory() as tmpdir:
            temp_path = os.path.join(tmpdir, "sample_input.txt")

            with open(temp_path, "w") as data:
                data.write("using std::vector;\n")

            with self.assertRaises(Exception) as context:
                autofix_module.autofix_file(path=temp_path, config=config)

        self.assertEqual(str(context.exception), "extension type not supported")


if __name__ == "__main__":
    unittest.main()
