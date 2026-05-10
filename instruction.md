DOCKER IMAGE AUDITOR AGENT - PROJECT INSTRUCTIONS

This document is the single source of truth for building this project from scratch. Read everything before writing a single line of code.


WHAT THIS PROJECT IS

This is a production-grade web application that acts as an intelligent Docker image auditing platform. Users connect their DockerHub or AWS ECR registries, browse their repositories, add them to a workspace, and run deep AI-powered scans on their images. The scan results are surfaced through a rich dashboard showing security vulnerabilities, bloat analysis, base image health, compliance scores, AI-generated Dockerfile optimizations, and more. Seven specialized AI agents collaborate to produce findings. The entire infrastructure runs on AWS and is provisioned by Terraform.


WHO BUILT THIS AND WHY

This is an LLM-powered DevOps tool targeting developers and platform engineers who want actionable intelligence about their container images without manually running scanners. The AI layer adds reasoning on top of raw scan data — it does not just list CVEs, it explains exploitability, prioritizes by real risk, and generates optimized Dockerfiles with annotated explanations.


CODING RULES - READ BEFORE WRITING ANY CODE

No comments anywhere in the codebase. Not in frontend, not in backend, not in Terraform, not anywhere.
No emojis anywhere in the codebase or in the web UI.
No large monolithic files. If something can be split into smaller focused modules, split it.
No over-engineering. If it can be done simply, do it simply.
Every async operation must be non-blocking. Use async/await and Promise.all everywhere.
All agent calls that can run in parallel must run in parallel using Promise.all.
No hardcoded values. Everything goes through environment variables.
No storing credentials anywhere on the frontend. Ever.
The app must work in one run after setup. No multiple attempts to fix broken things.
Write code defensively. Handle errors at every layer. Never let an unhandled error crash the app.
Use TypeScript in the frontend. Use Python with strict type hints and Pydantic models everywhere in the backend and worker.
Keep functions small and single-purpose.


TECH STACK

Frontend: Next.js with TypeScript. Dark interactive DevOps-themed UI. No generic AI aesthetics. Use a distinctive font pairing. Animated ring scores, interactive cards, real-time WebSocket updates for scan progress. Side-by-side Dockerfile diff view with per-line annotations. Communicates with the FastAPI backend via REST. Never calls AWS directly.

Backend: Python FastAPI. Runs as its own ECS Fargate service. Handles all business logic, credential management, registry API calls, scan job dispatch, and agent orchestration. Fully async using asyncio and httpx. Separate Python worker service also on ECS for heavy scan processing. FastAPI and the worker are two separate services in the same ECS cluster.

AI Agents: LangGraph for multi-agent orchestration. OpenAI GPT-4o as the LLM. Seven agents total described below.

Scanning: Trivy as a Lambda layer for CVE scanning. AWS Inspector for ECR-native scanning. Both are used together and results are merged and deduplicated.

Database: DynamoDB for user data, scan results, agent memory, job status.

Cache: ElastiCache Redis. Cache scan results by image digest, layer analysis by layer digest, Trivy CVE database, repo listings, sessions.

Queue: SQS for scan jobs with a dead letter queue. Fan-out pattern so all agents process in parallel.

Real-time: API Gateway WebSocket API for pushing scan progress to the frontend.

Auth: AWS Cognito for user authentication and JWT issuance.

Secrets: AWS Secrets Manager with KMS encryption. Each user's credentials stored at secret/users/{cognito_user_id}/dockerhub and secret/users/{cognito_user_id}/aws_ecr. OpenAI API key and LangSmith API key also stored here.

Email: AWS SES. Two emails per scan — one when scan starts, one when scan completes with summary and link.

Observability: OpenTelemetry SDK instrumented throughout. ADOT collector as ECS sidecar. CloudWatch and X-Ray as backend. Grafana on ECS for dashboards pulling from CloudWatch.

LLM Observability: LangSmith for tracing every agent call, evaluation scores, prompt versioning.

LLM Evaluation: Ragas library evaluating faithfulness, answer relevancy, hallucination score, context precision, context recall, answer correctness. Scores stored in DynamoDB and pushed to LangSmith. Displayed on dashboard.

Deployment: ECS Fargate. Application Load Balancer with fixed DNS. Route 53 and ACM for custom domain and SSL. CloudFront in front of ALB for static assets. CI/CD via GitHub Actions.

