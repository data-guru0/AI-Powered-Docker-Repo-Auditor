import os
import logging
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor, SpanExporter
from opentelemetry.sdk.resources import Resource
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor

logger = logging.getLogger(__name__)


def _build_exporter() -> SpanExporter:
    endpoint = os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT")
    if endpoint:
        try:
            from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
            return OTLPSpanExporter(endpoint=endpoint)
        except Exception as exc:
            logger.warning("OTLP exporter failed, falling back to console: %s", exc)
    from opentelemetry.sdk.trace.export import ConsoleSpanExporter
    return ConsoleSpanExporter()


def setup_telemetry(app) -> None:
    try:
        resource = Resource.create({
            "service.name": "docker-auditor-backend",
            "service.version": "1.0.0",
        })

        kwargs: dict = {"resource": resource}
        try:
            from opentelemetry.sdk.extension.aws.trace import AwsXRayIdGenerator
            kwargs["id_generator"] = AwsXRayIdGenerator()
            logger.info("Using AWS X-Ray ID generator")
        except ImportError:
            pass

        provider = TracerProvider(**kwargs)
        provider.add_span_processor(BatchSpanProcessor(_build_exporter()))
        trace.set_global_tracer_provider(provider)

        FastAPIInstrumentor.instrument_app(
            app,
            tracer_provider=provider,
            excluded_urls="/health",
        )
        logger.info("OpenTelemetry instrumentation enabled")
    except Exception as exc:
        logger.warning("Telemetry setup failed (non-fatal): %s", exc)
