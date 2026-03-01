# Chapter 11: Log Analysis System

## Diagram 1: Centralized Logging
```mermaid
graph TD
    App1[App Server 1] --> Agent[Log Agent]
    App2[App Server 2] --> Agent
    App3[App Server 3] --> Agent
    Agent --> Collector[Log Collector]
    Collector --> Pipeline[Processing Pipeline]
    Pipeline --> Storage[(Elasticsearch)]
    Storage --> Kibana[Kibana UI]
```

## Diagram 2: Log Levels
```mermaid
graph TD
    Output --> DEBUG[DEBUG - Detailed]
    Output --> INFO[INFO - General]
    Output --> WARNING[WARNING]
    Output --> ERROR[ERROR]
    Output --> CRITICAL[CRITICAL]
```

## Diagram 3: Structured Logging
```mermaid
graph TD
    Raw[Raw Log] --> Parse[Parse]
    Parse --> Extract[Extract Fields]
    Extract --> Enrich[Enrich Data]
    Enrich --> Index[Index]
    Index --> Search[Search/Query]
```

## Diagram 4: Log Aggregation Flow
```mermaid
graph TD
    App[Application] --> File[Log File]
    File --> Shipper[Log Shipper]
    Shipper --> Queue[Message Queue]
    Queue --> Processor[Log Processor]
    Processor --> Storage[(Storage)]
```

## Diagram 5: Distributed Tracing
```mermaid
graph TD
    Request[User Request] --> Trace[Trace ID]
    Trace --> SvcA[Service A]
    SvcA --> Span1[Span 1]
    SvcA --> SvcB[Service B]
    SvcB --> Span2[Span 2]
    SvcB --> SvcC[Service C]
    Span2 --> Span3[Span 3]
```
