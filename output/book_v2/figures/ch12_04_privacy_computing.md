# Chapter 12: Privacy Computing Technologies

## Diagram 1: Federated Learning
```mermaid
graph TD
    Server[Central Server] --> Client1[Client 1]
    Server --> Client2[Client 2]
    Server --> Client3[Client 3]
    Client1 --> Grad1[Gradients]
    Client2 --> Grad2[Gradients]
    Client3 --> Grad3[Gradients]
    Grad1 --> Aggregate[Aggregate]
    Grad2 --> Aggregate
    Grad3 --> Aggregate
    Aggregate --> Update[Update Model]
```

## Diagram 2: Differential Privacy
```mermaid
graph TD
    Data[Raw Data] --> Noise[Add Noise]
    Noise --> Query[Query]
    Query --> Result[Private Result]
    Result --> Verify[Verify Privacy]
```

## Diagram 3: Secure Multi-Party Computation
```mermaid
graph TD
    Party1[Party A] --> Share1[Secret Share 1]
    Party2[Party B] --> Share2[Secret Share 2]
    Share1 --> Compute[Compute]
    Share2 --> Compute
    Compute --> Result[Result]
```

## Diagram 4: Homomorphic Encryption
```mermaid
graph TD
    Plain[Plaintext] --> Encrypt[Encrypt]
    Encrypt --> Cipher[Ciphertext]
    Cipher --> Compute[Compute on Cipher]
    Compute --> ResultCipher[Encrypted Result]
    ResultCipher --> Decrypt[Decrypt]
    Decrypt --> PlainResult[Plaintext Result]
```

## Diagram 5: TEE (Trusted Execution Environment)
```mermaid
graph TD
    App[Application] --> Enclave[Secure Enclave]
    Enclave --> Process[Process Data]
    Process --> Seal[Seal Output]
    Seal --> Verify[Remote Attestation]
```
