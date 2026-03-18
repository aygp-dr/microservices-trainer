"""Microservices Architecture Trainer — learn microservices through lessons, quizzes, and diagrams."""
import hashlib
import json
import os
import sqlite3
import uuid
from datetime import datetime, timezone

from flask import Flask, g, jsonify, make_response, redirect, render_template_string, request, url_for

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "dev-key-change-in-production")

DB_PATH = os.environ.get("DB_PATH", "data/app.db")

# ---------------------------------------------------------------------------
# Lesson content
# ---------------------------------------------------------------------------

LESSONS = [
    {
        "id": "what-are-microservices",
        "title": "What Are Microservices?",
        "order": 1,
        "content": """\
Microservices architecture is a design approach where an application is composed of **small,
independent services** that communicate over well-defined APIs.

### Key Characteristics

- **Single Responsibility** — each service does one thing well
- **Independently Deployable** — deploy one service without redeploying others
- **Decentralized Data** — each service owns its own data store
- **Technology Agnostic** — services can use different languages/frameworks
- **Fault Isolation** — a failure in one service doesn't cascade to others

### Monolith vs Microservices

In a monolithic application all features live in a single deployable unit. As the
codebase grows, deployments become risky, scaling is coarse-grained, and teams step
on each other. Microservices trade that coupling for network complexity, but gain
independent scaling, deployment, and team autonomy.

### When to Use Microservices

Microservices shine when you need independent scaling, polyglot persistence, or
autonomous team ownership. They add operational overhead, so small projects may be
better served by a well-structured monolith.""",
        "diagram": r"""
┌─────────────────────────────────────────────┐
│              MONOLITH                       │
│  ┌─────┐ ┌─────┐ ┌─────┐ ┌─────┐          │
│  │ UI  │ │Users│ │Order│ │ Pay │          │
│  └─────┘ └─────┘ └─────┘ └─────┘          │
│           Single Database                   │
└─────────────────────────────────────────────┘

                    ↓ decompose

┌──────┐  ┌──────┐  ┌──────┐  ┌──────┐
│ UI   │  │Users │  │Order │  │ Pay  │
│  GW  │──│ Svc  │  │ Svc  │  │ Svc  │
└──────┘  └──┬───┘  └──┬───┘  └──┬───┘
             │         │         │
           [DB1]     [DB2]     [DB3]
""",
        "quiz": [
            {
                "question": "What is a key characteristic of microservices?",
                "options": [
                    "All services share a single database",
                    "Each service is independently deployable",
                    "Services must use the same programming language",
                    "One team manages all services",
                ],
                "answer": 1,
            },
            {
                "question": "What is a trade-off when moving from monolith to microservices?",
                "options": [
                    "Simpler networking",
                    "Less operational overhead",
                    "Increased network complexity",
                    "Faster initial development",
                ],
                "answer": 2,
            },
            {
                "question": "When are microservices most beneficial?",
                "options": [
                    "Small projects with a single developer",
                    "When you need independent scaling and team autonomy",
                    "When you want the simplest possible architecture",
                    "When all components must share the same database",
                ],
                "answer": 1,
            },
        ],
    },
    {
        "id": "service-decomposition",
        "title": "Service Decomposition",
        "order": 2,
        "content": """\
Service decomposition is the process of breaking a monolith into well-scoped microservices.

### Decomposition Strategies

- **By Business Capability** — align services with business functions (payments, inventory, shipping)
- **By Subdomain (DDD)** — use Domain-Driven Design bounded contexts to find service boundaries
- **By Use Case** — group operations that change together

### Bounded Contexts

A bounded context defines the boundary within which a particular domain model applies.
The same word ("Order") can mean different things in different contexts (sales vs warehouse).
Each bounded context gets its own service.

### Strangler Fig Pattern

When migrating a monolith, the Strangler Fig pattern incrementally replaces pieces:
1. Identify a seam in the monolith
2. Build the new service behind a facade
3. Route traffic to the new service
4. Remove the old code once the new service is stable

### Common Pitfalls

- **Too fine-grained** — "nano-services" create excessive network overhead
- **Shared databases** — coupling services through a common database defeats the purpose
- **Synchronous chains** — long chains of sync calls create fragile dependencies""",
        "diagram": r"""
    ┌─────────── Monolith ───────────┐
    │ ┌───────┐ ┌───────┐ ┌───────┐ │
    │ │Catalog│ │Orders │ │Billing│ │
    │ └───┬───┘ └───┬───┘ └───┬───┘ │
    │     └─────────┴─────────┘     │
    │         Shared Database       │
    └───────────────────────────────┘
                  │
        Strangler Fig Pattern
                  ↓
    ┌────────┐ ┌────────┐ ┌────────┐
    │Catalog │ │Orders  │ │Billing │
    │Service │ │Service │ │Service │
    └───┬────┘ └───┬────┘ └───┬────┘
      [DB1]      [DB2]      [DB3]
""",
        "quiz": [
            {
                "question": "What is the Strangler Fig pattern used for?",
                "options": [
                    "Building a new application from scratch",
                    "Incrementally migrating a monolith to microservices",
                    "Load balancing across services",
                    "Database sharding",
                ],
                "answer": 1,
            },
            {
                "question": "What is a bounded context in DDD?",
                "options": [
                    "A security boundary for API access",
                    "A deployment region for services",
                    "A boundary within which a domain model applies",
                    "A rate limit for service calls",
                ],
                "answer": 2,
            },
            {
                "question": "Which is a common decomposition pitfall?",
                "options": [
                    "Services owning their own databases",
                    "Using bounded contexts for service boundaries",
                    "Sharing a database between services",
                    "Aligning services with business capabilities",
                ],
                "answer": 2,
            },
        ],
    },
    {
        "id": "api-gateway",
        "title": "API Gateway Pattern",
        "order": 3,
        "content": """\
An API Gateway is a single entry point for all client requests in a microservices architecture.

### Responsibilities

- **Request Routing** — routes requests to the appropriate backend service
- **Authentication & Authorization** — validates tokens/credentials before forwarding
- **Rate Limiting** — protects services from excessive traffic
- **Response Aggregation** — combines responses from multiple services into one
- **Protocol Translation** — e.g., REST to gRPC

### Backend for Frontend (BFF)

Instead of a single gateway, the BFF pattern creates a dedicated gateway per client type
(web, mobile, IoT). Each BFF tailors the API to the specific needs of its client.

### Popular Implementations

- **Kong** — open-source, plugin-based
- **AWS API Gateway** — managed, serverless-friendly
- **Envoy** — high-performance L7 proxy used in service meshes
- **NGINX** — widely used reverse proxy with gateway capabilities

### Considerations

- The gateway can become a single point of failure — deploy it with redundancy
- Avoid putting business logic in the gateway — keep it thin
- Monitor gateway latency; it adds a network hop to every request""",
        "diagram": r"""
  ┌──────┐  ┌──────┐  ┌──────┐
  │Mobile│  │ Web  │  │ IoT  │
  └──┬───┘  └──┬───┘  └──┬───┘
     │         │         │
     └─────────┼─────────┘
               │
        ┌──────▼──────┐
        │ API Gateway │
        │  - Auth     │
        │  - Rate Lim │
        │  - Routing  │
        └──────┬──────┘
     ┌─────────┼─────────┐
     ▼         ▼         ▼
  ┌──────┐ ┌──────┐ ┌──────┐
  │User  │ │Order │ │Stock │
  │ Svc  │ │ Svc  │ │ Svc  │
  └──────┘ └──────┘ └──────┘
""",
        "quiz": [
            {
                "question": "What is the primary role of an API Gateway?",
                "options": [
                    "Store data for all microservices",
                    "Provide a single entry point for client requests",
                    "Run background batch jobs",
                    "Replace the need for service discovery",
                ],
                "answer": 1,
            },
            {
                "question": "What is the Backend for Frontend (BFF) pattern?",
                "options": [
                    "A pattern where all backends share one frontend",
                    "A single gateway for all client types",
                    "A dedicated gateway per client type (web, mobile, etc.)",
                    "A pattern for database federation",
                ],
                "answer": 2,
            },
            {
                "question": "What should you avoid putting in an API Gateway?",
                "options": [
                    "Authentication logic",
                    "Rate limiting rules",
                    "Business logic",
                    "Routing configuration",
                ],
                "answer": 2,
            },
        ],
    },
    {
        "id": "service-discovery",
        "title": "Service Discovery",
        "order": 4,
        "content": """\
In a microservices architecture, services need to find each other. Service discovery
automates this process so services don't rely on hard-coded addresses.

### Client-Side Discovery

The client queries a **service registry** to get available instances, then picks one
(using a load-balancing strategy like round-robin) and calls it directly.

### Server-Side Discovery

The client sends requests to a **load balancer** or router, which queries the registry
and forwards the request to an available instance. The client doesn't need to know
about the registry.

### Service Registry

A database of available service instances. Services register on startup and
deregister on shutdown. The registry performs health checks to remove unhealthy instances.

- **Consul** — HashiCorp's service mesh with built-in discovery
- **etcd** — distributed key-value store used by Kubernetes
- **ZooKeeper** — Apache's coordination service
- **Eureka** — Netflix's service registry for Java (Spring Cloud)

### DNS-Based Discovery

Kubernetes uses DNS for service discovery. Each service gets a DNS name
(`my-service.namespace.svc.cluster.local`) that resolves to the service's cluster IP.""",
        "diagram": r"""
  Client-Side Discovery:

  ┌────────┐  1.query   ┌──────────┐
  │ Client ├───────────►│ Service  │
  │        │◄───────────┤ Registry │
  └───┬────┘  2.respond └──────────┘
      │                  ▲  ▲  ▲
      │ 3.call      register│  │
      ▼                  │  │  │
  ┌──────┐ ┌──────┐ ┌──────┐
  │Svc A │ │Svc A │ │Svc B │
  │inst 1│ │inst 2│ │inst 1│
  └──────┘ └──────┘ └──────┘

  Server-Side Discovery:

  ┌────────┐         ┌────────────┐
  │ Client ├────────►│Load Balancer│
  └────────┘         └─────┬──────┘
                           │query
                    ┌──────▼──────┐
                    │  Registry   │
                    └─────────────┘
""",
        "quiz": [
            {
                "question": "In client-side discovery, who queries the service registry?",
                "options": [
                    "The load balancer",
                    "The service itself",
                    "The client",
                    "The API gateway",
                ],
                "answer": 2,
            },
            {
                "question": "What does a service registry store?",
                "options": [
                    "Application source code",
                    "Available service instances and their locations",
                    "Database schemas",
                    "API documentation",
                ],
                "answer": 1,
            },
            {
                "question": "How does Kubernetes handle service discovery?",
                "options": [
                    "Manual configuration files",
                    "Client-side library (Eureka)",
                    "DNS-based discovery",
                    "Shared environment variables only",
                ],
                "answer": 2,
            },
        ],
    },
    {
        "id": "circuit-breaker",
        "title": "Circuit Breaker Pattern",
        "order": 5,
        "content": """\
The Circuit Breaker pattern prevents cascading failures by stopping requests to a
failing service, giving it time to recover.

### States

- **Closed** — requests flow normally. Failures are counted.
- **Open** — requests are immediately rejected (fail fast). A timer runs.
- **Half-Open** — after the timer, a limited number of test requests are allowed through.
  If they succeed, the circuit closes. If they fail, it reopens.

### Configuration Parameters

- **Failure Threshold** — number of failures before opening (e.g., 5 failures in 60 seconds)
- **Timeout** — how long the circuit stays open before trying half-open
- **Success Threshold** — number of successes in half-open needed to close

### Fallback Strategies

When the circuit is open, provide a degraded response:
- Return cached data
- Return a default value
- Queue the request for later processing
- Show a user-friendly error message

### Implementations

- **Hystrix** (Netflix, now in maintenance) — the pattern's popularizer
- **Resilience4j** — modern Java library
- **Polly** — .NET resilience library
- **pybreaker** — Python implementation""",
        "diagram": r"""
             ┌──────────────────────┐
             │       CLOSED         │
             │  (requests flow      │
             │   normally)          │
             └──────┬───────────────┘
                    │ failure threshold
                    │ exceeded
                    ▼
             ┌──────────────────────┐
             │        OPEN          │
             │  (requests rejected  │──► Fallback
             │   immediately)       │    Response
             └──────┬───────────────┘
                    │ timeout expires
                    ▼
             ┌──────────────────────┐
             │     HALF-OPEN        │
             │  (test requests      │
             │   allowed)           │
             └──────┬───────┬───────┘
                    │       │
              success│     failure
                    │       │
                    ▼       ▼
               [CLOSED]  [OPEN]
""",
        "quiz": [
            {
                "question": "What happens when a circuit breaker is in the Open state?",
                "options": [
                    "Requests flow normally",
                    "Requests are queued for later",
                    "Requests are immediately rejected",
                    "The service is restarted",
                ],
                "answer": 2,
            },
            {
                "question": "What is the purpose of the Half-Open state?",
                "options": [
                    "To reject half of all requests",
                    "To test if the failing service has recovered",
                    "To double the timeout period",
                    "To switch to a backup service permanently",
                ],
                "answer": 1,
            },
            {
                "question": "Which is NOT a typical fallback strategy?",
                "options": [
                    "Return cached data",
                    "Return a default value",
                    "Restart the database server",
                    "Show a user-friendly error message",
                ],
                "answer": 2,
            },
        ],
    },
    {
        "id": "saga-pattern",
        "title": "Saga Pattern",
        "order": 6,
        "content": """\
The Saga pattern manages distributed transactions across multiple microservices without
using a traditional two-phase commit (2PC).

### The Problem

In a monolith, a single database transaction ensures consistency. In microservices, each
service has its own database. A business operation spanning multiple services needs a way
to maintain consistency.

### How Sagas Work

A saga is a sequence of local transactions. Each service performs its transaction and
publishes an event. If a step fails, **compensating transactions** undo the previous steps.

### Choreography vs Orchestration

**Choreography** — each service listens for events and decides what to do next.
No central coordinator. Simple for small flows, but hard to track for complex ones.

**Orchestration** — a central orchestrator tells each service what to do and when.
Easier to understand and debug, but the orchestrator is a single point of control.

### Compensating Transactions

If step 3 fails after steps 1 and 2 succeeded, compensating transactions reverse them:
- Step 2 compensation: refund payment
- Step 1 compensation: cancel order

### Design Considerations

- Sagas provide **eventual consistency**, not immediate consistency
- Compensating transactions must be **idempotent**
- Consider a **saga log** to track progress and enable recovery""",
        "diagram": r"""
  Choreography Saga:

  ┌───────┐  event  ┌───────┐  event  ┌───────┐
  │Order  ├────────►│Payment├────────►│Ship   │
  │Service│         │Service│         │Service│
  └───────┘         └───────┘         └───────┘
       ◄─── compensate ◄─── compensate

  Orchestration Saga:

            ┌──────────────┐
            │    Saga      │
            │ Orchestrator │
            └──┬───┬───┬───┘
               │   │   │
          step1│ step2│ step3
               │   │   │
               ▼   ▼   ▼
            ┌──┐ ┌──┐ ┌──┐
            │O │ │P │ │S │
            └──┘ └──┘ └──┘
""",
        "quiz": [
            {
                "question": "Why can't microservices use traditional database transactions?",
                "options": [
                    "Databases don't support transactions",
                    "Each service has its own database",
                    "Transactions are too fast",
                    "Network latency is too low",
                ],
                "answer": 1,
            },
            {
                "question": "What is a compensating transaction?",
                "options": [
                    "A faster version of a normal transaction",
                    "A transaction that undoes the effect of a previous step",
                    "A transaction that runs in parallel",
                    "A transaction that skips validation",
                ],
                "answer": 1,
            },
            {
                "question": "What is the main difference between choreography and orchestration?",
                "options": [
                    "Choreography is faster",
                    "Orchestration doesn't use events",
                    "Choreography has no central coordinator; orchestration does",
                    "Orchestration doesn't support compensating transactions",
                ],
                "answer": 2,
            },
        ],
    },
    {
        "id": "event-sourcing",
        "title": "Event Sourcing",
        "order": 7,
        "content": """\
Event Sourcing stores state as a sequence of **immutable events** rather than overwriting
current state in a database.

### Core Idea

Instead of storing "Account balance = $500", store every event:
1. AccountCreated(amount=0)
2. MoneyDeposited(amount=1000)
3. MoneyWithdrawn(amount=500)

The current state is derived by replaying events from the beginning.

### Benefits

- **Complete Audit Trail** — every change is recorded
- **Temporal Queries** — reconstruct state at any point in time
- **Event Replay** — rebuild read models or fix bugs by replaying events
- **Decoupling** — other services can subscribe to the event stream

### Challenges

- **Event Schema Evolution** — events are immutable, but their schema may need to change
- **Storage Growth** — the event store grows indefinitely
- **Snapshots** — periodically save current state to avoid replaying all events
- **Eventual Consistency** — read models may lag behind the event stream

### Event Store

An append-only log of events. Each event has:
- Event type, timestamp, aggregate ID, payload
- Events are ordered within an aggregate (e.g., a specific order or account)""",
        "diagram": r"""
  Traditional (State):     Event Sourcing:

  ┌──────────┐             ┌──────────────────────┐
  │ Account  │             │     Event Store       │
  │          │             │                       │
  │ bal: 500 │             │ 1. Created(0)         │
  │          │             │ 2. Deposit(1000)      │
  └──────────┘             │ 3. Withdraw(500)      │
                           │        ↓ replay       │
   Current state           │ Current: bal=500      │
   is mutable              └──────────────────────┘

  Event Flow:

  Command ──► Aggregate ──► Event ──► Event Store
                                  │
                                  ├──► Projection A
                                  └──► Projection B
""",
        "quiz": [
            {
                "question": "How is current state determined in event sourcing?",
                "options": [
                    "By reading the latest row in a database table",
                    "By replaying all events from the event store",
                    "By querying a cache layer",
                    "By asking another service",
                ],
                "answer": 1,
            },
            {
                "question": "What is a snapshot in event sourcing?",
                "options": [
                    "A backup of the entire database",
                    "A periodically saved current state to avoid full replay",
                    "A copy of the event store schema",
                    "A frozen version of the API",
                ],
                "answer": 1,
            },
            {
                "question": "Which is a key benefit of event sourcing?",
                "options": [
                    "Simpler database schema",
                    "Less storage usage",
                    "Complete audit trail of all changes",
                    "Immediate consistency everywhere",
                ],
                "answer": 2,
            },
        ],
    },
    {
        "id": "cqrs",
        "title": "CQRS (Command Query Responsibility Segregation)",
        "order": 8,
        "content": """\
CQRS separates **read operations** (queries) from **write operations** (commands) into
different models, often with different data stores.

### Why Separate Reads and Writes?

- Read and write workloads often have very different characteristics
- Read models can be denormalized for fast queries
- Write models can be normalized for data integrity
- Each side can be scaled independently

### How It Works

- **Command Side** — handles create, update, delete operations. Validates business rules.
  Uses a normalized data model optimized for writes.
- **Query Side** — handles read operations. Uses denormalized views/projections optimized
  for specific query patterns.

### CQRS + Event Sourcing

CQRS pairs naturally with Event Sourcing:
- Commands produce events stored in the event store
- Events are projected into read-optimized views
- Multiple read models can be built from the same events

### When to Use CQRS

- High read-to-write ratio (read-heavy applications)
- Complex domain models where read and write shapes differ significantly
- When you need different scaling strategies for reads vs writes

### When NOT to Use CQRS

- Simple CRUD applications — the added complexity isn't justified
- When eventual consistency between read and write models is unacceptable""",
        "diagram": r"""
                    ┌────────┐
                    │ Client │
                    └───┬────┘
               ┌────────┴────────┐
               ▼                 ▼
        ┌─────────────┐  ┌─────────────┐
        │  Command    │  │   Query     │
        │  (Write)    │  │   (Read)    │
        │  Handler    │  │   Handler   │
        └──────┬──────┘  └──────┬──────┘
               │                │
               ▼                ▼
        ┌─────────────┐  ┌─────────────┐
        │ Write Model │  │ Read Model  │
        │ (normalized)│  │(denormalized│
        └──────┬──────┘  └─────────────┘
               │ events        ▲
               └───────────────┘
                  projection
""",
        "quiz": [
            {
                "question": "What does CQRS separate?",
                "options": [
                    "Frontend and backend code",
                    "Read operations from write operations",
                    "Development and production environments",
                    "Authentication from authorization",
                ],
                "answer": 1,
            },
            {
                "question": "Why is the read model typically denormalized?",
                "options": [
                    "To save storage space",
                    "To enforce business rules",
                    "To optimize for fast query performance",
                    "To support transactions",
                ],
                "answer": 2,
            },
            {
                "question": "When should you NOT use CQRS?",
                "options": [
                    "When read and write workloads differ significantly",
                    "When you need independent scaling of reads and writes",
                    "For simple CRUD applications",
                    "When using event sourcing",
                ],
                "answer": 2,
            },
        ],
    },
    {
        "id": "observability",
        "title": "Observability",
        "order": 9,
        "content": """\
Observability is the ability to understand a system's internal state from its external
outputs. In microservices, this is critical because a single request may traverse many services.

### Three Pillars of Observability

**1. Logs** — discrete events recorded by each service.
- Use structured logging (JSON) for machine-parseable output
- Include correlation IDs to trace requests across services
- Centralize logs with tools like ELK Stack or Loki

**2. Metrics** — numerical measurements over time.
- RED method: Rate, Errors, Duration (for request-driven services)
- USE method: Utilization, Saturation, Errors (for resources)
- Tools: Prometheus, Grafana, Datadog

**3. Distributed Traces** — track a request's path through multiple services.
- Each service adds a span to the trace
- Visualize the full request path and identify bottlenecks
- Tools: Jaeger, Zipkin, OpenTelemetry

### OpenTelemetry

OpenTelemetry is the emerging standard for instrumentation. It provides vendor-neutral
APIs and SDKs for logs, metrics, and traces. Instrument once, export to any backend.

### Health Checks

Every service should expose health check endpoints:
- **Liveness** — is the process running? (`/healthz`)
- **Readiness** — can it accept traffic? (`/readyz`)""",
        "diagram": r"""
  Request Flow with Observability:

  Client ──► API GW ──► Svc A ──► Svc B ──► Svc C
    │           │          │         │         │
    │         trace      trace     trace     trace
    │         span       span      span      span
    │           │          │         │         │
    ▼           ▼          ▼         ▼         ▼
  ┌─────────────────────────────────────────────┐
  │            Observability Platform           │
  │  ┌──────┐  ┌───────┐  ┌───────────────┐    │
  │  │ Logs │  │Metrics│  │  Traces       │    │
  │  │(Loki)│  │(Prom) │  │  (Jaeger)     │    │
  │  └──────┘  └───────┘  └───────────────┘    │
  │         ┌──────────────┐                    │
  │         │   Grafana    │ ◄── dashboards     │
  │         └──────────────┘                    │
  └─────────────────────────────────────────────┘
""",
        "quiz": [
            {
                "question": "What are the three pillars of observability?",
                "options": [
                    "CPU, Memory, Disk",
                    "Logs, Metrics, Traces",
                    "Auth, Rate Limiting, Caching",
                    "Unit Tests, Integration Tests, E2E Tests",
                ],
                "answer": 1,
            },
            {
                "question": "What is a correlation ID used for?",
                "options": [
                    "Authenticating users across services",
                    "Tracing a request across multiple services",
                    "Encrypting inter-service communication",
                    "Load balancing between instances",
                ],
                "answer": 1,
            },
            {
                "question": "What does OpenTelemetry provide?",
                "options": [
                    "A specific monitoring backend",
                    "Vendor-neutral APIs for logs, metrics, and traces",
                    "A replacement for API gateways",
                    "A service mesh implementation",
                ],
                "answer": 1,
            },
        ],
    },
    {
        "id": "deployment-strategies",
        "title": "Deployment Strategies",
        "order": 10,
        "content": """\
Deployment strategies determine how new versions of a service are rolled out to production.

### Blue-Green Deployment

Run two identical environments: Blue (current) and Green (new). Switch traffic from
Blue to Green once the new version is verified. Instant rollback by switching back.

### Canary Deployment

Release the new version to a small subset of users (e.g., 5%). Monitor for errors.
Gradually increase traffic (5% → 25% → 50% → 100%). Roll back if issues arise.

### Rolling Deployment

Replace instances one at a time. At any point, some instances run the old version and
some the new. No extra infrastructure needed, but rollback is slower.

### A/B Testing

Similar to canary, but routes users based on criteria (geography, user group).
Used for feature validation and business metrics, not just technical health.

### Feature Flags

Decouple deployment from release. Deploy code with features hidden behind flags.
Enable features for specific users or percentages without redeploying.

### Infrastructure as Code

- **Docker** — containerize each service for consistent environments
- **Kubernetes** — orchestrate containers with built-in rolling updates
- **Terraform** — provision infrastructure declaratively
- **CI/CD Pipelines** — automate build, test, and deploy (GitHub Actions, GitLab CI)""",
        "diagram": r"""
  Blue-Green:
  ┌──────┐      ┌──────┐
  │ Blue │ ←──  │Router│ ──→ ┌──────┐
  │(curr)│      └──────┘     │Green │
  └──────┘         ↑switch   │(new) │
                             └──────┘

  Canary:
  ┌──────┐  95%
  │ v1   │◄────┐
  │      │     │   ┌──────┐
  └──────┘     ├───│Router│
  ┌──────┐     │   └──────┘
  │ v2   │◄────┘
  │canary│  5%
  └──────┘

  Rolling:
  [v1] [v1] [v1] [v1]   start
  [v2] [v1] [v1] [v1]   step 1
  [v2] [v2] [v1] [v1]   step 2
  [v2] [v2] [v2] [v1]   step 3
  [v2] [v2] [v2] [v2]   done
""",
        "quiz": [
            {
                "question": "What is the main advantage of blue-green deployment?",
                "options": [
                    "Uses less infrastructure",
                    "Instant rollback by switching traffic back",
                    "No downtime ever, under any circumstance",
                    "Automatically fixes bugs in the new version",
                ],
                "answer": 1,
            },
            {
                "question": "How does canary deployment work?",
                "options": [
                    "Deploy to all users at once",
                    "Release to a small subset, then gradually increase",
                    "Run two full environments simultaneously",
                    "Deploy only during off-peak hours",
                ],
                "answer": 1,
            },
            {
                "question": "What do feature flags allow you to do?",
                "options": [
                    "Speed up CI/CD pipelines",
                    "Decouple deployment from feature release",
                    "Eliminate the need for testing",
                    "Automatically scale services",
                ],
                "answer": 1,
            },
        ],
    },
]

