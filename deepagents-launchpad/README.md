
```md
# LaunchPilot — DeepAgents LaunchPad

**SimplifyNext Hackathon 2026 — Agentic AI Track**

The multi-agent marketing team behind every repo that ships.

LaunchPilot reads a project description, researches its market positioning, drafts a full social content calendar, and publishes to X — with a human approval gate before every single post goes live.

Built with **LangGraph**, **AWS Bedrock (Claude 3 Haiku + Titan Image Generator)**, **Streamlit**, and **Tweepy**.

---

## Quick Start

Follow these steps in order. This assumes you're on **Windows with PowerShell** and already have `uv` installed at:

```powershell
$env:USERPROFILE\.local\bin\uv.exe
```

### 1. Spin up a clean virtual environment

```powershell
& "$env:USERPROFILE\.local\bin\uv.exe" venv
```

### 2. Install your required dependencies

```powershell
& "$env:USERPROFILE\.local\bin\uv.exe" pip install -r requirements.txt
```

### 3. Establish your 12-hour regional AWS Bedrock session in Singapore

```powershell
aws sso login --profile workshop

When prompted in the terminal, carefully paste your credentials and settings:
- AWS Access Key ID [None]: <Paste your Access Key ID>
- AWS Secret Access Key [None]: <Paste your Secret Access Key>
- Default region name [None]: ap-southeast-1 (Singapore)
- Default output format [None]: json
```

### 4. Set up your `.env` file with your credentials

Before launching the app, create a `.env` file in the project root (same folder as `src/`) if one doesn't already exist.

Example:

```env
AWS_PROFILE=workshop
AWS_DEFAULT_REGION=ap-southeast-1

AWS_ACCESS_KEY_ID=your_temporary_access_key_id_here
AWS_SECRET_ACCESS_KEY=your_temporary_secret_access_key_here
AWS_SESSION_TOKEN=your_temporary_session_token_here

```

#### AWS configuration

- `AWS_PROFILE` and `AWS_DEFAULT_REGION` tell the app which AWS SSO profile and region to use for Bedrock.
- These should match the profile you logged into in Step 3.
- `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`, and `AWS_SESSION_TOKEN` are **temporary credentials** issued by `aws sso login`.
- These credentials expire after approximately **12 hours**.
- When the app throws an `ExpiredTokenException`, re-run Step 3 and refresh the credentials if you are using explicit environment variables.

> **Note:**  

> `aws sso login --profile workshop` refreshes credentials cached locally by the AWS CLI. `boto3.Session(profile_name="workshop")` can read these credentials automatically.

> ### Important: Never commit `.env`

> Never commit `.env` to version control.
> If `.gitignore` does not already exist, add:

```gitignore
.env
```

> The AWS credentials are temporary, but they are still live credentials tied to the workshop AWS account.

---

## 5. Launch the Streamlit workspace

Run:

```powershell
& "$env:USERPROFILE\.local\bin\uv.exe" run streamlit run src/app.py
```

The application will open at:

```text
http://localhost:8501
```

---

# Project Structure

```text
deepagents-launchpad/
├── src/
│   ├── app.py
│   │   └── Streamlit UI
│   │       ├── Idea input
│   │       ├── Agent output tabs
│   │       ├── Approval gate
│   │       └── X integration sidebar
│   │
│   └── supervisor.py
│       ├── LangGraph pipeline
│       ├── Agent node definitions
│       ├── AWS / Bedrock setup
│       └── Tweepy publishing logic
│
├── requirements.txt
├── .env
└── published_social_feed.txt
```

---

# How It Works

LaunchPilot uses a multi-agent workflow to transform a project idea into an approved social media campaign.

## 1. Repo Analyst

Reads the project description and extracts:

- Plain-language project summary
- Target audience
- Technology stack
- Key project characteristics

## 2. Market / Positioning Agent

Researches the competitive landscape and identifies:

- Relevant competitors
- Market positioning
- Differentiation opportunities
- Potential messaging angles

## 3. Strategist

Creates the marketing strategy, including:

- Content pillars
- Posting cadence
- Messaging direction
- Content themes

## 4. Content Creator

Creates a complete social media calendar based on the strategy.

Each post is mapped back to the defined content pillars.

## 5. Human Approval Gate

The pipeline pauses before publishing.

LangGraph's `interrupt_before` mechanism is used to ensure that a human reviews and approves each post before it goes live.

```text
Agent-generated post
        ↓
   Human Review
        ↓
   ┌────┴────┐
   │         │
Reject     Approve
             ↓
        Publishing
