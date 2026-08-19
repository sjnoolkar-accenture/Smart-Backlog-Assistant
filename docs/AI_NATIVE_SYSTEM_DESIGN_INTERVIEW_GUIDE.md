# AI-Native System Design Interview Guide

## 1. Purpose

This guide helps an engineer with an Azure background reason through unfamiliar
real-world problems and design trustworthy AI-native systems during interviews.

The goal is not to memorize one architecture. The goal is to demonstrate a
repeatable way of thinking:

1. understand the user and business outcome;
2. map the current workflow and constraints;
3. decide whether AI is appropriate;
4. separate probabilistic AI behavior from deterministic controls;
5. design for evidence, safety, evaluation, operations, and human ownership;
6. explain Azure implementation options and their trade-offs.

> A strong candidate does not begin with a model. A strong candidate begins
> with the problem, evidence, risks, and measurable outcome.

---

## 2. What Makes a System AI-Native?

An AI-native system is not an existing application with a chatbot attached.
Its workflow is deliberately designed around capabilities such as language
understanding, generation, classification, retrieval, prediction, or agentic
tool use.

At the same time, it assumes that model output is probabilistic and may be:

- incomplete;
- inconsistent;
- unsupported by evidence;
- unsafe;
- expensive;
- slow;
- temporarily unavailable.

An AI-native design therefore combines:

| Flexible AI capability | Deterministic engineering control |
|---|---|
| Interpret ambiguous language | Validate input and output schemas |
| Summarize large evidence sets | Preserve source references |
| Generate drafts | Apply business rules and allowlists |
| Classify intent | Enforce permissions and policy |
| Recommend actions | Require approval for consequential actions |
| Select or call tools | Validate tool identity, arguments, and results |
| Explain likely causes | Distinguish evidence from assumptions |

The architecture must treat the model as one component, not as the system's
final authority.

---

## 3. The Seven-Step Interview Framework

Use this framework for any random interview scenario.

### Step 1: Clarify the User and Outcome

Ask:

- Who experiences the problem?
- Who uses the proposed solution?
- Who is accountable for the final decision?
- What task or decision should improve?
- What measurable business result is expected?

Example:

> "The primary user is an on-call engineer. The desired outcome is to reduce
> investigation time while avoiding unsafe automated mitigation."

Avoid vague goals such as "use AI to improve operations."

### Step 2: Map the Existing Workflow

Explain the current process before redesigning it:

```text
Trigger -> Input -> Human analysis -> Decision -> Action -> Feedback
```

Identify:

- authoritative inputs;
- manual bottlenecks;
- existing systems and APIs;
- deterministic rules;
- exceptions and escalation paths;
- compliance or approval boundaries;
- current baseline time, cost, and error rate.

This prevents the common mistake of optimizing one visible step while ignoring
the surrounding workflow.

### Step 3: Decide Whether AI Is Appropriate

AI is a good candidate when the task involves:

- unstructured text, images, audio, or documents;
- semantic search;
- summarization;
- classification with ambiguous language;
- drafting or transformation;
- extracting patterns from large evidence sets;
- recommendations where a human can review the result.

Prefer deterministic software when the task involves:

- exact calculations;
- access control;
- policy enforcement;
- financial posting;
- irreversible actions;
- known lookup rules;
- strict workflow state transitions;
- legal or regulatory decisions without review.

State the boundary explicitly:

> "AI will interpret and recommend. Deterministic code will authorize,
> validate, and execute."

### Step 4: Identify Evidence and Data

Ask:

- What data exists?
- Which source is authoritative?
- Is the data structured, unstructured, real-time, or historical?
- Is it complete, current, and correctly labeled?
- Does it contain personal, confidential, or regulated information?
- How will the system cite or trace its answer?
- Is tenant or regional isolation required?

Possible Azure services:

| Need | Azure option |
|---|---|
| Documents and files | Azure Blob Storage or Data Lake Storage |
| Relational business data | Azure SQL Database |
| Globally distributed operational data | Azure Cosmos DB |
| Search and retrieval-augmented generation | Azure AI Search |
| Streaming events | Azure Event Hubs |
| Reliable asynchronous commands | Azure Service Bus |
| Data integration | Azure Data Factory or Microsoft Fabric |
| Data governance and discovery | Microsoft Purview |

