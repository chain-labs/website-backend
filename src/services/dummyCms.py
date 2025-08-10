from typing import Any, Dict
# ------------------------------------------------------------------------------
# In-memory CMS "database"
# ------------------------------------------------------------------------------

_CASE_STUDIES: Dict[str, Dict[str, Any]] = {
    "case-1": {
        "id": "case-1",
        "title": "FinBank — Instant KYC with Zero-Knowledge Proofs",
        "shortDescription": (
            "KYC onboarding reduced from 48 hours to under 5 minutes using zero-knowledge proofs."
        ),
        "description": (
            "*Goal:* Reduce onboarding time from 48 h to <5 min.\n"
            "*Outcome:* 93% faster onboarding, no data leaks, SOC 2 Type II in 10 weeks.\n\n"
            "## Overview\n"
            "FinBank set out to eliminate the slow, error-prone KYC process that frustrated customers and overloaded compliance teams. "
            "The legacy flow required customers to upload sensitive documents and wait for human review across multiple vendors. "
            "Turnaround often stretched to 48 hours, with abandonment spiking at each handoff. The bank’s mandate was simple: "
            "achieve a **sub-5-minute** KYC decision without compromising security, auditability, or regulator trust.\n\n"
            "## What We Built\n"
            "We introduced a selective-disclosure identity architecture grounded in **zero-knowledge proofs (ZKPs)**. "
            "Instead of transmitting raw PII to FinBank, customers present cryptographic attestations—proofs that they *meet* specific policy thresholds "
            "(e.g., age > 18, residency in permitted jurisdictions, document validity within expiry), without revealing the actual data. "
            "Credential issuers (government, bank partners, and eKYC providers) sign attributes; the wallet software generates succinct proofs; "
            "FinBank verifies these proofs in milliseconds.\n\n"
            "### Key Capabilities\n"
            "- **Selective disclosure:** Only the facts required by policy are revealed—nothing more.\n"
            "- **Revocation & freshness:** Proofs embed revocation checks and time-bound validity, preventing replay or use of stale credentials.\n"
            "- **Policy as code:** KYC and AML rules are expressed declaratively. Risk changes can be deployed in minutes and instantly impact verification.\n"
            "- **Observable compliance:** Every verification emits tamper-evident logs, creating a granular audit trail that supports SOC 2 and internal audits.\n\n"
            "## Architecture Highlights\n"
            "- **Wallet + Attestors:** Users hold credentials issued by trusted attestors. We supported multiple issuance routes to avoid single-vendor lock-in.\n"
            "- **Verifier Service:** A stateless microservice validates proofs, enforces policy, and returns a decision token used by downstream systems.\n"
            "- **Risk Orchestrator:** High-risk signals (device anomalies, sanctions list updates) can escalate from ZK auto-pass to human review with clear reason codes.\n"
            "- **Privacy Posture:** No raw PII is persisted by FinBank during auto-pass flows; only non-identifying evidence and audit hashes are retained.\n\n"
            "## Rollout & Adoption\n"
            "We piloted with a 5% traffic slice, then ramped to 100% over three weeks. Customer support received a compact playbook explaining proof failures "
            "and fallback flows. Risk and compliance teams reviewed dashboards that trace every decision path without exposing customer data.\n\n"
            "## Outcomes\n"
            "- **Time to decision:** From ~48 hours to **under 5 minutes** for 87% of applicants; the remainder routes to assisted review due to risk flags or missing attestors.\n"
            "- **Security posture:** No raw PII leaves the user’s device in auto-pass flows; audit artifacts are hashed and integrity-checked.\n"
            "- **Regulatory alignment:** **SOC 2 Type II** achieved in **10 weeks**, aided by deterministic controls and audit-ready logs.\n"
            "- **Operational lift:** Manual reviews dropped by 68%, freeing analysts to focus on true investigations instead of form-checking.\n\n"
            "## Why It Worked\n"
            "By separating *proof of compliance* from *disclosure of data*, FinBank removed the main source of delay and risk. "
            "ZKPs provided mathematically verifiable assurances, policies became versioned code, and evidence collection stopped being synonymous with data collection. "
            "The bank now ships policy updates safely, measures their impact immediately, and maintains customer trust by keeping sensitive data local.\n\n"
            "## Next Steps\n"
            "- Expand issuer ecosystem to widen auto-pass coverage.\n"
            "- Integrate portable KYC tokens for partner fintechs to reduce re-verification.\n"
            "- Layer in privacy-preserving device reputation to cut synthetic identity attempts without invasive tracking.\n"
        ),
        "thumbnail": "https://via.placeholder.com/600x400?text=FinBank+KYC",
    },
    "case-2": {
        "id": "case-2",
        "title": "MediShare — HIPAA-Safe Analytics over 750 M Records",
        "shortDescription": (
            "HIPAA-compliant analytics on 750 million patient records without exposing raw data."
        ),
        "description": (
            "*Goal:* Enable analytics on PHI without exposing raw data.\n"
            "*Outcome:* Queries run on 750 M rows under 0.01 ε privacy budget; FDA audit passed.\n\n"
            "## Context\n"
            "MediShare operates a multi-institution data collaboration spanning EHR, claims, labs, imaging, and device telemetry. "
            "Researchers needed timely population-level insights (outcomes, safety signals, care pathway analysis), but the underlying **PHI** could not be centralized or "
            "exposed. Prior approaches either copied data into a secure enclave (creating operational bottlenecks) or stripped identifiers so aggressively that "
            "analyses lost fidelity.\n\n"
            "## Approach\n"
            "We implemented a federated analytics platform with **differential privacy (DP)** and query governance baked in. "
            "Data stays within each provider’s boundary; only **privacy-guaranteed aggregates** leave. Analysts submit standard SQL and statistical queries; "
            "a policy engine rewrites them into privacy-aware plans that compute locally, apply per-site noise, and combine results with secure aggregation.\n\n"
            "### Privacy & Governance\n"
            "- **ε-budgeting:** Each project receives a strict privacy budget (ε). The orchestrator tracks cumulative spend, blocks queries that would exceed limits, "
            "and suggests lower-sensitivity alternatives.\n"
            "- **Noise calibration:** Mechanisms (Laplace/Gaussian) are selected per query shape with sensitivity bounds derived from schema metadata and policy hints.\n"
            "- **K-anonymity guardrails:** For small cohorts, the system applies row suppression or generalization prior to DP, preventing singling-out even before noise.\n"
            "- **Provenance & audit:** Every query is hashed, signed, and logged with inputs, transformations, and ε usage, producing FDA/IRB-ready audit trails.\n\n"
            "## Architecture\n"
            "- **Local Executors:** Lightweight services run next to each data warehouse (Snowflake, BigQuery, Postgres). They push down filters/joins, compute safe "
            "aggregates, and emit only privacy-protected results.\n"
            "- **Coordinator:** Plans multi-site queries, harmonizes schemas, enforces budget, and merges noisy partials using secure aggregation so no site can infer "
            "another’s raw counts.\n"
            "- **Analyst Portal:** Researchers write familiar queries, preview sensitivity and estimated error, then run jobs with one click. Results include "
            "confidence intervals and data quality notes.\n\n"
            "## Results\n"
            "- **Scale:** Stable performance on **750 million rows** across 9 institutions; median query wall-time under 90 seconds for typical cohort analyses.\n"
            "- **Privacy:** Typical projects operated at **ε ≤ 0.01** per analysis window, with automatic throttling when budgets approached limits.\n"
            "- **Compliance:** External auditors validated HIPAA controls; an **FDA audit** of a device-safety study passed with no findings.\n"
            "- **Utility:** DP-aware visualizations helped analysts interpret confidence bounds instead of treating noisy counts as exact truths.\n\n"
            "## Why It Matters\n"
            "MediShare can now answer high-value questions—therapy effectiveness, care variation, early safety signals—without creating new honeypots of PHI or "
            "requiring bespoke data use agreements for every inquiry. Privacy isn’t a bolt-on; it’s the execution model. "
            "This shift unlocks collaboration at speed while keeping trust with patients and regulators.\n\n"
            "## What’s Next\n"
            "- Expand to time-series modeling (survival analysis, hazard ratios) with privacy-aware estimators.\n"
            "- Introduce synthetic cohorts for teaching and rapid prototyping, backed by fidelity reports and disclosure risk scores.\n"
            "- Automate schema drift handling so new codes and panels are absorbed without manual re-mapping.\n"
        ),
        "thumbnail": "https://via.placeholder.com/600x400?text=MediShare+Analytics",
    },
    "case-3": {
        "id": "case-3",
        "title": "CityGov — Transparent Grant Distribution",
        "shortDescription": (
            "Privacy-preserving grant program disbursed $45 million with zero disputes and full public transparency."
        ),
        "description": (
            "*Goal:* Publicly verifiable yet private beneficiary selection.\n"
            "*Outcome:* $45 M disbursed with zero disputes; 12 k weekly dashboard users.\n\n"
            "## Background\n"
            "CityGov planned a relief program to support small businesses and households. Prior rounds faced criticism: opaque scoring, unclear eligibility, and "
            "accusations of favoritism. The new mandate required two things that seem at odds: **strong privacy** for applicants and **strong transparency** for the public.\n\n"
            "## Design Principles\n"
            "- **Fairness without exposure:** Publish how decisions are made and prove they were followed—without exposing individuals’ sensitive data.\n"
            "- **End-to-end auditability:** Every step—from application intake to funds transfer—should be reconstructable with cryptographic evidence.\n"
            "- **Operational simplicity:** Civil-service teams must run the program without heavy specialist support.\n\n"
            "## Solution\n"
            "We introduced a **commit-and-prove** pipeline. Applicants submit data that is immediately hashed into a **Merkle tree**, producing a receipt for the "
            "applicant and a public commitment for observers. Eligibility and prioritization rules (income thresholds, business status, neighborhood criteria) are "
            "codified as machine-readable policies. A proving service generates **zero-knowledge proofs** that each selected recipient satisfies the rules **and** "
            "that the overall selection respects published constraints (budget caps, geographic quotas, tie-breakers) without revealing private fields.\n\n"
            "### Public Transparency Layer\n"
            "- A web dashboard publishes:\n"
            "  - The committed Merkle roots per intake window\n"
            "  - The canonical policy version used for scoring\n"
            "  - Batched ZK proofs attesting that allocations match policy and budget\n"
            "  - Aggregate, differentially private statistics (by neighborhood, sector) so citizens can see impact without re-identification risk\n"
            "- Anyone can independently verify proofs with a lightweight verifier. Community groups ran their own checks and posted validations.\n\n"
            "## Operations\n"
            "Intake ran weekly. After each window closed, the selection engine produced a ranked list with proof artifacts. Payments executed only if verification "
            "passed. Appeals were simplified: an applicant could see exactly **which policy clause** led to their outcome (eligible/ineligible) without exposing raw fields.\n\n"
            "## Outcomes\n"
            "- **$45 million** disbursed across two quarters with **zero disputes** escalating beyond the first tier.\n"
            "- **12,000** weekly dashboard users on average; several local universities contributed independent audits.\n"
            "- The city council reported markedly improved public trust scores in post-program surveys.\n\n"
            "## Why It Worked\n"
            "By separating public accountability (did the city follow its own rules and budget?) from private information (what is a household’s income?), "
            "CityGov achieved both transparency and dignity. The program demonstrated that cryptographic verification can be civic-grade: understandable to "
            "non-experts, resilient to tampering, and inexpensive to operate.\n\n"
            "## Next Steps\n"
            "- Expand to recurring benefits with portable eligibility proofs to reduce re-application burden.\n"
            "- Open-source the policy and proof templates so other municipalities can adapt them quickly.\n"
            "- Add participatory budgeting modules to let residents simulate allocations under alternative priorities—still privacy-preserving.\n"
        ),
        "thumbnail": "https://via.placeholder.com/600x400?text=CityGov+Grants",
    },
}