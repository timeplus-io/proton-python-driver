import types
try:
    import numpy as np
    import pandas as pd
except ImportError:
    np = None
    pd = None

from tests.testcase import BaseTestCase
from tests.numpy.testcase import NumpyBaseTestCase
from proton_driver import connect
from datetime import datetime
from decimal import Decimal


class GenericTestCase(NumpyBaseTestCase):
    n = 10

    def test_columnar(self):
        rv = self.client.execute(
            'SELECT number FROM numbers({})'.format(self.n), columnar=True
        )

        self.assertEqual(len(rv), 1)
        self.assertIsInstance(rv[0], (np.ndarray, ))

    def test_rowwise(self):
        rv = self.client.execute(
            'SELECT number FROM numbers({})'.format(self.n)
        )

        self.assertEqual(len(rv), self.n)
        self.assertIsInstance(rv[0], (np.ndarray, ))

    def test_insert_not_supported(self):
        data = [np.array(range(self.n))]

        with self.create_stream('a int32'):
            with self.assertRaises(ValueError) as e:
                self.client.execute(
                    'INSERT INTO test (a) VALUES', data
                )

            self.assertEqual(
                'NumPy inserts is only allowed with columnar=True',
                str(e.exception)
            )

    def test_with_column_types(self):
        rv = self.client.execute(
            'SELECT CAST(2 AS int32) AS x', with_column_types=True
        )

        self.assertEqual(rv, ([(2, )], [('x', 'int32')]))


class NumpyProgressTestCase(NumpyBaseTestCase):
    def test_select_with_progress(self):
        progress = self.client.execute_with_progress('SELECT 2')
        self.assertEqual(
            list(progress),
            [(1, 0), (1, 0)]
        )
        self.assertEqual(progress.get_result(), [(2,)])
        self.assertTrue(self.client.connection.connected)

    def test_select_with_progress_no_progress_obtaining(self):
        progress = self.client.execute_with_progress('SELECT 2')
        self.assertEqual(progress.get_result(), [(2,)])


class NumpyIteratorTestCase(NumpyBaseTestCase):
    def test_select_with_iter(self):
        result = self.client.execute_iter(
            'SELECT number FROM system.numbers LIMIT 10'
        )
        self.assertIsInstance(result, types.GeneratorType)

        self.assertEqual(list(result), list(zip(range(10))))
        self.assertEqual(list(result), [])

    def test_select_with_iter_with_column_types(self):
        result = self.client.execute_iter(
            'SELECT CAST(number AS uint32) as number '
            'FROM system.numbers LIMIT 10',
            with_column_types=True
        )
        self.assertIsInstance(result, types.GeneratorType)

        self.assertEqual(
            list(result),
            [[('number', 'uint32')]] + list(zip(range(10)))
        )
        self.assertEqual(list(result), [])


class DataFrameTestCase(NumpyBaseTestCase):
    def test_query_simple(self):
        df = self.client.query_dataframe(
            'SELECT CAST(number AS int64) AS x FROM system.numbers LIMIT 100'
        )

        self.assertTrue(df.equals(pd.DataFrame({'x': range(100)})))

    def test_query_replace_whitespace_in_column_names(self):
        df = self.client.query_dataframe(
            'SELECT number AS "test me" FROM system.numbers LIMIT 100'
        )

        self.assertIn('test_me', df)

    def test_insert_simple(self):
        n = 10
        df = pd.DataFrame({
            'a': range(n),
            'b': [float(x) for x in range(n)]
        })

        with self.create_stream('a int64, b float64'):
            rv = self.client.insert_dataframe('INSERT INTO test VALUES', df)
            self.assertEqual(rv, n)
            df2 = self.client.query_dataframe('SELECT * FROM test ORDER BY a')
            self.assertTrue(df.equals(df2))

    def test_insert_chunking(self):
        with self.create_stream('a int64'):
            rv = self.client.execute(
                'INSERT INTO test VALUES', [np.array(range(3))], columnar=True,
                settings={'insert_block_size': 1}
            )
            self.assertEqual(rv, 3)

    def test_insert_not_ordered_columns(self):
        n = 10
        df = pd.DataFrame({
            'b': range(n),
            'a': [str(x) for x in range(n)]
        })[['b', 'a']]

        with self.create_stream('a string, b float64'):
            rv = self.client.insert_dataframe(
                'INSERT INTO test (a, b) VALUES', df
            )
            self.assertEqual(rv, n)