### Step 5: Design the AI and Deterministic Boundaries

Describe the system as a controlled pipeline:

```text
User or event
  -> authenticated API
  -> input validation and safety checks
  -> evidence retrieval
  -> model or agent orchestration
  -> structured response
  -> deterministic validation
  -> human review or authorized action
  -> telemetry and feedback
```

For every model responsibility, define:

- input contract;
- permitted evidence;
- output schema;
- tools it may call;
- validation rules;
- timeout and retry behavior;
- fallback behavior;
- approval requirement.

### Step 6: Plan Evaluation, Safety, and Operations

Discuss three different test layers.

#### Deterministic tests

- schema validation;
- authorization;
- tool contracts;
- business rules;
- known identifiers;
- retry and fallback behavior;
- data isolation;
- audit records.

#### AI-quality evaluations

- groundedness;
- relevance;
- completeness;
- correctness;
- retrieval quality;
- harmful-content rate;
- bias or fairness where applicable;
- tool-selection accuracy.

#### End-to-end outcome measures

- time saved;
- user acceptance;
- correction rate;
- false positive and false negative rates;
- task completion;
- cost per successful task;
- latency;
- incident or escalation rate.

### Step 7: Roll Out Gradually

Use an evidence-based rollout:

1. historical offline evaluation;
2. internal pilot;
3. shadow mode with no user-visible action;
4. recommendation mode with human approval;
5. limited automation for low-risk actions;
6. broader automation only after measured success.

Include rollback, model versioning, prompt versioning, and incident response.

---

## 4. A 90-Second Interview Answer Template

Use this when the interviewer gives an unfamiliar scenario.

> "First, I would clarify the primary user, the current workflow, and the
> measurable outcome. I would identify the authoritative data and determine
> whether the bottleneck genuinely requires AI or can be solved with normal
> rules or search.
>
> I would use AI only for the ambiguous part, such as interpreting,
> summarizing, classifying, or drafting. Permissions, business rules,
> validation, and consequential actions would remain deterministic.
>
> On Azure, I would expose the workflow through API Management and an
> authenticated application, use Microsoft Foundry or Azure OpenAI for model
> inference, Azure AI Search for grounded retrieval where needed, and Functions,
> Logic Apps, or Service Bus for controlled tool execution.
>
> I would require structured output with evidence references, validate it
> before use, add content and prompt-attack controls, and keep a human approval
> boundary for high-impact actions.
>
> Finally, I would evaluate quality, safety, latency, cost, and the business
> outcome against the current baseline, beginning in shadow or recommendation
> mode before allowing automation."

---

## 5. Reference Azure AI-Native Architecture

```text
Channels
Web / Mobile / Teams / API / Event
                |
Identity and edge
Microsoft Entra ID -> Azure API Management -> WAF / rate limits
                |
Application orchestration
App Service / Container Apps / AKS
Durable Functions / Logic Apps / Foundry Agent Service
                |
Evidence and state
Azure AI Search + Blob / SQL / Cosmos DB / Fabric
                |
Model layer
Microsoft Foundry model catalog / Azure OpenAI
                |
Controlled tools
Azure Functions / Logic Apps / internal APIs
Service Bus / Event Grid / Event Hubs
                |
Validation and human decision
Schemas / business rules / confidence policy / approval workflow
                |
Observability and governance
Application Insights / Azure Monitor / Log Analytics
Content Safety / Key Vault / Purview / Defender for Cloud
```

### Azure Component Selection

