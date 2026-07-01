import unittest
import os
import tempfile

import automatic_code_review_commons as commons
from src import review as review_module


class TestReviewCall(unittest.TestCase):
    def build_config(self, new_path):
        return {
            "message": "Ordenacao de using namespace incorreta no arquivo ${FILE_PATH}. Ordem sugerida: ${ORDERED}",
            "regexOrder": [
                {
                    "orderType": "group",
                    "regex": [
                        r"^using std::.*;$",
                        r"^using company::.*;$",
                        r"^using project::.*;$",
                    ]
                }
            ],
            "path_source": "tests/fixtures",
            "merge": {
                "changes": [
                    {
                        "deleted_file": False,
                        "new_path": new_path,
                    }
                ]
            }
        }

    def test_review_gera_comentario(self):
        config = self.build_config("sample_input.cpp")

        comments = review_module.review(config)

        expected_ordered_lines = [
            "using project::Widget;",
            "using std::string;",
            "using std::vector;",
        ]
        expected_comment_readable = (
            "Ordenacao de using namespace incorreta no arquivo sample_input.cpp. "
            "Ordem sugerida:\n"
            + "\n".join(expected_ordered_lines)
        )

        expected_comment = (
            "Ordenacao de using namespace incorreta no arquivo sample_input.cpp. "
            f"Ordem sugerida: <pre>{'<br>'.join(expected_ordered_lines)}<br></pre>"
        )
        actual_comment_readable = (
            comments[0]["comment"]
            .replace("Ordem sugerida: <pre>", "Ordem sugerida:\n")
            .replace("<br></pre>", "")
            .replace("<br>", "\n")
        )

        self.assertEqual(len(comments), 1)
        self.assertEqual(actual_comment_readable, expected_comment_readable)
        self.assertEqual(comments[0]["comment"], expected_comment)
        self.assertEqual(comments[0]["id"], commons.comment_generate_id(expected_comment))
        self.assertEqual(comments[0]["position"], {
            "language": None,
            "path": "sample_input.cpp",
            "startInLine": 1,
            "endInLine": 1,
            "snipset": False,
        })

    def test_review_sem_comentarios_quando_ordem_esta_correta(self):
        config = self.build_config("sample_input_ok.cpp")

        comments = review_module.review(config)

        self.assertEqual(comments, [])

    def test_review_deveria_ignorar_using_dentro_de_ifdef(self):
        config = self.build_config("sample_input_ifdef_bug.cpp")

        comments = review_module.review(config)

        self.assertEqual(comments, [])

    def test_review_deveria_ignorar_using_dentro_de_ifdef_v2(self):
        config = self.build_config("sample_input_ifdef_bug_v2.cpp")

        comments = review_module.review(config)

        self.assertEqual(comments, [])

    def test_review_deveria_ignorar_using_dentro_de_elif(self):
        config = self.build_config("sample_input_elif_bug.cpp")

        comments = review_module.review(config)

        self.assertEqual(comments, [])

    def test_review_deveria_ignorar_using_dentro_de_else(self):
        config = self.build_config("sample_input_else_bug.cpp")

        comments = review_module.review(config)

        self.assertEqual(comments, [])

    def test_review_ignora_deleted_file_e_extensao_nao_cpp(self):
        config = {
            "message": "msg ${FILE_PATH} ${ORDERED}",
            "regexOrder": [
                {
                    "orderType": "group",
                    "regex": [r"^using std::.*;$"],
                }
            ],
            "path_source": "tests/fixtures",
            "merge": {
                "changes": [
                    {
                        "deleted_file": True,
                        "new_path": "sample_input.cpp",
                    },
                    {
                        "deleted_file": False,
                        "new_path": "ignored.txt",
                    },
                ]
            },
        }

        comments = review_module.review(config)

        self.assertEqual(comments, [])


class TestReviewHelpers(unittest.TestCase):
    def test_remove_duplicate_usings_remove_repeticoes(self):
        usings = [
            "using std::vector;",
            "using std::vector;",
            "using company::Widget;",
        ]

        deduplicated = review_module.remove_duplicate_usings(usings)

        self.assertEqual(deduplicated, ["using std::vector;", "using company::Widget;"])

    def test_is_using_namespace_ignora_alias_e_self_alias(self):
        self.assertFalse(review_module.is_using_namespace("using Name = company::Widget;"))
        self.assertFalse(review_module.is_using_namespace("using Widget::Widget;"))

    def test_adjust_order_individual_ordena_cada_regex(self):
        using_list = ["using std::vector;", "using std::string;"]
        regex_order = [
            {
                "orderType": "individual",
                "regex": [r"^using std::.*;$"],
            }
        ]

        ordered = review_module.adjust_order(using_list, regex_order)

        self.assertEqual(ordered, ["using std::string;\n", "using std::vector;\n", "\n"])

    def test_get_last_include_position_ignora_arquivo_moc(self):
        lines = [
            "#include \"widget.moc\"\n",
            "#include <vector>\n",
        ]

        include_pos = review_module.get_last_include_position(lines)

        self.assertEqual(include_pos, 1)

    def test_verify_sem_using_global_mantem_conteudo(self):
        regex_order = [
            {
                "orderType": "group",
                "regex": [r"^using std::.*;$", r"^using company::.*;$"],
            }
        ]
        source = "#ifdef FOO\nusing company::OnlyInsideIfdef;\n#endif\n"

        with tempfile.TemporaryDirectory() as temp_dir:
            file_path = os.path.join(temp_dir, "only_ifdef.cpp")

            with open(file_path, "w") as data:
                data.write(source)

            changed, _, lines_fix = review_module.verify(file_path, regex_order)

        self.assertFalse(changed)
        self.assertEqual("".join(lines_fix), "\n" + source)


if __name__ == "__main__":
    unittest.main()
