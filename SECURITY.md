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

Unknown projects or changed commands must fail closed.

No article-content rules, quality rules, production logic, or publish authority live in this repository.
