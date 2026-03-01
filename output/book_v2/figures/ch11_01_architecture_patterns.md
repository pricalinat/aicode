# Chapter 11: Industrial Practice - System Architecture Design Patterns

## Diagram 1: Load Balancing Architecture
```mermaid
graph TD
    Client --> LB[Load Balancer]
    LB --> S1[Server 1]
    LB --> S2[Server 2]
    LB --> S3[Server 3]
    S1 --> DB[(Primary DB)]
    S2 --> DB
    S3 --> DB
```

## Diagram 2: Microservices Architecture
```mermaid
graph TD
    Gateway[API Gateway] --> Auth[Auth Service]
    Gateway --> Order[Order Service]
    Gateway --> Payment[Payment Service]
    Gateway --> Inventory[Inventory Service]
    Order --> MSG[Message Queue]
    MSG --> Notification[Notification Service]
    Order --> DB1[(Order DB)]
    Payment --> DB2[(Payment DB)]
    Inventory --> DB3[(Inventory DB)]
```

## Diagram 3: Event-Driven Architecture
```mermaid
graph LR
    Producer -->|Events| Broker[Event Broker]
    Broker -->|Subscribe| Consumer1[Consumer 1]
    Broker -->|Subscribe| Consumer2[Consumer 2]
    Broker -->|Subscribe| Consumer3[Consumer 3]
```

## Diagram 4: CQRS Pattern
```mermaid
graph TD
    Client --> CMD[Command Side]
    Client --> QUERY[Query Side]
    CMD --> CommandHandler[Command Handler]
    QUERY --> QueryHandler[Query Handler]
    CommandHandler --> WriteDB[(Write DB)]
    QueryHandler --> ReadDB[(Read DB)]
    WriteDB --> Sync[Sync Process]
    Sync --> ReadDB
```

## Diagram 5: Saga Pattern
```mermaid
graph TD
    Start[Start] --> Order[Create Order]
    Order --> Payment[Process Payment]
    Payment -->|Success| Inventory[Reserve Inventory]
    Payment -->|Fail| Compensate1[Compensate: Cancel Order]
    Inventory -->|Success| Shipping[Start Shipping]
    Inventory -->|Fail| Compensate2[Compensate: Refund Payment]
    Shipping -->|Success| Complete[Complete]
```

## Diagram 6: Circuit Breaker Pattern
```mermaid
stateDiagram-v2
    [*] --> Closed
    Closed --> Open : Failure threshold exceeded
    Open --> HalfOpen : Timeout
    HalfOpen --> Closed : Success
    HalfOpen --> Open : Failure
```

## Diagram 7: API Gateway Pattern
```mermaid
graph TD
    Client --> Gateway[API Gateway]
    Gateway --> Auth[/auth]
    Gateway --> Users[/users]
    Gateway --> Products[/products]
    Gateway --> Orders[/orders]
    Auth --> AuthSvc[Auth Service]
    Users --> UserSvc[User Service]
    Products --> ProductSvc[Product Service]
    Orders --> OrderSvc[Order Service]
```

## Diagram 8: Service Mesh Architecture
```mermaid
graph TD
    subgraph "Data Plane"
        Pod1[Pod 1] --> Sidecar1[Sidecar Proxy]
        Pod2[Pod 2] --> Sidecar2[Sidecar Proxy]
        Pod3[Pod 3] --> Sidecar3[Sidecar Proxy]
    end
    subgraph "Control Plane"
        Sidecar1 --> Controller[Service Mesh Controller]
        Sidecar2 --> Controller
        Sidecar3 --> Controller
    end
```

## Diagram 9: Multi-Tenant Architecture
```mermaid
graph TD
    Request --> LB[Load Balancer]
    LB --> Gateway[API Gateway]
    Gateway --> TenantRouter[Tenant Router]
    TenantRouter -->|Tenant A| SvcA[Service A - DB A]
    TenantRouter -->|Tenant B| SvcB[Service A - DB B]
    TenantRouter -->|Tenant C| SvcC[Service A - DB C]
```

## Diagram 10: Hexagonal Architecture
```mermaid
graph TD
    subgraph "Driving Adapters"
        UI[UI] --> PortIn[Input Port]
        API[API] --> PortIn
    end
    subgraph "Application Core"
        PortIn --> UseCase[Use Case]
        UseCase --> Domain[Domain Logic]
    end
    subgraph "Driven Adapters"
        PortOut[Output Port] --> DB[Database]
        PortOut --> Queue[Message Queue]
        PortOut --> Ext[External API]
    end
    UseCase --> PortOut
```
