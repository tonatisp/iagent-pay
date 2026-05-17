"""
iAgentPay — Observability
Real-time monitoring, structured logging, and anomaly detection.
Compatible with OpenTelemetry, Prometheus, and standard log aggregators.

Features:
  - Structured JSON logging for all payment events
  - Real-time spending dashboard (terminal)
  - Anomaly detection (unusual spend patterns)
  - OpenTelemetry metrics export (optional)
  - Prometheus metrics endpoint (optional)

Usage:
    from iagent_pay.observability import PaymentObserver, ObservabilityConfig

    observer = PaymentObserver(ObservabilityConfig(
        log_level="INFO",
        enable_anomaly_detection=True,
        anomaly_threshold_multiplier=3.0,
    ))

    # Record events
    observer.record_payment(amount=5.0, currency="USDC", to="0x...", success=True)
    observer.record_x402(url="https://api.com/data", amount=0.01, success=True)

    # Print dashboard
    observer.print_dashboard()

    # Get Prometheus metrics
    metrics = observer.get_prometheus_metrics()
"""
import time
import json
import logging
import threading
import statistics
from typing import Optional, List, Dict, Any
from dataclasses import dataclass, field
from collections import deque

logger = logging.getLogger("iagentpay.observability")


@dataclass
class ObservabilityConfig:
    log_level: str = "INFO"
    log_format: str = "json"            # "json" or "text"
    enable_anomaly_detection: bool = True
    anomaly_threshold_multiplier: float = 3.0   # Flag if > 3x avg amount
    enable_otel: bool = False           # OpenTelemetry export
    otel_endpoint: str = ""             # e.g., "http://localhost:4317"
    enable_prometheus: bool = False
    prometheus_port: int = 9090
    history_window: int = 100           # Keep last N events for stats


@dataclass
class PaymentEvent:
    event_type: str          # "payment", "x402", "swap", "budget_exceeded", etc.
    timestamp: float
    amount: float
    currency: str
    success: bool
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_json(self) -> str:
        return json.dumps({
            "timestamp":  self.timestamp,
            "event":      self.event_type,
            "amount":     self.amount,
            "currency":   self.currency,
            "success":    self.success,
            **self.metadata,
        })


class AnomalyDetector:
    """
    Simple statistical anomaly detector for payment amounts.
    Flags transactions that are unusually large compared to history.
    """

    def __init__(self, threshold_multiplier: float = 3.0, min_samples: int = 5):
        self._amounts: deque = deque(maxlen=100)
        self._threshold = threshold_multiplier
        self._min_samples = min_samples

    def check(self, amount: float) -> Optional[str]:
        """
        Returns an anomaly message if amount is unusual, else None.
        """
        self._amounts.append(amount)

        if len(self._amounts) < self._min_samples:
            return None  # Not enough data yet

        avg    = statistics.mean(self._amounts)
        stddev = statistics.stdev(self._amounts) if len(self._amounts) > 1 else 0

        if stddev > 0 and amount > avg + (self._threshold * stddev):
            return (
                f"⚠️ ANOMALY: {amount:.4f} is {amount/avg:.1f}x above average "
                f"({avg:.4f} ± {stddev:.4f})"
            )
        return None


