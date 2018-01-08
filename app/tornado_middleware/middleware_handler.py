"""This emulates middlewares from Flask/Werkzeug.

A middleware is injected into the general request processing and is able to
run code before and after a request. Typical use cases are timing, logging,
validation, etc.

Using a middleware makes it possible to avoid overriding
:meth:`tornado.web.RequestHandler._execute` and have an arbitrary list of
middlewares.

A middleware is basically just a callable object that takes 3 arguments,
for example:

.. code-block:: python

    def dummy_middleware(request, handler, next_mw):
      log.debug(request.headers.get('X-Source'))
      yield next_mw()


A middleware *must* either `yield` the next_mw argument to proceed or write
a response by itself using the handler argument. Failure to do so will make
the request hang.

If a middleware raises an exception, a ``500 Server Error`` will be returned
to the client.

Using
-----

To use middlewares, don't construct the :class:`tornado.web.Application`
object directly. Instead, use the :func:`build_app` function, which will
enable the middlewares.
"""
from functools import partial
import logging
import sys

from tornado import gen
from tornado.web import RequestHandler


log = logging.getLogger(__name__)


class MiddlewareHandler(RequestHandler):
    """Handler to execute middlewares.

    This works as a delegate for the actual request handler. Before the
    real handler is invoked, any configured middlewares will be executed.

    The middleware execution is done by chaining calls, and middlewares
    themselves must make sure to invoke the next in the chain.
    """
    def __init__(self, application, request, handler_class, middlewares,
                 kwargs):
        self.delegate = handler_class(application, request, **kwargs)
        self.middlewares = middlewares

    def __getattr__(self, name):
        return getattr(self.delegate, name)

    @gen.coroutine
    def _execute(self, transforms, *args, **kwargs):
        self.delegate._transforms = transforms
        try:
            res = yield self.run_middleware(0, transforms, *args, **kwargs)
        except:
            log.exception('Error while executing middlewares')
            self.delegate.send_error(500, exc_info=sys.exc_info())
        else:
            raise gen.Return(res)

    @gen.coroutine
    def run_middleware(self, idx, transforms, *args, **kwargs):
        if idx == len(self.middlewares) - 1:
            next_mw = partial(self._execute_handler, transforms,
                              *args, **kwargs)
        else:
            next_mw = partial(self.run_middleware, idx + 1, transforms,
                              *args, **kwargs)
        res = yield self.middlewares[idx](self.delegate.request, self.delegate,
                                          next_mw)
        raise gen.Return(res)

    @gen.coroutine
    def _execute_handler(self, transforms, *args, **kwargs):
        res = yield self.delegate._execute(transforms, *args, **kwargs)
        raise gen.Return(res)
