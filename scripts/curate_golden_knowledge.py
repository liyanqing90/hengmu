#!/usr/bin/env python3
"""Curate the small, high-signal architecture knowledge set.

The broad catalog is useful for recall.  These entries are intentionally deeper:
they name concrete options, operating boundaries, failure semantics, exit paths,
and the claim-to-source mapping required by the golden-entry quality contract.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

ROOT = Path(__file__).resolve().parent.parent
KNOWLEDGE = ROOT / "resources" / "knowledge"
REVIEW_DATE = "2026-07-28"


def source(
    title: str,
    url: str,
    authority: str,
    *claims: str,
) -> dict[str, Any]:
    return {
        "title": title,
        "url": url,
        "authority": authority,
        "supports": list(claims),
    }


DECISIONS: dict[str, dict[str, Any]] = {
    "data-loading-and-refresh": {
        "title": "Data Loading and Refresh",
        "problem": (
            "Choose when a client obtains data, what may be reused, and how freshness "
            "is restored without hiding stale or contradictory state from the user."
        ),
        "mechanism": (
            "Separate initial load, revalidation, and mutation. Give every cached result "
            "a freshness rule and an owner; cancel or supersede obsolete requests, and "
            "merge a response only when its resource key and request generation still match."
        ),
        "options": [
            (
                "Load on demand",
                "Cold or infrequent views where latency is acceptable.",
                "Navigation must feel instant or the data is predictably needed.",
                "Visible loading latency and repeated origin work.",
                "Request waterfalls or empty states become the normal experience.",
            ),
            (
                "Prefetch then revalidate",
                "Likely navigation and bounded, cacheable read models.",
                "Data is sensitive, expensive, or unlikely to be consumed.",
                "Extra bandwidth, cache bookkeeping, and possible unused work.",
                "Unbounded prefetch amplifies load and returns stale snapshots.",
            ),
            (
                "Push invalidation plus pull refresh",
                "Active clients need fast awareness but the server remains authoritative.",
                "Clients cannot maintain subscriptions or tolerate reconnect logic.",
                "Subscription infrastructure and replay/version semantics.",
                "Missed invalidations leave a client stale unless reconnect triggers a full check.",
            ),
        ],
        "required": "Stable resource keys, freshness budgets, cancellation, version-aware merge rules, loading/error UI, and request/cache telemetry.",
        "benefits": "Makes perceived latency and staleness explicit while preventing late responses from overwriting newer client state.",
        "costs": "More client states and network policy must be tested; prefetch and revalidation can increase origin traffic.",
        "failures": "Race between navigations, cache keys omitting tenant or authorization scope, retry storms, and background refresh silently replacing user edits.",
        "migration": "Instrument the current load path, introduce one resource-keyed loader, add revalidation to a single high-value view, and retain a forced-refresh escape hatch until stale-rate and origin-load targets hold.",
        "evidence": "Navigation traces, request waterfalls, cache hit/stale rates, resource-key construction, abort handling, authorization scope, and tests for out-of-order responses.",
        "changes": "Prefer on-demand loading when prefetch hit rate is low; prefer push invalidation only when measured freshness targets cannot be met by bounded revalidation.",
        "tradeoffs": "Prefetch improves latency at bandwidth cost; revalidation improves freshness at origin-load cost; push improves timeliness at connection and recovery cost.",
        "claims": {
            "LOAD-BOUNDARY": "Initial loading, reuse, and revalidation are separate lifecycle decisions.",
            "CACHE-FRESHNESS": "HTTP caches require explicit freshness and validation semantics.",
        },
        "sources": [
            source(
                "MDN HTTP caching",
                "https://developer.mozilla.org/en-US/docs/Web/HTTP/Caching",
                "official",
                "CACHE-FRESHNESS",
            ),
            source(
                "MDN Fetch API",
                "https://developer.mozilla.org/en-US/docs/Web/API/Fetch_API",
                "official",
                "LOAD-BOUNDARY",
            ),
        ],
        "related": [
            "decision.cache-strategy",
            "decision.optimistic-vs-pessimistic-update",
        ],
    },
    "cache-strategy": {
        "title": "Cache Strategy",
        "problem": "Reduce repeated computation or origin reads without treating a cache as an unowned second source of truth.",
        "mechanism": "Define the authoritative store first, then choose cache placement, key scope, population, invalidation, TTL, and stampede control for each read model. A cache miss must preserve correctness.",
        "options": [
            (
                "Cache-aside",
                "Read-heavy data with tolerable bounded staleness.",
                "A miss cannot safely load from the authority.",
                "Application-owned invalidation and duplicate cache logic.",
                "Write races or external writers serve stale values until expiry.",
            ),
            (
                "Read/write-through",
                "A cache product can mediate all relevant reads or writes.",
                "Some writers bypass the cache or product semantics are unclear.",
                "Vendor coupling and a larger critical data path.",
                "Partial cache/store failure obscures which write committed.",
            ),
            (
                "Precomputed read model",
                "Queries are expensive and can consume an explicitly lagging projection.",
                "Strong read-after-write consistency is mandatory.",
                "Projection storage, rebuilds, and lag monitoring.",
                "A broken projector returns plausible but incomplete results.",
            ),
        ],
        "required": "Authority declaration, tenant- and permission-safe keys, TTL or version invalidation, stampede suppression, capacity policy, hit/stale metrics, and a bypass path.",
        "benefits": "Can lower latency and origin load while keeping staleness and consistency observable.",
        "costs": "Consumes memory and operational attention; every invalidation path adds a consistency obligation.",
        "failures": "Cache penetration, thundering herds, hot keys, cross-tenant leakage, unbounded cardinality, and treating a cache outage as an authority outage.",
        "migration": "Measure the uncached baseline, cache one idempotent read behind a flag, validate key isolation and stale bounds, then expand only while hit rate and origin relief justify the memory and complexity.",
        "evidence": "Query latency distribution, repetition and cardinality, key construction, write paths, invalidation traces, eviction behavior, cache-outage tests, and authorization boundaries.",
        "changes": "Do not cache when reuse is low, correctness requires current authority reads, or sensitive values cannot be safely partitioned; choose a projection when computation rather than retrieval dominates.",
        "tradeoffs": "Latency and origin protection trade against freshness, memory, failure modes, and operational coupling.",
        "claims": {
            "CACHE-ASIDE": "Cache-aside loads on misses and requires an explicit consistency strategy.",
            "CACHE-SAFETY": "Sensitive or low-hit data can make caching inappropriate.",
        },
        "sources": [
            source(
                "Azure Cache-Aside pattern",
                "https://learn.microsoft.com/en-us/azure/architecture/patterns/cache-aside",
                "official",
                "CACHE-ASIDE",
                "CACHE-SAFETY",
            ),
        ],
        "related": ["pattern.materialized-view", "decision.data-loading-and-refresh"],
    },
    "polling-vs-sse-vs-websocket": {
        "title": "Polling vs SSE vs WebSocket",
        "problem": "Select an update channel from direction, freshness, connection count, recovery, proxy behavior, and interaction semantics.",
        "mechanism": "Keep the durable state behind a normal resource contract. The live channel carries versions or event IDs; reconnect either resumes from a cursor or performs a full resource refresh.",
        "options": [
            (
                "Bounded polling",
                "Updates are infrequent and seconds-to-minutes freshness is enough.",
                "Request volume or freshness makes repeated empty responses unaffordable.",
                "Repeated requests and synchronized-client spikes.",
                "Fixed intervals overload the origin or miss required freshness.",
            ),
            (
                "Server-Sent Events",
                "Browser clients need ordered, server-to-client text events over HTTP.",
                "Binary data or client-to-server streaming is central.",
                "Long-lived connections, heartbeat, cursor, and proxy tuning.",
                "Reconnect without a replay cursor loses updates or duplicates side effects.",
            ),
            (
                "WebSocket",
                "Low-latency bidirectional messages are a product requirement.",
                "Ordinary HTTP requests or one-way push satisfy the flow.",
                "Connection state, backpressure, authentication refresh, and fleet fan-out.",
                "Slow consumers exhaust buffers or connection routing loses session state.",
            ),
        ],
        "required": "Measured freshness, connection budget, authentication renewal, heartbeat, backoff with jitter, replay or resync, backpressure, and connection/event metrics.",
        "benefits": "Matches transport complexity to the actual direction and latency requirement rather than to a vague real-time label.",
        "costs": "Moving from polling to a persistent channel adds stateful operations and recovery behavior.",
        "failures": "Reconnect storms, missed cursors, duplicate event application, proxy idle timeouts, slow consumers, and authorization changes not reaching an open connection.",
        "migration": "Start with bounded polling and ETags when sufficient; add SSE for one-way freshness or WebSocket for proven two-way needs, keeping a full-refresh endpoint as the recovery authority.",
        "evidence": "Update frequency, tolerated staleness, concurrent-client forecast, message direction and size, proxy/load-balancer limits, reconnect traces, and event idempotency tests.",
        "changes": "A one-way flow favors SSE over WebSocket; low change frequency favors polling; binary or interactive bidirectional traffic can justify WebSocket.",
        "tradeoffs": "Lower latency costs persistent connections, recovery machinery, and more complex capacity planning.",
        "claims": {
            "SSE-DIRECTION": "SSE provides server-to-client event delivery through EventSource.",
            "WS-DUPLEX": "WebSocket provides a two-way interactive session.",
        },
        "sources": [
            source(
                "MDN Server-sent events",
                "https://developer.mozilla.org/en-US/docs/Web/API/Server-sent_events",
                "official",
                "SSE-DIRECTION",
            ),
            source(
                "MDN WebSocket API",
                "https://developer.mozilla.org/en-US/docs/Web/API/WebSockets_API",
                "official",
                "WS-DUPLEX",
            ),
        ],
        "related": [
            "decision.data-loading-and-refresh",
            "decision.message-system-selection",
        ],
    },
    "sync-vs-async": {
        "title": "Synchronous vs Asynchronous Interaction",
        "problem": "Choose whether the caller waits for completion or hands work to a durable boundary with later status.",
        "mechanism": "Synchronous calls bind caller latency and availability to the callee. Asynchronous calls acknowledge durable acceptance, carry an idempotency key and correlation ID, and expose completion or failure independently.",
        "options": [
            (
                "Synchronous request-reply",
                "Fast bounded work where the caller needs the result to continue.",
                "Latency is long or the dependency frequently fails independently.",
                "Tight latency and availability coupling.",
                "Timeouts trigger duplicate work or cascading resource exhaustion.",
            ),
            (
                "Asynchronous command with status",
                "Work is long-running, bursty, retryable, or independently scalable.",
                "The caller requires immediate atomic completion.",
                "Queue, status model, idempotency, retries, and operator tooling.",
                "Accepted work is lost, stuck, duplicated, or never reaches a terminal state.",
            ),
        ],
        "required": "Latency budget, timeout and cancellation semantics, durable acceptance for async work, idempotency, bounded retries, dead-letter handling, correlation, and terminal status.",
        "benefits": "Makes coupling and overload behavior deliberate and lets long-running work scale independently.",
        "costs": "Async interaction adds state machines and eventual outcomes; sync interaction consumes caller capacity during waits.",
        "failures": "Retry amplification, orphan jobs, poison messages, invisible partial completion, and using language-level async while retaining distributed synchronous coupling.",
        "migration": "Measure tail latency and timeout retries, introduce an operation resource returning HTTP 202 for one long path, dual-observe results, then retire the synchronous completion contract after consumers migrate.",
        "evidence": "p95/p99 duration, timeout rate, retry behavior, job durability, queue age, idempotency store, cancellation needs, and consumer expectations.",
        "changes": "Keep synchronous behavior when completion is reliably within budget and required by the next step; choose async when durability and load leveling matter more than immediate completion.",
        "tradeoffs": "Synchronous flows are simpler to reason about but couple failures; asynchronous flows isolate and buffer at the cost of state and delayed feedback.",
        "claims": {
            "ASYNC-ACCEPT": "Long-running HTTP work can acknowledge acceptance and expose a status resource.",
            "ASYNC-COMPLEXITY": "Decoupling request and response adds completion and failure coordination.",
        },
        "sources": [
            source(
                "Azure Asynchronous Request-Reply pattern",
                "https://learn.microsoft.com/en-us/azure/architecture/patterns/asynchronous-request-reply",
                "official",
                "ASYNC-ACCEPT",
                "ASYNC-COMPLEXITY",
            ),
        ],
        "related": ["decision.request-vs-background-job", "style.durable-workflow"],
    },
    "request-vs-background-job": {
        "title": "Request Handler vs Background Job",
        "problem": "Place work in the interactive request path or in a separately owned worker without creating hidden fire-and-forget behavior.",
        "mechanism": "A request handler validates and performs only bounded work needed for the response. A background job begins after a durable handoff, has a lease or message, records attempts, and reaches a visible terminal state.",
        "options": [
            (
                "Inline request work",
                "Short, bounded operations whose result defines the response.",
                "CPU, I/O, or external dependencies exceed the request budget.",
                "Consumes request concurrency and couples failures.",
                "Timeouts leave unknown completion and retries duplicate effects.",
            ),
            (
                "Durable background job",
                "Long, bursty, scheduled, or independently retryable work.",
                "No durable queue/status owner exists or immediate completion is required.",
                "Worker fleet, queue, idempotency, retries, status, and support runbooks.",
                "Jobs disappear, poison messages loop, or leases cause concurrent execution.",
            ),
        ],
        "required": "Explicit acceptance boundary, idempotency key, durable payload or reference, attempt limits, lease/visibility timeout, dead-letter path, progress/status, and cancellation policy.",
        "benefits": "Protects interactive latency and permits job-specific scaling and recovery.",
        "costs": "Introduces operational state, delayed outcomes, and coordination between API and worker.",
        "failures": "In-process background threads die on deploy, job payloads become incompatible, retry repeats non-idempotent effects, or queue age grows unnoticed.",
        "migration": "Extract the slowest self-contained step, persist a job before returning, run a worker with idempotent completion, expose status, and remove the old inline branch after result parity and restart tests pass.",
        "evidence": "Request latency and timeout traces, task duration distribution, deployment interruption behavior, queue depth/age, job retry history, and terminal-state coverage.",
        "changes": "Inline is preferable for consistently short atomic work; a durable job is required when completion must survive process or deployment failure.",
        "tradeoffs": "Background execution protects responsiveness and scalability but adds eventual completion and operational ownership.",
        "claims": {
            "JOB-SEPARATION": "Background jobs run independently from the initiating UI or request process.",
            "JOB-RELIABILITY": "Reliable background work needs restart, conflict, result, and poison-message handling.",
        },
        "sources": [
            source(
                "Azure background job guidance",
                "https://learn.microsoft.com/en-us/azure/architecture/best-practices/background-jobs",
                "official",
                "JOB-SEPARATION",
                "JOB-RELIABILITY",
            ),
        ],
        "related": ["decision.sync-vs-async", "style.durable-workflow"],
    },
    "monolith-vs-microservices": {
        "title": "Modular Monolith vs Microservices",
        "problem": "Choose deployment boundaries from independent change and scaling needs, not from module count or anticipated prestige.",
        "mechanism": "A modular monolith enforces domain ownership inside one deployable and transaction boundary. Microservices turn selected domain boundaries into separately deployed, versioned, observed, and failure-isolated services.",
        "options": [
            (
                "Modular monolith",
                "A small team, coupled release cadence, and shared operational envelope.",
                "Independent scaling, compliance, or release ownership is already measurable.",
                "Discipline is needed to keep modules and data ownership explicit.",
                "Internal imports and shared tables erode boundaries into a big ball of mud.",
            ),
            (
                "Selective service extraction",
                "One bounded context has proven independent change, load, data, or isolation needs.",
                "The candidate boundary still changes transactionally with neighbors.",
                "Network contracts, deployment, tracing, eventual consistency, and on-call load.",
                "A distributed monolith preserves coupling while adding network failure.",
            ),
            (
                "Broad microservice decomposition",
                "Multiple autonomous teams and operational capabilities can own many services.",
                "A small team cannot sustain platform and incident overhead.",
                "Highest delivery, runtime, data, and governance complexity.",
                "Service sprawl, incompatible contracts, and cross-service transaction failure.",
            ),
        ],
        "required": "Domain/data ownership, dependency rules, consumer contracts, deployment and rollback, distributed tracing, service SLOs, and teams able to own incidents.",
        "benefits": "A proportional boundary choice preserves simplicity while leaving a measured path to independent deployment.",
        "costs": "Microservices multiply runtime and coordination surfaces; monoliths require strong internal enforcement.",
        "failures": "Shared databases, chatty synchronous calls, cyclic service dependencies, coordinated releases, and extraction before the domain stabilizes.",
        "migration": "First establish modules and owner-owned tables; measure change/load coupling; extract one edge boundary with an anti-corruption interface and reversible routing before considering another.",
        "evidence": "Commit and release coupling, team ownership, hot spots, scaling asymmetry, transaction boundaries, incident history, dependency graph, and deployment capability.",
        "changes": "Prefer a modular monolith until independent deployment or isolation produces measurable value greater than distributed-systems cost.",
        "tradeoffs": "Services improve independent evolution and isolation but trade away local transactions, simple debugging, and low operational overhead.",
        "claims": {
            "SERVICE-BOUNDARY": "Microservice boundaries carry independent deployment and distributed interaction consequences.",
            "MONOLITH-MODULARITY": "A single deployable can still enforce explicit internal modules.",
        },
        "sources": [
            source(
                "Azure microservices architecture style",
                "https://learn.microsoft.com/en-us/azure/architecture/guide/architecture-styles/microservices",
                "official",
                "SERVICE-BOUNDARY",
            ),
            source(
                "Martin Fowler: Monolith First",
                "https://martinfowler.com/bliki/MonolithFirst.html",
                "maintainer",
                "MONOLITH-MODULARITY",
            ),
        ],
        "related": ["foundation.system-boundaries", "pattern.outbox"],
    },
    "rest-vs-graphql-vs-grpc": {
        "title": "REST vs GraphQL vs gRPC",
        "problem": "Select an API interaction model from consumers, query shape, streaming, compatibility, caching, and operational constraints.",
        "mechanism": "REST exposes resource representations through HTTP semantics; GraphQL evaluates a typed query against a schema; gRPC invokes generated service methods over Protocol Buffers and HTTP/2.",
        "options": [
            (
                "REST over HTTP",
                "Resource-oriented public or browser APIs benefit from HTTP tooling and caching.",
                "Clients need arbitrary graph-shaped aggregation or high-rate typed streaming.",
                "Endpoint/version discipline and possible over/under-fetching.",
                "Action endpoints, ambiguous status semantics, or breaking representations accumulate.",
            ),
            (
                "GraphQL",
                "Many client views need different compositions over a governed graph.",
                "Simple resources suffice or query cost cannot be controlled.",
                "Schema governance, resolver performance, authorization, and query limits.",
                "N+1 resolution or unbounded queries exhaust backends.",
            ),
            (
                "gRPC",
                "Controlled service-to-service clients need generated types, low overhead, or streaming.",
                "Direct browser/public interoperability and ordinary HTTP caching dominate.",
                "IDL/toolchain coupling, proxies, observability, and compatibility rules.",
                "Breaking field reuse or deadline propagation failures disrupt clients.",
            ),
        ],
        "required": "Consumer inventory, compatibility policy, authentication and field-level authorization, error semantics, deadlines, observability, payload/query limits, and generated-contract discipline where used.",
        "benefits": "Aligns API mechanics with actual consumers instead of standardizing all interaction on one fashionable protocol.",
        "costs": "Supporting multiple protocols adds gateways and duplicated policy; forcing one protocol creates local workarounds.",
        "failures": "GraphQL N+1 and authorization gaps, REST chatty aggregation, gRPC deadline/compatibility mistakes, or leaking internal schemas publicly.",
        "migration": "Stabilize domain operations behind an application boundary, pilot the new protocol for one consumer, run contract tests and telemetry in parallel, then retire the old adapter only after consumers migrate.",
        "evidence": "Consumer environments, request shapes, payload and round-trip traces, streaming needs, cache behavior, schema change history, gateway support, and team tooling.",
        "changes": "REST is the default for ordinary resource APIs; GraphQL earns its cost with real composition diversity; gRPC earns it in controlled typed and streaming service links.",
        "tradeoffs": "Flexibility, interoperability, runtime efficiency, cacheability, and schema governance pull in different directions.",
        "claims": {
            "GRAPHQL-SCHEMA": "GraphQL executes client-specified typed queries against a schema.",
            "GRPC-CONTRACT": "gRPC uses service definitions to generate clients and servers.",
            "HTTP-SEMANTICS": "HTTP methods and status codes provide standardized resource interaction semantics.",
        },
        "sources": [
            source(
                "GraphQL Learn",
                "https://graphql.org/learn/",
                "official",
                "GRAPHQL-SCHEMA",
            ),
            source(
                "gRPC introduction",
                "https://grpc.io/docs/what-is-grpc/introduction/",
                "official",
                "GRPC-CONTRACT",
            ),
            source(
                "RFC 9110 HTTP Semantics",
                "https://www.rfc-editor.org/rfc/rfc9110",
                "standard",
                "HTTP-SEMANTICS",
            ),
        ],
        "related": ["pattern.backend-for-frontend", "decision.sync-vs-async"],
    },
    "database-selection": {
        "title": "Database Selection",
        "problem": "Select a persistence engine from owned data invariants, access paths, consistency, recovery, scale, and operational capability.",
        "mechanism": "Start with the aggregate and invariant boundary, enumerate critical reads and writes, then verify transaction, index, partition, backup, restore, migration, and failure behavior against representative data.",
        "options": [
            (
                "Existing general-purpose database",
                "It satisfies invariants and access paths with known operations.",
                "A measured workload cannot meet a critical scenario.",
                "May require careful indexing or a bounded extension.",
                "Convenience schemas hide contention or unbounded queries.",
            ),
            (
                "Purpose-specific database",
                "A distinct model or workload has proven requirements the current engine cannot meet.",
                "The choice is based only on data shape or projected scale.",
                "New expertise, backup, security, monitoring, and integration.",
                "A second authority creates dual writes and recovery ambiguity.",
            ),
            (
                "Polyglot persistence with derived store",
                "One authority feeds a rebuildable search, graph, cache, or analytic projection.",
                "The derived store is treated as the only copy without recovery design.",
                "Replication lag, reconciliation, lineage, and additional operations.",
                "Projection drift serves incomplete or unauthorized data.",
            ),
        ],
        "required": "Authority and ownership, consistency/invariant scenarios, access-path benchmarks, schema evolution, backup/restore proof, security, data lifecycle, capacity model, and operator skill.",
        "benefits": "Keeps database choice tied to durable correctness and operations rather than feature checklists.",
        "costs": "Every engine adds a lifecycle, failure model, and staffing obligation; migrations have dual-run and rollback costs.",
        "failures": "Benchmarking toy data, using one database per feature, missing restore tests, cross-store transactions, and selecting for hypothetical scale.",
        "migration": "Build a representative benchmark and restore drill, place the candidate behind a repository interface, backfill with checksums, dual-read for evidence, then cut authority only with rollback and reconciliation.",
        "evidence": "Data invariants, query/write distribution, cardinality and growth, contention, retention, residency, backup RPO/RTO, migration history, cost, and operational ownership.",
        "changes": "Retain the current engine unless a critical measured scenario fails and the candidate demonstrates both workload fit and sustainable operations.",
        "tradeoffs": "Model fit and performance trade against transactional scope, portability, operational simplicity, and recovery confidence.",
        "claims": {
            "DB-TRANSACTIONS": "Transaction isolation and failure behavior are first-class persistence capabilities.",
            "DB-RECOVERY": "Backup and restore procedures are part of a database's production suitability.",
        },
        "sources": [
            source(
                "PostgreSQL transaction isolation",
                "https://www.postgresql.org/docs/current/transaction-iso.html",
                "official",
                "DB-TRANSACTIONS",
            ),
            source(
                "PostgreSQL backup and restore",
                "https://www.postgresql.org/docs/current/backup.html",
                "official",
                "DB-RECOVERY",
            ),
        ],
        "related": [
            "decision.relational-vs-document-vs-graph",
            "pattern.materialized-view",
        ],
    },
    "relational-vs-document-vs-graph": {
        "title": "Relational vs Document vs Graph Data Model",
        "problem": "Choose a primary data model from invariants and access paths while avoiding a different authority for every query shape.",
        "mechanism": "Relational models normalize facts and enforce constraints across rows; document models persist aggregates together; graph models make nodes and relationships the traversal surface. Any secondary model should remain a rebuildable projection unless ownership moves deliberately.",
        "options": [
            (
                "Relational",
                "Cross-entity constraints, transactions, reporting, and evolving queries matter.",
                "The workload is almost entirely aggregate-local and schema joins dominate cost.",
                "Schema migrations and joins require discipline.",
                "Missing constraints or unindexed joins erode integrity and latency.",
            ),
            (
                "Document",
                "Aggregates are read and written together with bounded document size.",
                "Many-to-many relations and cross-aggregate invariants dominate.",
                "Duplication, update fan-out, and application-enforced consistency.",
                "Unbounded documents or duplicated facts drift.",
            ),
            (
                "Graph",
                "Variable-depth relationship traversal is a core measured operation.",
                "Simple key, aggregate, or set queries cover the product.",
                "New query language, operations, projection synchronization, and access control.",
                "A graph is introduced for conceptual elegance but ordinary lookups remain primary.",
            ),
        ],
        "required": "Named aggregates and invariants, representative query corpus, cardinality and growth, transaction scope, index plan, migration/rebuild path, authorization traversal, and operator capability.",
        "benefits": "Connects model shape to actual correctness and query behavior and permits derived models without confused ownership.",
        "costs": "Specialized models simplify selected paths while making other constraints, joins, or operations harder.",
        "failures": "Choosing from entity diagrams alone, unbounded documents, graph supernodes, duplicated authorities, and application-only constraints without tests.",
        "migration": "Keep one authority, project a bounded read model into the candidate, compare query and recovery behavior, and move authority only after constraints and rollback are proven.",
        "evidence": "Invariant map, aggregate size, relationship depth/fan-out, query plans, transaction conflicts, schema-change frequency, restore tests, and authorization rules.",
        "changes": "Use relational by default for broad transactional needs; document or graph should be justified by dominant aggregate-local or traversal workloads.",
        "tradeoffs": "Each model moves complexity among storage shape, query expressiveness, integrity enforcement, duplication, and operations.",
        "claims": {
            "RELATIONAL-ISO": "Relational transaction isolation protects concurrent database behavior.",
            "GRAPH-TX": "Graph database operations execute within transactional boundaries.",
        },
        "sources": [
            source(
                "PostgreSQL transaction isolation",
                "https://www.postgresql.org/docs/current/transaction-iso.html",
                "official",
                "RELATIONAL-ISO",
            ),
            source(
                "Neo4j database internals and transactions",
                "https://neo4j.com/docs/operations-manual/current/database-internals/",
                "official",
                "GRAPH-TX",
            ),
        ],
        "related": ["decision.database-selection", "pattern.materialized-view"],
    },
    "message-system-selection": {
        "title": "Message System Selection",
        "problem": "Choose queue, publish/subscribe, or durable stream semantics from ownership, delivery, ordering, replay, fan-out, and recovery needs.",
        "mechanism": "A queue assigns work to one consumer group, pub/sub distributes notifications to subscribers, and a stream retains ordered records for independent cursor-based consumption. The application must still define idempotency and business ordering.",
        "options": [
            (
                "Work queue",
                "Each command should be processed by one scalable consumer pool.",
                "Every subscriber needs an independent copy or replay.",
                "Visibility/lease tuning, retries, and dead letters.",
                "Poison work loops or visibility expiry causes concurrent effects.",
            ),
            (
                "Publish/subscribe",
                "Several consumers react independently to an event.",
                "Consumers need long retention or arbitrary historical replay.",
                "Subscription lifecycle, schema compatibility, and fan-out cost.",
                "A missing subscription silently loses events.",
            ),
            (
                "Durable event stream",
                "Replay, audit, ordered partition history, or many independent consumers are required.",
                "The workload is a simple task queue with no replay value.",
                "Partition/key design, retention, consumer lag, and heavier operations.",
                "Hot partitions or incorrect offsets cause lag, gaps, or duplication.",
            ),
        ],
        "required": "Message ownership, schema/version policy, delivery guarantee, idempotent consumers, ordering key, retry and dead-letter policy, retention, backpressure, lag/age monitoring, and access control.",
        "benefits": "Prevents broker brand selection from substituting for delivery and recovery semantics.",
        "costs": "Durability and fan-out increase storage and operational burden; simple queues limit replay and broadcast.",
        "failures": "Assuming exactly-once business effects, global ordering without partition cost, retry storms, unbounded lag, oversized payloads, and incompatible event changes.",
        "migration": "Document current producer/consumer semantics, introduce an adapter and versioned envelope, shadow-consume without side effects, compare counts and ordering, then migrate one consumer group at a time.",
        "evidence": "Producer and consumer graph, throughput/burst, payload size, ordering scope, replay window, retry distribution, poison rate, lag SLO, and team operations.",
        "changes": "Prefer a queue for work distribution, pub/sub for live fan-out, and a retained stream only when replay or independent history has measurable value.",
        "tradeoffs": "Replay, ordering, delivery isolation, latency, simplicity, and storage cost vary by semantic model.",
        "claims": {
            "QUEUE-SEMANTIC": "Competing consumers distribute queued work across a consumer pool.",
            "MESSAGE-CHOICE": "Message brokers and event streaming platforms expose different delivery and retention trade-offs.",
        },
        "sources": [
            source(
                "Azure Competing Consumers pattern",
                "https://learn.microsoft.com/en-us/azure/architecture/patterns/competing-consumers",
                "official",
                "QUEUE-SEMANTIC",
            ),
            source(
                "Azure asynchronous messaging options",
                "https://learn.microsoft.com/en-us/azure/architecture/guide/technology-choices/messaging",
                "official",
                "MESSAGE-CHOICE",
            ),
        ],
        "related": ["pattern.outbox", "decision.sync-vs-async"],
    },
    "ssr-vs-csr-vs-ssg": {
        "title": "SSR vs CSR vs SSG",
        "problem": "Choose where and when HTML is produced for each route from freshness, personalization, discoverability, interaction, security, and delivery cost.",
        "mechanism": "SSG renders at build or revalidation time, SSR renders per request, and CSR renders primarily in the browser after JavaScript and data arrive. A product may compose these at route or component boundaries.",
        "options": [
            (
                "Static generation",
                "Content changes on a bounded cadence and fast cacheable delivery matters.",
                "Per-request personalization or immediate freshness is mandatory.",
                "Build/revalidation pipelines and invalidation delay.",
                "Build duration or stale pages grow without bounds.",
            ),
            (
                "Server-side rendering",
                "Request-specific or frequently changing content needs useful initial HTML.",
                "Server cost and latency cannot meet traffic targets.",
                "Per-request compute, caching, and hydration complexity.",
                "Slow dependencies delay the whole response or leak user-scoped content through caches.",
            ),
            (
                "Client-side rendering",
                "The view is highly interactive, authenticated, and initial indexing/HTML is secondary.",
                "Low-end clients, discoverability, or first-content latency are critical.",
                "Larger JavaScript, client data waterfalls, and loading states.",
                "Blank shells, hydration/state bugs, or exposed browser-only trust decisions.",
            ),
        ],
        "required": "Route inventory, freshness and personalization matrix, cache keys, bundle and server budgets, loading/error behavior, hydration tests, and security boundaries.",
        "benefits": "Allows rendering to follow route needs instead of forcing a whole application into one mode.",
        "costs": "Hybrid rendering adds mental models and cache rules; single-mode designs may waste server or client resources.",
        "failures": "Caching personalized SSR output, client waterfalls, rebuild bottlenecks, hydration mismatch, and moving authorization to the browser.",
        "migration": "Classify routes, move one stable public page to static or one dynamic page to server rendering, measure user timing and server cost, then expand by route rather than by global rewrite.",
        "evidence": "Route freshness/personalization, web-vital traces, HTML usefulness without JavaScript, bundle size, server latency/cost, cache headers, and hydration errors.",
        "changes": "Static is preferred for stable public content; SSR for request-dependent initial content; CSR for interaction-heavy private surfaces where client cost is acceptable.",
        "tradeoffs": "Freshness, initial content, server spend, client work, cacheability, and implementation complexity trade at route level.",
        "claims": {
            "STATIC-RENDER": "Static generation can emit HTML ahead of requests.",
            "SSR-REQUEST": "SSR generates HTML for each request.",
            "CLIENT-BOUNDARY": "Client components are needed for browser APIs and interactive state.",
        },
        "sources": [
            source(
                "Next.js automatic static optimization",
                "https://nextjs.org/docs/pages/building-your-application/rendering/automatic-static-optimization",
                "official",
                "STATIC-RENDER",
            ),
            source(
                "Next.js server-side rendering",
                "https://nextjs.org/docs/pages/building-your-application/rendering/server-side-rendering",
                "official",
                "SSR-REQUEST",
            ),
            source(
                "Next.js Server and Client Components",
                "https://nextjs.org/docs/app/getting-started/server-and-client-components",
                "official",
                "CLIENT-BOUNDARY",
            ),
        ],
        "related": ["decision.data-loading-and-refresh", "decision.state-management"],
    },
    "state-management": {
        "title": "UI State Management",
        "problem": "Place state with the narrowest owner that can preserve correctness, rather than copying all remote and local state into one global store.",
        "mechanism": "Distinguish server authority, URL/navigation state, form drafts, component UI state, and durable local data. Store a value once at its authority and derive or cache downstream representations.",
        "options": [
            (
                "Component or feature-local state",
                "Only one subtree owns a transient interaction.",
                "Multiple distant features must coordinate the same durable fact.",
                "Prop/context wiring at feature boundaries.",
                "Lifting everything upward creates incidental coupling.",
            ),
            (
                "Server-state cache",
                "Remote resources need deduplication, freshness, retry, and mutation invalidation.",
                "The value is purely local UI or an unsaved draft.",
                "Cache keys, stale policy, and mutation reconciliation.",
                "Cached copies are mistaken for authority or leak across users.",
            ),
            (
                "Application store or state machine",
                "Several features coordinate client-owned state or explicit transitions.",
                "Ordinary remote reads or local toggles are the only need.",
                "Actions, lifecycle, persistence, and debugging conventions.",
                "A universal store becomes a dependency hub with ambiguous ownership.",
            ),
        ],
        "required": "State inventory, authoritative owner, lifecycle/reset rules, scope key including user/tenant, serialization policy, transition tests, and devtools/telemetry for complex flows.",
        "benefits": "Reduces duplicated truth and makes reset, persistence, and synchronization behavior reviewable.",
        "costs": "Several small state mechanisms may coexist; teams must understand the boundary between them.",
        "failures": "Global-store sprawl, copied props drifting, stale server data, persistence across logout, circular derived state, and race-prone effects.",
        "migration": "Inventory values in the global store, move remote resources to a server-state boundary and leaf interactions local, preserve selectors during transition, then delete duplicated copies after behavior tests pass.",
        "evidence": "Read/write ownership graph, reset and login/logout paths, persistence keys, duplicate representations, effect dependencies, render traces, and transition tests.",
        "changes": "Escalate from local state only when multiple owners or explicit cross-feature transitions are demonstrated.",
        "tradeoffs": "Centralization improves discoverability and coordination but increases coupling, lifetime, and accidental persistence.",
        "claims": {
            "STATE-IDENTITY": "React state is associated with a component's position and must be reset deliberately.",
            "STATE-USER-SCOPE": "Preserved client state can cross authentication changes unless reset.",
        },
        "sources": [
            source(
                "React preserving and resetting state",
                "https://react.dev/learn/preserving-and-resetting-state",
                "official",
                "STATE-IDENTITY",
            ),
            source(
                "Next.js preserving UI state",
                "https://nextjs.org/docs/app/guides/preserving-ui-state",
                "official",
                "STATE-USER-SCOPE",
            ),
        ],
        "related": [
            "decision.optimistic-vs-pessimistic-update",
            "decision.data-loading-and-refresh",
        ],
    },
    "local-first-vs-server-first": {
        "title": "Local-First vs Server-First",
        "problem": "Choose the authoritative and interaction path for data when devices may be offline, concurrent, constrained, or shared.",
        "mechanism": "Server-first commits against a central authority and may cache locally. Local-first commits to a device replica and synchronizes operations or versions later, so conflicts and convergence are product semantics rather than transport details.",
        "options": [
            (
                "Server-first with local cache",
                "Connectivity is expected and shared authority must arbitrate changes.",
                "Core work must remain writable for long offline periods.",
                "Offline behavior is limited and latency depends on network.",
                "A cache is mistaken for a writable replica and loses edits.",
            ),
            (
                "Offline queue over server authority",
                "Users need bounded offline commands that can replay later.",
                "Concurrent offline edits require rich merging.",
                "Command durability, ordering, idempotency, expiry, and rejection UI.",
                "Replayed commands are no longer valid or execute twice.",
            ),
            (
                "Local-first replicated data",
                "Instant offline-capable collaboration is a defining product requirement.",
                "The team cannot define conflict and convergence semantics.",
                "Replica identity, sync protocol, merge model, tombstones, migration, and support.",
                "Silent conflict resolution loses intent or replicas never converge.",
            ),
        ],
        "required": "Authority declaration, offline duration, replica/device identity, version or operation model, conflict UX, encryption, deletion/tombstone rules, schema migration, and sync observability.",
        "benefits": "Makes offline reliability and user-perceived responsiveness an explicit architecture property.",
        "costs": "Local-first moves distributed-systems complexity onto every device; server-first depends on connectivity.",
        "failures": "Last-write-wins data loss, duplicate offline commands, clock assumptions, unbounded tombstones, account crossover, and incompatible local schema upgrades.",
        "migration": "Begin with read caching and a single idempotent offline command, simulate long disconnect and concurrent edits, introduce versioned conflict handling, and expand only after convergence and recovery tests pass.",
        "evidence": "Offline product scenarios, concurrent editor count, data sensitivity, conflict examples, device storage limits, sync traces, deletion behavior, and migration tests across skipped versions.",
        "changes": "Server-first remains simpler unless offline writes and instant local interaction are critical product capabilities, not convenience features.",
        "tradeoffs": "Availability and local latency trade against centralized consistency, simpler authorization, and lower client complexity.",
        "claims": {
            "LOCAL-FIRST": "Local-first software treats the local copy as primary for interaction and synchronizes in the background.",
            "SYNC-CONFLICT": "Replicated writes require explicit conflict or convergence behavior.",
        },
        "sources": [
            source(
                "Local-first software",
                "https://www.inkandswitch.com/essay/local-first/",
                "research",
                "LOCAL-FIRST",
                "SYNC-CONFLICT",
            ),
        ],
        "related": [
            "decision.optimistic-vs-pessimistic-update",
            "decision.state-management",
        ],
    },
    "optimistic-vs-pessimistic-update": {
        "title": "Optimistic vs Pessimistic Update",
        "problem": "Choose how a client represents a mutation before authority confirms it and how concurrent conflict is detected and repaired.",
        "mechanism": "Optimistic UI applies a reversible local projection tagged to a mutation ID; pessimistic UI waits for authority. Both need an authoritative concurrency condition such as version, ETag, or lock and a defined conflict outcome.",
        "options": [
            (
                "Optimistic projection",
                "Success is common, the action is reversible, and fast feedback matters.",
                "Failure is frequent, irreversible, regulated, or difficult to explain.",
                "Rollback/rebase logic and temporary identity mapping.",
                "Late failure rolls back newer intent or duplicates a retried effect.",
            ),
            (
                "Pessimistic confirmation",
                "The authoritative result or scarce resource must be known first.",
                "Network latency would make frequent low-risk actions unusable.",
                "Visible wait states and lower interaction throughput.",
                "Disabled UI hides timeout uncertainty or duplicate submissions.",
            ),
            (
                "Optimistic concurrency with explicit conflict",
                "Multiple writers edit versioned resources and conflicts can be presented.",
                "No meaningful merge or user resolution exists.",
                "Version checks, conflict payloads, merge UX, and retry discipline.",
                "Last-write-wins silently discards another actor's change.",
            ),
        ],
        "required": "Mutation identity, authority version/ETag, idempotency, reversible patch or re-fetch path, temporary IDs, conflict UX, retry limits, and tests for out-of-order completion.",
        "benefits": "Balances interaction latency with explicit correctness and conflict behavior.",
        "costs": "Optimism increases client state complexity; pessimism increases perceived latency and blocking.",
        "failures": "Rollback overwrites later edits, duplicate commands, stale version checks, inaccessible failure feedback, and optimistic handling of irreversible money or permission effects.",
        "migration": "Add server concurrency conditions first, introduce a mutation state model, enable optimism for one reversible action, inject conflicts and failures, and keep pessimistic fallback for high-risk cases.",
        "evidence": "Mutation success/failure rate, latency, reversibility, concurrency frequency, server version checks, idempotency behavior, user impact, and race tests.",
        "changes": "Choose optimism only when rollback and conflict semantics are safer than making the user wait; high-risk irreversible effects generally require confirmation.",
        "tradeoffs": "Responsiveness trades against client complexity, rollback risk, and the clarity of authoritative completion.",
        "claims": {
            "HTTP-CONDITION": "HTTP conditional requests support version-based lost-update prevention.",
            "OPTIMISTIC-STATE": "Optimistic UI needs a pending state and explicit failure handling.",
        },
        "sources": [
            source(
                "MDN conditional requests",
                "https://developer.mozilla.org/en-US/docs/Web/HTTP/Guides/Conditional_requests",
                "official",
                "HTTP-CONDITION",
            ),
            source(
                "React useOptimistic",
                "https://react.dev/reference/react/useOptimistic",
                "official",
                "OPTIMISTIC-STATE",
            ),
        ],
        "related": [
            "decision.state-management",
            "decision.local-first-vs-server-first",
        ],
    },
    "workflow-vs-agent": {
        "title": "Deterministic Workflow vs Agent",
        "problem": "Decide which steps remain explicit software control flow and where model-directed tool selection is justified by ambiguity.",
        "mechanism": "A workflow owns a known state machine and may call models inside bounded steps. An agent lets a model choose the next action from tools and instructions until an exit condition, with budgets, guardrails, evidence, and human control around the loop.",
        "options": [
            (
                "Deterministic workflow",
                "Steps, branching, and acceptance rules can be specified and tested.",
                "Unstructured context makes enumerated rules unmaintainable.",
                "Rule and workflow maintenance as cases evolve.",
                "A rigid flow accumulates exceptions and manual handoffs.",
            ),
            (
                "Workflow with bounded model steps",
                "Interpretation or generation is fuzzy but process authority is known.",
                "The model must discover and execute an open-ended plan.",
                "Structured outputs, evaluation data, and fallback handling.",
                "Model output silently controls a later high-impact step.",
            ),
            (
                "Tool-using agent",
                "The task requires contextual planning across variable tools and can be safely bounded.",
                "A deterministic flow meets the need or mistakes have irreversible impact.",
                "Evaluation, tool security, loop limits, recovery, cost, latency, and approval UX.",
                "Prompt injection or looping drives unauthorized or untraceable actions.",
            ),
        ],
        "required": "Task success metric, tool allowlist and least privilege, structured state, step/latency/cost budgets, evidence trail, injection defenses, recovery, evaluation set, and approval for consequential actions.",
        "benefits": "Uses model autonomy only where ambiguity creates real value while retaining deterministic control elsewhere.",
        "costs": "Agents add nondeterminism, evaluation and security work, latency, cost, and harder incident reconstruction.",
        "failures": "Agent used as a queue or state machine, prompt-injected tool calls, unbounded loops, hidden context loss, fabricated completion, and no human recovery path.",
        "migration": "Implement the deterministic happy path, isolate one ambiguous decision behind structured output, compare it with a labeled evaluation set, and grant tools incrementally with shadow or approval mode.",
        "evidence": "Exception rate, rule maintenance burden, unstructured inputs, action reversibility, tool permissions, eval pass rate, trace completeness, loop distribution, latency, and cost.",
        "changes": "Prefer workflows whenever explicit rules are adequate; introduce an agent only after a bounded model step proves insufficient.",
        "tradeoffs": "Adaptability trades against predictability, auditability, security surface, latency, and operating cost.",
        "claims": {
            "AGENT-DEFINITION": "An agent uses a model to manage workflow execution and choose tools within guardrails.",
            "AGENT-FIT": "Agents are best suited to complex judgment, difficult rules, or unstructured information.",
        },
        "sources": [
            source(
                "OpenAI practical guide to building agents",
                "https://openai.com/business/guides-and-resources/a-practical-guide-to-building-ai-agents/",
                "official",
                "AGENT-DEFINITION",
                "AGENT-FIT",
            ),
        ],
        "related": ["decision.single-agent-vs-multi-agent", "style.durable-workflow"],
    },
    "single-agent-vs-multi-agent": {
        "title": "Single-Agent vs Multi-Agent Orchestration",
        "problem": "Choose one agent loop or multiple specialized agents from evaluation evidence, context/tool boundaries, ownership, and failure isolation.",
        "mechanism": "A single agent owns the user context and chooses among tools. Multi-agent orchestration introduces typed delegation: a manager invokes specialists or a handoff transfers control, and every boundary constrains context, authority, result schema, and termination.",
        "options": [
            (
                "Single agent with tools",
                "One instruction hierarchy and context can handle the task reliably.",
                "Tool overlap or instruction complexity causes measured failures.",
                "Prompt/tool growth and context management.",
                "The agent selects the wrong similar tool or loses critical instructions.",
            ),
            (
                "Manager with specialist tools",
                "Specialized tasks need separate context but one controller should retain authority.",
                "Delegation overhead exceeds the task or the manager cannot verify results.",
                "Routing, schemas, nested latency/cost, and trace composition.",
                "The manager trusts an unsupported specialist answer.",
            ),
            (
                "Peer handoffs",
                "Different agents genuinely own separate conversational domains and control may transfer.",
                "A single user-facing authority or strong transaction boundary is required.",
                "Handoff state, permission change, return path, and user clarity.",
                "Context or authority disappears between peers and no agent owns completion.",
            ),
        ],
        "required": "Single-agent baseline, labeled routing and task evals, typed delegation, context minimization, tool/permission scopes, hop and budget limits, trace correlation, failure return, and accountable final owner.",
        "benefits": "Preserves simple orchestration until specialization measurably improves quality or isolation.",
        "costs": "Every agent boundary adds model calls, context transformation, evaluation combinations, and unclear accountability risk.",
        "failures": "Role-play agents without isolation value, delegation loops, contradictory instructions, authority escalation, context leakage, and final answers with no evidence owner.",
        "migration": "Benchmark the single agent first, extract the highest-confusion capability as one typed specialist, shadow its routing, compare quality/cost/latency, and stop if the gain is not material.",
        "evidence": "Tool confusion matrix, instruction length, task clusters, context sensitivity, single-agent baseline, routing accuracy, hop count, cost, latency, and failure traces.",
        "changes": "Keep one agent until evaluation shows a specific specialization or permission boundary that outweighs orchestration cost.",
        "tradeoffs": "Specialization and isolation trade against latency, cost, context loss, routing errors, and accountability.",
        "claims": {
            "SINGLE-FIRST": "A single agent can gain capability incrementally by adding tools.",
            "MULTI-PATTERNS": "Multi-agent orchestration commonly uses manager or decentralized handoff patterns.",
        },
        "sources": [
            source(
                "OpenAI practical guide to building agents",
                "https://openai.com/business/guides-and-resources/a-practical-guide-to-building-ai-agents/",
                "official",
                "SINGLE-FIRST",
                "MULTI-PATTERNS",
            ),
        ],
        "related": ["decision.workflow-vs-agent", "foundation.proportional-design"],
    },
}

CONCEPTS: dict[str, dict[str, Any]] = {
    "architecture-styles/durable-workflow": {
        "title": "Durable Workflow",
        "operating": (
            "A workflow definition advances persisted execution state through named, "
            "idempotent activities. The runtime records enough history to replay or "
            "resume after worker, process, or deployment failure; external effects occur "
            "only through activities with explicit retry and compensation semantics."
        ),
        "problem": (
            "Coordinate long-running, multi-step work that must survive process failure, "
            "wait for external events, and expose a trustworthy lifecycle."
        ),
        "mechanism": (
            "Persist workflow identity, input, current state, timers, event correlation, "
            "and terminal result. Keep orchestration deterministic under replay and isolate "
            "nondeterministic I/O in retryable activities."
        ),
        "fit": "Business processes last beyond one request, cross deploys or outages, wait on humans/external systems, and need visible recovery.",
        "avoid": "A short database transaction, simple queue consumer, or stateless request already provides adequate durability.",
        "required": "Stable workflow/activity IDs, idempotency, replay-safe orchestration, bounded retry and timeout policy, cancellation, compensation, versioning, history retention, and operator search/recovery.",
        "benefits": "Makes long-running state and recovery explicit and removes ad hoc cron, status-table, and retry glue.",
        "costs": "Adds a workflow runtime, deterministic coding constraints, history lifecycle, new deployment/versioning rules, and specialist operations.",
        "failures": "Nondeterministic replay, duplicated external effects, unbounded histories, incompatible workflow code upgrades, stuck waits, and compensation that is assumed to be rollback.",
        "alternatives": "Use a database-backed job for one durable step, a broker consumer for independent events, or an application state machine when an additional runtime is not justified.",
        "migration": "Model the existing state machine and failure states, move one restart-sensitive process behind stable workflow/activity contracts, replay production-like histories through upgrades, and retain an operator fallback until recovery drills pass.",
        "evidence": "Process duration, wait states, restart/deploy failures, current retry tables and cron jobs, side effects, recovery time, state-machine transitions, and workflow-history growth.",
        "changes": "A queue plus idempotent worker is simpler when work has one step; adopt durable workflow only when persisted orchestration and timers remove demonstrated failure or maintenance cost.",
        "tradeoffs": "Recovery and visibility improve at the cost of runtime dependence, replay constraints, history storage, and migration discipline.",
        "claims": {
            "DURABLE-EXEC": "Durable execution preserves workflow progress through infrastructure failure.",
            "DURABLE-REPLAY": "Workflow code and activities require replay- and retry-aware design.",
        },
        "sources": [
            source(
                "Temporal durable execution",
                "https://docs.temporal.io/encyclopedia/durable-execution",
                "official",
                "DURABLE-EXEC",
                "DURABLE-REPLAY",
            ),
        ],
        "related": [
            "decision.sync-vs-async",
            "decision.request-vs-background-job",
            "decision.workflow-vs-agent",
        ],
    },
    "patterns/backend-for-frontend": {
        "title": "Backend for Frontend",
        "operating": (
            "A client-specific edge service authenticates the caller, invokes domain or "
            "backend APIs, and shapes a response for one experience. It owns composition "
            "and presentation adaptation, not business truth or another copy of domain data."
        ),
        "problem": "Different web, mobile, or partner clients need materially different aggregation, payload, cadence, or protocol behavior without coupling every backend to presentation details.",
        "mechanism": "Place a BFF between one client class and backend capabilities. Keep domain commands in owning services, propagate identity and deadlines, bound fan-out, and cache only responses with safe user/tenant keys.",
        "fit": "Client teams have distinct release and aggregation needs and a shared API gateway has accumulated client-specific branching.",
        "avoid": "One thin API serves all clients, or the proposed BFF would merely proxy requests without owning composition.",
        "required": "Named client owner, upstream contract/version policy, authorization propagation, timeout and partial-failure semantics, fan-out budget, cache isolation, tracing, and no domain-data ownership.",
        "benefits": "Allows client-oriented APIs and independent experience evolution while protecting domain services from UI-specific churn.",
        "costs": "Adds a deployable hop, duplicated cross-cutting policy risk, more contracts, and possible aggregation latency.",
        "failures": "BFFs become mini-monoliths, duplicate business rules, call many services serially, leak credentials, or multiply one per screen.",
        "alternatives": "Use a gateway for uniform routing/policy, GraphQL for governed cross-client query composition, or add a single endpoint to the owning backend.",
        "migration": "Measure client-specific gateway branches, extract one high-value composition behind the existing route, compare latency and authorization behavior, then transfer ownership to the client team without moving domain writes.",
        "evidence": "Client release cadence, payload divergence, round trips, gateway conditionals, upstream call graph, authorization mapping, p95 fan-out latency, and team ownership.",
        "changes": "Prefer a shared API when differences are cosmetic; use a BFF when client-specific composition and ownership are persistent and measurable.",
        "tradeoffs": "Client autonomy and fewer round trips trade against service count, duplicated policy, and an extra runtime hop.",
        "claims": {
            "BFF-CLIENT": "A BFF separates client-specific backend concerns for different interfaces.",
            "BFF-COST": "Multiple BFF services add operational and duplication overhead.",
        },
        "sources": [
            source(
                "Azure Backends for Frontends pattern",
                "https://learn.microsoft.com/en-us/azure/architecture/patterns/backends-for-frontends",
                "official",
                "BFF-CLIENT",
                "BFF-COST",
            ),
        ],
        "related": ["decision.rest-vs-graphql-vs-grpc", "foundation.system-boundaries"],
    },
    "patterns/outbox": {
        "title": "Transactional Outbox",
        "operating": (
            "The domain update and an outbox record commit in one local database "
            "transaction. A separate relay claims committed outbox rows and publishes "
            "them at least once; consumers deduplicate by stable message or business key."
        ),
        "problem": "Prevent a committed domain change and its external message from diverging because two independent writes cannot be made atomic.",
        "mechanism": "Insert an immutable event envelope beside the aggregate update, commit both, relay only committed rows, retry publication, and record or infer progress without deleting evidence before retention and replay needs are met.",
        "fit": "One service owns both the state change and an event/command that must eventually reach an external broker or consumer.",
        "avoid": "There is no external publication, the operation is already one atomic broker transaction, or change-data capture reliably provides the required event semantics.",
        "required": "Single local transaction, immutable event ID, partition/order key, relay lease, bounded retry, idempotent consumers, lag/oldest-row metrics, retention, replay, and schema compatibility.",
        "benefits": "Eliminates lost events between database commit and broker publish while allowing relay recovery after crashes.",
        "costs": "Publication is eventually consistent and may duplicate; the table, relay, retention, and consumer idempotency require operations.",
        "failures": "Writing the outbox outside the aggregate transaction, marking published before broker acknowledgement, concurrent relays breaking order, unbounded table growth, and consumers assuming exactly once.",
        "alternatives": "Use database change-data capture when the log contains sufficient business semantics, broker-native transactions inside one supported boundary, or keep the operation local.",
        "migration": "Add the outbox table and envelope, dual-observe current direct publication and relay counts without double effects, inject crashes after commit and publish, then remove direct publication after reconciliation is clean.",
        "evidence": "Transaction boundary, direct broker writes, crash window, relay claim/update logic, oldest unrelayed row, duplicate rate, consumer dedupe, ordering scope, and cleanup/replay tests.",
        "changes": "Do not introduce an outbox when no dual write exists; choose CDC when it offers owned event transformation and equivalent recovery with less application code.",
        "tradeoffs": "Reliability of state-to-message handoff trades against lag, duplicates, storage, and relay complexity.",
        "claims": {
            "OUTBOX-ATOMIC": "State and event are recorded atomically in one local transaction.",
            "OUTBOX-DELIVERY": "The relay is replayable and consumers must tolerate at-least-once delivery.",
        },
        "sources": [
            source(
                "Azure Transactional Outbox sample",
                "https://learn.microsoft.com/en-us/samples/azure-samples/cosmos-db-design-patterns/transactional-outbox/",
                "official",
                "OUTBOX-ATOMIC",
                "OUTBOX-DELIVERY",
            ),
        ],
        "related": ["decision.message-system-selection", "style.durable-workflow"],
    },
    "patterns/materialized-view": {
        "title": "Materialized View",
        "operating": (
            "A projector derives a query-optimized representation from authoritative "
            "records or events. The view stores its source position or generation, can "
            "be rebuilt, and is served only within an explicit freshness and completeness contract."
        ),
        "problem": "Serve expensive joins, aggregates, search, graph traversal, or dashboard reads without moving write authority into a query-specific structure.",
        "mechanism": "Define the projection schema and source checkpoint, build snapshots or consume changes idempotently, publish a completed generation atomically, and expose lag and reconciliation results.",
        "fit": "A stable high-value query cannot meet latency/load targets directly and bounded projection lag is acceptable.",
        "avoid": "The authoritative query already meets its scenario, strong read-after-write is mandatory, or no owner can rebuild and reconcile the view.",
        "required": "Source authority, deterministic transform, idempotent update, checkpoint, backfill/rebuild, atomic generation switch, deletion handling, freshness SLO, reconciliation, and authorization-safe fields.",
        "benefits": "Improves read latency and isolates read load while allowing data shape to match the consuming query.",
        "costs": "Duplicates data, introduces lag, consumes storage/compute, and requires schema coordination and rebuild operations.",
        "failures": "Projector skips or reorders changes, rebuild mixes generations, deleted or permission-revoked data remains visible, and clients treat stale data as authoritative.",
        "alternatives": "Add or change an index, optimize the authoritative query, cache the final response, or use an on-demand aggregate for low-frequency reads.",
        "migration": "Capture baseline query cost, backfill a versioned projection with counts/checksums, shadow-read and compare, switch a bounded cohort, then retain rebuild and fallback procedures.",
        "evidence": "Query plan and latency, source change volume, acceptable staleness, projection lag, checkpoint durability, reconciliation mismatches, rebuild time, access-control changes, and storage cost.",
        "changes": "Prefer indexing or cache-aside for simpler repeated reads; choose a materialized view when a distinct query model and rebuildable lag are justified.",
        "tradeoffs": "Read speed and workload isolation trade against consistency lag, duplicated storage, rebuild complexity, and another observable pipeline.",
        "claims": {
            "MV-PRECOMPUTE": "A materialized view precomputes data suited to query needs.",
            "MV-CONSISTENCY": "The view requires a refresh/update strategy and can lag its sources.",
        },
        "sources": [
            source(
                "Azure Materialized View pattern",
                "https://learn.microsoft.com/en-us/azure/architecture/patterns/materialized-view",
                "official",
                "MV-PRECOMPUTE",
                "MV-CONSISTENCY",
            ),
        ],
        "related": ["decision.cache-strategy", "decision.database-selection"],
    },
    "technology-profiles/fastapi": {
        "title": "FastAPI",
        "operating": (
            "FastAPI is an ASGI web framework that maps Python type annotations and "
            "dependency declarations to request validation, OpenAPI generation, and "
            "async or sync endpoint execution. The application still owns domain, "
            "transaction, authorization, and background-work boundaries."
        ),
        "capabilities": (
            "Use it for HTTP routing, validated request/response models, dependency "
            "composition, OpenAPI contracts, and ASGI integration. Do not treat "
            "dependencies as a service locator, background tasks as a durable job "
            "system, or Pydantic transport models as domain ownership."
        ),
        "problem": "Evaluate FastAPI as a Python API delivery adapter without letting framework conveniences define the application architecture.",
        "mechanism": "Keep route functions thin: authenticate and validate, invoke an application use case, commit at an owned transaction boundary, and map typed results/errors to the HTTP contract.",
        "fit": "The team owns Python/ASGI operations and values typed validation and OpenAPI for HTTP APIs.",
        "avoid": "An existing framework already meets the need, CPU-bound work dominates the request path, or the team cannot operate Python packaging and ASGI lifecycle behavior.",
        "required": "Supported Python/runtime policy, pinned dependencies, explicit lifespan and resource ownership, request/response schemas, authorization at use-case boundaries, transaction policy, timeout/body limits, and integration/contract tests.",
        "benefits": "Provides concise typed HTTP adapters and generated API documentation while retaining ordinary Python application structure.",
        "costs": "Framework and validation-library upgrades can affect generated schemas and behavior; async code introduces cancellation and blocking-I/O obligations.",
        "failures": "Blocking calls inside async handlers, request-scoped transactions leaking, trusting validation as authorization, incompatible OpenAPI drift, in-process tasks lost on restart, and overly large dependency graphs.",
        "alternatives": "Use the repository's current Python web framework, a smaller ASGI layer for minimal endpoints, or a non-Python stack when organizational ownership dominates.",
        "migration": "Wrap one use case behind a FastAPI adapter, snapshot the OpenAPI contract, load-test sync/async dependencies, verify shutdown and transaction cleanup, then migrate routes without moving domain rules into handlers.",
        "evidence": "Current Python stack, route/use-case separation, generated OpenAPI diff, dependency lifecycle, blocking-call traces, concurrency/load tests, transaction cleanup, security tests, and deployment shutdown logs.",
        "changes": "Reject adoption when it duplicates a healthy framework or when measured runtime and team constraints do not fit; recheck current compatibility in official release documentation.",
        "tradeoffs": "Developer speed and typed contracts trade against framework coupling, Python runtime limits, async correctness, and schema migration work.",
        "claims": {
            "FASTAPI-OPENAPI": "FastAPI uses Python types to validate data and generate OpenAPI-based documentation.",
            "FASTAPI-ASYNC": "FastAPI supports both async and normal path-operation functions with different execution behavior.",
        },
        "sources": [
            source(
                "FastAPI features",
                "https://fastapi.tiangolo.com/features/",
                "official",
                "FASTAPI-OPENAPI",
            ),
            source(
                "FastAPI async guidance",
                "https://fastapi.tiangolo.com/async/",
                "official",
                "FASTAPI-ASYNC",
            ),
        ],
        "related": ["domain.backend-api", "decision.request-vs-background-job"],
    },
}


def parse_frontmatter(path: Path) -> dict[str, Any]:
    text = path.read_text(encoding="utf-8")
    parts = text.split("---", 2)
    if len(parts) != 3:
        raise ValueError(f"{path} has invalid frontmatter")
    metadata = yaml.safe_load(parts[1])
    if not isinstance(metadata, dict):
        raise ValueError(f"{path} frontmatter is not a mapping")
    return metadata


def decision_body(spec: dict[str, Any]) -> str:
    option_names = ", ".join(item[0] for item in spec["options"])
    options = []
    for name, fit, avoid, cost, failure in spec["options"]:
        options.append(
            "\n".join(
                (
                    f"### {name}",
                    "",
                    f"- Fit: {fit}",
                    f"- Avoid: {avoid}",
                    f"- Cost: {cost}",
                    f"- Failure: {failure}",
                )
            )
        )
    claims = "\n".join(
        f"- {claim_id}: {claim}" for claim_id, claim in spec["claims"].items()
    )
    return f"""# {spec["title"]}