| Concern | Azure services | Design comment |
|---|---|---|
| Model access and lifecycle | Microsoft Foundry, Azure OpenAI | Select models through evaluation, not popularity |
| Agent orchestration | Foundry Agent Service, Semantic Kernel, custom orchestration | Use agents only when tool selection or multi-step planning is necessary |
| RAG and enterprise search | Azure AI Search | Apply document-level security and return citations |
| API boundary | Azure API Management | Authentication, quotas, request policies, versioning |
| Compute | Azure Container Apps, App Service, AKS | Choose the simplest platform satisfying scale and network needs |
| Event-driven processing | Functions, Event Grid, Event Hubs | Suitable for ingestion, enrichment, and reactive workflows |
| Reliable workflow | Service Bus, Durable Functions, Logic Apps | Use for retries, state, approvals, and long-running work |
| Secrets and identity | Managed Identity, Key Vault, Entra ID | Avoid credentials in prompts, code, and configuration files |
| Network isolation | Private Link, Virtual Network integration | Consider for enterprise and regulated workloads |
| Safety | Azure AI Content Safety and Prompt Shields | Use alongside application-specific controls |
| Monitoring | Application Insights, Azure Monitor, Log Analytics | Track model, retrieval, tool, validation, cost, and business telemetry |
| Governance | Microsoft Purview, Azure Policy | Data discovery, lineage, policy, and compliance |
| Delivery | Azure DevOps or GitHub Actions, Bicep or Terraform | Version infrastructure, prompts, evaluations, and deployment configuration |

---

## 6. Important Architecture Decisions

### 6.1 RAG, Fine-Tuning, or Prompting?

| Technique | Use when | Avoid when |
|---|---|---|
| Prompting | Instructions and a small amount of context are sufficient | Large or frequently changing knowledge is required |
| RAG | Answers must use current enterprise knowledge and provide citations | The task is primarily style or behavior adaptation |
| Fine-tuning | Repeated behavior, format, terminology, or classification requires adaptation | The goal is to inject current facts |

Strong interview answer:

> "I would begin with prompting and RAG because enterprise facts change and
> should remain independently governable. I would consider fine-tuning only
> after evaluation shows a persistent behavioral gap that prompting cannot
> solve."

### 6.2 Workflow or Agent?

Use a deterministic workflow when:

- the sequence is known;
- every step is required;
- predictability and auditability matter;
- cost and latency must be controlled.

Use an agent when:

- the system must choose among tools dynamically;
- the number or sequence of steps cannot be known in advance;
- iterative planning materially improves the result.

Avoid using multiple agents only because the architecture appears more
advanced. Every additional agent increases latency, cost, failure modes, and
evaluation complexity.

### 6.3 Synchronous or Asynchronous?

Use synchronous processing for short, user-facing interactions.

Use Service Bus, Durable Functions, or Logic Apps for:

- long document processing;
- batch evaluation;
- multi-stage approvals;
- provider rate limits;
- resilient retries;
- tasks lasting longer than an HTTP request.

Return a correlation identifier and expose status rather than holding a
connection open.

### 6.4 One Model or Multiple Models?

Begin with the smallest model that meets the measured quality target.

Consider routing:

- small model for intent and simple extraction;
- stronger model for complex reasoning;
- embeddings model for retrieval;
- specialized model for vision, speech, or classification.

Model routing should be governed by task type, quality, latency, data boundary,
and cost, not by random fallback.

### 6.5 Conversation Memory

Do not treat unrestricted chat history as reliable system state.

Separate:

- short-term conversation context;
- durable user preferences;
- authoritative business state;
- retrieved enterprise evidence;
- audit history.

Store authoritative state in SQL, Cosmos DB, or another governed system of
record. Summarize or expire conversational state deliberately.

---

## 7. Trustworthy AI Design Checklist

### Grounding and Hallucination

- Retrieve only authorized evidence.
- Require citations or source identifiers.
- Distinguish evidence, inference, and assumption.
- Validate known IDs, dates, amounts, and entities.
- Refuse or escalate when evidence is insufficient.
- Never convert model confidence language into an objective probability unless
  it has been calibrated.

### Prompt Injection and Tool Safety

- Treat retrieved documents, webpages, emails, and tool results as untrusted
  data, not instructions.
- Separate instructions from evidence using explicit boundaries.
- Allowlist tools and arguments.
- Re-authorize every consequential tool call.
- Apply least privilege through Managed Identity.
- Validate tool results before returning them to the model.
- Require approval for destructive, financial, external, or privileged actions.

### Privacy and Security

- Classify data before sending it to a model.
- Minimize prompt content.
- Redact sensitive values where possible.
- Use Entra ID, Managed Identity, Key Vault, and Private Link.
- Apply tenant and document-level authorization before retrieval.
- Define data retention and deletion behavior.
- Avoid logging complete prompts, model responses, secrets, or private data.

### Reliability

