import json
from time import sleep
from tests.testcase import BaseTestCase


class JSONTestCase(BaseTestCase):
    def test_simple(self):
        rv = self.client.execute("SELECT '{\"bb\": {\"cc\": [255, 1]}}'::json")
        self.assertEqual(rv, [({'bb': {'cc': [255, 1]}},)])

    def test_from_table(self):
        self.emit_cli('CREATE STREAM test (a json)')
        data = [
            ({},),
            ({'key1': 1}, ),
            ({'key1': 2.1, 'key2': {'nested': 'key'}}, ),
            ({'key1': 3, 'key3': ['test'], 'key4': [10, 20]}, )
        ]
        self.client.execute('INSERT INTO test (a) VALUES', data)
        sleep(3)
        query = 'SELECT a FROM table(test)'
        inserted = self.client.execute(query)
        self.assertEqual(
            inserted,
            [
                ((0.0, ('',), [], []),),
                ((1.0, ('',), [], []),),
                ((2.1, ('key',), [], []),),
                ((3.0, ('',), ['test'], [10, 20]),)
            ]
        )
        inserted = self.client.execute(
            query, settings=dict(namedtuple_as_json=True)
        )
        data_with_all_keys = [
            ({'key1': 0, 'key2': {'nested': ''}, 'key3': [], 'key4': []},),
            ({'key1': 1, 'key2': {'nested': ''}, 'key3': [], 'key4': []},),
            ({'key1': 2.1, 'key2': {'nested': 'key'}, 'key3': [],
                'key4': []},),
            ({'key1': 3, 'key2': {'nested': ''}, 'key3': ['test'],
                'key4': [10, 20]},)
        ]
        self.assertEqual(inserted, data_with_all_keys)
        self.emit_cli('DROP STREAM test')

    def test_insert_json_strings(self):
        self.emit_cli('CREATE STREAM test (a json)')
        data = [
            (json.dumps({'i-am': 'dumped json'}),),
        ]
        self.client.execute('INSERT INTO test (a) VALUES', data)
        sleep(3)
        query = 'SELECT a FROM table(test)'
        inserted = self.client.execute(query)
        self.assertEqual(
            inserted,
            [(('dumped json',),)]
        )
        inserted = self.client.execute(
            query, settings=dict(namedtuple_as_json=True)
        )
        data_with_all_keys = [
            ({'`i-am`': 'dumped json'},)
        ]
        self.assertEqual(inserted, data_with_all_keys)
        self.emit_cli('DROP STREAM test')

    def test_json_as_named_tuple(self):
        settings = {'namedtuple_as_json': True}
        query = 'SELECT a FROM table(test)'

        self.emit_cli('CREATE STREAM test (a json)')
        data = [
            ({'key': 'value'}, ),
        ]
        self.client.execute('INSERT INTO test (a) VALUES', data)
        sleep(3)
        inserted = self.client.execute(query)
        self.assertEqual(inserted, [(('value',),)])

        with self.created_client(settings=settings) as client:
            inserted = client.execute(query)
            self.assertEqual(inserted, data)
        self.emit_cli('DROP STREAM test')