## Problem and intent

{spec["problem"]}

## Mechanism

{spec["mechanism"]}

## Options

{chr(10).join(options)}

## Fit when

At least one named option fits a measured quality scenario and the team can own its
required failure and recovery behavior.

## Avoid when

The choice is driven only by a technology name, hypothetical scale, or a problem
already solved by the current design.

## Required capabilities

{spec["required"]}

## Benefits

{spec["benefits"]}

## Costs and liabilities

{spec["costs"]}

## Failure modes

{spec["failures"]}

## Alternatives

Compare the current design and the named options—{option_names}—against the same
quality scenarios; do not compare feature lists without operating consequences.

## Migration and exit

{spec["migration"]}

## Evidence to inspect

{spec["evidence"]}

## Evidence that changes the recommendation

{spec["changes"]}

## Quality trade-offs

{spec["tradeoffs"]}

## Claim map

{claims}

## Volatile facts

Product versions, protocol/library support, service limits, pricing, licensing, and
security advisories must be rechecked in the cited official sources at decision time.
The mechanisms and decision criteria above are maintained separately from those facts.
"""


def concept_body(spec: dict[str, Any], kind: str) -> str:
    claims = "\n".join(
        f"- {claim_id}: {claim}" for claim_id, claim in spec["claims"].items()
    )
    specific = ""
    if kind in {"architecture-style", "pattern"}:
        specific = f"""## Operating model