LESSON_MAP = {lesson["id"]: lesson for lesson in LESSONS}

# ---------------------------------------------------------------------------
# Database helpers
# ---------------------------------------------------------------------------


def get_db():
    if "db" not in g:
        os.makedirs(os.path.dirname(DB_PATH) or ".", exist_ok=True)
        g.db = sqlite3.connect(DB_PATH)
        g.db.row_factory = sqlite3.Row
        _init_db(g.db)
    return g.db


def _init_db(db):
    db.executescript("""
        CREATE TABLE IF NOT EXISTS progress (
            session_id TEXT NOT NULL,
            lesson_id TEXT NOT NULL,
            completed INTEGER DEFAULT 0,
            quiz_score INTEGER DEFAULT 0,
            quiz_total INTEGER DEFAULT 0,
            completed_at TIMESTAMP,
            PRIMARY KEY (session_id, lesson_id)
        );
        CREATE TABLE IF NOT EXISTS certificates (
            id TEXT PRIMARY KEY,
            session_id TEXT NOT NULL,
            student_name TEXT NOT NULL,
            completed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            total_score INTEGER DEFAULT 0,
            total_possible INTEGER DEFAULT 0
        );
    """)


@app.teardown_appcontext
def close_db(e=None):
    db = g.pop("db", None)
    if db:
        db.close()


