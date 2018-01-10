import sys
import logging

import tornado.httpserver
import tornado.httpclient
import tornado.gen
import tornado.web
import tornado.routing

from app.tornado_middleware.middleware_app import build_app
from app.jaeger_tornado_tracer.middleware import JaegerTracerMiddleware


PORT = 8888
logging.basicConfig(stream=sys.stdout, level=logging.DEBUG)


class ExampleHandler(tornado.web.RequestHandler):

    @tornado.gen.coroutine
    def get(self):
        self.set_header("Content-Type", "application/json")

        http_client = tornado.httpclient.AsyncHTTPClient()

        # Do async things
        yield http_client.fetch("https://postman-echo.com/delay/1")

        yield [
            http_client.fetch("https://postman-echo.com/delay/0.5"),
            http_client.fetch("https://postman-echo.com/delay/0.5")
        ]

        self.write({
            "service": "jaeger-test-endpoint",
            "status": 200,
            "version": "2.0.0",
            "message": "ok"
        })


def make_application():
    routes = [
        (r"/", ExampleHandler)
    ]

    middlewares = [
        get_jaeger_middleware()
    ]

    app = build_app(tornado.web.Application, middlewares, routes, debug=True)
    return app


def get_jaeger_middleware():
    config_doc = {
        "sampler": {
            "type": "const",
            'param': 1,
        },
        "client_hooks": "all",
        "logging": True,
    }

    return JaegerTracerMiddleware(config=config_doc, service_name="jaeger-tornado-example")


if __name__ == '__main__':
    app = make_application()
    server = tornado.httpserver.HTTPServer(app)
    logging.info("Running application on {0}".format(PORT))

    server.listen(PORT)
    tornado.ioloop.IOLoop.current().start()
