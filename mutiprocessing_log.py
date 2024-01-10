import logging
import logging.handlers
import multiprocessing
from multiprocessing.pool import Pool

# Taken from
# https://docs.python.org/3.6/howto/logging-cookbook.html#logging-to-a-single-file-from-multiple-processes


def listener_process(queue, formatting, filename):
    root = logging.getLogger()
    f = logging.Formatter(formatting)
    h = logging.StreamHandler()
    h.setFormatter(f)
    root.addHandler(h)
    if filename is not None:
        h = logging.FileHandler(filename, 'a')
        h.setFormatter(f)
        root.addHandler(h)
    while True:
        try:
            record = queue.get()
            if record is None:  # We send this as a sentinel to tell the listener to quit.
                break
            logger = logging.getLogger(record.name)
            logger.handle(record)  # No level or filter logic applied - just do it!
        except Exception:
            import sys, traceback
            print('Whoops! Problem:', file=sys.stderr)
            traceback.print_exc(file=sys.stderr)


def worker_configurer(queue, level):
    h = logging.handlers.QueueHandler(queue)  # Just the one handler needed
    root = logging.getLogger()
    root.addHandler(h)
    root.setLevel(level)


class LoggingPool:

    __shared_state = {}

    def __init__(self, formatting="", filename=None, level=logging.DEBUG):
        self.__dict__ = self.__shared_state
        if not LoggingPool.__shared_state:
            self._queue = multiprocessing.Queue(-1)
            self._log_level = level
            self._listener = multiprocessing.Process(target=listener_process, args=(self._queue, formatting, filename))
            self._listener.start()
            worker_configurer(self._queue, self._log_level)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.release_logging()

    def make_pool(self, processes=None) -> Pool:
        return Pool(processes=processes, initializer=worker_configurer, initargs=(self._queue, self._log_level))

    def release_logging(self):
        self._queue.put_nowait(None)
        self._listener.join()