Infrastructure: All provisioned by Terraform with modular structure. Remote state in S3 with DynamoDB locking. Separate workspaces for dev, staging, prod.

Security: AWS WAF on ALB. VPC with private subnets. VPC Endpoints for all AWS services. NAT Gateway only for DockerHub external calls. GuardDuty. Security Hub. CloudTrail. AWS Config. AWS Shield Standard. DynamoDB DAX for accelerated reads.

Performance: All agent calls in parallel via Promise.all. Streaming responses from OpenAI to frontend. Read-through Redis cache. Write-behind async DynamoDB writes. Batch DynamoDB writes for scan findings. Lambda SnapStart. WebSocket for real-time progress instead of polling.


THE SEVEN AI AGENTS

All agents are built with LangGraph and use GPT-4o. All agents run with OpenAI moderation API as guardrail on input and output. All agent calls are traced in LangSmith automatically via LangChain integration.

Agent 1 - Orchestrator Agent
This is the entry point for every scan. It reads image metadata, decides which specialist agents to invoke, fires them all in parallel using Promise.all, collects their outputs, passes combined context to the Dockerfile Optimizer and Risk Scorer agents, stores everything in DynamoDB, and returns the unified result. It has memory of previous scans for the same repo stored in DynamoDB so it can detect regressions.

Agent 2 - CVE Analysis Agent
Receives raw Trivy and AWS Inspector output. Does not just re-list CVEs. Reasons about actual exploitability — is the vulnerable binary in the runtime path, is there a known exploit, is it in the CISA KEV list. Cross-references NVD for descriptions, EPSS scores for exploit probability, and CISA KEV for actively exploited status. Prioritizes by real risk not just CVSS score. Detects regressions — CVEs that appeared since last scan. Returns structured findings with severity, evidence, exact fix version, and exploitability reasoning.

Agent 3 - Bloat Detective Agent
Receives full layer manifest from ECR or DockerHub API. Identifies root cause of each bloat source — which RUN command, which COPY instruction caused it. Detects ghost files added then deleted across layers. Finds package manager caches, dev tools left in prod, test fixtures, docs, build artifacts. Returns structured findings with layer reference, size impact, and exact fix.

Agent 4 - Base Image Strategist Agent
Identifies current base image and exact digest. Checks upstream for newer versions and EOL status. Reasons about migration path from current base toward distroless or scratch. Produces tradeoff analysis per migration option covering size, compatibility, and security. Checks if app dependencies are compatible with suggested alternatives. Warns about mutable tags like latest.

Agent 5 - Dockerfile Optimizer Agent
Receives original reconstructed Dockerfile plus findings from CVE, Bloat, and Base Image agents as context. Produces a fully rewritten optimized Dockerfile. Applies multi-stage builds where applicable. Reorders layers for cache efficiency. Cleans package caches in same RUN instruction. Removes dev tools. Pins base image to digest. Returns both the optimized Dockerfile and a structured list of every change made with category (security, bloat, cache, best-practice), what was wrong, what was fixed, and estimated savings. This powers the annotated diff view in the UI.

Agent 6 - Risk Scorer Agent
Receives all specialist agent outputs. Produces four scores from 0 to 100 — Security, Bloat, Freshness, Best Practices. Derives an overall grade A through F. Produces a prioritized list of top 5 actions by impact. Compares against previous scan scores to show trend. Generates a plain English executive summary. Flags if image should be blocked from production based on configurable policy thresholds stored in DynamoDB per user.

Agent 7 - Chat Agent
Uses ReAct pattern. Has all other agents registered as callable tools. Can query DynamoDB for historical scan data. Answers natural language questions about scan results across all repos in the user's workspace. Applies guardrails on every input via OpenAI moderation API before processing. Examples of questions it handles: which images have critical CVEs running in prod right now, what would my image size be if I switched to distroless, has this CVE appeared in any of my other images, show me all high severity findings from this week.


APPLICATION STRUCTURE

The application has three main tabs.

Tab 1 - Connections
User connects DockerHub with username and access token. User connects AWS ECR with access key, secret key, and region. Credentials are sent to the backend, backend writes them to Secrets Manager under the user's Cognito ID path, frontend never sees them again. Connection status shown with live validation badges.

