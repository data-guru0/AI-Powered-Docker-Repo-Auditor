import os
import logging

logger = logging.getLogger(__name__)


def setup_telemetry(app) -> None:
    try:
        from opentelemetry import trace
        from opentelemetry.sdk.trace import TracerProvider
        from opentelemetry.sdk.trace.export import BatchSpanProcessor, ConsoleSpanExporter
        from opentelemetry.sdk.resources import Resource
        from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor

        resource = Resource.create({
            "service.name": "docker-auditor-backend",
            "service.version": "1.0.0",
        })

        kwargs: dict = {"resource": resource}
        try:
            from opentelemetry.sdk.extension.aws.trace import AwsXRayIdGenerator
            kwargs["id_generator"] = AwsXRayIdGenerator()
        except ImportError:
            pass

        endpoint = os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT")
        if endpoint:
            try:
                from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
                exporter = OTLPSpanExporter(endpoint=endpoint)
            except Exception:
                exporter = ConsoleSpanExporter()
        else:
            exporter = ConsoleSpanExporter()

        provider = TracerProvider(**kwargs)
        provider.add_span_processor(BatchSpanProcessor(exporter))
        trace.set_global_tracer_provider(provider)

        FastAPIInstrumentor.instrument_app(
            app,
            tracer_provider=provider,
            excluded_urls="/health",
        )
        logger.info("OpenTelemetry instrumentation enabled")
    except Exception as exc:
        logger.warning("Telemetry setup failed (non-fatal): %s", exc)
