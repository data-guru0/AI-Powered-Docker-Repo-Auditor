import logging
import os

logger = logging.getLogger(__name__)


def setup_telemetry(app) -> None:
    _init_sentry()
    _init_otel(app)


def _init_sentry() -> None:
    dsn = os.environ.get("SENTRY_DSN", "")
    if not dsn:
        return
    try:
        import sentry_sdk
        from sentry_sdk.integrations.fastapi import FastApiIntegration
        from sentry_sdk.integrations.starlette import StarletteIntegration

        sentry_sdk.init(
            dsn=dsn,
            integrations=[
                StarletteIntegration(transaction_style="url"),
                FastApiIntegration(),
            ],
            traces_sample_rate=0.1,
            environment=os.environ.get("ENVIRONMENT", "dev"),
            send_default_pii=False,
        )
        logger.info("Sentry initialized for backend")
    except Exception as exc:
        logger.warning("Sentry init failed (continuing without it): %s", exc)


def _init_otel(app) -> None:
    endpoint = os.environ.get("OTEL_EXPORTER_OTLP_ENDPOINT", "")
    if not endpoint:
        return
    try:
        from opentelemetry import trace, metrics
        from opentelemetry.sdk.trace import TracerProvider
        from opentelemetry.sdk.trace.export import BatchSpanProcessor
        from opentelemetry.sdk.metrics import MeterProvider
        from opentelemetry.sdk.metrics.export import PeriodicExportingMetricReader
        from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
        from opentelemetry.exporter.otlp.proto.http.metric_exporter import OTLPMetricExporter
        from opentelemetry.sdk.resources import Resource, SERVICE_NAME
        from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor

        resource = Resource.create({
            SERVICE_NAME: f"docker-auditor-backend-{os.environ.get('ENVIRONMENT', 'dev')}",
        })

        tracer_provider = TracerProvider(resource=resource)
        tracer_provider.add_span_processor(BatchSpanProcessor(OTLPSpanExporter()))
        trace.set_tracer_provider(tracer_provider)

        metric_reader = PeriodicExportingMetricReader(
            OTLPMetricExporter(), export_interval_millis=30_000
        )
        meter_provider = MeterProvider(resource=resource, metric_readers=[metric_reader])
        metrics.set_meter_provider(meter_provider)

        FastAPIInstrumentor.instrument_app(app, excluded_urls="health,docs,openapi.json")

        logger.info("OpenTelemetry initialized → %s", endpoint)
    except Exception as exc:
        logger.warning("OTel init failed (continuing without it): %s", exc)
