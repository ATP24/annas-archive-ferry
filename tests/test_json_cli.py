import io
import json
import unittest
from contextlib import redirect_stderr, redirect_stdout
from unittest.mock import patch

from annas_archive_ferry import engine


class JsonCliTests(unittest.TestCase):
    def run_cli(self, argv, function_name, result):
        output, errors = io.StringIO(), io.StringIO()

        def fake(*args, **kwargs):
            print('progress from nested operation')
            return result

        with patch('sys.argv', ['annas-ferry', *argv]), patch.object(engine, function_name, fake):
            with redirect_stdout(output), redirect_stderr(errors):
                code = engine.main()
        self.assertEqual(code, 0)
        self.assertIn('progress from nested operation', errors.getvalue())
        self.assertEqual(json.loads(output.getvalue()), result)

    def test_search_json_stdout_is_parseable(self):
        self.run_cli(['search', 'Austen', '--json'], 'search_books', [{'title': 'Pride and Prejudice'}])

    def test_probe_json_stdout_is_parseable(self):
        self.run_cli(['probe', '--md5', '0' * 32, '--json'], 'probe_book', {'size_bytes': 123, 'estimated_minutes': None})


if __name__ == '__main__':
    unittest.main()
