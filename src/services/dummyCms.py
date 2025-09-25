from typing import Any, Dict
# ------------------------------------------------------------------------------
# In-memory CMS "database"
# ------------------------------------------------------------------------------

_CASE_STUDIES: Dict[str, Dict[str, Any]] = {
    "p1": {
        "id": "p1",
        "title": "HFT Bot for Market Making and Arbitrage with Millisecond Latency",
        "shortDescription": "(Modular HFT stack using WebSockets, NATS, and Python/TS for market making and arbitrage at sub-millisecond paths.)",
        "description": (
            "## Goal\n"
            "Reduce decision and execution latency for market making and arbitrage while preserving full auditability and safe risk limits.\n\n"
            "## Role\n"
            "Lead Backend Engineer and Blockchain Engineer.\n\n"
            "## Overview\n"
            "Built a modular HFT system with real-time ingestion, parallel persistence for research/backtests, and a low-latency execution layer. "
            "The design separates ingest, analytics, and execution with message-bus isolation to keep paths short and observable.\n\n"
            "## What We Built\n"
            "- **Real-time ingest:** Multi-venue order book and trades via WebSockets with gap detection and replay.\n"
            "- **Parallel storage:** Tick and derived features written to a time-series store for backtests while live strategies read from in-memory caches.\n"
            "- **Strategy engine:** Python/TypeScript strategies including **GARCH + Monte Carlo** for short-horizon volatility and spread selection.\n"
            "- **Execution router:** Atomic order submission, internal netting, and position management with cancellation storms handling.\n"
            "- **Messaging fabric:** **NATS** for nanosecond-scale pub/sub, backpressure, and at-least-once delivery semantics.\n"
            "- **Risk and limits:** Per-venue throttles, exposure caps, and kill-switch topics.\n\n"
            "## Architecture\n"
            "- **Ingestors → Normalizers → Feature builders → Strategy workers → Execution router → Exchange adapters.**\n"
            "- Redis and in-proc caches for hot books; columnar DB for research.\n"
            "- Deterministic logs and **full audit trail** across topics.\n\n"
            "## Key Capabilities\n"
            "- Sub-ms fanout inside the bus; micro-batch feature updates; async I/O for network jitter tolerance.\n"
            "- Warm-start backtests using live schemas; identical code paths for sim and prod.\n\n"
            "## Outcomes\n"
            "- Stable market-making loops under volatile bursts; safe unwind under risk triggers; reproducible research from live mirrors.\n\n"
            "## Why It Worked\n"
            "Tight separation of concerns, immutable event logs, and a transport designed for latency kept the critical path minimal without sacrificing observability.\n\n"
            "## Next Steps\n"
            "- Add venue-agnostic smart order routing and latency arbitration.\n"
            "- Extend Monte Carlo to regime-switching models.\n"
            "- Hardware timestamping and kernel-bypass trials.\n"
        ),
        "thumbnail": "https://via.placeholder.com/600x400?text=HFT+Bot"
    },
    "p2": {
        "id": "p2",
        "title": "Intelligent Consciousness Interface (ICI) Core for Sidetrip AI",
        "shortDescription": "(Python framework that links personal data to LLM agents with LangChain, RAG, and graph indexing.)",
        "description": (
            "## Goal\n"
            "Let developers build secure, extensible agents that reason over user data with strong retrieval guarantees.\n\n"
            "## Role\n"
            "Founding Engineer.\n\n"
            "## Overview\n"
            "**ICI Core** is a Python framework that unifies personal data sources, vector search, and LLM toolchains. "
            "It abstracts ingestion, indexing, retrieval, and prompting so teams can focus on agent logic.\n\n"
            "## What We Built\n"
            "- **RAG pipelines:** Chunking, embeddings, and retrieval over **Chroma** with hybrid keyword + vector routing.\n"
            "- **Graph indexing:** Entity and relationship extraction to improve context selection and reduce hallucinations.\n"
            "- **Multi-LLM support:** OpenAI, Anthropic, and others behind a consistent interface.\n"
            "- **Policy and security:** Scoped data access, redaction, and attribution in agent responses.\n\n"
            "## Architecture\n"
            "- Ingest → Normalize → Embed/Index → Graph linker → Retriever → Prompt composer → LLM → Tools.\n"
            "- Caches for embeddings and prompt templates; observability hooks for retrieval traces.\n\n"
            "## Key Capabilities\n"
            "- Context windows built from vector and graph signals.\n"
            "- Tool calling with guardrails and per-tenant isolation.\n\n"
            "## Outcomes\n"
            "- Higher answer precision on user-specific queries and faster iteration on agent skills.\n\n"
            "## Resources\n"
            "- github.com/sidetrip-ai/ici-core\n"
            "- sidetrip.ai\n\n"
            "## Next Steps\n"
            "- Add online learning from feedback.\n"
            "- Expand connectors and upgrade to streaming rerankers.\n"
        ),
        "thumbnail": "https://via.placeholder.com/600x400?text=Sidetrip+ICI+Core"
    },
    "p3": {
        "id": "p3",
        "title": "Supermigrate — One-Click ERC-20 Migration to the Superchain",
        "shortDescription": "(800M+ USD tokens migrated; Base grant; seamless mainnet→OP Stack migrations.)",
        "description": (
            "## Goal\n"
            "Enable token teams to migrate ERC-20 liquidity and holder base from Ethereum mainnet to Optimism-aligned chains with minimal friction.\n\n"
            "## Role\n"
            "Solidity Smart Contracts, System Design.\n\n"
            "## Overview\n"
            "Designed a **one-click migration** flow that preserves supply integrity, emits transparent proofs, and minimizes user steps.\n\n"
            "## What We Built\n"
            "- **Lock-and-mint bridge logic** with replay protection and event finality checks.\n"
            "- Batch migration for large holder sets.\n"
            "- Clear receipts and explorer-friendly events.\n\n"
            "## Outcomes\n"
            "- **$800M+** equivalent tokens migrated (aggregate reported by teams).\n"
            "- Grant support from **Base**.\n\n"
            "## Resources\n"
            "- supermigrate.xyz\n"
            "- https://x.com/jessepollak/status/1775188959200674294\n\n"
            "## Next Steps\n"
            "- Add cross-chain governance hooks and liquidity incentives.\n"
        ),
        "thumbnail": "https://via.placeholder.com/600x400?text=Supermigrate"
    },
    "p4": {
        "id": "p4",
        "title": "Bipzy — Pre-Token Launchpad, NFT Staking, and Migration",
        "shortDescription": "(80+ ETH raised in 10 minutes; audit fixes, NFT staking with multipliers, subgraph, dApp.)",
        "description": (
            "## Goal\n"
            "Ship a reliable pre-token launch and loyalty stack with NFT staking and migration paths.\n\n"
            "## Role\n"
            "Smart Contract Engineer, Web3 Frontend Engineer.\n\n"
            "## Overview\n"
            "Hardened pool contracts, built **NFT staking with multipliers**, and delivered a subgraph and front-end.\n\n"
            "## What We Built\n"
            "- Audit remediations for pool logic.\n"
            "- ERC-721 staking with reward multipliers and checkpointing.\n"
            "- The Graph subgraph for fast UI queries.\n"
            "- Next.js + Ethers.js dApp.\n\n"
            "## Outcomes\n"
            "- **80+ ETH** in first **10 minutes**.\n"
            "- Cleaner ops and on-chain transparency.\n\n"
            "## Resource\n"
            "- bipzy.com\n\n"
            "## Next Steps\n"
            "- On-chain reward schedules and progressive multipliers.\n"
        ),
        "thumbnail": "https://via.placeholder.com/600x400?text=Bipzy"
    },
    "p5": {
        "id": "p5",
        "title": "Antigravity — End-to-End Web3 Product",
        "shortDescription": "(Raised $300k pre-sale; full stack build across UX, contracts, frontend, animations, backend.)",
        "description": (
            "## Goal\n"
            "Deliver a cohesive token pre-sale experience and foundation for a long-running product.\n\n"
            "## Role\n"
            "Solidity, Next.js Frontend, Framer Motion, Backend, Viem, Wagmi.\n\n"
            "## Overview\n"
            "Owned UX/UI, tokenomics implementation, smart contracts, animated front-end, and backend services supporting a successful pre-sale.\n\n"
            "## What We Built\n"
            "- Token sale contracts and vesting.\n"
            "- Next.js app with **Framer Motion** animations; Viem/Wagmi wallet UX.\n"
            "- Backend services for metrics and verification.\n\n"
            "## Outcomes\n"
            "- **$300k** raised in pre-sale with strong conversion.\n\n"
            "## Resources\n"
            "- agproject.io\n"
            "- Antigravity Home Page / Video walkthrough\n\n"
            "## Next Steps\n"
            "- Post-sale governance and staking modules; audit and mainnet scale-up.\n"
        ),
        "thumbnail": "https://via.placeholder.com/600x400?text=Antigravity"
    },
    "p6": {
        "id": "p6",
        "title": "Prime Launch — DEX Launchpad with Governance Controls",
        "shortDescription": "(Balancer LBP integration, delegate governance on Gnosis Safe, and lazy deploy. $20M+ launches supported.)",
        "description": (
            "## Goal\n"
            "Provide fair token launch mechanics with transparent governance and safer deploys.\n\n"
            "## Role\n"
            "Smart Contracts, TypeScript/Node, Security & Governance Design.\n\n"
            "## Overview\n"
            "Integrated **Balancer LBP** with curated access and **delegate-based governance**. "
            "Added a **lazy deploy** flow that requires governance approval before any on-chain deployment.\n\n"
            "## What We Built\n"
            "- LBP adapters and orchestration.\n"
            "- Gnosis Safe + delegate framework for approvals.\n"
            "- Node/TS services for queueing and attestations.\n\n"
            "## Outcomes\n"
            "- Supported launches totaling **$20M+**.\n"
            "- Reduced misconfig risk and improved fairness.\n\n"
            "## Resource\n"
            "- launch.prime.xyz\n\n"
            "## Next Steps\n"
            "- Add real-time risk checks and MEV-aware parameters at launch.\n"
        ),
        "thumbnail": "https://via.placeholder.com/600x400?text=Prime+Launch"
    },
    "p7": {
        "id": "p7",
        "title": "Wagr.gg — Competitive Gaming Solidity Infrastructure",
        "shortDescription": "(Trustless rails for matches, ~40% gas savings on sigs, subgraph for fast UI; 6-figure pre-seed.)",
        "description": (
            "## Goal\n"
            "Enable transparent peer competitions with programmable payouts and minimal gas.\n\n"
            "## Role\n"
            "Core Solidity & Research; Blockchain Strategist.\n\n"
            "## Overview\n"
            "Designed settlement rails, multi-party distribution, and signature schemes that cut costs while keeping security.\n\n"
            "## What We Built\n"
            "- Escrow and conditional payouts with dispute paths.\n"
            "- **Gas-efficient crypto signatures (~40% savings).**\n"
            "- The Graph subgraph for match views.\n\n"
            "## Outcomes\n"
            "- **Six-figure pre-seed**, creator/influencer adoption, and faster UX.\n\n"
            "## Resource\n"
            "- wagr.gg\n\n"
            "## Next Steps\n"
            "- Cross-chain payouts and anti-collusion telemetry.\n"
        ),
        "thumbnail": "https://via.placeholder.com/600x400?text=Wagr"
    },
    "p8": {
        "id": "p8",
        "title": "Toucan Earth — Cross-Chain Carbon Token Bridge",
        "shortDescription": "(Hyperlane bridge Celo↔Polygon with AMP; >$2M volume; security-first design.)",
        "description": (
            "## Goal\n"
            "Expand Carbon token reach with safe cross-chain transfers and messaging.\n\n"
            "## Role\n"
            "Lead ERC-20 Cross-chain Researcher & Engineer.\n\n"
            "## Overview\n"
            "Built **Hyperlane-based** arbitrary message passing for token actions between **Celo** and **Polygon** with strict verification and replay protections.\n\n"
            "## What We Built\n"
            "- Bridge contracts and relayer flows.\n"
            "- Unit tests and monitoring for message finality.\n\n"
            "## Outcomes\n"
            "- **>$2M** cross-chain volume and active users.\n\n"
            "## Resource\n"
            "- app.toucan.earth\n\n"
            "## Next Steps\n"
            "- Upgrade to v3 bridge and add rate limits and fraud proofs.\n"
        ),
        "thumbnail": "https://via.placeholder.com/600x400?text=Toucan+Earth"
    },
    "p9": {
        "id": "p9",
        "title": "SdVVVorks — Web3 Loyalty with Account Abstraction",
        "shortDescription": "(Membership, rewards, purchases, governance; Privy, Biconomy, Stripe, Hypersub; AA UX.)",
        "description": (
            "## Goal\n"
            "Create a unified fan membership and commerce platform with smooth wallets and governance.\n\n"
            "## Role\n"
            "Solidity; Backend; Project & Product Management.\n\n"
            "## Overview\n"
            "Built a loyalty system with NFT/points, AA wallets, fiat on-ramps, and governance actions.\n\n"
            "## What We Built\n"
            "- ERC-721/1155 memberships and reward logic.\n"
            "- **Account abstraction** via Biconomy for gasless UX.\n"
            "- Privy auth, Stripe/Hypersub payments, and admin backoffice.\n\n"
            "## Outcomes\n"
            "- Higher conversion from non-crypto users and recurring revenue via subs.\n\n"
            "## Resource\n"
            "- sdvvvorks.io\n\n"
            "## Next Steps\n"
            "- Tiered perks and on-chain voting with snapshotting.\n"
        ),
        "thumbnail": "https://via.placeholder.com/600x400?text=SdVVVorks"
    },
    "p10": {
        "id": "p10",
        "title": "Launchbox — Pump.fun-Style Token Mechanism on Base",
        "shortDescription": "(Uniswap V2 pricing/exchange layer; Base grant; launch pending.)",
        "description": (
            "## Goal\n"
            "Let creators launch memecoins with predictable curves and sane guardrails on **Base**.\n\n"
            "## Role\n"
            "Solidity Smart Contract.\n\n"
            "## Overview\n"
            "Forked core mechanics with adjustments for **Uniswap V2** liquidity, anti-abuse rules, and creator flows.\n\n"
            "## What We Built\n"
            "- Bonding/curve logic with LP mint/burn steps.\n"
            "- Admin controls for freezes and finalization.\n\n"
            "## Outcomes\n"
            "- **Grant from Base**; mainnet launch pending.\n\n"
            "## Resource\n"
            "- launchbox-interface.vercel.app\n\n"
            "## Next Steps\n"
            "- Add fee-splitter, anti-MEV protections, and audited release.\n"
        ),
        "thumbnail": "https://via.placeholder.com/600x400?text=Launchbox+on+Base"
    },
    "p11": {
        "id": "p11",
        "title": "Lit Protocol — Lit Privacy SDK",
        "shortDescription": "(Pragmatic privacy toolkit for on-chain governance and workflows. Alternative to bespoke ZK.)",
        "description": (
            "## Goal\n"
            "Ship privacy for on-chain actions without building a custom ZK stack.\n\n"
            "## Overview\n"
            "**Lit Privacy SDK** enables policy-gated decryption and private condition checks so DAO and app workflows can keep sensitive data off-chain while proving rights on-chain.\n\n"
            "## What We Built\n"
            "- SDK flows for key management, policy evaluation, and gated execution.\n"
            "- Samples for ERC-20/721/1155 contexts.\n\n"
            "## Outcomes\n"
            "- Faster privacy deployments and simpler audits.\n\n"
            "## Resource\n"
            "- spark.litprotocol.com/enabling-private-on-chain-txns/\n\n"
            "## Next Steps\n"
            "- Compose with ZK attestations for hybrid privacy.\n"
        ),
        "thumbnail": "https://via.placeholder.com/600x400?text=Lit+Privacy+SDK"
    },
    "p12": {
        "id": "p12",
        "title": "Primobots — 3D NFT Collection",
        "shortDescription": "(ERC721A drop with +12% gas optimization; >$150k sales; full mint in 2 days including migration.)",
        "description": (
            "## Goal\n"
            "Launch a 3D avatar collection with low gas, strong UX, and safe migration.\n\n"
            "## Role\n"
            "Core Solidity & Frontend (Next.js, Ethers).\n\n"
            "## Overview\n"
            "Delivered **ERC721A** contracts, front-end mint, internal audits with **100% BDD coverage**, and a seamless migration path.\n\n"
            "## What We Built\n"
            "- Gas-optimized minting (**~12% better than baseline**).\n"
            "- Allowlists, reveals, and provenance anchors.\n"
            "- Next.js mint UI with Ethers.js and wallet checks.\n\n"
            "## Outcomes\n"
            "- **>$150k** sales; **full mint in 2 days** including migration.\n\n"
            "## Contracts\n"
            "- Main: `0x86EBD2Ba0f0e34cEa74F5aa8dC2c6Ed3dD9b017e`\n"
            "- Migration: `0xe7ef0280c3207d68f8f0d63263075cd9bfc162a6`\n\n"
            "## Resource\n"
            "- primobots.io\n\n"
            "## Next Steps\n"
            "- Trait staking and cross-collection utility.\n"
        ),
        "thumbnail": "https://via.placeholder.com/600x400?text=Primobots+NFT"
    }
}