class NoNumPyTestCase(BaseTestCase):
    def setUp(self):
        super(NoNumPyTestCase, self).setUp()

        try:
            import numpy  # noqa: F401
            import pandas  # noqa: F401
        except Exception:
            pass

        else:
            self.skipTest('NumPy extras are installed')

    def test_runtime_error_without_numpy(self):
        with self.assertRaises(RuntimeError) as e:
            with self.created_client(settings={'use_numpy': True}) as client:
                client.execute('SELECT 1')

        self.assertEqual(
            'Extras for NumPy must be installed', str(e.exception)
        )

    def test_query_dataframe(self):
        with self.assertRaises(RuntimeError) as e:
            with self.created_client(settings={'use_numpy': True}) as client:
                client.query_dataframe('SELECT 1 AS x')

        self.assertEqual(
            'Extras for NumPy must be installed', str(e.exception)
        )


class DataFrameDBAPITestCase(NumpyBaseTestCase):
    types = \
        'a int64, b string, c datetime,' \
        'd fixed_string(10), e decimal(9, 5), f float64,' \
        'g low_cardinality(string), h nullable(int32)'

    columns = 'a,b,c,d,e,f,g,h'
    data = [
        [
            123, 'abc', datetime(2024, 5, 20, 12, 11, 10),
            'abcefgcxxx', Decimal('300.42'), 3.402823e12,
            '127001', 332
        ],
        [
            456, 'cde', datetime(2024, 6, 21, 12, 13, 50),
            '1234567890', Decimal('171.31'), -3.4028235e13,
            '127001', None
        ],
        [
            789, 'efg', datetime(1998, 7, 22, 12, 30, 10),
            'stream sql', Decimal('894.22'), float('inf'),
            '127001', None
        ],
    ]

    def setUp(self):
        super(DataFrameDBAPITestCase, self).setUp()
        self.conn = connect('proton://localhost')
        self.cur = self.conn.cursor()
        self.cur.execute('DROP STREAM IF EXISTS test')
        self.cur.execute(f'CREATE STREAM test ({self.types}) ENGINE = Memory')
        self.cur.execute(
            f'INSERT INTO test ({self.columns}) VALUES',
            self.data
        )
        self.cur.execute(f'SELECT {self.columns} FROM test')

    def tearDown(self):
        super(DataFrameDBAPITestCase, self).tearDown()
        self.cur.execute('DROP STREAM test')

    def test_dbapi_fetchnumpy(self):
        expect = {
            col: np.array([row[i] for row in self.data])
            for i, col in enumerate(self.columns.split(','))
        }
        rv = self.cur.fetchnumpy()
        for key, value in expect.items():
            self.assertIsNotNone(rv.get(key))
            self.assertarraysEqual(value, rv[key])

    def test_dbapi_df(self):
        expect = pd.DataFrame(self.data, columns=self.columns.split(','))
        df = self.cur.df()

        self.assertIsInstance(df, pd.DataFrame)
        self.assertEqual(df.shape, (3, 8))
        self.assertEqual(
            [type.name for type in df.dtypes],
            ['int64', 'object', 'datetime64[ns]',
             'object', 'object', 'float64',
             'object', 'float64']
        )
        self.assertTrue(expect.equals(df))

    def test_dbapi_pl(self):
        try:
            import polars as pl
        except ImportError:
            self.skipTest('Polars extras are not installed')

        expect = pl.DataFrame({
            col: [row[i] for row in self.data]
            for i, col in enumerate(self.columns.split(','))
        })

        df = self.cur.pl()
        self.assertIsInstance(df, pl.DataFrame)
        self.assertEqual(df.shape, (3, 8))
        self.assertSequenceEqual(
            df.schema.dtypes(),
            [pl.Int64, pl.String, pl.Datetime, pl.String,
             pl.Decimal, pl.Float64, pl.String, pl.Int64]
        )
        self.assertTrue(expect.equals(df))

    def test_dbapi_arrow(self):
        try:
            import pyarrow as pa
        except ImportError:
            self.skipTest('Pyarrow extras are not installed')

        expect = pa.table({
            col: [row[i] for row in self.data]
            for i, col in enumerate(self.columns.split(','))
        })
        at = self.cur.arrow()
        self.assertEqual(at.shape, (3, 8))
        self.assertSequenceEqual(
            at.schema.types,
            [pa.int64(), pa.string(), pa.timestamp('us'),
             pa.string(), pa.decimal128(5, 2), pa.float64(),
             pa.string(), pa.int64()]
        )
        self.assertTrue(expect.equals(at))