```

No post should be published without human approval.

## 6. Publishing Agent

Once a post is approved:

1. Generates a graphic using **AWS Bedrock Titan Image Generator**.
2. Falls back to a placeholder graphic if Titan is unavailable.
3. Publishes the post through **Tweepy** if X credentials are configured.
4. Otherwise, simulates the dispatch locally.

After publishing, the graph loops back to content creation until the calendar is exhausted.

A hard safety cap of **5 cycles** is enforced to prevent runaway AWS usage.

---

# Architecture

```text
                         ┌──────────────────┐
                         │   Project Idea   │
                         └────────┬─────────┘
                                  │
                                  ▼
                         ┌──────────────────┐
                         │   Repo Analyst   │
                         └────────┬─────────┘
                                  │
                                  ▼
                     ┌──────────────────────────┐
                     │ Market / Positioning     │
                     │         Agent            │
                     └────────────┬─────────────┘
                                  │
                                  ▼
                         ┌──────────────────┐
                         │    Strategist    │
                         └────────┬─────────┘
                                  │
                                  ▼
                     ┌──────────────────────────┐
                     │     Content Creator      │
                     └────────────┬─────────────┘
                                  │
                                  ▼
                         ┌──────────────────┐
                         │  Human Approval  │
                         │       Gate       │
                         └────────┬─────────┘
                                  │
                              Approved
                                  │
                                  ▼
                     ┌──────────────────────────┐
                     │   Publishing Agent       │
                     │                          │
                     │ Titan Image Generator    │
                     │          +               │
                     │       Tweepy             │
                     └────────────┬─────────────┘
                                  │
                                  ▼
                         ┌──────────────────┐
                         │  X / Simulation  │
                         └────────┬─────────┘
                                  │
                                  ▼
                         Next Calendar Post
```

---

# Technologies

| Technology | Purpose |
|---|---|
| **LangGraph** | Multi-agent workflow orchestration |
| **AWS Bedrock** | LLM and image generation |
| **Claude 3 Haiku** | Agent reasoning and content generation |
| **Titan Image Generator** | Social media graphics |
| **Streamlit** | Interactive application interface |
| **Tweepy** | X API integration |
| **Python** | Application logic |
| **uv** | Python environment and dependency management |

---

# Troubleshooting

## `ModuleNotFoundError`

If you encounter:

```text
ModuleNotFoundError
```

Re-run:

```powershell
& "$env:USERPROFILE\.local\bin\uv.exe" pip install -r requirements.txt
```

Then confirm that your terminal or VS Code interpreter points to:

```text
.venv\Scripts\python.exe
```

rather than a global Python installation.

---

## AWS `ExpiredTokenException`

This usually means your AWS SSO session has expired.

Run:

```powershell
aws sso login --profile workshop
```

If you are using explicit AWS credentials in `.env`, update all three values together:

```env
AWS_ACCESS_KEY_ID=...
AWS_SECRET_ACCESS_KEY=...
AWS_SESSION_TOKEN=...
```

The AWS CLI refreshing its own cached credentials does **not** automatically update credentials hardcoded in `.env`.

---

## AWS `UnrecognizedClientException` or `InvalidClientTokenId`

This usually means the AWS credentials in `.env` are:

- Expired
- Mismatched
- Incomplete
- Incorrectly copied
- Contain extra whitespace or typos

Regenerate the complete credential set from the same SSO session:

```env
AWS_ACCESS_KEY_ID=...
AWS_SECRET_ACCESS_KEY=...
AWS_SESSION_TOKEN=...
```

Do not mix credentials from different sessions.

---

# Simulated Dispatch (demo)

With no X credentials configured, LaunchPilot still demonstrates:

```text
Project Analysis
       ↓
Market Research
       ↓
Marketing Strategy
       ↓
Social Content Calendar
       ↓
Human Approval
       ↓
Image Generation
       ↓
Simulated X Publishing
```

Published posts are recorded in:

```text
published_social_feed.txt
```

This helps as the entire agentic workflow can be demonstrated without making paid X API calls.

---

# Safety

LaunchPilot includes a human approval gate before every individual post.

The workflow also has a hard limit of **5 publishing cycles** to guard against runaway execution and unnecessary AWS spending.

```text
Agent creates post
       ↓
Human reviews
       ↓
Human approves
       ↓
Post is published
```

The system never automatically publishes a generated post without passing through the approval step.

---

# Team

**Team LaunchPilot**

SimplifyNext Hackathon 2026

**Track:** Agentic AI
```