from __future__ import absolute_import

from tornado import gen
from opentracing_instrumentation import http_server, request_context
from .initializer import JaegerTracerInitializer


class JaegerTracerMiddleware(object):
    """
    clay-tornado style middleware that creates OpenTracing spans
    for each inbound request.

    It also initializes Jaeger tracer if not initialized already.
    """
    def __init__(self, config=None, service_name=None):
        self._initializer = JaegerTracerInitializer(config=config, service_name=service_name)
        self._initializer.initialize_tracer()

    @gen.coroutine
    def __call__(self, request, _, next_mw):
        # TODO find out if the route can be read from handler
        request_wrapper = http_server.TornadoRequestWrapper(request=request)
        span = http_server.before_request(request=request_wrapper)
        try:
            with request_context.span_in_stack_context(span=span):
                next_mw_future = next_mw()  # cannot yield inside StackContext
            yield next_mw_future
        except Exception as e:
            span.set_tag('error', True)
            span.log_event(event='error', payload=e)
            raise
        finally:
            span.finish()
