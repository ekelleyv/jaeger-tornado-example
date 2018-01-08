import logging
import json

from jaeger_client import Config
from opentracing_instrumentation.client_hooks import tornado_http


def install_patches():
    tornado_http.install_patches()


def init_tracer():
    config_doc = {
        "sampler": {
            "type": "const",
            'param': 1,
        },
        "logging": True,
    }

    logging.info("Initializing tracer with config: {0}".format(json.dumps(config_doc)))

    config = Config(
        config=config_doc,
        service_name='jaeger-tornado-example',
    )

    config.initialize_tracer()
