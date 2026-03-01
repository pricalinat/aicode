# Chapter 11: Monitoring and Alerting System

## Diagram 1: Monitoring Architecture
```mermaid
graph TD
    App1[App Instance 1] --> Collector[Metrics Collector]
    App2[App Instance 2] --> Collector
    App3[App Instance 3] --> Collector
    Collector --> TimeSeriesDB[(Time Series DB)]
    Collector --> Dashboard[Dashboard]
    Collector --> Alert[Alert Manager]
```

## Diagram 2: The RED Method
```mermaid
graph TD
    subgraph "RED Metrics"
        R[Rate - Requests/sec]
        E[Errors - Error Rate]
        D[Duration - Latency]
    end
```

## Diagram 3: The USE Method
```mermaid
graph TD
    subgraph "USE Metrics"
        U[Utilization]
        S[Saturation]
        E[Errors]
    end
```

## Diagram 4: Alert Severity Levels
```mermaid
graph TD
    Trigger[Trigger Condition] --> P1{Priority}
    P1 -->|P1 Critical| Page[On-Call Paging]
    P1 -->|P2 High| Email[Email + SMS]
    P1 -->|P3 Medium| Slack[Slack Notification]
    P1 -->|P4 Low| Ticket[Create Ticket]
```

## Diagram 5: Alert Flow
```mermaid
graph TD
    Metric[Metric Threshold] --> Evaluate[Evaluate]
    Evaluate -->|Exceeded| Group[Alert Grouping]
    Evaluate -->|Normal| Clear[Clear]
    Group --> Route[Route to Team]
    Route --> Notify[Notify]
    Notify --> Ack{Ack?}
    Ack -->|Yes| Resolve[Resolve]
    Ack -->|No| Escalate[Escalate]
```
