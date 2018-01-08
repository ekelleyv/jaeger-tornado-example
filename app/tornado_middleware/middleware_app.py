import logging

from tornado.web import Application
from tornado.web import _RequestDispatcher

from .middleware_handler import MiddlewareHandler

log = logging.getLogger(__name__)


class MiddlewareApp(Application):
    """Middleware-aware Application class.

    This basically replaces the default
    :class:`tornado.web._RequestDispatcher` with a
    :class:`MiddlewareDispatcher`.

    Normally, this shouldn't be used directly as it will be constructed by
    :func:`build_app`.
    """

    def __init__(self, middlewares, *args, **kwargs):
        super(MiddlewareApp, self).__init__(*args, **kwargs)
        self.middlewares = middlewares

    def start_request(self, server_conn, request_conn):
        return MiddlewareDispatcher(
            self.middlewares, self, request_conn)

    def __call__(self, request):
        dispatcher = MiddlewareDispatcher(self.middlewares, self, None)
        dispatcher.set_request(request)
        return dispatcher.execute()


class MiddlewareDispatcher(_RequestDispatcher):
    """Middleware-aware request dispatcher.

    The dispatcher delegates all work to the default dispatcher, but it
    injects a :class:`MiddlewareHandler` as handler for all requests, which
    will actually run the middlewares.
    """
    def __init__(self, middlewares, *args, **kwargs):
        super(MiddlewareDispatcher, self).__init__(*args, **kwargs)
        self.middlewares = middlewares

    def _find_handler(self):

        super(MiddlewareDispatcher, self)._find_handler()
        args = {
            'kwargs': self.handler_kwargs,
            'middlewares': self.middlewares,
            'handler_class': self.handler_class,
        }
        self.handler_class = MiddlewareHandler
        self.handler_kwargs = args


def build_app(middlewares, *args, **kwargs):
    """Create a Tornado ``Application`` object with optional support for
    middlewares.

    :param list middlewares: A list of callable objects, which will be
                             configured as middlewares on the application.
                             If the list contains a class then the class
                             will be instantiated using a no-args constructor,
                             and the result is expected to be callable.
    :param args: Args to pass into the ``Application`` constructor.
    :param kwargs: kwargs to pass into the ``Application`` constructor.
    """
    if middlewares:
        mws = []
        for mw in middlewares:
            if isinstance(mw, type):
                mw = mw()
            if not callable(mw):
                raise ValueError(
                    'Middleware object must be callable. %s is not.' % mw)
            mws.append(mw)
        return MiddlewareApp(mws, *args, **kwargs)
    else:
        return Application(*args, **kwargs)
