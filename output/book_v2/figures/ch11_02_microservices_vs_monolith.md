# Chapter 11: Microservices vs Monolith Comparison

## Diagram 1: Monolithic Architecture
```mermaid
graph TD
    Client --> WebUI[Web UI]
    WebUI --> Monolith[Monolithic Application]
    Monolith --> Controller[Controllers]
    Controller --> Service[Business Logic]
    Service --> Model[Data Models]
    Service --> DB[(Shared Database)]
```

## Diagram 2: Microservices Architecture
```mermaid
graph TD
    Client --> Gateway[API Gateway]
    Gateway --> Svc1[User Service]
    Gateway --> Svc2[Order Service]
    Gateway --> Svc3[Payment Service]
    Svc1 --> DB1[(User DB)]
    Svc2 --> DB2[(Order DB)]
    Svc3 --> DB3[(Payment DB)]
```

## Diagram 3: Comparison - Deployment
```mermaid
graph LR
    subgraph Monolith
        M1[Single Deploy] --> M2[All or Nothing]
    end
    subgraph Microservices
        S1[Service A] --> S2[Independent Deploy]
        S3[Service B] --> S2
        S4[Service C] --> S2
    end
```

## Diagram 4: Comparison - Data Management
```mermaid
graph TD
    subgraph Monolith
        M1[Shared Database] --> M2[Strong Consistency]
        M2 --> M3[ACID Transactions]
    end
    subgraph Microservices
        S1[Distributed Databases]
        S1 --> S2[Eventual Consistency]
        S2 --> S3[SAGA Pattern]
    end
```

## Diagram 5: Decision Matrix
```mermaid
graph TD
    Start[Start] --> TeamSize{Team Size}
    TeamSize -->|Small| Monolith[Choose Monolith]
    TeamSize -->|Large| Complexity{Circuit Breaker Needed?}
    Complexity -->|Yes| Microservices[Choose Microservices]
    Complexity -->|No| Scale{Scale Requirements?}
    Scale -->|High| Microservices
    Scale -->|Low| Monolith
```
