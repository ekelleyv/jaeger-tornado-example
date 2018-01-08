import sys
import logging

import tornado.httpserver
import tornado.httpclient
import tornado.gen
import tornado.web

from app.base_handler import BaseHandler
from app.middleware.middleware_app import build_app
from app.jaeger_tracer.middleware import JaegerTracerMiddleware


PORT = 8888
logging.basicConfig(stream=sys.stdout, level=logging.DEBUG)


class ExampleHandler(BaseHandler):

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

    config_doc = {
        "sampler": {
            "type": "const",
            'param': 1,
        },
        "logging": True,
    }

    middlewares = [
        JaegerTracerMiddleware(config=config_doc, service_name="jaeger-tornado-example")
    ]

    app = build_app(middlewares, routes, debug=True)
    return app


if __name__ == '__main__':
    app = make_application()
    server = tornado.httpserver.HTTPServer(app)
    logging.info("Running application on {0}".format(PORT))

    server.listen(PORT)
    tornado.ioloop.IOLoop.current().start()