Tab 2 - Repositories
Toggle between DockerHub and ECR. Lists all repositories fetched from the respective registry using credentials read server-side from Secrets Manager. Shows repo name, image count, last pushed date, total size. Add to Workspace button per repo. Repo list cached in Redis for 5 minutes.

Tab 3 - Workspace
Cards for every repo added by the user. Each card shows repo name, last scan date, overall grade, critical CVE count. Click into a repo to open the Repo Dashboard.

Repo Dashboard
Top section shows four animated ring score components for Security, Bloat, Freshness, and Best Practices plus the overall grade letter with color coding. Below that are twelve cards: Image Inventory, Critical Alerts, Size Overview, Base Image Health, Scan History Timeline (line chart with deploy markers), Top 5 Riskiest Images, Active CVEs Breakdown (donut chart), Layer Bloat Heatmap, Unused Images, AI Recommendations, Compliance Status against CIS Docker Benchmark, Cost Intelligence. All scan findings are listed below the cards with severity badge, category, title, detail, evidence, impact, fix, effort estimate, and which agent found it. Findings are filterable by severity, category, agent, and effort. Sortable by impact. Summary bar shows total findings, estimated fix time, and potential size reduction.

Per-Image Drill Down
Clicking any image opens a detail view with six tabs: Overview showing size, digest, OS, architecture, created date; Layers showing full layer breakdown with size and originating command; CVEs showing full table with EPSS scores and exploitability reasoning; Secrets showing any credentials detected in layers; Dockerfile showing reconstructed vs optimized side-by-side diff with per-line color-coded annotations (red for security, orange for bloat, yellow for cache, blue for best practice); History showing changes across tags and versions.

LLM Eval Dashboard Panel
Separate panel in the dashboard showing per-agent Ragas scores, score trends over time, total evaluations run, flagged low-score responses requiring review, worst performing agent, and per-scan eval breakdown.


INFRASTRUCTURE ARCHITECTURE

Networking: One VPC with public and private subnets across two availability zones. NAT Gateway in public subnet for outbound DockerHub calls from private subnets. VPC Endpoints for ECR, Secrets Manager, Bedrock, SQS, DynamoDB, S3, CloudWatch, X-Ray so all AWS traffic stays inside the AWS network. Security groups with least-privilege rules.

Compute: ECS Fargate cluster. One service for the Next.js frontend. One service for the FastAPI backend. One service for the Python scan worker. One service for Grafana. ADOT collector as sidecar on each task. Auto-scaling based on CPU, memory, and SQS queue depth. Multi-AZ task placement. ECS circuit breaker enabled for auto-rollback on failed deploys.

Load Balancing: Application Load Balancer with HTTPS listener on port 443. ACM certificate for SSL. HTTP redirects to HTTPS. Target groups with health checks. CloudFront distribution in front of ALB for static asset caching at edge. AWS WAF attached to ALB with rules for SQL injection, XSS, and rate limiting.

Database: DynamoDB tables for users, repos, scans, findings, agent memory, job status, eval scores. Point-in-time recovery enabled. DAX cluster for accelerated reads on hot paths.

Cache: ElastiCache Redis cluster in private subnet. Used for scan results by digest, layer analysis by layer digest, Trivy CVE DB refresh every 6 hours, repo listings TTL 5 minutes, sessions TTL 1 hour.

Queue: SQS standard queue for scan jobs. Dead letter queue after 3 failed attempts. Fan-out via SNS or parallel Lambda invocations so all agents start simultaneously.

Storage: S3 bucket for scan result archives and LLM eval logs. Versioning enabled. Lifecycle policies to move old results to Glacier after 90 days.

Auth: Cognito User Pool with email verification. JWT tokens used for all API calls. Tokens verified server-side on every request.

Secrets: Secrets Manager with KMS CMK. One secret per user per registry type. OpenAI API key at secret/app/openai. LangSmith API key at secret/app/langsmith. Automatic rotation where applicable.

Email: SES with verified sending domain. Two email templates — scan started and scan completed. Scan completed email includes grade, CVE counts, top 3 findings summary, and deep link to report.

Monitoring: CloudWatch log groups for all services. X-Ray tracing on all Lambda and ECS tasks. OpenTelemetry SDK in all services sending to ADOT collector. Grafana on ECS pulling from CloudWatch datasource. CloudWatch alarms for error rates, latency, queue depth. CloudTrail for all API calls. GuardDuty enabled. Security Hub enabled. AWS Config rules for compliance. AWS Shield Standard enabled.