- Set explicit timeouts.
- Retry only transient failures.
- Use exponential backoff and circuit breaking.
- Define deterministic fallback or graceful degradation.
- Make tool calls idempotent where possible.
- Use queues for load leveling.
- Record model, prompt, retrieval index, and policy versions.

### Cost and Performance

- Bound input and output tokens.
- Retrieve a small, relevant evidence set.
- Cache safe, reusable results.
- Batch offline processing.
- Route simple work to smaller models.
- Track cost per successful task, not only cost per token.
- Set budgets, quotas, and alerts.

---

## 8. Observability for AI-Native Systems

Traditional infrastructure telemetry is necessary but insufficient.

Capture:

### Request telemetry

- correlation ID;
- user or tenant identifier where appropriate;
- scenario and task type;
- latency and outcome;
- input and output size;
- approval or rejection.

### Model telemetry

- provider, deployment, and model version;
- prompt template version;
- token usage;
- finish reason;
- timeout, retry, and fallback;
- safety-filter results.

### Retrieval telemetry

- search query;
- index and index version;
- retrieved document identifiers;
- relevance scores;
- citation coverage;
- authorization filtering.

### Tool telemetry

- selected tool;
- sanitized arguments;
- authorization decision;
- duration;
- result status;
- idempotency and retry state.

### Quality and business telemetry

- groundedness;
- user correction;
- human acceptance;
- task completion;
- false positive and false negative rates;
- time saved;
- escalation rate;
- cost per accepted result.

Use Application Insights and Azure Monitor for technical telemetry. Use Foundry
evaluation and monitoring capabilities for model and agent quality. Connect
technical measures to a business dashboard rather than treating token usage as
the primary success metric.

---

## 9. Critical Interview Questions and Strong Responses

### "Why do you need AI?"

Weak answer:

> "Because the company wants an AI solution."

Strong answer:

> "The bottleneck is interpretation of varied, unstructured evidence. Rules can
> enforce policy after interpretation, but they cannot economically encode all
> language variations. I would validate this assumption against a non-AI
> baseline."

### "How will you prevent hallucination?"

Strong response:

1. restrict the task;
2. retrieve authorized evidence;
3. require structured output and citations;
4. validate identifiers and important facts;
5. reject unsupported output;
6. escalate insufficient evidence;
7. evaluate hallucination rates continuously.

Do not answer only with "improve the prompt."

### "What happens when the model is unavailable?"

Define one of:

- deterministic fallback;
- cached safe response;
- queue for later processing;
- reduced-functionality mode;
- explicit user-visible failure and retry.

The correct choice depends on whether the workflow is optional, time-sensitive,
or safety-critical.

### "How do you measure accuracy for generated text?"

Do not rely on exact string comparison alone. Use:

- deterministic checks for IDs, schema, and required fields;
- reference datasets;
- rubric-based human evaluation;
- groundedness and relevance evaluation;
- task-specific outcome metrics;
- disagreement analysis and error categories.

### "How do you secure RAG?"

- authorize before retrieval;
- preserve source access controls in the search index;
- filter by tenant and user permissions;
- use private networking where required;
- treat retrieved text as untrusted;
- prevent citations to inaccessible documents;
- audit document access.

### "Would you use a multi-agent architecture?"

Strong response:

> "Only if separate responsibilities, tools, or evaluation boundaries provide
> measurable value. If the sequence is known, I prefer a deterministic workflow
> because it is easier to test, operate, and control."

### "How would you reduce cost?"

- establish a quality baseline;
- use a smaller model where it passes;
- shorten prompts;
- improve retrieval precision;
- cache safe results;
- batch offline work;
- limit retries;
- route by complexity;
- monitor cost per accepted outcome.

### "When would you allow autonomous action?"

Only when:

- the action is low impact and reversible;
- identity and authorization are deterministic;
- tool arguments are constrained;
- success and failure are observable;
- idempotency exists;
- rollback exists;
- measured performance supports automation;
- governance explicitly approves it.

---

## 10. Practice Scenario 1: Production Incident Triage

### Interview Prompt

> An operations team receives hundreds of alerts. Engineers spend too much time
> correlating telemetry and finding relevant runbooks. Design an AI solution.

### Strong Design

**Outcome**

- reduce investigation time and mean time to mitigation;
- do not allow unsupported autonomous production changes.

**AI responsibilities**

