# testing

Build a Production-Grade AI-Powered VAPT Platform
1. Objective

Build a production-oriented, modular AI-powered VAPT (Vulnerability Assessment and Penetration Testing) platform for applications that we own or are explicitly authorized to test.

The product should combine capabilities inspired by:

Burp Suite
OWASP Web Security Testing Guide
OWASP Top 10
OWASP API Security Top 10
DAST
Reconnaissance
API security testing
Browser-based application discovery
Automated security testing
Evidence-based vulnerability validation
AI-assisted security reasoning
Automated VAPT reporting

The system must NOT rely on an LLM alone to identify vulnerabilities.

The core principle is:

AI decides, security engines execute, evidence proves, validation confirms.

Never claim 100% vulnerability-detection accuracy. Instead, design the system for high coverage, low false positives, reproducibility, evidence-backed findings, and explicit confidence/status.

All scanning/testing functionality must enforce explicit target authorization and scope restrictions.

2. Primary Product Flow

Implement this end-to-end flow:

User
  |
  v
Create Project
  |
  v
Register Authorized Target
  |
  v
Define Scope
  |
  v
Reconnaissance
  |
  v
Asset Discovery
  |
  v
Browser / API Crawling
  |
  v
HTTP Proxy
  |
  v
HTTP History
  |
  v
Application Map
  |
  v
Authentication Context
  |
  v
AI Test Planner
  |
  v
Security Test Engine
  |
  +-----------------------------+
  |                             |
  v                             v
Custom Security Tests       External Scanners
  |                         ZAP / Nuclei / Nmap
  |                             |
  +-------------+---------------+
                |
                v
         Result Normalization
                |
                v
         Evidence Collection
                |
                v
         Validation Engine
                |
        +-------+-------+
        |               |
        v               v
    Confirmed        Rejected
        |
        v
   Finding Correlation
        |
        v
    AI Analysis
        |
        v
Risk / Severity / OWASP / CWE / CVSS
        |
        v
    VAPT Report
3. Technology Stack

Use the following stack unless there is a strong technical reason to change it.

Frontend
Next.js
React
TypeScript
Tailwind CSS
Component-based architecture
WebSocket support for live scan progress
Backend
Python 3.11+
FastAPI
Pydantic
SQLAlchemy
Alembic
Database
PostgreSQL
Queue / Background Jobs
Redis
Celery
Proxy

Use mitmproxy rather than implementing a complete HTTPS proxy from scratch.

The proxy must support:

HTTP
HTTPS interception
Request capture
Response capture
Request modification
Response inspection
Request replay
WebSocket traffic where supported
Scope enforcement
Browser Automation

Use Playwright.

Support:

Chromium
Login workflows
Navigation
Forms
Click actions
JavaScript-heavy applications
Network request discovery
Screenshots
Browser sessions
Containerization
Docker
Docker Compose for local development
Security Tools

Integrate existing security tools where appropriate rather than reimplementing them:

OWASP ZAP
Nmap
Nuclei

Build custom security tests for application-specific logic and tests that require application context.

Storage

Use:

PostgreSQL for metadata
S3-compatible storage / MinIO for large evidence objects

Store large:

request bodies
response bodies
screenshots
HTML
reports
scanner artifacts

outside the main database.

AI

Create an abstraction:

LLMProvider
    |
    +-- Groq
    +-- AWS Bedrock
    +-- Local Model
    +-- OpenAI-compatible provider

The application should not be tightly coupled to one LLM provider.

4. Repository Structure

Create:

