# Round 09 — G3 Verifiable Memory & Resource Planning Final Seal

Round 09 introduces the first explicit NOVA resource-planning layer without changing canonical Graph semantics.

The implemented chain is:

$$
\boxed{
G
\rightarrow
\text{ResourceAnalysis}
\rightarrow
\text{MemoryPlan Candidate}
\rightarrow
\text{Independent Verifier}
\rightarrow
\text{Selection / Conservative Fallback}
}
$$

Implemented capabilities:

- deterministic node scheduling for resource analysis;
- explicit ownership states;
- first/last-use lifetime analysis;
- concrete tensor byte accounting;
- symbolic-size runtime obligations;
- static physical buffer-pool planning;
- conservative unique-buffer mode;
- verified lifetime-based buffer reuse;
- explicit device-transfer records;
- deterministic MemoryPlan hashing/codec;
- independent plan verification;
- `safe / conditionally_safe / unsafe` status;
- conservative fallback for unsafe external/AI candidates;
- Python API and JSON CLI for planning, verification, and selection.

The first implementation deliberately does not make a native allocator or GPU runtime. `MemoryPlan` is a compiler/runtime planning artifact and safety certificate input, not an unchecked allocator command.

## G3 seal

The static example reserves 48 bytes conservatively and 32 bytes after proven-safe buffer reuse. A malicious overlapping alias plan, a missing transfer plan, and forged peak accounting are all independently rejected. Symbolic sizes remain explicit runtime obligations.

Therefore:

$$
\boxed{G3\;\text{SEALED}}
$$

Round 10 proceeds to G4: Nova-A AI-native GraphPatch construction over the already verified structural core.
