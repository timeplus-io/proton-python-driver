from datetime import date
from time import sleep
from tests.testcase import BaseTestCase
from proton_driver import errors
from proton_driver.errors import ServerException


class InsertTestCase(BaseTestCase):
    def test_type_mismatch(self):
        with self.create_stream('a float32'):
            with self.assertRaises(errors.TypeMismatchError):
                data = [(date(2012, 10, 25), )]
                self.client.execute(
                    'INSERT INTO test (a) VALUES', data
                )

    def test_no_such_column(self):
        with self.create_stream('a float32'):
            with self.assertRaises(ServerException):
                data = [(1, )]
                self.client.execute(
                    'INSERT INTO test (b) VALUES', data
                )

    def test_data_malformed_rows(self):
        with self.create_stream('a int8'), self.assertRaises(TypeError):
            data = [1]
            self.client.execute(
                'INSERT INTO test (a) VALUES', data
            )

    def test_data_less_columns_then_expected(self):
        with self.create_stream('a int8, b int8'):
            with self.assertRaises(ValueError) as e:
                data = [(1, )]
                self.client.execute(
                    'INSERT INTO test (a, b) VALUES', data
                )
            self.assertEqual(str(e.exception), 'Expected 2 columns, got 1')

    def test_data_more_columns_then_expected(self):
        with self.create_stream('a int8, b int8'):
            with self.assertRaises(ValueError) as e:
                data = [(1, 2, 3)]
                self.client.execute(
                    'INSERT INTO test (a, b) VALUES', data
                )
            self.assertEqual(str(e.exception), 'Expected 2 columns, got 3')

    def test_data_different_rows_length(self):
        with self.create_stream('a int8, b int8'):
            with self.assertRaises(ValueError) as e:
                data = [(1, 2), (3, )]
                self.client.execute(
                    'INSERT INTO test (a, b) VALUES', data
                )
            self.assertEqual(str(e.exception), 'Different rows length')

    def test_data_different_rows_length_from_dicts(self):
        with self.create_stream('a int8, b int8'):
            with self.assertRaises(KeyError):
                data = [{'a': 1, 'b': 2}, {'a': 3}]
                self.client.execute(
                    'INSERT INTO test (a, b) VALUES', data
                )

    def test_data_unsupported_row_type(self):
        with self.create_stream('a int8'):
            with self.assertRaises(TypeError) as e:
                data = [1]
                self.client.execute(
                    'INSERT INTO test (a) VALUES', data, types_check=True
                )
            self.assertIn('dict, list or tuple is expected', str(e.exception))

    def test_data_dicts_ok(self):
        with self.create_stream('a int8, b int8'):
            data = [{'a': 1, 'b': 2}, {'a': 3, 'b': 4}]
            self.client.execute(
                'INSERT INTO test (a, b) VALUES', data
            )

            query = 'SELECT * FROM test'
            inserted = self.emit_cli(query)
            self.assertEqual(inserted, '1\t2\n3\t4\n')
            inserted = self.client.execute(query)
            self.assertEqual(inserted, [(1, 2), (3, 4)])

    def test_data_generator_type(self):
        with self.create_stream('a int8'):
            data = ((x, ) for x in range(3))
            self.client.execute(
                'INSERT INTO test (a) VALUES', data
            )
            query = 'SELECT * FROM test'
            inserted = self.emit_cli(query)
            self.assertEqual(inserted, '0\n1\n2\n')
            inserted = self.client.execute(query)
            self.assertEqual(inserted, [(0,), (1, ), (2, )])

    def test_data_dicts_mixed_with_lists(self):
        with self.create_stream('a int8'):
            with self.assertRaises(TypeError) as e:
                data = [{'a': 1}, (2, )]
                self.client.execute(
                    'INSERT INTO test (a) VALUES', data, types_check=True
                )

            self.assertIn('dict is expected', str(e.exception))

            with self.assertRaises(TypeError) as e:
                data = [(1, ), {'a': 2}]
                self.client.execute(
                    'INSERT INTO test (a) VALUES', data, types_check=True
                )

            self.assertIn('list or tuple is expected', str(e.exception))

    def test_empty_insert(self):
        with self.create_stream('a int8'):
            self.client.execute(
                'INSERT INTO test (a) VALUES', []
            )

            query = 'SELECT * FROM test'
            inserted = self.emit_cli(query)
            self.assertEqual(inserted, '')
            inserted = self.client.execute(query)
            self.assertEqual(inserted, [])

    def test_insert_from_select(self):
        with self.create_stream('a uint64'):
            inserted = self.client.execute(
                'INSERT INTO test (a) '
                'SELECT number FROM system.numbers LIMIT 5'
            )
            self.assertEqual(inserted, [])

    def test_insert_return(self):
        with self.create_stream('a int8'):
            rv = self.client.execute(
                'INSERT INTO test (a) VALUES', []
            )
            self.assertEqual(rv, 0)

            rv = self.client.execute(
                'INSERT INTO test (a) VALUES', [(x,) for x in range(5)]
            )
            self.assertEqual(rv, 5)

    def test_idempotent_insert(self):
        self.client.execute('CREATE STREAM test (i int, v string)')

        data = [
            (123, 'abc'), (456, 'def'), (789, 'ghi'),
            (987, 'ihg'), (654, 'fed'), (321, 'cba'),
        ]

        setting = {
            'idempotent_id': 'batch1'
        }

        for _ in range(20):
            rv = self.client.execute(
                'INSERT INTO test (i, v) VALUES',
                data,
                settings=setting
            )
            self.assertEqual(rv, 6)
        sleep(3)
        rv = self.client.execute('SELECT count(*) FROM table(test)')
        self.assertEqual(rv, [(6, )])

        self.client.execute('DROP STREAM test')


