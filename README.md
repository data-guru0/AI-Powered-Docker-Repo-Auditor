# Docker Image Auditor

A production-grade AI-powered platform that audits Docker images for security vulnerabilities, bloat, and optimization opportunities using 7 parallel LangGraph agents backed by GPT-4o, deployed on AWS ECS Fargate.

## What it does

- Scans any Docker image from ECR or Docker Hub
- Runs 7 specialized AI agents in parallel: CVE Analyst, Bloat Detective, Base Image Strategist, Dockerfile Optimizer, Risk Scorer, Security Narrator, and a Chat Agent
- Streams real-time scan progress via API Gateway WebSocket
- Produces an animated ring-score dashboard with CVE breakdown, Dockerfile diff, and executive summary
- Runs Ragas LLM evaluation on every scan to measure agent quality
- Archives all reports to S3 with Glacier lifecycle

## Architecture

```
User → ALB → Next.js Frontend (ECS Fargate)
               ↓
       API Gateway WebSocket (real-time progress)
               ↓
       FastAPI Backend (ECS Fargate)
               ↓
       SQS FIFO Queue
               ↓
       Python Worker (ECS Fargate)
               ↓
    ┌──────────────────────────────────────┐
    │  7 LangGraph Agents (asyncio.gather) │
    │  CVE + Bloat + Base Image (parallel) │
    │  Dockerfile Optimizer (sequential)   │
    │  Risk Scorer → Ragas Eval (task)     │
    └──────────────────────────────────────┘
               ↓
    DynamoDB + S3 + ElastiCache Redis
```

**Infrastructure:** ECS Fargate, DynamoDB, ElastiCache Redis, SQS FIFO, API Gateway WebSocket, Cognito, Secrets Manager, SES, S3 + Glacier, Lambda (Trivy), Inspector2, WAFv2, Route53, ACM, CloudWatch, X-Ray

## Prerequisites

- AWS account with appropriate permissions
- AWS CLI v2 configured (`aws configure`)
- Terraform >= 1.7
- Docker
- A verified SES email identity


### Email and AWS Setup

Go to terraform\environments\dev.tfvars


```hcl
aws_account_id = "YOUR_ACCOUNT_ID"
ses_from_email = "noreply@yourdomain.com"
```
```bash
aws sts get-caller-identity
```

```bash
aws ses verify-email-identity --email-address sudhanshugusain45@gmail.com --region us-east-1
```
Click on the link and your email is verified !!!




### Bootstrap Terraform state

Run once to create the S3 bucket and DynamoDB table for Terraform remote state:

```bash
aws s3 mb s3://docker-auditor-terraform-state-789438508565 --region us-east-1

aws dynamodb create-table --table-name docker-auditor-terraform-locks --attribute-definitions AttributeName=LockID,AttributeType=S --key-schema AttributeName=LockID,KeyType=HASH --billing-mode PAY_PER_REQUEST --region us-east-1
```

### Verify whther S3 and DynamoDB is created or not

```bash
aws s3 ls | findstr docker-auditor-terraform-state-789438508565

aws dynamodb describe-table --table-name docker-auditor-terraform-locks --query "Table.TableStatus"

```


### Run Teraaform

Go inside terraform directory

```bash
terraform init -backend-config="bucket=docker-auditor-terraform-state-789438508565" -backend-config="key=dev/terraform.tfstate" -backend-config="region=us-east-1" -backend-config="dynamodb_table=docker-auditor-terraform-locks"

```

```bash
terraform plan -var-file="environments/dev.tfvars"
```

```bash
terraform apply -var-file="environments/dev.tfvars"
```
It will take 15-20 mins to setup all the infrastructure...



### OPENAI and Langfuse Secret

For LangSmith project — yes, update dev.tfvars.

- Terraform sets LANGCHAIN_PROJECT = "docker-auditor-dev" automatically. So make sure whatver is written same name project is on Langsmith also

Then Generate API key for Langsmith and OPENAI and inject them using:

```bash
aws secretsmanager put-secret-value --secret-id "docker-auditor/dev/openai-api-key" --secret-string "{\"api_key\":\"sk-proj-abc123\"}"

```

```bash
aws secretsmanager put-secret-value --secret-id "docker-auditor/dev/langsmith-api-key" --secret-string "{\"api_key\":\"lsv2_pt_xxxxx\"}"
```


Verify whther they are stored or not:

```bash
aws secretsmanager get-secret-value --secret-id "docker-auditor/dev/openai-api-key" --query "SecretString"

```

```bash
aws secretsmanager get-secret-value --secret-id "docker-auditor/dev/langsmith-api-key" --query "SecretString"

```



### Push the Code to the Github

```bash
cd "d:\TESTING EVOLVUE\TESTING"

git init
git add .
git commit -m "Initial commit"
git branch -M main
git remote add origin https://github.com/YOUR_GITHUB_USERNAME/docker-image-auditor.git
git push -u origin main
```

### Step 6: Store API keys in Secrets Manager

```bash
OPENAI_SECRET=$(terraform output -raw openai_secret_name)
LANGSMITH_SECRET=$(terraform output -raw langsmith_secret_name)

aws secretsmanager put-secret-value \
  --secret-id "$OPENAI_SECRET" \
  --secret-string '{"api_key":"sk-..."}'

aws secretsmanager put-secret-value \
  --secret-id "$LANGSMITH_SECRET" \
  --secret-string '{"api_key":"ls__..."}'
```

### Step 7: Build and push initial images