vapt-agent/
│
├── frontend/
│   ├── app/
│   ├── components/
│   ├── features/
│   ├── lib/
│   └── types/
│
├── backend/
│   ├── app/
│   │   ├── api/
│   │   ├── core/
│   │   ├── models/
│   │   ├── schemas/
│   │   ├── services/
│   │   ├── agents/
│   │   ├── proxy/
│   │   ├── recon/
│   │   ├── browser/
│   │   ├── scanners/
│   │   ├── security_tests/
│   │   ├── evidence/
│   │   ├── validation/
│   │   ├── findings/
│   │   └── reports/
│   │
│   ├── alembic/
│   ├── tests/
│   └── requirements.txt
│
├── workers/
│   ├── scan_worker.py
│   ├── recon_worker.py
│   ├── browser_worker.py
│   └── validation_worker.py
│
├── proxy/
│   ├── mitm_addon.py
│   └── README.md
│
├── security-tests/
│   ├── authentication/
│   ├── authorization/
│   ├── injection/
│   ├── configuration/
│   ├── ssrf/
│   ├── api/
│   └── business_logic/
│
├── docker/
│   ├── Dockerfile.backend
│   ├── Dockerfile.worker
│   └── Dockerfile.frontend
│
├── docker-compose.yml
├── .env.example
├── README.md
└── docs/
    ├── architecture.md
    ├── security-model.md
    └── development.md
5. Core Data Model

Implement PostgreSQL models for at least:

users
projects
targets
scopes
assets
endpoints
parameters
authentication_profiles
browser_sessions
http_requests
http_responses
replays
scans
scan_tasks
security_tests
scanner_results
findings
finding_evidence
validation_runs
reports
ai_runs
audit_logs

Relationships:

Project
  |
  +-- Target
       |
       +-- Scope
       |
       +-- Assets
       |
       +-- Endpoints
       |
       +-- Authentication Profiles
       |
       +-- Scans
            |
            +-- Scan Tasks
            |
            +-- Scanner Results
            |
            +-- Findings
                  |
                  +-- Evidence
                  |
                  +-- Validation Runs

Use UUIDs for externally exposed identifiers.

6. Scope and Authorization System

This is mandatory.

Every target must have:

Target
Allowed domains
Allowed subdomains
Allowed IPs
Excluded domains
Excluded paths
Excluded methods
Allowed test categories
Rate limits

Before ANY automated request:

Request
  |
  v
Scope Validator
  |
  +-- Allowed --> Execute
  |
  +-- Not allowed --> Block

Implement a centralized:

ScopeValidator

that every scanner, browser worker, proxy action, replay operation, and security test must use.

Never allow a tool to bypass scope validation.

Add an audit log for blocked out-of-scope requests.

7. Project Management

Create UI and APIs for:

Create Project
Update Project
Delete Project
Create Target
Update Target
Define Scope
Start Scan
Stop Scan
View Scan
View Findings
Generate Report

Example:

Project:
ContractIQ Security Assessment

Target:
https://authorized-test.example.com

Scope:
*.authorized-test.example.com

Excluded:
 /logout
 /payment
 /admin/delete
8. Reconnaissance Engine

Build an authorized-target reconnaissance engine.

Capabilities:

DNS
Subdomains
IP addresses
Open services
HTTP/HTTPS services
Technology detection
robots.txt
sitemap.xml
JavaScript discovery
API discovery
Web crawling

Use external tools where appropriate.

Normalize everything into:

Asset

Example:

{
  "type": "api",
  "host": "api.example.com",
  "port": 443,
  "protocol": "https",
  "technology": ["FastAPI", "PostgreSQL"]
}

Do not perform unrestricted internet-wide reconnaissance.

Only operate within the configured scope.

9. HTTP Proxy

Integrate mitmproxy.

The proxy must capture:

HTTP method
URL
host
path
query parameters
headers
request body
response status
response headers
response body
timestamp
session
source

Store metadata in PostgreSQL.

Store large bodies in object storage.

Expose the traffic in the UI.

10. HTTP History UI

Create a Burp-like HTTP history interface.

Example:

HTTP History

GET     /login                 200
POST    /api/login             200
GET     /api/profile           200
GET     /api/users/123         200
POST    /api/contracts         201
PUT     /api/contracts/123     200

Features:

Search
Filter by method
Filter by status
Filter by endpoint
Filter by host
Filter by authentication context
View request
View response
Send to Repeater
Send to Scanner
Send to AI Analysis
11. Repeater

Build a Burp-like Repeater.

Flow:

HTTP History
    |
    v
Send to Repeater
    |
    v
