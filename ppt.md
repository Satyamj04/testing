# Build an Interactive AWS + Salesforce Technical Presentation Webpage

Create a complete, polished, interactive presentation website for an internal technical session explaining **AWS, Salesforce, their differences, service-level comparison, real-world use cases, and our AWS + Salesforce Security Incident Management project**.

The website must feel like a professional technical presentation/demo — NOT like a generic AI-generated dashboard.

## 1. TECHNOLOGY STACK

Use:

- React
- TypeScript
- Tailwind CSS
- Lucide React icons
- Framer Motion for subtle animations
- Responsive design
- Reusable components
- Clean component architecture

Create reusable components such as:

- PresentationLayout
- Section
- ServiceCard
- ComparisonTable
- ArchitectureDiagram
- FlowDiagram
- UseCaseCard
- ImplementationTimeline
- StatusBadge
- Quiz
- CodeBlock
- Navigation
- PresentationMode

Do not introduce unnecessary technologies.

---

# 2. OVERALL LEARNING FLOW

The presentation should follow this exact learning path:

AWS
↓
Salesforce
↓
AWS vs Salesforce
↓
Service-by-service comparison
↓
Top 5 important services
↓
When to use AWS / Salesforce / Both
↓
4 real-world use cases
↓
Our Security Incident Management project
↓
Architecture
↓
End-to-end implementation
↓
Testing/demo explanation
↓
AI / Amazon Bedrock
↓
Project status
↓
Interactive quiz
↓
Final summary

---

# 3. LANDING / TITLE SECTION

Create an attractive opening presentation slide.

Title:

# AWS + Salesforce

Subtitle:

## Cloud Infrastructure + Business Workflow + AI

Additional text:

"Understanding AWS and Salesforce through real-world architecture and implementation."

Show two visual sides:

AWS
"Build, process, store and analyze"

Salesforce
"Manage, investigate, automate and report"

Animated connection between them.

CTA:

"Start Presentation"

Secondary button:

"Explore Project"

---

# 4. WHAT IS AWS?

Create a simple explanation suitable for someone who is new to cloud.

Title:

## What is AWS?

Explain:

"AWS (Amazon Web Services) is a cloud platform that provides infrastructure and managed services for building and running applications."

Use an easy example.

Example:

Suppose we build an online shopping application.

AWS can provide:

User requests
↓
API
↓
Application processing
↓
Database
↓
File storage
↓
Monitoring

Explain that instead of purchasing and maintaining physical servers, we can use AWS cloud services.

Show simple animated architecture.

---

# 5. AWS SIMPLE REAL-WORLD EXAMPLE

Create a visual example:

User
↓
API Gateway
↓
Lambda
↓
DynamoDB

Explain each component in simple language:

API Gateway:
"Receives requests from users/applications."

Lambda:
"Runs backend code without managing servers."

DynamoDB:
"Stores application data."

Add a small example:

User clicks "Login"

→ API Gateway receives request
→ Lambda processes login
→ DynamoDB stores/retrieves data
→ Response goes back to user

---

# 6. WHAT IS SALESFORCE?

Create a simple explanation.

Title:

## What is Salesforce?

Explain:

"Salesforce is a cloud-based CRM and business application platform used to manage customers, business processes, workflows, data and automation."

Use an easy example.

Example:

A company receives a customer issue.

Salesforce can manage:

Customer
↓
Case
↓
Assigned employee
↓
Investigation
↓
Resolution
↓
Closure

Explain that Salesforce is focused heavily on business processes, CRM, workflows and enterprise operations.

---

# 7. SALESFORCE SIMPLE EXAMPLE

Create visual workflow:

Customer reports issue
↓
Salesforce Case
↓
Assign employee
↓
Investigate
↓
Resolve
↓
Close

Explain:

"Salesforce helps organizations manage what happens after a business event occurs."

---

# 8. AWS VS SALESFORCE

Create an attractive comparison.

Important:

Do NOT say that AWS and Salesforce are direct competitors.

Explain:

"They solve different categories of problems and can work together."

Comparison:

| Area | AWS | Salesforce |
|---|---|---|
| Main purpose | Cloud infrastructure and services | CRM/business platform |
| Application logic | Lambda, ECS, EC2, etc. | Apex, Flow, etc. |
| Database | DynamoDB, RDS, etc. | Salesforce Objects |
| API | API Gateway | Salesforce REST APIs |
| Automation | Lambda, Step Functions, EventBridge | Flow, Apex |
| Identity | IAM, Cognito | Salesforce Identity |
| Monitoring | CloudWatch | Salesforce monitoring/tools |
| Business workflow | Usually custom-built | Native workflows |
| CRM | Not its primary purpose | Core capability |
| AI | Bedrock | Einstein / Salesforce AI |
| Infrastructure | Highly customizable | Managed SaaS platform |