def get_session_id():
    session_id = request.cookies.get("session_id")
    if not session_id:
        session_id = uuid.uuid4().hex
    return session_id


def set_session_cookie(response, session_id):
    response.set_cookie("session_id", session_id, max_age=60 * 60 * 24 * 365, httponly=True, samesite="Lax")
    return response


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------


@app.route("/")
def index():
    session_id = get_session_id()
    db = get_db()
    rows = db.execute("SELECT lesson_id, completed, quiz_score, quiz_total FROM progress WHERE session_id = ?", (session_id,)).fetchall()
    progress = {r["lesson_id"]: dict(r) for r in rows}
    completed_count = sum(1 for r in rows if r["completed"])
    total_lessons = len(LESSONS)
    resp = make_response(render_template_string(INDEX_TEMPLATE, lessons=LESSONS, progress=progress, completed_count=completed_count, total_lessons=total_lessons))
    return set_session_cookie(resp, session_id)


@app.route("/lesson/<lesson_id>")
def lesson(lesson_id):
    if lesson_id not in LESSON_MAP:
        return redirect(url_for("index"))
    session_id = get_session_id()
    db = get_db()
    row = db.execute("SELECT * FROM progress WHERE session_id = ? AND lesson_id = ?", (session_id, lesson_id)).fetchone()
    lesson_data = LESSON_MAP[lesson_id]
    prev_lesson = next((l for l in LESSONS if l["order"] == lesson_data["order"] - 1), None)
    next_lesson = next((l for l in LESSONS if l["order"] == lesson_data["order"] + 1), None)
    resp = make_response(render_template_string(
        LESSON_TEMPLATE,
        lesson=lesson_data,
        progress=dict(row) if row else None,
        prev_lesson=prev_lesson,
        next_lesson=next_lesson,
    ))
    return set_session_cookie(resp, session_id)


