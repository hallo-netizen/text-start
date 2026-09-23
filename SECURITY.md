# Security

The default branch `main` is the immutable start door.

Required GitHub-side protection:
- updates to `main` restricted;
- deletions blocked;
- force-pushes blocked;
- no bypass actor for the ChatGPT GitHub connection.

The chat may request a start through an Issue only.
A valid current request is exactly:

`START:pferdeatelier`

`text-start` never binds a concrete batch, article count, source file or production command. It only authorizes the fixed project receiver. The receiver must resolve the current 1..N assignment at run time and fail closed on ambiguity or drift.

Unknown projects, changed target receivers, static batch bindings or free parameters must fail closed.

No article-content rules, quality rules, production logic, or publish authority live in this repository.