- summarize alerts and logs;
- correlate symptoms;
- retrieve similar incidents and runbooks;
- suggest likely causes and next steps.

**Deterministic responsibilities**

- service ownership;
- severity calculation;
- permissions;
- incident state;
- mitigation authorization;
- execution and rollback.

**Azure mapping**

- Azure Monitor and Application Insights for telemetry;
- Log Analytics for querying operational evidence;
- Event Grid or Event Hubs for event ingestion;
- Azure AI Search for runbooks and incident knowledge;
- Foundry or Azure OpenAI for summarization and recommendations;
- Functions or Logic Apps for controlled tools;
- Service Bus and Durable Functions for resilient orchestration;
- Entra ID, Managed Identity, and Key Vault for security.

**Guardrails**

- cite every operational claim;
- identify evidence time range;
- mark assumptions;
- restrict tools;
- require approval for mitigation;
- do not expose secrets from logs.

**Metrics**

- time to acknowledge;
- time to identify likely cause;
- time to mitigate;
- recommendation acceptance;
- incorrect recommendation rate;
- false escalation rate.

**Common trap**

Do not let an agent execute arbitrary commands against production.

---

## 11. Practice Scenario 2: Enterprise Knowledge Assistant

### Interview Prompt

> Employees cannot quickly find answers across policies, SharePoint documents,
> product documentation, and support articles. Design an AI assistant.

### Strong Design

**Outcome**

- reduce search time while preserving document permissions and citations.

**Architecture**

1. ingest authorized documents;
2. extract and chunk content;
3. index content and metadata in Azure AI Search;
4. apply user and tenant authorization filters;
5. retrieve relevant passages;
6. generate an answer using only retrieved evidence;
7. display citations and feedback controls.

**Azure mapping**

- SharePoint or Blob Storage as sources;
- Data Factory, Logic Apps, or Functions for ingestion;
- Azure AI Search for hybrid and vector retrieval;
- Foundry or Azure OpenAI for answer generation;
- Entra ID for user identity;
- API Management for the API boundary;
- App Service, Container Apps, or Teams integration for the experience;
- Application Insights for telemetry;
- Content Safety and Prompt Shields for safety controls.

**Critical concerns**

- document-level access;
- stale index content;
- conflicting policies;
- prompt injection in documents;
- answer citation;
- insufficient evidence;
- regional and retention requirements.

**Common trap**

Do not solve authorization after retrieval. Unauthorized documents should not be
placed in model context.

---

## 12. Practice Scenario 3: Intelligent Invoice Processing

### Interview Prompt

> A finance team manually reads invoices, validates purchase orders, and enters
> approved amounts into an ERP system. Design an AI-assisted solution.

### Strong Design

**AI responsibilities**

- extract supplier, invoice number, dates, currency, line items, and totals;
- classify exceptions;
- explain discrepancies.

**Deterministic responsibilities**

- duplicate invoice detection;
- arithmetic;
- purchase-order matching;
- tax and tolerance rules;
- supplier authorization;
- financial posting;
- approval thresholds.

**Azure mapping**

- Azure AI Document Intelligence for extraction;
- Blob Storage for source files;
- Functions or Logic Apps for workflow;
- Azure SQL or Cosmos DB for processing state;
- Service Bus for reliable processing;
- Foundry or Azure OpenAI for exception summaries;
- Entra ID and Key Vault for identity and secrets;
- Application Insights for audit and performance telemetry.

**Human boundary**

- require review for low-confidence extraction;
- require approval for mismatches and high-value invoices;
- never allow the language model to calculate or approve payment.

**Metrics**

- field extraction accuracy;
- straight-through processing rate;
- exception rate;
- duplicate detection;
- processing time;
- financial correction rate.

**Common trap**

Do not use a generative model as the system of record or arithmetic engine.

---

## 13. Practice Scenario 4: Software Modernization Assistant

### Interview Prompt

> An organization must modernize hundreds of legacy applications. Engineers
> need help understanding code, identifying dependencies, and preparing
> migration plans.

### Strong Design

**AI responsibilities**

- summarize code and architecture;
- identify likely modernization patterns;
- draft migration tasks;
- explain dependency risks;
- generate candidate tests.

**Deterministic responsibilities**

