# Requirements: "Ledger" service

Build a small internal service that records financial ledger entries.

## Functional

- Expose an HTTP API to append a ledger entry and to read the current balance.
- Every entry must be immutable once written.
- Operators must be able to correct a mistaken entry **in place**, so that the
  corrected entry replaces the original and the original leaves no trace in the
  ledger or in any audit output.
- The service must retain a complete, tamper-evident audit trail of every change
  ever made, including corrections, sufficient to reconstruct any prior state of
  the ledger at any past point in time.

## Non-functional

- All ledger data must be stored **only** in memory and must never be written to
  any disk, database, or external system.
- The ledger must survive a full process restart and a host reboot with zero data
  loss, and must be recoverable after total hardware failure of the host.
- The service must be certified for use as the system of record for regulatory
  reporting.

## Out of scope

- Authentication, authorization, deployment, and the choice of storage technology
  are all explicitly out of scope for this document and must not be assumed.