@app.route("/quiz/<lesson_id>", methods=["POST"])
def submit_quiz(lesson_id):
    if lesson_id not in LESSON_MAP:
        return redirect(url_for("index"))
    session_id = get_session_id()
    lesson_data = LESSON_MAP[lesson_id]
    quiz = lesson_data["quiz"]
    score = 0
    total = len(quiz)
    for i, q in enumerate(quiz):
        submitted = request.form.get(f"q{i}")
        if submitted is not None and int(submitted) == q["answer"]:
            score += 1
    db = get_db()
    now = datetime.now(timezone.utc).isoformat()
    db.execute(
        """INSERT INTO progress (session_id, lesson_id, completed, quiz_score, quiz_total, completed_at)
           VALUES (?, ?, 1, ?, ?, ?)
           ON CONFLICT(session_id, lesson_id) DO UPDATE SET
           completed=1, quiz_score=MAX(quiz_score, excluded.quiz_score), quiz_total=?, completed_at=?""",
        (session_id, lesson_id, score, total, now, total, now),
    )
    db.commit()
    resp = make_response(render_template_string(
        QUIZ_RESULT_TEMPLATE,
        lesson=lesson_data,
        score=score,
        total=total,
        quiz=quiz,
        submitted={f"q{i}": request.form.get(f"q{i}") for i in range(len(quiz))},
    ))
    return set_session_cookie(resp, session_id)


