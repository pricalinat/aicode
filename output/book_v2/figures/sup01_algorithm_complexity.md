# Supplementary: Algorithm Complexity Comparison

## Diagram 1: Time Complexity Comparison
```mermaid
graph TD
    O1[O(1)] --> Best[Best]
    OlogN[O(log n)] --> Good[Good]
    ON[O(n)] --> Fair[Fair]
    ONlogN[O(n log n)] --> Fair
    ON2[O(n²)] --> Poor[Poor]
    O2N[O(2^n)] --> Worst[Worst]
```

## Diagram 2: Search Algorithms
```mermaid
graph LR
    Linear[Linear Search] --> ON[O(n)]
    Binary[Binary Search] --> OlogN[O(log n)]
    Hash[Hash Table] --> O1[O(1)]
    BST[Binary Search Tree] --> OlogN
```

## Diagram 3: Sorting Algorithms
```mermaid
graph LR
    Bubble[Bubble Sort] --> ON2[O(n²)]
    Quick[Quick Sort] --> ONlogN[O(n log n)]
    Merge[Merge Sort] --> ONlogN
    Heap[Heap Sort] --> ONlogN
    Timsort[Timsort] --> ONlogN
```

## Diagram 4: Space Complexity
```mermaid
graph TD
    InPlace[In-Place] --> Small[Small Space]
    OutPlace[Out-of-Place] --> Large[Large Space]
    Recursive[Recursive] --> Stack[Stack Space]
```

## Diagram 5: Neural Network Complexity
```mermaid
graph TD
    FC[Fully Connected] --> ON[O(n×m)]
    Conv[Convolutional] --> Okernel[O(k²×c×f)]
    Attention[Attention] --> Osequence2[O(n²×d)]
```

## Diagram 6: Model Size Trends
```mermaid
graph TD
    2018[2018] --> GPT1[117M]
    2019[2019] --> GPT2[1.5B]
    2020[2020] --> GPT3[175B]
    2023[2023] --> GPT4[1.7T]
```

## Diagram 7: Training Cost Comparison
```mermaid
graph LR
    CPU[CPU Training] --> Days[Days-Weeks]
    GPU[Single GPU] --> Hours[Hours-Days]
    TPU[TPU Cluster] --> Minutes[Minutes-Hours]
    Distributed[Distributed] --> Fast[Minutes]
```

## Diagram 8: Inference Latency
```mermaid
graph LR
    Small[Small Model] --> RealTime[Real-time]
    Medium[Medium Model] --> NearReal[Near Real-time]
    Large[Large Model] --> Batch[Batch Processing]
```

## Diagram 9: Memory Requirements
```mermaid
graph LR
    Float32[FP32] --> 4x[4 bytes]
    Float16[FP16] --> 2x[2 bytes]
    Int8[Int8] --> 1x[1 byte]
    Quantized[Quantized] --> 0.25x[0.25 bytes]
```

## Diagram 10: Optimization Methods
```mermaid
graph TD
    SGD[SGD] --> Simple[Simple]
    Momentum[Momentum] --> Faster[Faster]
    Adam[Adam] --> Popular[Popular]
    AdamW[AdamW] --> Best[Best Generalization]
```
