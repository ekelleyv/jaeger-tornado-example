import logging

from .middleware_handler import MiddlewareHandler

log = logging.getLogger(__name__)


def _get_middleware_app(base):
    class MiddlewareApp(base):
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

        def find_handler(self, request):
            handler_delegate = super(MiddlewareApp, self).find_handler(request)

            args = {
                'kwargs': handler_delegate.handler_kwargs,
                'middlewares': self.middlewares,
                'handler_class': handler_delegate.handler_class,
            }

            handler_delegate.handler_class = MiddlewareHandler
            handler_delegate.handler_kwargs = args
            return handler_delegate

        def __call__(self, request):
            dispatcher = self.find_handler(request)
            return dispatcher.execute()

    return MiddlewareApp


def build_app(base_app, middlewares, *args, **kwargs):
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
        return _get_middleware_app(base_app)(mws, *args, **kwargs)
    else:
        return base_app(*args, **kwargs)
