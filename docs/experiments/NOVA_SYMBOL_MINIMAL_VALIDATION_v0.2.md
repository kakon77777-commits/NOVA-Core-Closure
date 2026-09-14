# NOVA Symbol-Minimal v0.2 Validation Note

- NSM2 magic and registry revision added.
- NSM1 backward decoding retained.
- Global semantic domains implemented with append-only numeric identities.
- Unknown atoms retain deterministic local-symbol fallback.
- Context-sensitive `kind` handling separates node operators, edge kinds and structural record kinds.
- v0.2 implementation does not change NOVA Core schema or semantic hash authority.
- Local package syntax and isolated codec harness are validated before GitHub synchronization.
- Full repository regression remains a repository-side/local-worktree gate because this execution environment cannot clone GitHub over the network.
