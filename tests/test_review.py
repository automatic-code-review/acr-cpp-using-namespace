import unittest

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

    def test_review_deveria_ignorar_using_dentro_de_elif(self):
        config = self.build_config("sample_input_elif_bug.cpp")

        comments = review_module.review(config)

        self.assertEqual(comments, [])

    def test_review_deveria_ignorar_using_dentro_de_else(self):
        config = self.build_config("sample_input_else_bug.cpp")

        comments = review_module.review(config)

        self.assertEqual(comments, [])


if __name__ == "__main__":
    unittest.main()