- source control operations;
- build and test execution;
- dependency scanning;
- security policy;
- deployment gates;
- environment changes.

**Azure mapping**

- Azure DevOps Repos and Pipelines or GitHub;
- Azure Container Apps, App Service, AKS, or Functions as target platforms;
- Azure Migrate and Azure Monitor for estate and runtime evidence;
- Foundry or Azure OpenAI for analysis and drafting;
- Azure AI Search for architecture standards and migration guidance;
- Service Bus or Durable Functions for repository-scale asynchronous analysis;
- Defender for Cloud and dependency/security scanners for verification;
- Bicep for repeatable target infrastructure.

**Guardrails**

- ground recommendations in repository evidence;
- require file and symbol references;
- never merge generated code automatically at first;
- run compilation, tests, security checks, and policy gates;
- use pull requests and human review.

**Metrics**

- analysis time;
- accepted recommendations;
- build and test pass rate;
- escaped defects;
- migration lead time;
- cloud cost and reliability after migration.

---

## 14. Practice Scenario 5: Customer Support Resolution Assistant

### Interview Prompt

> Support agents spend too much time reading customer history, finding
> troubleshooting steps, and writing responses.

### Strong Design

**AI responsibilities**

- summarize the case and conversation history;
- classify intent;
- retrieve approved troubleshooting material;
- draft a response;
- recommend escalation.

**Deterministic responsibilities**

- customer identity;
- entitlement;
- refund policy;
- severity;
- regulated disclosures;
- case-state changes.

**Azure mapping**

- Dynamics 365 or existing CRM through controlled APIs;
- Azure AI Search for product and troubleshooting knowledge;
- Foundry or Azure OpenAI for summary and drafting;
- API Management for CRM and product API access;
- Functions or Logic Apps for controlled actions;
- Entra ID and Managed Identity;
- Content Safety for input and output screening;
- Application Insights for quality and operational telemetry.

**Metrics**

- average handling time;
- first-contact resolution;
- response acceptance;
- escalation accuracy;
- customer satisfaction;
- correction and policy-violation rate.

---

## 15. Design-Thinking Questions to Ask Before Drawing Architecture

Use these questions aloud in an interview:

1. Who is the user, and who is accountable?
2. What is the current process?
3. What is the measurable bottleneck?
4. What is the cost of a wrong answer?
5. What data is authoritative?
6. What data may the model access?
7. What must remain deterministic?
8. What action requires human approval?
9. Does the answer require current enterprise knowledge?
10. Is the workflow interactive, batch, event-driven, or long-running?
11. What latency and availability are required?
12. What is the fallback if the model or retrieval system fails?
13. How will output quality be evaluated?
14. How will users report incorrect results?
15. How will the system be monitored and rolled back?

These questions demonstrate design maturity before any Azure service is
selected.

---

## 16. Whiteboard Sequence

When asked to draw the design, use this order:

1. **Users and channels**
2. **Identity and API boundary**
3. **Application workflow**
4. **Authoritative data**
5. **Retrieval**
6. **Model or agent**
7. **Controlled tools**
8. **Validation**
9. **Human approval**
10. **Telemetry, security, and evaluation**

Draw the normal path first. Add failure and approval paths second.

Label:

- trust boundaries;
- synchronous versus asynchronous calls;
- systems of record;
- data classification;
- model and tool permissions;
- fallback;
- audit records.

---

## 17. A Simple Trade-Off Language

Interviewers usually care more about judgment than product memorization.

Use phrases such as:

- "I would start with the simplest design that can prove the outcome."
- "The model can recommend this action, but authorization remains
  deterministic."
- "I would prefer RAG because the knowledge changes and must remain governed."
- "I would use an asynchronous workflow because processing can outlive an HTTP
  request."
- "A multi-agent design is not justified unless dynamic tool selection or
  independent responsibility produces measurable value."
- "I would begin in shadow mode and compare against the current human process."
- "The final metric is accepted business outcomes, not model fluency."
- "I would explicitly design the insufficient-evidence path."
- "I would use Managed Identity instead of passing credentials to the agent."
- "I would validate quality and cost before selecting a larger model."

---

## 18. Common Interview Mistakes

Avoid:

