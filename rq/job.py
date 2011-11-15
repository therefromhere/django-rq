import uuid
from pickle import loads, dumps
from .proxy import conn
from .queue import Queue


class DelayedResult(object):
    def __init__(self, key):
        self.key = key
        self._rv = None

    @property
    def return_value(self):
        if self._rv is None:
            rv = conn.get(self.key)
            if rv is not None:
                # cache the result
                self._rv = loads(rv)
        return self._rv


class job(object):
    def __init__(self, queue_name='default'):
        self.queue = Queue(queue_name)

    def __call__(self, f):
        def enqueue(queue, *args, **kwargs):
            if not isinstance(queue, Queue):
                raise ValueError('Argument queue must be a Queue.')
            rv_key = '%s:result:%s' % (queue.key, str(uuid.uuid4()))
            if f.__module__ == '__main__':
                raise ValueError('Functions from the __main__ module cannot be processed by workers.')
            s = dumps((f, rv_key, args, kwargs))
            conn.rpush(queue.key, s)
            return DelayedResult(rv_key)
        f.enqueue = enqueue

        def delay(*args, **kwargs):
            return f.enqueue(self.queue, *args, **kwargs)
        f.delay = delay
        return f