```bash
FRONTEND_ECR=$(terraform output -raw frontend_ecr_url)
BACKEND_ECR=$(terraform output -raw backend_ecr_url)
WORKER_ECR=$(terraform output -raw worker_ecr_url)
ECS_CLUSTER=$(terraform output -raw ecs_cluster_name)

aws ecr get-login-password --region us-east-1 | \
  docker login --username AWS --password-stdin \
  "$(echo $FRONTEND_ECR | cut -d'/' -f1)"

docker build -t "$FRONTEND_ECR:latest" --target production ./frontend
docker build -t "$BACKEND_ECR:latest" ./backend
docker build -t "$WORKER_ECR:latest" ./worker

docker push "$FRONTEND_ECR:latest"
docker push "$BACKEND_ECR:latest"
docker push "$WORKER_ECR:latest"

for SVC in frontend backend worker; do
  aws ecs update-service \
    --cluster "$ECS_CLUSTER" \
    --service "docker-auditor-dev-${SVC}" \
    --force-new-deployment
done
```

After this, all future deployments are handled automatically by the CI/CD pipeline.

## CI/CD

| Branch | Action |
|--------|--------|
| Pull request to `main` | Runs tests, posts Terraform plan as PR comment |
| Push to `develop` | Runs tests → builds images → deploys to dev |
| Push to `main` | Runs tests → builds images → deploys to prod |

Manually trigger infrastructure changes via **Actions → Terraform → Run workflow**.

## Using the application

### Register and sign in

1. Open `https://yourdomain.com`
2. Click **Sign Up**, enter email and password (min 12 chars, uppercase, number, symbol)
3. Enter the verification code sent to your email
4. Sign in

### Connect a registry

1. Go to the **Connections** tab
2. Click **Add Connection**
3. For ECR: enter your AWS account ID and region
4. For Docker Hub: enter your username and access token
5. Credentials are stored encrypted in Secrets Manager

### Run a scan

1. Go to **Repositories** → select a repository → select an image tag
2. Click **Scan Image**
3. Watch real-time agent progress stream via WebSocket
4. View results: ring scores, CVE table, Dockerfile diff, executive summary

### Understand the scores

| Score | Meaning |
|-------|---------|
| 80–100 | Green — production ready |
| 60–79 | Yellow — minor issues |
| 40–59 | Orange — significant issues |
| 0–39 | Red — critical, do not deploy |

### Chat with the AI

Use the chat panel on any scan result to ask:
- "What are the top 3 CVEs I should fix first?"
- "How much would switching to distroless reduce image size?"
- "Explain the risk score for this image"

## Observability

### CloudWatch

Log groups:
- `/ecs/docker-auditor-{env}/frontend`
- `/ecs/docker-auditor-{env}/backend`
- `/ecs/docker-auditor-{env}/worker`

Dashboard: AWS Console → CloudWatch → Dashboards → `docker-auditor-{env}`

### LangSmith

Agent traces, prompts, and latency at https://smith.langchain.com → Project: `docker-auditor-{env}`

### X-Ray

Distributed traces: AWS Console → X-Ray → Traces → filter by `docker-auditor-{env}`

### Ragas evaluation

LLM quality metrics stored in DynamoDB table `docker-auditor-{env}-eval-results` and S3 `eval-reports` bucket after each scan.

## Common errors

**`UnauthorizedException` on API calls**
Cognito token expired (1-hour TTL). Sign out and sign in again.

**WebSocket connects but no progress events**
Check worker service is running: `aws ecs describe-services --cluster docker-auditor-dev --services docker-auditor-dev-worker`. Verify SQS queue URL and IAM permissions in CloudWatch worker logs.

**Scan stuck in `queued`**
Worker is not consuming from SQS. Check CloudWatch logs — common cause: invalid `OPENAI_API_KEY_SECRET_NAME` or missing Secrets Manager permissions.

**`ResourceNotFoundException` for DynamoDB**
Tables not yet created or wrong region. Confirm `terraform apply` completed successfully and `AWS_REGION` matches.

**ECR `no basic auth credentials`**
Re-run the ECR login command — credentials expire after 12 hours.

**`CertificateNotYetIssued` during Terraform apply**
ACM DNS validation takes 5–30 minutes. Re-run `terraform apply` — Terraform will resume waiting for the existing certificate.

## Teardown

```bash
cd terraform
terraform destroy \
  -var-file="environments/dev.tfvars" \
  -var="aws_account_id=YOUR_ACCOUNT_ID"
```

To preserve scan data, back up S3 buckets before destroying.

## Project structure

```
.
├── frontend/                  Next.js 14 TypeScript app
│   ├── src/app/              App Router pages
│   ├── src/components/       UI components (RingScore, FindingsTable, DockerfileTab, etc.)
│   ├── src/hooks/            useWebSocket, useScanProgress
│   ├── src/lib/              API client, Amplify auth
│   └── src/types/            TypeScript interfaces
├── backend/                   FastAPI REST + WebSocket server
│   └── app/
│       ├── api/v1/           connections, repositories, scans, images, chat, evals
│       ├── core/             Cognito JWT auth, AWS clients, config
│       ├── models/           Pydantic schemas
│       └── services/         SQS dispatch, Secrets Manager vault
├── worker/                    Async scan processor
│   └── app/
│       ├── agents/           7 LangGraph agents + orchestrator
│       ├── core/             AWS clients, config
│       └── services/         Ragas eval, WebSocket push, S3, SES
└── terraform/                 Infrastructure as code
    ├── modules/              14 modules: networking, ecr, auth, secrets, database,
    │                         storage, queue, cache, lambda, api, dns, monitoring, waf, ecs
    └── environments/         dev.tfvars, staging.tfvars, prod.tfvars
```
