import os
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import (
    BatchSpanProcessor,
)
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor

from opentelemetry import trace
from opentelemetry.instrumentation.logging import LoggingInstrumentor
from opentelemetry.instrumentation.requests import RequestsInstrumentor
from opentelemetry.sdk.resources import Resource
import logging

_otlp_endpoint = os.environ.get("OTLP_ENDPOINT", None)


def _create_tracer(endpoint):
    tracer = TracerProvider(
        resource=Resource.create(
            {
                "service.name": "jopaper",
            }
        )
    )
    trace.set_tracer_provider(tracer)
    tracer.add_span_processor(
        BatchSpanProcessor(OTLPSpanExporter(endpoint=endpoint, insecure=True))
    )

    return tracer


if _otlp_endpoint is None:
    logging.warn("No monitoring endpoint defined")
    _tracer = None
else:
    _tracer = _create_tracer(_otlp_endpoint)
    LoggingInstrumentor().instrument(
        set_logging_format=True, log_level=logging.DEBUG, tracer_provider=_tracer
    )
    RequestsInstrumentor().instrument(tracer_provider=_tracer)
    logging.debug(f"Using otlp endpoint {_otlp_endpoint}")


def setup_fastapi(fastapi_app):
    if _tracer is not None:
        FastAPIInstrumentor.instrument_app(fastapi_app, tracer_provider=_tracer)