{spec["operating"]}

"""
    elif kind == "technology-profile":
        specific = f"""## Operating model

{spec["operating"]}

## Capability boundaries

{spec["capabilities"]}

"""
    return f"""# {spec["title"]}

## Problem and intent

{spec["problem"]}

## Mechanism

{spec["mechanism"]}

{specific}## Fit when

{spec["fit"]}

## Avoid when

{spec["avoid"]}

## Required capabilities

{spec["required"]}

## Benefits

{spec["benefits"]}

## Costs and liabilities

{spec["costs"]}

## Failure modes

{spec["failures"]}

## Alternatives

{spec["alternatives"]}

## Migration and exit

{spec["migration"]}

## Evidence to inspect

{spec["evidence"]}

## Evidence that changes the recommendation

{spec["changes"]}

## Quality trade-offs

{spec["tradeoffs"]}

## Claim map

{claims}

## Volatile facts

Runtime versions, limits, compatibility, security advisories, pricing, and licensing
must be confirmed from the cited official source at decision time. The stable operating
mechanism remains distinct from those current facts.
"""


def write_entry(relative: Path, spec: dict[str, Any]) -> None:
    path = KNOWLEDGE / relative
    metadata = parse_frontmatter(path)
    metadata["version"] = "2.0.0"
    metadata["status"] = "active"
    metadata["maturity"] = "golden"
    metadata["curation"] = {
        "method": "assisted-reviewed",
        "reviewer": "Hengmu review",
        "reviewed_at": REVIEW_DATE,
    }
    metadata["related"] = spec["related"]
    metadata["last_reviewed"] = REVIEW_DATE
    metadata["sources"] = spec["sources"]
    body = (
        decision_body(spec)
        if metadata["kind"] == "decision-guide"
        else concept_body(spec, str(metadata["kind"]))
    )
    frontmatter = yaml.safe_dump(
        metadata,
        sort_keys=False,
        allow_unicode=True,
        width=100,
    ).strip()
    path.write_text(f"---\n{frontmatter}\n---\n\n{body}", encoding="utf-8")


def main() -> int:
    for name, spec in DECISIONS.items():
        write_entry(Path("decision-guides") / f"{name}.md", spec)
    for relative, spec in CONCEPTS.items():
        write_entry(Path(f"{relative}.md"), spec)
    print(f"Curated {len(DECISIONS) + len(CONCEPTS)} golden knowledge entries.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