Add an important note:

"AWS provides cloud building blocks. Salesforce provides a business application platform."

---

# 9. SERVICE-WISE COMPARISON

Create a detailed but easy-to-understand service comparison.

Use wording:

"Closest conceptual comparison"

Do NOT claim the services are technically equivalent.

Create cards for:

1. AWS Lambda vs Salesforce Apex
2. API Gateway vs Salesforce REST API
3. DynamoDB vs Salesforce Custom Objects
4. IAM vs Salesforce Permission Sets / Profiles
5. Amazon Bedrock vs Salesforce Einstein / AI capabilities

For every service, show:

- What it is
- Why we use it
- Simple example
- How it works
- When to use it
- AWS example
- Salesforce conceptual counterpart

---

# 10. TOP 5 AWS + SALESFORCE SERVICES

Create a section called:

## Top 5 Services You Should Know

For each service, create a detailed expandable card.

---

## SERVICE 1 — AWS LAMBDA

Definition:

"AWS Lambda is a serverless compute service that runs code in response to events without requiring us to manage servers."

Why use it:

- No server management
- Event-driven execution
- Automatic scaling
- Good for APIs and processing
- Pay based on usage

How we use it:

User/API request
↓
API Gateway
↓
Lambda
↓
Business logic
↓
Database

Example:

A suspicious login reaches API Gateway.

Lambda:

- Reads the event
- Calculates risk
- Determines severity
- Stores the event
- Sends incident information to Salesforce

Salesforce conceptual comparison:

Apex

Explain:

"Apex is Salesforce's programming language for implementing custom business logic inside Salesforce."

Important:

"Lambda and Apex are not technically equivalent. They are a conceptual comparison of where backend/business logic can execute."

---

# 11. SERVICE 2 — API GATEWAY

Definition:

"Amazon API Gateway is a managed service used to create, publish and manage APIs."

Why use it:

- Receives HTTP requests
- Connects frontend applications to backend services
- Provides API management
- Supports authentication and authorization mechanisms
- Acts as an entry point

Example:

Frontend
↓
POST /security/login
↓
API Gateway
↓
Lambda

Salesforce comparison:

Salesforce REST API

Explain:

"Salesforce provides REST APIs that allow external applications to interact with Salesforce data and functionality."

---

# 12. SERVICE 3 — DYNAMODB

Definition:

"Amazon DynamoDB is a fully managed NoSQL database designed for high-performance applications."

Why use it:

- Fast reads/writes
- Serverless
- Automatic scaling
- Flexible schema
- Good for event data

Our example:

SecurityLoginEvents

Store:

- Event ID
- User
- IP address
- Failed attempts
- Risk score
- Severity
- Detection result
- Reasons
- Timestamp

Flow:

Security Event
↓
Lambda
↓
DynamoDB

Salesforce conceptual comparison:

Salesforce Custom Object

Important:

"DynamoDB and Salesforce Custom Objects are NOT technically equivalent databases. They serve different architectural purposes."

---

# 13. SERVICE 4 — IAM

Definition:

"AWS IAM controls who or what can access AWS resources and what actions they are allowed to perform."

Why use it:

- Authentication
- Authorization
- Least privilege
- Resource access control

Our project example:

Lambda execution role:

security-incident-processor-role

Permissions include access required for:

- DynamoDB
- Secrets Manager
- Bedrock when enabled

Salesforce conceptual comparison:

- Profiles
- Permission Sets
- Permission Set Groups
- Roles

Explain that Salesforce permissions control access to Salesforce resources and records.

---

# 14. SERVICE 5 — AMAZON BEDROCK

Definition:

"Amazon Bedrock is a managed AWS service that provides access to foundation models through APIs."

Why use it:

- AI-generated analysis
- Text generation
- Summarization
- Classification
- Recommendations

Our planned use:

Security Incident
↓
Bedrock
↓
AI Explanation
↓
Recommended Action
↓
Risk Summary

Example:

Input:

Risk Score: 100
Severity: CRITICAL
Reasons:
- Multiple failed attempts
- New IP
- New location
- New device
- Impossible travel
- Suspicious IP

AI output:

Explanation:
"The login is highly suspicious because multiple independent security indicators were detected."