class PaymentObserver:
    """
    Central observability hub for all iAgentPay events.
    """

    def __init__(self, config: Optional[ObservabilityConfig] = None):
        self.config   = config or ObservabilityConfig()
        self._events: List[PaymentEvent] = []
        self._lock    = threading.Lock()
        self._anomaly = AnomalyDetector(
            threshold_multiplier=self.config.anomaly_threshold_multiplier
        )

        # Counters
        self._counters = {
            "payments_total":   0,
            "payments_success": 0,
            "payments_failed":  0,
            "x402_total":       0,
            "x402_paid":        0,
            "swaps_total":      0,
            "anomalies_detected": 0,
            "budget_blocks":    0,
        }
        self._total_spent_usd: float = 0.0

        # Setup logging
        self._setup_logging()

        # Optional: OpenTelemetry
        if self.config.enable_otel:
            self._setup_otel()

    def _setup_logging(self):
        """Configure structured logging."""
        level = getattr(logging, self.config.log_level.upper(), logging.INFO)
        logging.getLogger("iagentpay").setLevel(level)

    def _setup_otel(self):
        """Try to setup OpenTelemetry metrics."""
        try:
            from opentelemetry import metrics
            from opentelemetry.sdk.metrics import MeterProvider
            from opentelemetry.exporter.otlp.proto.grpc.metric_exporter import OTLPMetricExporter
            from opentelemetry.sdk.metrics.export import PeriodicExportingMetricReader

            exporter = OTLPMetricExporter(endpoint=self.config.otel_endpoint)
            reader   = PeriodicExportingMetricReader(exporter)
            provider = MeterProvider(metric_readers=[reader])
            metrics.set_meter_provider(provider)
            self._meter = metrics.get_meter("iagentpay", "5.0.0")
            logger.info(f"[Observability] OpenTelemetry enabled → {self.config.otel_endpoint}")
        except ImportError:
            logger.debug("[Observability] OpenTelemetry not installed (optional)")
            self.config.enable_otel = False

    def _record_event(self, event: PaymentEvent):
        """Internal: record an event and update counters."""
        with self._lock:
            self._events.append(event)
            if len(self._events) > self.config.history_window:
                self._events = self._events[-self.config.history_window:]

        # Structured log
        if self.config.log_format == "json":
            logger.info(event.to_json())
        else:
            status = "✅" if event.success else "❌"
            logger.info(
                f"{status} [{event.event_type}] {event.amount} {event.currency}"
                f" — {event.metadata.get('description', '')}"
            )

    # ─── Public Recording API ─────────────────────────────────────────────────

    def record_payment(
        self,
        amount: float,
        currency: str,
        to: str,
        success: bool,
        tx_hash: str = "",
        description: str = "",
        usd_price: float = 1.0,
    ):
        """Record a payment event."""
        self._counters["payments_total"] += 1
        if success:
            self._counters["payments_success"] += 1
            amount_usd = amount * usd_price
            self._total_spent_usd += amount_usd

            # Anomaly detection
            anomaly = self._anomaly.check(amount_usd)
            if anomaly:
                self._counters["anomalies_detected"] += 1
                logger.warning(f"[Observability] {anomaly}")
        else:
            self._counters["payments_failed"] += 1

        event = PaymentEvent(
            event_type="payment",
            timestamp=time.time(),
            amount=amount,
            currency=currency,
            success=success,
            metadata={"to": to[:20], "tx_hash": tx_hash, "description": description},
        )
        self._record_event(event)

    def record_x402(self, url: str, amount: float, success: bool):
        """Record an x402 micropayment."""
        self._counters["x402_total"] += 1
        if success:
            self._counters["x402_paid"] += 1
        event = PaymentEvent(
            event_type="x402",
            timestamp=time.time(),
            amount=amount,
            currency="USDC",
            success=success,
            metadata={"url": url[:60]},
        )
        self._record_event(event)

    def record_budget_block(self, reason: str, amount: float, currency: str):
        """Record a payment blocked by the Safety Kernel."""
        self._counters["budget_blocks"] += 1
        event = PaymentEvent(
            event_type="budget_blocked",
            timestamp=time.time(),
            amount=amount,
            currency=currency,
            success=False,
            metadata={"reason": reason},
        )
        self._record_event(event)
        logger.warning(f"[Observability] 🛡️ Payment blocked: {reason}")

    def record_anomaly(self, description: str, amount: float):
        """Record a detected anomaly."""
        self._counters["anomalies_detected"] += 1
        logger.warning(f"[Observability] ⚠️ ANOMALY: {description} (amount: {amount})")

    # ─── Reporting ────────────────────────────────────────────────────────────

    def get_stats(self) -> dict:
        """Returns aggregated statistics."""
        amounts = [e.amount for e in self._events if e.success]
        return {
            **self._counters,
            "total_spent_usd":  round(self._total_spent_usd, 4),
            "success_rate":     (
                round(self._counters["payments_success"] /
                      max(1, self._counters["payments_total"]) * 100, 1)
            ),
            "avg_tx_amount":    round(statistics.mean(amounts), 4) if amounts else 0,
            "max_tx_amount":    round(max(amounts), 4) if amounts else 0,
            "recent_events":    len(self._events),
        }

    def print_dashboard(self):
        """Print a formatted terminal dashboard."""
        stats = self.get_stats()
        lines = [
            "",
            "╔══════════════════════════════════════════════╗",
            "║         iAgentPay Observability Dashboard     ║",
            "╠══════════════════════════════════════════════╣",
            f"║  Total Payments:  {stats['payments_total']:<5}  Success Rate: {stats['success_rate']}%      ║",
            f"║  Total Spent:     ${stats['total_spent_usd']:<10.4f}                   ║",
            f"║  Avg Tx Amount:   ${stats['avg_tx_amount']:<10.4f}                   ║",
            f"║  x402 Requests:   {stats['x402_total']:<5}  Paid: {stats['x402_paid']}             ║",
            f"║  Budget Blocks:   {stats['budget_blocks']:<5}                              ║",
            f"║  Anomalies:       {stats['anomalies_detected']:<5}                              ║",
            "╚══════════════════════════════════════════════╝",
            "",
        ]
        print("\n".join(lines))

    def get_prometheus_metrics(self) -> str:
        """Returns metrics in Prometheus text format."""
        stats = self.get_stats()
        lines = [
            "# HELP iagentpay_payments_total Total number of payment attempts",
            "# TYPE iagentpay_payments_total counter",
            f"iagentpay_payments_total {stats['payments_total']}",
            "# HELP iagentpay_payments_success_total Successful payments",
            "# TYPE iagentpay_payments_success_total counter",
            f"iagentpay_payments_success_total {stats['payments_success']}",
            "# HELP iagentpay_total_spent_usd Total USD spent",
            "# TYPE iagentpay_total_spent_usd gauge",
            f"iagentpay_total_spent_usd {stats['total_spent_usd']}",
            "# HELP iagentpay_budget_blocks_total Payments blocked by safety kernel",
            "# TYPE iagentpay_budget_blocks_total counter",
            f"iagentpay_budget_blocks_total {stats['budget_blocks']}",
            "# HELP iagentpay_anomalies_total Anomalies detected",
            "# TYPE iagentpay_anomalies_total counter",
            f"iagentpay_anomalies_total {stats['anomalies_detected']}",
        ]
        return "\n".join(lines)

    def get_recent_events(self, limit: int = 20) -> list:
        """Returns the most recent payment events."""
        return [
            {
                "time":     e.timestamp,
                "type":     e.event_type,
                "amount":   e.amount,
                "currency": e.currency,
                "success":  e.success,
                **e.metadata,
            }
            for e in self._events[-limit:]
        ]


# Global observer instance
_global_observer: Optional[PaymentObserver] = None


def get_observer() -> PaymentObserver:
    """Get or create the global PaymentObserver instance."""
    global _global_observer
    if _global_observer is None:
        _global_observer = PaymentObserver()
    return _global_observer