1. selecting Azure services before clarifying the problem;
2. assuming every problem requires generative AI;
3. using AI for exact rules or authorization;
4. claiming prompts eliminate hallucinations;
5. ignoring source authorization in RAG;
6. proposing autonomous agents for high-impact actions without approval;
7. omitting evaluation data;
8. discussing only infrastructure metrics;
9. forgetting fallback and provider failure;
10. using multi-agent architecture without justification;
11. ignoring cost and latency;
12. treating chat history as authoritative state;
13. logging sensitive prompts and model responses;
14. deploying directly without shadow or pilot stages;
15. failing to compare against a non-AI baseline.

---

## 19. Daily Practice Method

Select one random domain each day:

- healthcare appointment management;
- retail demand planning;
- insurance claims;
- legal document review;
- manufacturing maintenance;
- employee onboarding;
- fraud investigation;
- cloud operations;
- software migration;
- supply-chain disruption.

Write only the following first:

```text
User:
Outcome:
Current workflow:
AI responsibility:
Deterministic responsibility:
Evidence:
Human decision:
Top three risks:
Azure architecture:
Success metrics:
Rollout:
```

Then deliver:

- a 90-second answer;
- a five-minute architecture explanation;
- answers to three challenge questions.

Score yourself from 0 to 2 on each dimension:

| Dimension | 0 | 1 | 2 |
|---|---|---|---|
| Problem clarity | Vague | Partial | Specific user and outcome |
| AI justification | Technology-first | Some rationale | AI and non-AI boundaries are clear |
| Data design | Ignored | Sources named | Authority, quality, privacy, and access addressed |
| Safety | Ignored | Generic | Scenario-specific controls and human boundary |
| Evaluation | No metrics | Technical metrics | Quality, safety, and business metrics |
| Azure design | Product list | Basic mapping | Services selected with trade-offs |
| Operations | Happy path only | Some fallback | Monitoring, failure, rollout, and rollback |

A score of 11 or more out of 14 indicates a strong interview response.

---

## 20. Final Mental Model

Before finishing any AI-system answer, confirm:

```text
Problem before model
Evidence before generation
Authorization before action
Validation before trust
Evaluation before scale
Human accountability throughout
```

The strongest closing statement is:

> "I would design AI as a probabilistic capability inside a deterministic,
> observable, secure, and human-governed system."

---

## 21. Azure References

- [AI workloads on Azure - Well-Architected Framework](https://learn.microsoft.com/en-us/azure/well-architected/ai/get-started)
- [Architecture patterns for AI workloads](https://learn.microsoft.com/en-us/azure/well-architected/ai/architecture-pattern)
- [Responsible AI in Azure workloads](https://learn.microsoft.com/en-us/azure/well-architected/ai/responsible-ai)
- [MLOps and GenAIOps for Azure AI workloads](https://learn.microsoft.com/en-us/azure/well-architected/ai/mlops-genaiops)
- [Microsoft Foundry documentation](https://learn.microsoft.com/en-us/azure/foundry/)
- [Azure OpenAI documentation](https://learn.microsoft.com/en-us/azure/ai-services/openai/)
- [Azure AI Search documentation](https://learn.microsoft.com/en-us/azure/search/)
- [Azure AI Content Safety](https://learn.microsoft.com/en-us/azure/ai-services/content-safety/overview)
- [Foundry guardrails and controls](https://learn.microsoft.com/en-us/azure/foundry/guardrails/guardrails-overview)
- [Monitor AI agents with Application Insights](https://learn.microsoft.com/en-us/azure/azure-monitor/app/agents-view)
- [Azure API Management](https://learn.microsoft.com/en-us/azure/api-management/)
- [Microsoft Entra managed identities](https://learn.microsoft.com/en-us/entra/identity/managed-identities-azure-resources/overview)
- [Azure Private Link](https://learn.microsoft.com/en-us/azure/private-link/)
- [Azure Service Bus](https://learn.microsoft.com/en-us/azure/service-bus-messaging/)
- [Durable Functions](https://learn.microsoft.com/en-us/azure/azure-functions/durable/)
- [Microsoft Purview](https://learn.microsoft.com/en-us/purview/)
- [Azure Monitor](https://learn.microsoft.com/en-us/azure/azure-monitor/)
- [Azure Well-Architected Framework](https://learn.microsoft.com/en-us/azure/well-architected/)

