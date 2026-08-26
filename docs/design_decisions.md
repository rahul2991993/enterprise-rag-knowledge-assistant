# Design Decisions and Production Considerations

## Why Hybrid Search?

Vector search is strong for semantic similarity, but enterprise queries often contain exact terms, product names, policy names, IDs, and numbers.

Hybrid search combines:

- keyword search
- vector similarity
- semantic reranking

This improves both semantic recall and exact-term retrieval.

In evaluation, the improved retrieval pipeline increased:

- Hit@1 from 78.95% to 100%
- MRR from 0.895 to 1.000
- Expected Section Hit@5 from 78.95% to 100%

## Why Metadata Filtering?

Semantic similarity alone cannot determine which document version is authoritative.

For example, both Pricing2025.pdf and Pricing2026.pdf may be highly relevant to:

"What is the current OrbitSuite pricing?"

The index therefore stores:

```text
effective_year
is_current
```

Current-version questions can then filter obsolete content before answer generation.

## Why Query Decomposition?

Some questions require information from multiple entities or sections.

Example:

```text
Compare the Starter and Enterprise OrbitSuite plans.
```

The system may retrieve each entity independently and merge the evidence before generation.

However, query decomposition introduces additional latency.

Therefore, decomposition is applied only when the query appears complex enough to require it.

## Why Conversational Query Rewriting?

Follow-up questions may contain incomplete references.

Example:

```text
User: Tell me about the Enterprise plan.
User: What is its support level?
```

The second query is rewritten to:

```text
OrbitSuite Enterprise plan support level
```

Retrieval uses the rewritten standalone query instead of the vague conversational wording.

## How Are Ambiguous Queries Handled?

Queries such as:

```text
What is the limit?
```

do not contain enough context to identify the intended policy or value.

Instead of retrieving arbitrary content and risking hallucination, the system asks for clarification.

## How Does the System Handle Missing Information?

The generation layer is instructed to answer only from retrieved evidence.

If the context does not sufficiently support the requested fact, the system returns:

```text
I could not find sufficient information in the knowledge base.
```

The prompt also distinguishes between:

```text
absence of evidence
```

and:

```text
explicit negative evidence
```

For example:

- Netflix is not mentioned → insufficient information
- personal streaming subscriptions are explicitly non-reimbursable → answer "No" to a reimbursement question

## How Would This Scale From 10K to 10M Documents?

For approximately 10K documents:

- one Azure AI Search index may be sufficient
- batch or event-driven ingestion can be relatively simple
- embeddings can be generated asynchronously
- one application service can handle normal query traffic

For approximately 10M documents:

- separate ingestion and serving workloads
- queue-based ingestion
- parallel embedding workers
- incremental indexing
- document change detection
- Azure AI Search replica/partition scaling
- metadata partitioning where useful
- batch embedding
- backpressure and rate-limit handling
- dead-letter queues
- aggressive observability

The online query path should not depend on bulk indexing workloads.

## Document-Level Access Control

In production, retrieval must respect the requesting user's permissions.

Each indexed chunk can contain metadata such as:

```text
allowed_users
allowed_groups
department
classification
```

After authentication through Microsoft Entra ID, the API derives the user's permitted groups.

Azure AI Search filters are applied before retrieval.

Example concept:

```text
allowed_groups/any(g: g eq 'finance')
```

Unauthorized chunks therefore never reach the LLM.

This is preferable to retrieving everything and filtering after generation.

## Secrets Management

Local development currently uses `.env`.

Production should use:

- Azure Managed Identity
- Azure Key Vault
- least-privilege Azure RBAC

API keys should not be committed to Git or embedded inside container images.

## Network Security

For sensitive enterprise workloads:

- Private Endpoints
- restricted public network access
- VNet integration
- Azure API Management
- TLS
- Microsoft Entra authentication

should be considered.

## Monitoring and Observability

The current application records stage-level timings.

Production telemetry should include:

```text
request_id
rewrite_latency
decomposition_latency
embedding_latency
search_latency
generation_latency
total_latency
retrieved_document_ids
retrieval_scores
prompt_tokens
completion_tokens
errors
```

Application Insights and Azure Monitor can be used for:

- P50 / P95 / P99 latency
- dependency latency
- OpenAI failures
- Azure Search failures
- rate limiting
- token-cost monitoring
- ingestion failures

Sensitive document text should not be logged by default.

## How Would I Debug Latency Increasing From 3 Seconds to 12 Seconds?

I would first instrument each stage rather than guessing.

For this implementation, the request was split into:

```text
query rewrite
query decomposition
retrieval
generation
total
```

A simple factual query initially took approximately:

```text
decomposition: 6.96 s
retrieval:     6.87 s
generation:    3.86 s
total:        17.75 s
```

The query did not require decomposition.

After introducing conditional decomposition:

```text
decomposition: 0 s
retrieval:     6.84 s
generation:    4.23 s
total:        11.07 s
```

This reduced observed latency by approximately 38%.

Next I would split retrieval into:

```text
embedding latency
Azure AI Search latency
```

and optimize whichever dominates.

Potential optimizations include:

- embedding cache
- smaller rewrite model
- skip rewrite when no conversation history exists
- conditional decomposition
- parallel multi-query retrieval
- lower top-k where evaluation supports it
- result caching
- response streaming

## Reliability

Production controls should include:

- request timeouts
- bounded retries
- exponential backoff
- circuit breakers
- graceful error responses
- health/readiness endpoints
- idempotent ingestion
- retry queues
- dead-letter queues

Retries should not be unlimited because repeated LLM or Search failures can amplify load.

## Cost Optimization

Main cost drivers:

- embedding generation
- chat-model input tokens
- chat-model output tokens
- Azure AI Search capacity
- repeated rewrite/decomposition calls

Implemented optimizations:

- embedding cache during ingestion
- conditional query decomposition

Additional optimizations:

- query embedding cache
- safe response caching
- smaller model for query rewrite/decomposition
- context compression
- dynamic top-k
- batch embedding
- prompt reduction

## Why Not Send the Entire Knowledge Base to the LLM?

Sending all enterprise documents directly to the LLM would:

- increase token cost
- increase latency
- exceed context windows at scale
- expose irrelevant information
- weaken grounding
- complicate access control

Retrieval selects only the evidence needed for the current question.

## Why Keep Baseline Search?

The baseline vector implementation is intentionally preserved.

It provides a measurable reference against which hybrid search, semantic reranking, metadata filtering, and conversational improvements can be evaluated.

This allows improvements to be demonstrated quantitatively rather than claimed subjectively.