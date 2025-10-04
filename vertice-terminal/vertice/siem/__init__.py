"""
🔍 SIEM Integration & Log Management
Agregação, parsing, normalização e correlação de logs

Componentes:
- LogAggregator: Agregação de logs multi-source
- LogParser: Parsing e normalização de logs
- CorrelationEngine: Correlação de eventos
- SIEMConnector: Conectores para SIEMs enterprise
"""

from .log_aggregator import (
    LogAggregator,
    LogSource,
    LogEntry,
    LogSourceType,
)
from .log_parser import (
    LogParser,
    ParsedLog,
    LogFormat,
)
from .correlation_engine import (
    CorrelationEngine,
    CorrelationRule,
    CorrelatedEvent,
)
from .siem_connector import (
    SIEMConnector,
    SIEMType,
    SIEMConfig,
)

__all__ = [
    "LogAggregator",
    "LogSource",
    "LogEntry",
    "LogSourceType",
    "LogParser",
    "ParsedLog",
    "LogFormat",
    "CorrelationEngine",
    "CorrelationRule",
    "CorrelatedEvent",
    "SIEMConnector",
    "SIEMType",
    "SIEMConfig",
]
