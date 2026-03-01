# Chapter 12: Explainable AI Trends

## Diagram 1: XAI Methods
```mermaid
graph TD
    XAI[XAI Methods] --> PostHoc[Post-hoc]
    XAI --> Intrinsic[Intrinsic]
    PostHoc --> Feature[Feature Attribution]
    PostHoc --> Example[Example-based]
    Intrinsic --> Simple[Simple Models]
```

## Diagram 2: SHAP Values
```mermaid
graph TD
    Model[Model Prediction] --> Baseline[Baseline]
    Baseline --> Feature1[Feature 1 Impact]
    Feature1 --> Feature2[Feature 2 Impact]
    Feature2 --> Sum[Sum = Prediction]
```

## Diagram 3: LIME Explanation
```mermaid
graph TD
    Prediction[Prediction] --> Perturb[Perturb Input]
    Perturb --> Weight[Weight Samples]
    Weight --> Train[Train Simple Model]
    Train --> Explain[Explanation]
```

## Diagram 4: Attention Visualization
```mermaid
graph TD
    Input[Input] --> Encode[Encoder]
    Encode --> Attention[Attention Weights]
    Attention --> Visualize[Visualize]
    Visualize --> Interpret[Interpret]
```

## Diagram 5: Counterfactual Explanations
```mermaid
graph TD
    Original[Original Input] --> Predict[Prediction]
    Predict -->|Undesired| Change[Find Changes]
    Change --> Counter[Counterfactual]
    Counter --> NewPred[New Prediction]
```