@app.route("/certificate", methods=["GET", "POST"])
def certificate():
    session_id = get_session_id()
    db = get_db()
    rows = db.execute("SELECT lesson_id, completed, quiz_score, quiz_total FROM progress WHERE session_id = ?", (session_id,)).fetchall()
    completed_ids = {r["lesson_id"] for r in rows if r["completed"]}
    all_ids = {l["id"] for l in LESSONS}
    if not all_ids.issubset(completed_ids):
        resp = make_response(redirect(url_for("index")))
        return set_session_cookie(resp, session_id)
    total_score = sum(r["quiz_score"] for r in rows)
    total_possible = sum(r["quiz_total"] for r in rows)
    if request.method == "POST":
        student_name = request.form.get("name", "").strip()
        if not student_name:
            student_name = "Anonymous Learner"
        cert_id = hashlib.sha256(f"{session_id}:{student_name}".encode()).hexdigest()[:16]
        db.execute(
            """INSERT INTO certificates (id, session_id, student_name, total_score, total_possible)
               VALUES (?, ?, ?, ?, ?)
               ON CONFLICT(id) DO UPDATE SET student_name=excluded.student_name""",
            (cert_id, session_id, student_name, total_score, total_possible),
        )
        db.commit()
        resp = make_response(redirect(url_for("view_certificate", cert_id=cert_id)))
        return set_session_cookie(resp, session_id)
    resp = make_response(render_template_string(CERT_FORM_TEMPLATE, total_score=total_score, total_possible=total_possible))
    return set_session_cookie(resp, session_id)


