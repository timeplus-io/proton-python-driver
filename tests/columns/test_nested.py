from tests.testcase import BaseTestCase
from proton_driver.columns.util import (
    get_inner_spec,
    get_inner_columns,
    get_inner_columns_with_types
)


class NestedTestCase(BaseTestCase):
    def entuple(self, lst):
        return tuple(
            self.entuple(x) if isinstance(x, list) else x for x in lst
        )

    def test_simple(self):
        columns = 'n nested(i int32, s string)'

        # INSERT INTO test_nested VALUES ([(0, 'a'), (1, 'b')]);
        data = [([(0, 'a'), (1, 'b')],)]

        with self.create_stream(columns, flatten_nested=0):
            self.client.execute(
                'INSERT INTO test (n) VALUES', data
            )

            query = 'SELECT * FROM test'
            inserted = self.emit_cli(query)
            self.assertEqual(inserted, "[(0,'a'),(1,'b')]\n")

            inserted = self.client.execute(query)
            self.assertEqual(inserted, data)

            projected_i = self.client.execute('SELECT n.i FROM test')
            self.assertEqual(
                projected_i,
                [([0, 1],)]
            )

            projected_s = self.client.execute('SELECT n.s FROM test')
            self.assertEqual(
                projected_s,
                [(['a', 'b'],)]
            )

    def test_multiple_rows(self):
        columns = 'n nested(i int32, s string)'

        data = [([(0, 'a'), (1, 'b')],), ([(3, 'd'), (4, 'e')],)]

        with self.create_stream(columns, flatten_nested=0):
            self.client.execute(
                'INSERT INTO test (n) VALUES', data
            )

            query = 'SELECT * FROM test'
            inserted = self.emit_cli(query)
            self.assertEqual(
                inserted,
                "[(0,'a'),(1,'b')]\n[(3,'d'),(4,'e')]\n"
            )

            inserted = self.client.execute(query)
            self.assertEqual(inserted, data)

    def test_dict(self):
        columns = 'n nested(i int32, s string)'

        data = [
            {'n': [{'i': 0, 's': 'a'}, {'i': 1, 's': 'b'}]},
            {'n': [{'i': 3, 's': 'd'}, {'i': 4, 's': 'e'}]},
        ]

        with self.create_stream(columns, flatten_nested=0):
            self.client.execute(
                'INSERT INTO test (n) VALUES', data
            )

            query = 'SELECT * FROM test'
            inserted = self.emit_cli(query)
            self.assertEqual(
                inserted,
                "[(0,'a'),(1,'b')]\n[(3,'d'),(4,'e')]\n"
            )

            inserted = self.client.execute(query)
            self.assertEqual(
                inserted,
                [([(0, 'a'), (1, 'b')],), ([(3, 'd'), (4, 'e')],)]
            )

    def test_get_nested_columns(self):
        spec = 'nested(a tuple(array(int8)),\n b nullable(string))'
        columns = get_inner_columns('nested', spec)
        self.assertEqual(
            columns,
            ['tuple(array(int8))', 'nullable(string)']
        )

    def test_get_columns_with_types(self):
        spec = 'nested(a tuple(array(int8)),\n b nullable(string))'
        columns = get_inner_columns_with_types('nested', spec)
        self.assertEqual(
            columns,
            [('a', 'tuple(array(int8))'), ('b', 'nullable(string)')]
        )

    def test_get_inner_spec(self):
        inner = 'a tuple(array(int8), array(int64)), b nullable(string)'
        self.assertEqual(
            get_inner_spec('nested', 'nested({}) dummy '.format(inner)),
            inner
        )