Recommended action:
"Temporarily lock the account, verify the user's identity, investigate the IP address and review recent authentication activity."

Risk summary:

"CRITICAL — immediate investigation required."

Important project status:

Amazon Bedrock is currently pending because AWS account/model access is not available yet.

Do NOT pretend Bedrock is currently working.

---

# 15. WHEN SHOULD WE USE AWS?

Create a decision-style section.

Use AWS when we need:

- Custom backend
- APIs
- Serverless processing
- Large-scale infrastructure
- Event processing
- Databases
- Cloud-native applications
- AI infrastructure
- High customization

Example:

"We need to process millions of events and run custom backend logic."

AWS is a strong choice.

---

# 16. WHEN SHOULD WE USE SALESFORCE?

Use Salesforce when we need:

- CRM
- Customer management
- Case management
- Business workflows
- Enterprise records
- User assignment
- Approval processes
- Business reporting
- Sales/service operations

Example:

"Once a security incident is detected, analysts need to investigate, assign, update and resolve the incident."

Salesforce is a strong choice.

---

# 17. WHEN SHOULD WE USE BOTH?

Use both when:

"One system needs strong technical processing and another system needs business workflow management."

Example:

AWS:

Detect and process security events.

Salesforce:

Manage and resolve security incidents.

Architecture:

Application
↓
AWS
↓
Security Analysis
↓
Salesforce
↓
Incident Management

---

# 18. FOUR REAL-WORLD USE CASES

Create exactly 4 use cases.

## USE CASE 1 — Security Incident Management

AWS:

- Detect event
- Process event
- Calculate risk
- Store event
- AI analysis

Salesforce:

- Create incident
- Assign analyst
- Investigate
- Track remediation
- Resolve
- Close

---

## USE CASE 2 — E-Commerce

AWS:

- Application backend
- APIs
- Database
- Event processing

Salesforce:

- Customer management
- Support cases
- Customer communication
- Service workflow

---

## USE CASE 3 — Banking / Financial Services

AWS:

- Transaction processing
- Fraud detection
- Event processing
- Data processing

Salesforce:

- Customer relationship
- Service cases
- Investigation workflow
- Employee assignment

---

## USE CASE 4 — Healthcare / Enterprise Service

AWS:

- Application infrastructure
- APIs
- Data processing

Salesforce:

- Customer/patient service workflows where appropriate
- Case management
- Assignment
- Business processes
- Reporting

Make every use case simple and visual.

---

# 19. OUR PROJECT

Create a major section:

# Security Incident Management System

Subtitle:

## AWS + Salesforce

Explain the objective:

"When a suspicious login occurs, AWS detects and analyzes the event, while Salesforce manages the resulting security incident."

---

# 20. OUR PROJECT ARCHITECTURE

Create an attractive animated architecture diagram.

Use:

User
↓
Login Request
↓
API Gateway
↓
AWS Lambda
↓
Risk Analysis
↓
DynamoDB
↓
Salesforce REST API
↓
Security Incident

Then:

Security Incident
↓
Salesforce
↓
Investigation
↓
Containment
↓
Remediation
↓
Verification
↓
Resolution
↓
Closure

And planned:

Security Incident
↓
Amazon Bedrock
↓
AI Analysis
↓
Recommended Action
↓
Salesforce

Use animated data flow.

---

# 21. OUR ACTUAL IMPLEMENTATION

Show what has actually been built.

### AWS

Implemented:

- Lambda
- Risk calculation
- Suspicious login detection
- DynamoDB
- API Gateway
- IAM
- Secrets Manager

### Salesforce

Implemented:

- Salesforce Custom Object
- Security_Incident1__c
- OAuth integration
- Salesforce REST API
- Automatic Security Incident creation

### Integration

Implemented:

AWS Lambda
↓
Salesforce REST API
↓
Security_Incident1__c

### AI

Planned:

AWS Lambda
↓
Amazon Bedrock
↓
AI Security Recommendation
↓
Salesforce

Clearly mark Bedrock as pending.

---

# 22. END-TO-END IMPLEMENTATION STEPS

Create an animated horizontal/vertical timeline.

## STEP 1

Create AWS Lambda.

Function:

security-incident-processor

---

## STEP 2

Implement security risk calculation.

Factors include:

- Failed login attempts
- New IP
- New location
- New device
- Impossible travel
- Suspicious IP

Calculate:

Risk Score
Severity
Detected
Reasons

---

## STEP 3

Create DynamoDB table.

Table:

SecurityLoginEvents

Store security event information.

---

## STEP 4

Create IAM role.

Role:

security-incident-processor-role

Give only the permissions required by Lambda.

Explain least privilege.

---

## STEP 5

Create API Gateway.

Endpoint:

POST /security/login

Flow:

Frontend/Postman
↓
API Gateway
↓
Lambda

---

## STEP 6

Test Lambda/API using Postman.

Use real backend requests.

Example endpoint:

POST

{{API_GATEWAY_URL}}/security/login

Example body:

{
  "eventType": "LOGIN",
  "user": "john.smith",
  "ipAddress": "185.100.50.25",
  "failedAttempts": 6,
  "newIp": true,
  "newLocation": true,
  "newDevice": true,
  "impossibleTravel": true,
  "suspiciousIp": true
}

Explain:

The backend calculates the risk dynamically.

Do not hardcode the response.

---

## STEP 7

Create Salesforce Custom Object.

Object:

Security_Incident1__c

This represents a security incident in Salesforce.

---

## STEP 8

Configure Salesforce OAuth.

Allow AWS Lambda to authenticate with Salesforce.

---

## STEP 9

Store Salesforce credentials/secret in AWS Secrets Manager.

Secret:

security/salesforce/integration

Explain:

Secrets should not be hardcoded inside Lambda code.

---

## STEP 10

Give Lambda permission to access required AWS resources.

Examples:

- DynamoDB
- Secrets Manager
- Bedrock when enabled

---

## STEP 11

Lambda calls Salesforce REST API.

Flow:

Lambda
↓
Salesforce OAuth access
↓
Salesforce REST API
↓
Security_Incident1__c

---

## STEP 12

Salesforce creates Security Incident.

Incident contains information such as:

- Event ID
- User
- IP
- Risk Score
- Severity
- Detection reasons
- Status

---

## STEP 13

Build frontend/login simulator.

The frontend sends real login/security events to:

API Gateway
↓
Lambda

The presentation should explain this, but the actual simulator will be demonstrated manually.

---

## STEP 14

Connect frontend to API Gateway.

Frontend configuration:

VITE_API_URL

Frontend must communicate only with API Gateway.

Never expose:

- AWS credentials
- Salesforce credentials
- OAuth secrets
- Secrets Manager values

---

## STEP 15

Add AI using Amazon Bedrock.

Planned flow:

Security Incident
↓
Bedrock
↓
AI Explanation
↓
Recommended Action
↓
Risk Summary

---

## STEP 16

Display AI recommendation inside Salesforce.

Final workflow:

Security Event
↓
AWS Detection
↓
Risk Analysis
↓
DynamoDB
↓
Salesforce Incident
↓
AI Analysis
↓
Recommended Action
↓
Investigation
↓
Resolution
↓
Closure

---

# 23. PROJECT STATUS

Create attractive status badges.

### IMPLEMENTED

AWS Lambda: IMPLEMENTED

Risk Analysis: IMPLEMENTED

DynamoDB: IMPLEMENTED

API Gateway: IMPLEMENTED

IAM: IMPLEMENTED

Salesforce OAuth: IMPLEMENTED

Salesforce Incident Creation: IMPLEMENTED

Secrets Manager: IMPLEMENTED

### INTEGRATION / DEMONSTRATION

Frontend Login Simulator: INTEGRATION

Real-Time Dashboard: INTEGRATION

### PENDING

Amazon Bedrock AI: PENDING AWS ACCOUNT/MODEL ACCESS

Explain:

"Amazon Bedrock testing is currently blocked by AWS account/model access verification. The AI architecture is designed and can be enabled once access is available."

Do not show fake AI output as a live result.

---

# 24. SECURITY ARCHITECTURE PRINCIPLES

Create a short section explaining:

### Least Privilege

Lambda receives only required permissions.

### Secret Management

Salesforce credentials are stored in AWS Secrets Manager.

### API Separation

Frontend communicates with API Gateway rather than directly accessing AWS/Salesforce credentials.

### Backend Processing

Risk calculation happens on the backend.

### No Hardcoded Secrets

Never expose credentials in frontend code.

---

# 25. PRESENTATION MODE

Add a prominent:

"Presentation Mode"

button.

When enabled:

- Hide unnecessary navigation
- Show one major section at a time
- Keyboard arrows navigate slides
- Space = next slide
- Left arrow = previous slide
- Right arrow = next slide
- Escape = exit presentation mode

Show slide number:

01 / 18

Use smooth slide transitions.

---

# 26. INTERACTIVE QUIZ

Create an interactive 10-question quiz.

Questions:

1. What is AWS?
2. What is Salesforce?
3. What is AWS Lambda?
4. Why do we use API Gateway?
5. What is DynamoDB?
6. What is IAM?
7. What is Apex?
8. What is a Salesforce Custom Object?
9. Why connect AWS and Salesforce?
10. What happens when a suspicious login occurs?

Each question should have multiple-choice answers.

After answering:

- Show correct/incorrect
- Show correct answer
- Show explanation
- Update score

At the end:

0–3:

Beginner

4–6:

Good

7–8:

Strong

9–10:

Cloud + Salesforce Pro

Add:

"Restart Quiz"

button.

Use animations for correct and incorrect answers.

---

# 27. FINAL SUMMARY

Create a visually strong final slide.

AWS:

→ Detect
→ Process
→ Store
→ Analyze
→ AI

Salesforce:

→ Manage
→ Investigate
→ Assign
→ Resolve
→ Report

Together:

# AWS + Salesforce

## Technical Intelligence + Business Workflow

Final message:

"Cloud infrastructure handles the event.
Salesforce manages the incident.
AI helps the analyst decide what to do next."

---

# 28. TECHNICAL ACCURACY REQUIREMENTS

This is extremely important.

Do NOT claim:

Lambda = Apex

Instead say:

"Closest conceptual comparison"

Do NOT claim:

DynamoDB = Salesforce Custom Object

Explain that they have different roles.

Do NOT claim:

Salesforce is an AWS replacement.

Do NOT claim:

AWS is a Salesforce replacement.

Explain that they can complement each other.

Do NOT show fake real-time project data.

Do NOT claim Bedrock is currently working.

Bedrock must be clearly marked:

"PENDING AWS ACCOUNT/MODEL ACCESS"

---

# 29. VISUAL DESIGN

Create a modern professional cloud/enterprise visual style.

Requirements:

- Dark/light professional presentation theme
- Strong typography
- Clean cards
- Subtle gradients
- Professional icons
- Clear diagrams
- Good spacing
- Minimal clutter
- Smooth transitions
- Hover effects
- Scroll animations
- Animated arrows/data flow
- Animated architecture
- Animated implementation timeline
- Interactive quiz

Do not overuse animations.

The website should look suitable for:

- Technical presentation
- Internal architecture demo
- Team knowledge-sharing session
- AWS + Salesforce training

---

# 30. NAVIGATION

Create a left or top navigation menu.

Sections:

01 Introduction
02 AWS
03 Salesforce
04 AWS vs Salesforce
05 Service Comparison
06 Top 5 Services
07 When to Use What
08 Real-World Use Cases
09 Our Project
10 Architecture
11 Implementation
12 Project Status
13 Security Principles
14 Quiz
15 Final Summary

Navigation should highlight the current section.

---

# 31. RESPONSIVE DESIGN

Desktop:

Presentation-style widescreen layout.

Tablet:

Two-column layouts where appropriate.

Mobile:

Single-column layout.

Architecture diagrams should remain readable.

Use horizontal scrolling for very wide diagrams when necessary.

---

# 32. IMPORTANT: DO NOT BUILD THESE INTO THE WEBSITE

Do NOT implement:

- Login Simulator
- Live login form
- Real API Gateway calls
- Postman testing interface
- Live Salesforce incident viewer
- Real-time dashboard
- Mock real-time data
- Fake API responses

These will be demonstrated manually during the presentation.

The webpage should only explain these parts where necessary, especially in the architecture and implementation sections.

The website itself is the **presentation/learning experience**, not the actual security application.

---

# 33. FINAL QUALITY REQUIREMENT

Build the complete working website.

It should not be a collection of static slides.

It must include:

- Interactive navigation
- Presentation Mode
- Animated architecture
- Service comparison
- Expandable service explanations
- Real-world use cases
- Project architecture
- End-to-end implementation timeline
- Project status
- Security principles
- Interactive 10-question quiz
- Final summary

Prioritize:

1. Easy understanding
2. Technical accuracy
3. Visual storytelling
4. Professional presentation quality
5. Clear AWS concepts
6. Clear Salesforce concepts
7. Clear AWS vs Salesforce distinction
8. Clear service-level comparison
9. Clear explanation of our actual project
10. Interactive learning

The most important story is:

AWS
↓
Salesforce
↓
Difference
↓
Services
↓
When to use each
↓
Real-world use cases
↓
Our Security Incident Management project
↓
Architecture
↓
Implementation
↓
AI
↓
Quiz
↓
Final takeaway

Build the entire website end-to-end and make it presentation-ready.