@app.route("/certificate/<cert_id>")
def view_certificate(cert_id):
    db = get_db()
    cert = db.execute("SELECT * FROM certificates WHERE id = ?", (cert_id,)).fetchone()
    if not cert:
        return redirect(url_for("index"))
    resp = make_response(render_template_string(CERT_VIEW_TEMPLATE, cert=dict(cert)))
    return resp


@app.route("/reset", methods=["POST"])
def reset_progress():
    session_id = get_session_id()
    db = get_db()
    db.execute("DELETE FROM progress WHERE session_id = ?", (session_id,))
    db.commit()
    resp = make_response(redirect(url_for("index")))
    return set_session_cookie(resp, session_id)


# --- API endpoints ---

@app.route("/api/progress")
def api_progress():
    session_id = get_session_id()
    db = get_db()
    rows = db.execute("SELECT lesson_id, completed, quiz_score, quiz_total FROM progress WHERE session_id = ?", (session_id,)).fetchall()
    return jsonify([dict(r) for r in rows])


@app.route("/api/lessons")
def api_lessons():
    return jsonify([{"id": l["id"], "title": l["title"], "order": l["order"]} for l in LESSONS])


@app.route("/healthz")
def healthz():
    return jsonify({"status": "ok"})


# ---------------------------------------------------------------------------
# Templates
# ---------------------------------------------------------------------------