Modify Request
    |
    v
Send
    |
    v
Target
    |
    v
Response

Support modification of:

URL
method
query parameters
headers
body

Display:

Original Request
Modified Request
Original Response
Modified Response
Response Diff

Implement structured response comparison for:

status
headers
JSON
response length
important fields
12. Browser Automation

Integrate Playwright.

Browser flow:

Playwright
    |
    v
Browser
    |
    v
Proxy
    |
    v
Target

Support:

Open URL
Login
Navigate
Click
Fill forms
Submit forms
Capture screenshots
Capture network requests
Save browser session
Discover API endpoints

All browser traffic must still pass through scope validation.

13. Application Mapper

Build an application graph.

Example:

Application
│
├── Authentication
│   ├── POST /login
│   └── POST /logout
│
├── Users
│   ├── GET /users
│   ├── GET /users/{id}
│   └── PUT /users/{id}
│
├── Contracts
│   ├── GET /contracts
│   ├── GET /contracts/{id}
│   ├── POST /contracts
│   └── DELETE /contracts/{id}
│
└── Admin
    ├── GET /admin/users
    └── DELETE /admin/users/{id}

Each endpoint should contain:

method
path
host
parameters
authentication
content_type
observed_roles
request_examples
response_examples
source
14. Authentication Profiles

Implement authentication profiles.

Examples:

Admin
Manager
Normal User
Read Only User
Unauthenticated

Store authentication mechanisms securely.

Support where appropriate:

JWT
Session Cookie
API Key
OAuth/OIDC
Custom Header
Username/Password

Never log secrets in plaintext.

Mask:

Authorization
Cookie
API-Key
Set-Cookie
Password
Tokens

in UI/logs unless explicitly authorized for controlled debugging.

15. Security Test Framework

Create a plugin-based architecture.

Every security test must implement a common interface:

class SecurityTest:

    def can_test(self, endpoint, context):
        ...

    def prepare_test(self, endpoint, context):
        ...

    def execute(self, test_case):
        ...

    def analyze(self, result):
        ...

    def collect_evidence(self, result):
        ...

Tests must be deterministic wherever possible.

16. Initial Security Tests

Implement the first version with:

Authentication
Authentication state validation
Session handling checks
JWT configuration checks
Cookie security flags
Authentication bypass indicators
Authorization
Broken access control
BOLA/IDOR
Role-based access comparison
Privilege boundary testing
Configuration
Security headers
CORS configuration
HTTP method exposure
TLS-related configuration checks
Cookie flags
Information disclosure
API Security
Missing authentication
Excessive data exposure
Parameter manipulation
API authorization
Object-level authorization
Function-level authorization
Injection

Implement controlled, validated tests for relevant injection classes.

Do not blindly send destructive payloads.

SSRF

Only perform controlled validation within the authorized assessment environment.

Do not use arbitrary third-party infrastructure as a validation target.

17. OWASP Mapping

Map tests to:

OWASP Top 10
OWASP API Security Top 10
OWASP WSTG
CWE
CVSS

Each finding should contain:

owasp_category
wstg_category
cwe
cvss
severity

Do not invent mappings. Keep mappings in a versioned configuration file.

18. External Scanner Integration

Create adapters for:

Nmap
OWASP ZAP
Nuclei

Architecture:

Scanner Adapter
      |
      v
Execute
      |
      v
Raw Result
      |
      v
Normalize
      |
      v
Validation
      |
      v
Finding

Create a standard internal result format:

{
  "scanner": "example",
  "target": "...",
  "endpoint": "...",
  "category": "...",
  "severity": "...",
  "evidence": {},
  "raw_result": {}
}

Never directly expose scanner-specific formats to the rest of the application.

19. Evidence Engine

Every candidate vulnerability must have evidence.

Evidence may contain:

Original request
Test request
Original response
Test response
Response diff
Screenshot
Browser state
Scanner output
Validation result
Timestamp
Authentication context

Create:

Evidence ID

and associate it with findings.

The AI must never be allowed to fabricate evidence.

20. Validation Engine

