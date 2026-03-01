# Chapter 12: Human-Machine Collaboration Modes

## Diagram 1: Automation Spectrum
```mermaid
graph LR
    Human[Full Human] --> Assist[AI Assist]
    Assist --> Collaborate[Collaborate]
    Collaborate --> AI[Full AI]
```

## Diagram 2: Human-in-the-Loop
```mermaid
graph TD
    AI[AI System] --> Decision[Decision]
    Decision --> HumanReview[Human Review]
    HumanReview -->|Approve| Execute[Execute]
    HumanReview -->|Reject| Reject[Reject/Modify]
```

## Diagram 3: Human-on-the-Loop
```mermaid
graph TD
    AI[AI System] --> Execute[Execute]
    Execute --> Monitor[Human Monitor]
    Monitor -->|Intervene| Stop[Stop]
    Monitor -->|OK| Continue[Continue]
```

## Diagram 4: Mixed Initiative
```mermaid
graph TD
    Human[Human] --> Suggest[AI Suggest]
    Suggest --> Human[Human Decision]
    Human --> Act[Take Action]
    Act --> Feedback[Feedback to AI]
```

## Diagram 5: Trust Calibration
```mermaid
graph TD
    AI[AI Output] --> Confidence{Confidence Level}
    Confidence -->|High| Auto[Automate]
    Confidence -->|Medium| Explain[Explain]
    Confidence -->|Low| Escalate[Escalate]
```