BASE_STYLE = """
*{box-sizing:border-box;margin:0;padding:0}
body{font-family:'Segoe UI',system-ui,-apple-system,sans-serif;background:#0d1117;color:#c9d1d9;line-height:1.6}
a{color:#58a6ff;text-decoration:none}
a:hover{text-decoration:underline}
.container{max-width:900px;margin:0 auto;padding:20px}
h1{color:#58a6ff;margin-bottom:4px;font-size:1.8em}
h2{color:#58a6ff;margin:20px 0 10px;font-size:1.4em}
h3{color:#79c0ff;margin:16px 0 8px;font-size:1.15em}
.subtitle{color:#8b949e;margin-bottom:24px;font-size:0.95em}
.card{border:1px solid #30363d;border-radius:8px;padding:16px;margin:8px 0;background:#161b22}
.card:hover{border-color:#58a6ff30}
.btn{display:inline-block;padding:8px 20px;border:1px solid #30363d;background:#21262d;color:#c9d1d9;
 border-radius:6px;cursor:pointer;font-size:0.9em;transition:background 0.2s}
.btn:hover{background:#30363d;text-decoration:none}
.btn-primary{background:#238636;border-color:#2ea043;color:#fff}
.btn-primary:hover{background:#2ea043}
.btn-danger{background:#da3633;border-color:#f85149;color:#fff}
.btn-danger:hover{background:#f85149}
.progress-bar{background:#21262d;border-radius:6px;height:8px;margin:8px 0;overflow:hidden}
.progress-fill{background:#238636;height:100%;border-radius:6px;transition:width 0.5s}
.badge{display:inline-block;padding:2px 8px;border-radius:12px;font-size:0.75em;font-weight:600}
.badge-done{background:#238636;color:#fff}
.badge-pending{background:#30363d;color:#8b949e}
.lesson-content p{margin:8px 0}
.lesson-content ul,.lesson-content ol{margin:8px 0 8px 24px}
.lesson-content li{margin:4px 0}
.lesson-content strong{color:#e6edf3}
.lesson-content code{background:#1c2128;padding:2px 6px;border-radius:4px;font-size:0.9em}
pre.diagram{background:#1c2128;border:1px solid #30363d;border-radius:8px;padding:16px;
 overflow-x:auto;font-family:'Cascadia Code','Fira Code','Consolas',monospace;
 font-size:0.85em;line-height:1.4;color:#7ee787;white-space:pre}
.quiz-form label{display:block;padding:8px 12px;margin:4px 0;border:1px solid #30363d;
 border-radius:6px;cursor:pointer;transition:background 0.2s}
.quiz-form label:hover{background:#21262d}
.quiz-form input[type=radio]{margin-right:8px}
.quiz-question{margin:20px 0 8px;font-weight:600;color:#e6edf3}
.correct{border-color:#2ea043 !important;background:#2ea04315 !important}
.incorrect{border-color:#f85149 !important;background:#f8514915 !important}
.nav{display:flex;justify-content:space-between;align-items:center;margin:20px 0}
.score-display{font-size:1.5em;font-weight:700;color:#58a6ff}
input[type=text]{background:#0d1117;color:#c9d1d9;border:1px solid #30363d;border-radius:6px;
 padding:10px;width:100%;font-size:1em}
.cert-box{border:3px solid #58a6ff;border-radius:16px;padding:40px;text-align:center;
 background:#161b22;margin:20px 0}
.cert-box h2{font-size:2em;margin-bottom:16px}
.cert-box .name{font-size:1.8em;color:#7ee787;margin:20px 0;font-style:italic}
.header{display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;gap:8px}
.lesson-list{list-style:none;padding:0}
.lesson-list li{margin:0}
.lesson-link{display:flex;align-items:center;gap:12px;padding:12px 16px;border:1px solid #30363d;
 border-radius:8px;margin:6px 0;background:#161b22;transition:all 0.2s;text-decoration:none;color:#c9d1d9}
.lesson-link:hover{border-color:#58a6ff;background:#1c2128;text-decoration:none}
.lesson-num{background:#21262d;color:#58a6ff;width:32px;height:32px;border-radius:50%;
 display:flex;align-items:center;justify-content:center;font-weight:700;font-size:0.9em;flex-shrink:0}
.lesson-num.done{background:#238636;color:#fff}
@media(max-width:600px){.container{padding:12px}.cert-box{padding:20px}.cert-box .name{font-size:1.3em}}
"""

INDEX_TEMPLATE = """<!DOCTYPE html>
<html lang="en"><head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Microservices Architecture Trainer</title>
<style>""" + BASE_STYLE + """</style>
</head><body>
<div class="container">
<div class="header">
<div>
<h1>Microservices Architecture Trainer</h1>
<p class="subtitle">Learn microservices patterns through interactive lessons and quizzes</p>
</div>
{% if completed_count > 0 %}
<form method="POST" action="/reset" onsubmit="return confirm('Reset all progress?')">
<button type="submit" class="btn btn-danger">Reset Progress</button>
</form>
{% endif %}
</div>

<div class="card">
<div style="display:flex;justify-content:space-between;align-items:center">
<span>Progress: {{ completed_count }} / {{ total_lessons }} lessons completed</span>
<span class="score-display">{{ (completed_count * 100 / total_lessons)|int }}%</span>
</div>
<div class="progress-bar">
<div class="progress-fill" style="width:{{ (completed_count * 100 / total_lessons)|int }}%"></div>
</div>
{% if completed_count == total_lessons %}
<div style="margin-top:12px;text-align:center">
<a href="/certificate" class="btn btn-primary" style="font-size:1.1em;padding:12px 32px">
  Get Your Certificate
</a>
</div>
{% endif %}
</div>

<h2>Lessons</h2>
<ul class="lesson-list">
{% for lesson in lessons %}
<li>
<a href="/lesson/{{ lesson.id }}" class="lesson-link">
<span class="lesson-num {{ 'done' if progress.get(lesson.id, {}).get('completed') }}">{{ lesson.order }}</span>
<span style="flex:1">
<strong>{{ lesson.title }}</strong>
{% if progress.get(lesson.id, {}).get('completed') %}
<br><span style="color:#8b949e;font-size:0.85em">
  Score: {{ progress[lesson.id].quiz_score }}/{{ progress[lesson.id].quiz_total }}
</span>
{% endif %}
</span>
{% if progress.get(lesson.id, {}).get('completed') %}
<span class="badge badge-done">Completed</span>
{% else %}
<span class="badge badge-pending">Pending</span>
{% endif %}
</a>
</li>
{% endfor %}
</ul>
</div></body></html>"""

