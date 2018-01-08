import opentracing
from opentracing_instrumentation.http_server import (
    TornadoRequestWrapper,
    before_request
)
from opentracing_instrumentation.request_context import RequestContextManager
import tornado.web


class BaseHandler(tornado.web.RequestHandler):

    def prepare(self):
        super(BaseHandler, self).prepare()

        request = TornadoRequestWrapper(self.request)
        self.handler_span = before_request(request, tracer=opentracing.tracer)
        self.handler_span.set_operation_name("{0}: {1}".format(self.request.method, self.__class__.__name__))
        self.context_manager = RequestContextManager(span=self.handler_span)
        self.context_manager.__enter__()

    def on_finish(self):
        self.handler_span.finish()
        self.context_manager.__exit__()
