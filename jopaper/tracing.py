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

jaeger_endpoint = os.environ.get("JAEGER_ENDPOINT")


def setup_tracer(fastapi_app):
    tracer = TracerProvider(
        resource=Resource.create(
            {
                "service.name": "jopaper",
            }
        )
    )
    trace.set_tracer_provider(tracer)
    tracer.add_span_processor(
        BatchSpanProcessor(OTLPSpanExporter(endpoint=jaeger_endpoint, insecure=True))
    )

    FastAPIInstrumentor.instrument_app(fastapi_app, tracer_provider=tracer)
    LoggingInstrumentor().instrument(set_logging_format=True, tracer_provider=tracer)
    RequestsInstrumentor().instrument(tracer_provider=tracer)
