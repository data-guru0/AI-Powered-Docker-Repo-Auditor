import logging
import os

logger = logging.getLogger(__name__)

# Metric instruments — None until setup_telemetry() is called
scan_duration = None
agent_duration = None
scans_started = None
scans_completed = None
scans_failed = None


def setup_telemetry() -> None:
    _init_sentry()
    _init_otel()


def _init_sentry() -> None:
    dsn = os.environ.get("SENTRY_DSN", "")
    if not dsn:
        return
    try:
        import sentry_sdk

        sentry_sdk.init(
            dsn=dsn,
            traces_sample_rate=0.1,
            environment=os.environ.get("ENVIRONMENT", "dev"),
            send_default_pii=False,
        )
        logger.info("Sentry initialized for worker")
    except Exception as exc:
        logger.warning("Sentry init failed (continuing without it): %s", exc)


def _init_otel() -> None:
    global scan_duration, agent_duration, scans_started, scans_completed, scans_failed

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

        resource = Resource.create({
            SERVICE_NAME: f"docker-auditor-worker-{os.environ.get('ENVIRONMENT', 'dev')}",
        })

        tracer_provider = TracerProvider(resource=resource)
        tracer_provider.add_span_processor(BatchSpanProcessor(OTLPSpanExporter()))
        trace.set_tracer_provider(tracer_provider)

        metric_reader = PeriodicExportingMetricReader(
            OTLPMetricExporter(), export_interval_millis=30_000
        )
        meter_provider = MeterProvider(resource=resource, metric_readers=[metric_reader])
        metrics.set_meter_provider(meter_provider)

        meter = metrics.get_meter("docker-auditor.worker")
        scan_duration = meter.create_histogram(
            "scan.duration", unit="s", description="Total scan job duration"
        )
        agent_duration = meter.create_histogram(
            "agent.duration", unit="s", description="Per-agent execution duration"
        )
        scans_started = meter.create_counter(
            "scans.started", description="Scans started"
        )
        scans_completed = meter.create_counter(
            "scans.completed", description="Scans completed successfully"
        )
        scans_failed = meter.create_counter(
            "scans.failed", description="Scans that failed"
        )

        logger.info("OpenTelemetry initialized → %s", endpoint)
    except Exception as exc:
        logger.warning("OTel init failed (continuing without it): %s", exc)
