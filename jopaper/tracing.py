import os
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import (
    BatchSpanProcessor,
)
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor

from opentelemetry import trace
from opentelemetry.instrumentation.requests import RequestsInstrumentor
from opentelemetry.sdk.resources import Resource
import logging

otlp_endpoint = os.environ.get("OTLP_ENDPOINT", None)


def setup_tracer(fastapi_app, generators):
    if otlp_endpoint is None:
        logging.warn("No monitoring endpoint defined")
        return
    logging.debug(f"Using otlp endpoint {otlp_endpoint}")

    tracer = TracerProvider(
        resource=Resource.create(
            {
                "service.name": "jopaper",
            }
        )
    )
    trace.set_tracer_provider(tracer)
    tracer.add_span_processor(
        BatchSpanProcessor(OTLPSpanExporter(endpoint=otlp_endpoint, insecure=True))
    )

    FastAPIInstrumentor.instrument_app(fastapi_app, tracer_provider=tracer)
    RequestsInstrumentor().instrument(tracer_provider=tracer)
    generators.set_tracer(trace.get_tracer("generators"))
