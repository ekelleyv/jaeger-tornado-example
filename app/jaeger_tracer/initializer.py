from __future__ import absolute_import

import logging
import threading

import opentracing_instrumentation.config
import opentracing_instrumentation.client_hooks
from jaeger_client import Config

logger = logging.getLogger(__name__)


class JaegerTracerInitializer(object):
    """
    Base class for all initializers that instantiates Jaeger Config,
    installs Jaeger Tracer as global tracer, configures parameters of
    opentracing_instrumentation and installs client-lib patches.
    """

    _initialized = False
    _initialize_lock = threading.Lock()

    def __init__(self, config, service_name, metrics=None):
        self._config = config
        self.config = Config(
            config=config, metrics=metrics, service_name=service_name)

    def initialize_tracer(self, io_loop=None):
        """
        Install Jaeger Tracer as global tracer, configure parameters of
        opentracing_instrumentation and install client-lib patches.

        This method uses a static flag to check that it's only run once.

        :param io_loop: optional Tornado IOLoop to use for trace reporting.
        """
        with JaegerTracerInitializer._initialize_lock:
            if JaegerTracerInitializer._initialized:
                return
            JaegerTracerInitializer._initialized = True

        self.config.initialize_tracer(io_loop=io_loop)
        self._init_instrumentation_config()
        opentracing_instrumentation.client_hooks.install_patches(
            patchers=self._config.get('client_hooks', None)
        )
        opentracing_instrumentation.client_hooks.install_client_interceptors(
            client_interceptors=self._config.get('client_interceptors', ())
        )

    def _init_instrumentation_config(self):
        cfg = opentracing_instrumentation.config.CONFIG
        cfg.app_name = self.config.service_name
        cfg.caller_name_headers.append('X-Uber-Source')
        cfg.callee_endpoint_headers.append('X-Uber-Endpoint')
