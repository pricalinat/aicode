# Chapter 11: Cost Optimization Methods

## Diagram 1: Cloud Cost Hierarchy
```mermaid
graph TD
    Total[Total Cost] --> Compute[Compute]
    Total --> Storage[Storage]
    Total --> Network[Network]
    Total --> Managed[Managed Services]
```

## Diagram 2: Reserved vs On-Demand
```mermaid
graph TD
    Usage[Usage Pattern] --> Predict{Predictable?}
    Predict -->|Yes| Reserved[Reserved Instances]
    Predict -->|No| OnDemand[On-Demand]
    Reserved --> Savings[Cost Savings 40-60%]
    OnDemand --> Premium[Pay Premium]
```

## Diagram 3: Auto Scaling Cost
```mermaid
graph TD
    Traffic --> Scale{Scale Down?}
    Scale -->|Yes| Reduce[Reduce Instances]
    Scale -->|No| Maintain[Maintain Current]
    Reduce --> Save[Cost Saved]
```

## Diagram 4: Storage Tiering
```mermaid
graph TD
    Data[Data Age] --> Hot[Hot Storage]
    Data --> Warm[Warm Storage]
    Data --> Cold[Cold/Archive]
    Hot -->|SSD| Expensive[High Cost]
    Warm -->|HDD| Medium[Medium Cost]
    Cold -->|Tape/Glacier| Cheap[Low Cost]
```

## Diagram 5: Right-Sizing Resources
```mermaid
graph TD
    Monitor[Monitor Usage] --> Analyze[Analyze Metrics]
    Analyze --> OverProvision{Over-provisioned?}
    OverProvision -->|Yes| Downsize[Downsize]
    OverProvision -->|No| UnderProvision{Under-provisioned?}
    UnderProvision -->|Yes| Upsize[Upsize]
    UnderProvision -->|No| Optimal[Optimal]
```
