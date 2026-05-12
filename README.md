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

**Infrastructure:** ECS Fargate, DynamoDB, ElastiCache Redis, SQS FIFO, API Gateway WebSocket, Cognito, Secrets Manager, SES, S3 + Glacier, Lambda (Trivy), Inspector2, WAFv2, Route53, ACM, CloudWatch

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
github_org         = "data-guru0"
github_repo        = "TESTING-MAJOR-22"
```
```bash
aws sts get-caller-identity
```

```bash
aws ses verify-email-identity --email-address sudhanshugusain45@gmail.com --region us-east-1
```

Verify whather your email is done or not:

```bash
aws ses get-identity-verification-attributes --identities sudhanshugusain45@gmail.com --region us-east-1
```
Click on the link and your email is verified !!!


## Sentry Setup

### 1. Create a Sentry Account

1. Go to https://sentry.io
2. Click **Sign Up**
3. Create your free account
4. Verify your email address

---

### 2. Create Backend Project (FastAPI + Worker)

1. Click **Create Project**
2. Under **Platform**, select **FastAPI**
3. Set the project name:

```bash
docker-auditor-backend
```

4. Click **Create Project**

After creation, Sentry will show a **DSN** similar to:

```bash
https://abc123@o123456.ingest.sentry.io/789
```

Copy and save this DSN — it will be used in your backend environment variables.

---

## 3. Create Frontend Project (Next.js)

1. Click **+ Create Project**
2. Under **Platform**, select **Next.js**
3. Set the project name:

```bash
docker-auditor-frontend
```

4. Click **Create Project**

Sentry will again show a **DSN** similar to:

```bash
https://xyz456@o123456.ingest.sentry.io/123
```

Copy and save this DSN — it will be used in your frontend environment variables.


### Grafana Cloud
1. Add new connection
2. Select OTLP
3. SDK
4. Python
5. Linux
6. Direct
7. Geneerate a grafana token
8. From that page I only needed two things:

```bash

OTLP Endpoint — shown on the page as:
https://otlp-gateway-prod-ap-south-1.grafana.net/otlp

Auth header — shown in the example command as:
OTEL_EXPORTER_OTLP_HEADERS="Authorization=Basic%20MTYzMTgx..."

Both went into terraform/environments/dev.tfvars:

otel_exporter_otlp_endpoint = "https://otlp-gateway-prod-ap-south-1.grafana.net/otlp"
otel_exporter_otlp_headers  = "Authorization=Basic%20MTYzMTgx..."
```

### These should exist for Terraform running

Run once to create the S3 bucket and DynamoDB table for Terraform remote state:
```bash
aws iam create-open-id-connect-provider --url https://token.actions.githubusercontent.com --client-id-list sts.amazonaws.com --thumbprint-list 1b511abead59c6ce207077c0bf0e0043b1382612
```

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

```bash
terraform destroy -var-file="environments/dev.tfvars"
```


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

### Add Github Secrets

GitHub → Settings → Secrets and variables → Actions → New repository secret


Add the following 9 secrets to the repository:

| Secret Name | Value |
|---|---|
| `AWS_DEPLOY_ROLE_ARN` | `arn:aws:iam::789438508565:role/docker-auditor-dev-github-deploy` |
| `AWS_TERRAFORM_ROLE_ARN` | `arn:aws:iam::789438508565:role/docker-auditor-dev-github-terraform` |
| `AWS_ACCOUNT_ID` | `789438508565` |
| `TF_STATE_BUCKET` | `docker-auditor-terraform-state-789438508565` |
| `TF_LOCK_TABLE` | `docker-auditor-terraform-locks` |




| Secret Name | Value |
|---|---|
| `COGNITO_USER_POOL_ID` | `us-east-1_A86f32tcr` |
| `COGNITO_CLIENT_ID` | `3el8qdu5bdv7c0vtm03flg6vba` |
| `NEXT_PUBLIC_API_URL` | `http://docker-auditor-dev-backend-904913202.us-east-1.elb.amazonaws.com` |
| `NEXT_PUBLIC_WS_URL` | `wss://qdu7bk7qlj.execute-api.us-east-1.amazonaws.com/dev` |




- TF_STATE_BUCKET is the S3 bucket
- TF_LOCK_TABLE is the DynamoDB Table name
---

- Add SENTRY frontend DNS also in github secrets: 
- Name: NEXT_PUBLIC_SENTRY_DSN
- Value: https://ab2fc5f13383b74e531e8094feb53229@o4511369794158592.ingest.us.sentry.io/4511369866051584

---
### Execute the CICD Pipelines

Push changes to Github and Pipeline will execute...

- Terraform Pipeline
- CICD Deployment piepline

Watch pieplines go green then from terraform outputs get Public URL and open it!!


### Security Rules to check

In AWS Console:

- Click Edit inbound rules
- Find the HTTP port 80 rule
- Change Source from 10.0.0.0/16 to 0.0.0.0/0
- Click Save rules
This will allow internet traffic to reach the backend ALB on port 80.


### Testing Phase
```bash
aws ecr create-repository --repository-name bad-image-test --region us-east-1
```

- Create a folder bad-image/ and put these two files in it: bad-image/Dockerfile:

```dockerfile
FROM python:3.8

RUN apt-get update
RUN apt-get install -y curl wget git vim nano gcc build-essential libssl-dev
RUN apt-get install -y openssh-client nmap netcat

COPY . /app

RUN pip install flask requests boto3 pytest black flake8 jupyter pandas numpy

ENV SECRET_KEY=mysupersecretkey123
ENV DATABASE_PASSWORD=admin123
ENV AWS_ACCESS_KEY_ID=AKIAIOSFODNN7EXAMPLE

EXPOSE 22
EXPOSE 80

CMD ["python", "/app/app.py"]

```

bad-image/app.py also

```python
print("bad image running")
```


```bash
aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin 789438508565.dkr.ecr.us-east-1.amazonaws.com
```

```bash
docker build -t bad-image-test .
```

```bash
docker tag bad-image-test:latest 789438508565.dkr.ecr.us-east-1.amazonaws.com/bad-image-test:latest
```

```bash
docker push 789438508565.dkr.ecr.us-east-1.amazonaws.com/bad-image-test:latest
```


---------------------------------------------------------------------------------
---------------------------------------------------------------------------------
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