class InsertColumnarTestCase(BaseTestCase):
    def test_insert_tuple_ok(self):
        with self.create_stream('a int8, b int8'):
            data = [(1, 2, 3), (4, 5, 6)]
            self.client.execute(
                'INSERT INTO test (a, b) VALUES', data, columnar=True
            )

            query = 'SELECT * FROM test'
            inserted = self.emit_cli(query)
            self.assertEqual(inserted, '1\t4\n2\t5\n3\t6\n')
            inserted = self.client.execute(query)
            self.assertEqual(inserted, [(1, 4), (2, 5), (3, 6)])
            inserted = self.client.execute(query, columnar=True)
            self.assertEqual(inserted, [(1, 2, 3), (4, 5, 6)])

    def test_insert_data_different_column_length(self):
        with self.create_stream('a int8, b int8'):
            with self.assertRaises(ValueError) as e:
                data = [(1, 2, 3), (4, 5)]
                self.client.execute(
                    'INSERT INTO test (a, b) VALUES', data, columnar=True
                )
            self.assertEqual(str(e.exception), 'Expected 3 rows, got 2')

    def test_data_less_columns_then_expected(self):
        with self.create_stream('a int8, b int8'):
            with self.assertRaises(ValueError) as e:
                data = [(1, 2)]
                self.client.execute(
                    'INSERT INTO test (a, b) VALUES', data, columnar=True
                )
            self.assertEqual(str(e.exception), 'Expected 2 columns, got 1')

    def test_data_more_columns_then_expected(self):
        with self.create_stream('a int8, b int8'):
            with self.assertRaises(ValueError) as e:
                data = [(1, 2), (3, 4), (5, 6)]
                self.client.execute(
                    'INSERT INTO test (a, b) VALUES', data, columnar=True
                )
            self.assertEqual(str(e.exception), 'Expected 2 columns, got 3')

    def test_data_invalid_types(self):
        with self.create_stream('a int8, b int8'):
            with self.assertRaises(TypeError) as e:
                data = [(1, 2), {'a': 3, 'b': 4}]
                self.client.execute(
                    'INSERT INTO test (a, b) VALUES', data,
                    types_check=True, columnar=True
                )

            self.assertIn('list or tuple is expected', str(e.exception))

            with self.assertRaises(TypeError) as e:
                data = [(1, 2), 3]
                self.client.execute(
                    'INSERT INTO test (a, b) VALUES', data,
                    types_check=True, columnar=True
                )

            self.assertIn('list or tuple is expected', str(e.exception))