CI/CD: GitHub Actions workflow on push to main. Steps are run tests, build Docker image, push to ECR tagged with commit SHA, register new ECS task definition revision, update ECS service which triggers rolling deploy. ALB health checks new tasks before draining old ones. Zero downtime. Terraform apply runs in a separate workflow triggered manually or on infrastructure PRs.


TERRAFORM STRUCTURE

All infrastructure in a terraform directory at repo root. Modular structure with one module per concern. Remote state in S3 with DynamoDB locking. Three workspaces: dev, staging, prod. Modules to create: networking, ecs, ecr, auth, secrets, database, storage, queue, lambda, api, dns, monitoring, waf, cache. Each module has its own variables, outputs, and main file. No hardcoded region or account ID anywhere — all passed as variables.


SCAN EXECUTION FLOW

User clicks scan on a repo. Frontend calls API with repo identifier. API writes a scan job to SQS and immediately returns a job ID to the frontend. Frontend subscribes to WebSocket channel for that job ID. SQS triggers the Python worker ECS task. Worker reads credentials from Secrets Manager. Worker pulls image manifest from DockerHub or ECR — does not pull full image unless necessary. Worker runs Trivy scan against the image. Worker calls AWS Inspector for ECR images. Worker fetches layer contents for bloat analysis. Worker fires all specialist agents in parallel via Promise.all — CVE Agent, Bloat Detective Agent, Base Image Strategist Agent. Each agent receives its relevant data and reasons over it using GPT-4o. Worker passes all agent outputs to Dockerfile Optimizer Agent. Worker passes everything to Risk Scorer Agent. Worker stores all findings in DynamoDB in batch. Worker stores full report in S3. Worker publishes progress events to WebSocket API at key milestones. Worker triggers SES to send completion email. LangSmith automatically traces all agent calls. Ragas evaluation runs async after scan completes and stores scores.


TESTING PLAN

Unit tests for all utility functions, agent prompt builders, and data transformation logic using Jest for frontend and Pytest for backend and worker.

Integration tests for all FastAPI routes using pytest with httpx against a running FastAPI test server with mocked AWS services using localstack.

Agent tests using LangSmith datasets — create a set of known image scan inputs with expected outputs and run regression tests against them whenever prompts change.

End to end tests using Playwright covering the full user flow: register, connect registry, browse repos, add to workspace, trigger scan, view results, use chat agent.

Load testing using k6 — simulate 50 concurrent scan jobs and verify queue processing, Redis cache hit rates, and WebSocket delivery.

Infrastructure tests using Terratest — provision real AWS resources in a test account, verify outputs, destroy after.

Security tests using OWASP ZAP against the running app to check for XSS, injection, and auth bypass.

To run tests locally: install Node dependencies for frontend and Python dependencies for backend and worker, spin up localstack with Docker Compose for AWS service mocks, run Jest for frontend unit tests, run Pytest for backend unit and integration tests, run Playwright for end to end. All test commands documented in README.


README REQUIREMENTS

The README must be written so an absolute beginner can follow it. It must cover: what the project does in plain language, every tool that needs to be installed (Node, Docker, Terraform, AWS CLI, GitHub CLI) with the exact install command for each, every AWS account setup step (create account, create IAM user with required permissions, configure AWS CLI), every third party account needed (OpenAI API key, LangSmith account and API key, DockerHub account for testing, SES domain verification), how to clone the repo, how to configure all environment variables with a complete list of every variable and what it is, how to bootstrap the Terraform state bucket manually before first apply, how to run terraform init, plan, and apply for the first time, how to push to GitHub to trigger the CI/CD pipeline, how to verify the deployment is healthy, how to run all tests, how to access Grafana dashboard, how to access LangSmith dashboard, how to use the app for the first time step by step, how to tear everything down cleanly, common errors and how to fix them.


THINGS TO NEVER DO

Never put AWS credentials in the frontend.
Never commit secrets or API keys.
Never use latest tag for any Docker image in production.
Never skip input validation on any API route.
Never trust user input before sanitizing.
Never make synchronous blocking calls in the scan worker.
Never run ECS tasks in public subnets.
Never open port 22 or 3389 in any security group.
Never store scan results only in memory — always persist to DynamoDB and S3.
Never skip the Ragas evaluation step after a scan.
Never let an agent call succeed without LangSmith tracing.
