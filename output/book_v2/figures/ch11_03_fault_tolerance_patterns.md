# Chapter 11: Fault Tolerance Design Patterns

## Diagram 1: Circuit Breaker States
```mermaid
stateDiagram-v2
    [*] --> Closed
    Closed --> Open : Failures > Threshold
    Open --> HalfOpen : Recovery Timeout
    HalfOpen --> Closed : Test Passes
    HalfOpen --> Open : Test Fails
```

## Diagram 2: Retry Pattern
```mermaid
graph TD
    Start[Request] --> Call[Call Service]
    Call -->|Success| Success[Return Success]
    Call -->|Fail| Retry{Retry Count < Max?}
    Retry -->|Yes| Backoff[Exponential Backoff]
    Retry -->|No| Fail[Return Failure]
    Backoff --> Call
```

## Diagram 3: Bulkhead Pattern
```mermaid
graph TD
    Request --> Pool[Thread Pool]
    Pool -->|Pool A| SvcA[Critical Service]
    Pool -->|Pool B| SvcB[Normal Service]
    Pool -->|Pool C| SvcC[Background Service]
    Pool -->|Exhausted| Reject[Reject New Requests]
```

## Diagram 4: Timeout Pattern
```mermaid
graph TD
    Request --> Timeout[Set Timeout]
    Timeout --> Execute[Execute Operation]
    Execute -->|Before Timeout| Success[Return Success]
    Execute -->|Timeout| Cancel[Cancel Operation]
    Cancel --> Fallback[Call Fallback]
```

## Diagram 5: Fallback Pattern
```mermaid
graph TD
    Client --> Primary[Call Primary Service]
    Primary -->|Success| Return1[Return Data]
    Primary -->|Fail| Cache{Cache Available?}
    Cache -->|Yes| Return2[Return Cached Data]
    Cache -->|No| Default{Default Value?}
    Default -->|Yes| Return3[Return Default]
    Default -->|No| Return4[Return Error]
```