LESSON_TEMPLATE = """<!DOCTYPE html>
<html lang="en"><head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{{ lesson.title }} — Microservices Trainer</title>
<style>""" + BASE_STYLE + """</style>
</head><body>
<div class="container">
<div class="nav">
<a href="/" class="btn">&larr; All Lessons</a>
<div>
{% if prev_lesson %}<a href="/lesson/{{ prev_lesson.id }}" class="btn">&larr; Previous</a>{% endif %}
{% if next_lesson %}<a href="/lesson/{{ next_lesson.id }}" class="btn" style="margin-left:8px">Next &rarr;</a>{% endif %}
</div>
</div>

<h1>{{ lesson.order }}. {{ lesson.title }}</h1>
{% if progress and progress.completed %}
<p style="color:#2ea043;margin:8px 0">Completed — Score: {{ progress.quiz_score }}/{{ progress.quiz_total }}</p>
{% endif %}

<div class="card lesson-content" style="margin-top:16px;white-space:pre-line">
{{ lesson.content }}
</div>

<h2>Architecture Diagram</h2>
<pre class="diagram">{{ lesson.diagram }}</pre>

<h2>Quiz</h2>
{% if progress and progress.completed %}
<div class="card">
<p>You've already completed this quiz with a score of <strong>{{ progress.quiz_score }}/{{ progress.quiz_total }}</strong>.</p>
<p style="margin-top:8px;color:#8b949e">You can retake it to try for a higher score.</p>
</div>
{% endif %}
<form method="POST" action="/quiz/{{ lesson.id }}" class="quiz-form">
{% for q in lesson.quiz %}
{% set qi = loop.index0 %}
<p class="quiz-question">{{ loop.index }}. {{ q.question }}</p>
{% for opt in q.options %}
<label><input type="radio" name="q{{ qi }}" value="{{ loop.index0 }}" required> {{ opt }}</label>
{% endfor %}
{% endfor %}
<div style="margin-top:16px">
<button type="submit" class="btn btn-primary">Submit Quiz</button>
</div>
</form>

<div class="nav" style="margin-top:24px">
<a href="/" class="btn">&larr; All Lessons</a>
<div>
{% if prev_lesson %}<a href="/lesson/{{ prev_lesson.id }}" class="btn">&larr; Previous</a>{% endif %}
{% if next_lesson %}<a href="/lesson/{{ next_lesson.id }}" class="btn" style="margin-left:8px">Next &rarr;</a>{% endif %}
</div>
</div>
</div></body></html>"""

QUIZ_RESULT_TEMPLATE = """<!DOCTYPE html>
<html lang="en"><head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Quiz Results — {{ lesson.title }}</title>
<style>""" + BASE_STYLE + """</style>
</head><body>
<div class="container">
<a href="/lesson/{{ lesson.id }}" class="btn" style="margin-bottom:16px;display:inline-block">&larr; Back to Lesson</a>
<h1>Quiz Results: {{ lesson.title }}</h1>

<div class="card" style="text-align:center;margin:16px 0">
<div class="score-display" style="font-size:2.5em">{{ score }} / {{ total }}</div>
<p style="margin-top:8px;color:#8b949e">
{% if score == total %}Perfect score!
{% elif score >= total // 2 + 1 %}Good job! Review the questions you missed.
{% else %}Keep studying and try again!{% endif %}
</p>
</div>

{% for q in quiz %}
{% set sub = submitted['q' ~ loop.index0] %}
<div class="card {{ 'correct' if sub is not none and sub|int == q.answer else 'incorrect' }}">
<p class="quiz-question">{{ loop.index }}. {{ q.question }}</p>
{% for opt in q.options %}
<p style="margin:4px 0 4px 16px;{{ 'color:#2ea043;font-weight:600' if loop.index0 == q.answer else '' }}">
{{ '>' if sub is not none and sub|int == loop.index0 else ' ' }}
{{ opt }}
{% if loop.index0 == q.answer %} (correct answer){% endif %}
</p>
{% endfor %}
</div>
{% endfor %}

<div class="nav" style="margin-top:16px">
<a href="/lesson/{{ lesson.id }}" class="btn">&larr; Back to Lesson</a>
<a href="/" class="btn">All Lessons &rarr;</a>
</div>
</div></body></html>"""

CERT_FORM_TEMPLATE = """<!DOCTYPE html>
<html lang="en"><head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Get Your Certificate</title>
<style>""" + BASE_STYLE + """</style>
</head><body>
<div class="container">
<a href="/" class="btn" style="margin-bottom:16px;display:inline-block">&larr; Back</a>
<h1>Congratulations!</h1>
<p class="subtitle">You've completed all 10 lessons. Overall score: {{ total_score }}/{{ total_possible }}</p>
<div class="card" style="max-width:400px;margin:24px auto">
<form method="POST">
<label for="name" style="display:block;margin-bottom:8px;color:#e6edf3;font-weight:600">Enter your name for the certificate:</label>
<input type="text" id="name" name="name" placeholder="Your Name" required maxlength="100">
<button type="submit" class="btn btn-primary" style="width:100%;margin-top:12px">Generate Certificate</button>
</form>
</div>
</div></body></html>"""

CERT_VIEW_TEMPLATE = """<!DOCTYPE html>
<html lang="en"><head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Certificate — Microservices Trainer</title>
<style>""" + BASE_STYLE + """
@media print{body{background:#fff;color:#000}.btn{display:none}
.cert-box{border-color:#000}.cert-box h2,.cert-box h3{color:#000}
.cert-box .name{color:#006600}}
</style>
</head><body>
<div class="container">
<a href="/" class="btn" style="margin-bottom:16px;display:inline-block">&larr; Home</a>
<button onclick="window.print()" class="btn" style="margin-bottom:16px;margin-left:8px">Print Certificate</button>

<div class="cert-box">
<p style="font-size:0.9em;color:#8b949e;letter-spacing:4px;text-transform:uppercase">Certificate of Completion</p>
<h2 style="margin-top:12px">Microservices Architecture Trainer</h2>
<p style="margin:24px 0 8px;color:#8b949e">This certifies that</p>
<p class="name">{{ cert.student_name }}</p>
<p style="color:#8b949e">has successfully completed all 10 lessons on microservices architecture</p>
<p style="margin-top:8px;color:#c9d1d9">Score: <strong>{{ cert.total_score }}</strong> / {{ cert.total_possible }}</p>
<p style="margin-top:24px;color:#8b949e;font-size:0.85em">
Issued: {{ cert.completed_at[:10] if cert.completed_at|length > 10 else cert.completed_at }}<br>
Certificate ID: {{ cert.id }}
</p>
</div>
</div></body></html>"""


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 8080)), debug=True)
