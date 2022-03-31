from datetime import date

from tests.testcase import BaseTestCase
from clickhouse_driver import errors
from clickhouse_driver.errors import ServerException
import logging

logger = logging.getLogger(__name__)
formatter = logging.Formatter(
    "%(asctime)s.%(msecs)03d [%(levelname)8s] [%(processName)s] [%(module)s] [%(funcName)s] %(message)s (%(filename)s:%(lineno)s)"
)

class InsertColumnarTestCase(BaseTestCase):
    def test_insert_tuple_ok(self):
        with self.create_table('a int8, b int8'):
            data = [(1, 2, 3), (4, 5, 6)]
            self.client.execute(
                'INSERT INTO test (a, b) VALUES', data, columnar=True
            )
            logger.debug("running here...")
            print(f"running here")
            query = 'SELECT * FROM test'
            inserted = self.emit_cli(query)

            self.assertEqual(inserted, '1\t4\n2\t5\n3\t6\n')
            inserted = self.client.execute(query)
            self.assertEqual(inserted, [(1, 4), (2, 5), (3, 6)])
            inserted = self.client.execute(query, columnar=True)
            self.assertEqual(inserted, [(1, 2, 3), (4, 5, 6)])

    def test_insert_data_different_column_length(self):
        with self.create_table('a int8, b int8'):
            with self.assertRaises(ValueError) as e:
                data = [(1, 2, 3), (4, 5)]
                self.client.execute(
                    'INSERT INTO test (a, b) VALUES', data, columnar=True
                )
            self.assertEqual(str(e.exception), 'Expected 3 rows, got 2')
