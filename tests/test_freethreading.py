import threading
import time
from unittest import TestCase

from proton_driver.bufferedreader import BufferedSocketReader
from proton_driver.columns.largeint import int128_from_quads
from proton_driver.varint import make_varint

from tests.testcase import BaseTestCase


class _FakeSocket:
    """Replays a fixed byte stream through recv_into.

    A real mock.patch('socket.socket') would mutate global state and
    race between threads; this stays purely thread-local.
    """

    def __init__(self, data):
        self._data = data

    def recv_into(self, buf):
        buf[0:len(self._data)] = self._data
        return len(self._data)


class ExtensionConcurrencyTestCase(TestCase):
    """Hammer the compiled extensions from many threads at once.

    Needs no server, so the smoke-ft CI job runs it on 3.14t where the
    threads execute genuinely in parallel. On GIL builds it still
    exercises object lifetimes under thread contention.
    """

    THREADS = 8
    ITERATIONS = 2000

    def run_in_threads(self, work):
        barrier = threading.Barrier(self.THREADS)
        errors = []

        def runner():
            try:
                barrier.wait()
                work()
            except Exception as exc:
                errors.append(exc)

        threads = [
            threading.Thread(target=runner) for _ in range(self.THREADS)
        ]
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        self.assertEqual(errors, [])

    def test_varint_parallel(self):
        def work():
            for i in range(self.ITERATIONS):
                self.assertEqual(make_varint(i), make_varint(i))

        self.run_in_threads(work)

    def test_largeint_parallel(self):
        quads = (1, 2, 3, 4)
        expected = int128_from_quads(quads, 2)

        def work():
            for _ in range(self.ITERATIONS):
                self.assertEqual(int128_from_quads(quads, 2), expected)

        self.run_in_threads(work)

    def test_buffered_reader_parallel(self):
        # Each thread gets its own reader (the supported usage model);
        # parallelism stresses allocator paths and module-level setup.
        data = b'\x05hello' * 64

        def work():
            for _ in range(100):
                reader = BufferedSocketReader(_FakeSocket(data), 1024)
                strings = reader.read_strings(64, encoding='utf-8')
                self.assertEqual(len(strings), 64)
                self.assertEqual(strings[0], 'hello')

        self.run_in_threads(work)


class ParallelClientsTestCase(BaseTestCase):
    """Many threads, one Client each, against a live server.

    Validates the whole native-protocol stack (bufferedreader/writer,
    varint, columns) under genuine parallelism on free-threaded builds.
    """

    THREADS = 8

    def run_in_threads(self, work):
        barrier = threading.Barrier(self.THREADS)
        errors = []

        def runner(ix):
            try:
                barrier.wait()
                work(ix)
            except Exception as exc:
                errors.append(exc)

        threads = [
            threading.Thread(target=runner, args=(ix,))
            for ix in range(self.THREADS)
        ]
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        self.assertEqual(errors, [])

    def test_parallel_queries(self):
        results = [None] * self.THREADS

        def work(ix):
            client = self._create_client()
            try:
                results[ix] = client.execute(
                    'SELECT number FROM system.numbers LIMIT 1000'
                )
            finally:
                client.disconnect()

        self.run_in_threads(work)

        expected_rows = [(i,) for i in range(1000)]
        for rv in results:
            self.assertEqual(rv, expected_rows)

    def test_parallel_inserts(self):
        rows_per_thread = 100

        with self.create_stream('x int32'):
            def work(ix):
                client = self._create_client()
                try:
                    client.execute(
                        'INSERT INTO test (x) VALUES',
                        [(ix * rows_per_thread + i,)
                         for i in range(rows_per_thread)]
                    )
                finally:
                    client.disconnect()

            self.run_in_threads(work)

            # Plain SELECT is bounded on Memory-engine streams (table()
            # is not applicable to them on newer servers). Inserted rows
            # are eventually visible; poll briefly before failing.
            expected = self.THREADS * rows_per_thread
            deadline = time.monotonic() + 5
            while True:
                rv = self.client.execute('SELECT count(*) FROM test')
                if rv == [(expected,)] or time.monotonic() > deadline:
                    break
                time.sleep(0.2)
            self.assertEqual(rv, [(expected,)])