Implement:

Candidate
    |
    v
Validation
    |
    +--> Confirmed
    |
    +--> Rejected
    |
    +--> Needs Review

A finding should not become CONFIRMED simply because an LLM believes it exists.

Confirmation should require deterministic or reproducible evidence.

Store:

validation_status
validation_method
validation_attempts
validation_evidence
confidence
21. Finding Model

Create:

Finding

with:

id
title
description
severity
confidence
status
endpoint
method
parameter
owasp_category
wstg_category
cwe
cvss
impact
evidence
reproduction
remediation
references
created_at

Statuses:

SUSPECTED
VALIDATING
CONFIRMED
REJECTED
NEEDS_REVIEW
22. AI VAPT Agent

Only after the deterministic engine works, implement the AI layer.

The AI should act as an orchestrator/reasoning layer.

It receives:

Application Map
HTTP History
Authentication Context
Security Test Results
Evidence
Previous Findings

It should be able to call tools such as:

discover_assets()
get_application_map()
get_endpoint()
get_http_history()
replay_request()
compare_responses()
run_security_test()
validate_finding()
get_evidence()
get_findings()
correlate_findings()
generate_report()

The AI should NEVER directly bypass the security engine or scope manager.

23. AI Planner

Example:

AI sees:

GET /api/contracts/{id}

Authentication:
Employee
Manager
Admin

Observed resource ownership.

AI decides:

Run authorization comparison.

Employee -> own contract
Employee -> another employee's contract
Manager -> employee contract
Admin -> employee contract

Then the AI calls the authorization testing tool.

The tool executes the test.

The AI analyzes the resulting evidence.

This is the intended architecture:

AI
 |
 | decides
 v
Security Tool
 |
 | executes
 v
Evidence
 |
 | proves
 v
Validation
 |
 v
AI
 |
 | explains
 v
Finding
24. AI Guardrails

Implement strict rules:

AI cannot execute requests directly.
AI can only call registered tools.
Every tool call goes through ScopeValidator.
Dangerous/destructive operations require explicit approval.
No out-of-scope targets.
No arbitrary external callback infrastructure.
No credential extraction.
No secret exfiltration.
No destructive production actions.
Every AI action must be logged.

Create:

ai_action_log

with:

agent_id
tool
arguments
scope_check
result
timestamp
25. Scan Orchestration

Use Celery + Redis.

Do not execute long scans directly inside FastAPI.

Flow:

POST /scans
     |
     v
Create Scan
     |
     v
Queue Job
     |
     v
Redis
     |
     v
Celery Worker
     |
     +-- Recon
     +-- Browser
     +-- Proxy
     +-- Scanner
     +-- Validation
     |
     v
Update Scan Status

Statuses:

QUEUED
RECON
DISCOVERY
CRAWLING
TESTING
VALIDATING
COMPLETED
FAILED
CANCELLED

Support cancellation.

26. Dashboard

Create a professional security dashboard.

Display:

Target
Scan Status
Assets
Endpoints
Requests
Findings

Severity summary:

Critical
High
Medium
Low
Informational

Also show:

Confirmed Findings
Suspected Findings
Rejected Findings
False Positive Rate
Endpoints Tested
Security Tests Executed
Coverage

Do not represent unconfirmed findings as confirmed vulnerabilities.

27. Finding Details UI

Example:

Broken Object Level Authorization

Severity: HIGH
Confidence: HIGH
Status: CONFIRMED

Endpoint:
GET /api/contracts/{id}

OWASP:
API Security

CWE:
...

CVSS:
...

Description:
...

Evidence:
[Request]
[Response]
[Comparison]

Reproduction:
...

Impact:
...

Remediation:
...

[View HTTP Request]
[View Evidence]
[Run Validation Again]
28. AI Security Assistant

Add a chat panel.

Example:

User:

"Why is this finding high severity?"

AI:

"The endpoint exposes contract information to a user
who does not have authorization for that contract.
The finding was confirmed through a reproducible
authorization comparison."

Other supported questions:

What are the highest-risk findings?
Why was this endpoint tested?
Which OWASP categories are not covered?
Show me the evidence for this finding.
What should developers fix first?
Are these two findings duplicates?

The AI must answer using actual stored evidence and findings.

Do not hallucinate.

29. Report Generation

Generate:

HTML
PDF
JSON

Report sections:

Executive Summary
Scope
Methodology
Assets
Application Overview
Testing Coverage
Risk Summary
Detailed Findings
Evidence
Reproduction
OWASP Mapping
CWE
CVSS
Remediation
Appendix
30. API Design

Create REST APIs such as:

POST   /api/projects
GET    /api/projects
POST   /api/projects/{id}/targets

POST   /api/targets/{id}/scope
GET    /api/targets/{id}/assets

POST   /api/scans
GET    /api/scans/{id}
POST   /api/scans/{id}/cancel

GET    /api/http-history
GET    /api/http-history/{id}

POST   /api/repeater
POST   /api/repeater/{id}/execute

GET    /api/endpoints
GET    /api/findings
GET    /api/findings/{id}

POST   /api/findings/{id}/validate

POST   /api/ai/analyze
POST   /api/ai/chat

POST   /api/reports
GET    /api/reports/{id}

Use OpenAPI automatically through FastAPI.

31. WebSocket Events

Implement live scan events:

scan.started
scan.progress
asset.discovered
endpoint.discovered
request.captured
test.started
test.completed
finding.created
finding.confirmed
scan.completed

Frontend should update without refreshing.

32. Security Requirements

This is a security product, so apply strong security practices to the product itself.

Implement:

Authentication
RBAC
Secure password handling
OAuth/OIDC-ready architecture
Secrets management
Encryption in transit
Encryption at rest where appropriate
Audit logging
Input validation
Rate limiting
SSRF protections
Scope enforcement
Scanner isolation
Container isolation
No secrets in logs
Mask sensitive headers
Secure file handling

Scanner workers should run in isolated containers.

33. Testing Strategy

Create unit tests for:

ScopeValidator
Finding normalization
Evidence engine
Response comparison
Authentication context
Authorization logic
CVSS calculation
OWASP mapping

Integration tests for:

Proxy → Backend
Browser → Proxy → Target
Scanner → Normalizer
Test → Evidence → Validation
AI → Tool → Evidence

End-to-end tests should use a deliberately vulnerable local test application.

Do NOT test against random public applications.

Create a local security test target/container specifically for development.

34. Local Test Environment

Create a Docker-based test environment containing an intentionally vulnerable application.

Use it to validate:

Authentication
Authorization
IDOR/BOLA
Security headers
Injection classes
Configuration
API security

The VAPT platform should be able to scan this local authorized target end-to-end.

The acceptance test is:

Test Application
       |
       v
Recon
       |
       v
Discovery
       |
       v
Security Testing
       |
       v
Evidence
       |
       v
Validation
       |
       v
Finding
       |
       v
Report
35. Logging and Observability

Use structured logging.

Every important action should have:

timestamp
user_id
project_id
target_id
scan_id
task_id
action
result
duration

Add metrics:

requests_processed
tests_executed
findings_created
findings_confirmed
findings_rejected
scan_duration
scanner_errors
AI_calls
AI_latency
36. Development Phases

Do NOT attempt to implement everything in one step.

Implement sequentially.

Phase 1

Build:

Repository
Docker
FastAPI
Next.js
PostgreSQL
Redis
Project
Target
Scope
Authentication

Acceptance:

User can create project
User can add target
User can define allowed scope
Phase 2

Build:

mitmproxy
HTTP capture
HTTP history
Request viewer
Response viewer

Acceptance:

Browser traffic appears in HTTP History.
Phase 3

Build:

Repeater
Request modification
Replay
Response diff

Acceptance:

User can modify and replay an authorized request.
Phase 4

Build:

Playwright
Browser session
Login
Crawling
Network discovery

Acceptance:

Browser can navigate authorized target and discover APIs.
Phase 5

Build:

Application map
Endpoint inventory
Authentication profiles

Acceptance:

Application is represented as structured endpoints/resources/roles.
Phase 6

Build:

Security Test Framework
First OWASP tests
Evidence Engine
Validation Engine

Acceptance:

Platform can detect and confirm vulnerabilities in the local
intentionally vulnerable test application.
Phase 7

Integrate:

Nmap
OWASP ZAP
Nuclei

Acceptance:

External scanner results are normalized into internal findings.
Phase 8

Build:

AI Planner
AI Tool Calling
AI Finding Analysis
AI Correlation
AI Remediation

Acceptance:

AI can select appropriate tests and explain confirmed findings
using actual evidence.
Phase 9

Build:

Dashboard
AI Chat
Reports
PDF
JSON
HTML
Phase 10

Production hardening:

RBAC
Audit
Scanner isolation
Secrets management
Observability
Performance
Security testing
37. Critical Architectural Rule

Maintain this separation throughout the codebase:

                AI LAYER
                    |
                    | planning/reasoning
                    v
             SECURITY ENGINE
                    |
                    | execution
                    v
                 TARGET
                    |
                    | response/evidence
                    v
             VALIDATION ENGINE
                    |
                    v
                FINDING

Never implement:

LLM → arbitrary HTTP request → Internet

Instead:

LLM
 ↓
Registered Tool
 ↓
Scope Validator
 ↓
Security Engine
 ↓
Authorized Target
 ↓
Evidence
 ↓
Validation
38. Coding Standards

Follow these rules:

Production-quality Python
Type hints
Pydantic models
Async FastAPI where appropriate
Dependency injection
Clear service boundaries
Repository pattern where useful
No giant files
No hard-coded credentials
Environment variables
.env.example
Proper exception handling
Structured logging
Unit tests
Integration tests
Docker support
API documentation
Clear README
Database migrations
No duplicated business logic

Do not create fake implementations just to make the UI appear functional.

If a feature cannot yet be implemented, create a clearly marked interface/TODO and continue with the actual working parts.

39. Definition of Done for MVP

The MVP is complete only when the following works end-to-end against a local intentionally vulnerable application:

1. User logs in
2. Creates project
3. Adds authorized target
4. Defines scope
5. Starts scan
6. Recon runs
7. Browser crawler runs
8. HTTP traffic is captured
9. HTTP history appears
10. User can replay a request
11. Application map is generated
12. Security tests execute
13. Evidence is captured
14. Candidate findings are validated
15. Confirmed findings are stored
16. OWASP/CWE/CVSS mapping is generated
17. AI analyzes findings
18. AI explains findings using evidence
19. Report is generated
20. User can download/view report
40. Important Product Principle

This product should ultimately behave like:

             BURP-LIKE ENGINE
                    +
             AUTOMATED RECON
                    +
             BROWSER AGENT
                    +
             OWASP TESTING
                    +
           MULTI-SCANNER ENGINE
                    +
          EVIDENCE VALIDATION
                    +
             AI SECURITY AGENT
                    +
             VAPT REPORTING

The final goal is:

An authorized AI-assisted security engineer that can discover an application's attack surface, understand its API and authentication model, select appropriate security tests, execute those tests through deterministic security tooling, validate findings using reproducible evidence, correlate and prioritize vulnerabilities, and generate an enterprise-grade VAPT report.

Do not claim 100% vulnerability detection accuracy. Optimize for coverage + evidence quality + reproducibility + low false positives + validated findings.

41. Implementation Instruction

Start implementation with Phase 1 only.

Do not jump directly to the AI agent.

First create:

FastAPI
PostgreSQL
Redis
Next.js
Docker Compose
Authentication
Project management
Target management
Scope management
Database migrations

Then verify Phase 1 works.

After Phase 1 is functional, proceed to Phase 2.

At the end of every phase:

Run tests.
Fix errors.
Update README.
Document implemented APIs.
Verify Docker startup.
Verify database migrations.
Verify frontend/backend integration.
Provide a concise implementation summary.
List remaining TODOs.
Do not mark unimplemented features as completed.

Build incrementally and keep every phase runnable.
