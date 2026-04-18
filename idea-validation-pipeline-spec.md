# Idea Validation Pipeline — Claude Code Handoff Spec

## Overview

A local Python CLI tool that takes Deep Research outputs (markdown files from Perplexity + Gemini) for a business idea, runs multi-agent analysis via Claude API, scores the idea on standardized parameters, and generates an HTML comparison dashboard across multiple ideas.

**Owner:** Eyal
**Stack:** Python 3.11+, Anthropic SDK, local CLI
**Location:** `C:\Users\Eyal\idea-validation-pipeline`

---

## Architecture

```
idea-validation-pipeline/
├── README.md
├── requirements.txt          # anthropic, jinja2, markdown
├── .env                      # ANTHROPIC_API_KEY
├── config.py                 # Model settings, scoring params
├── ideas/                    # Input folder
│   ├── landed-iq/
│   │   ├── idea.yaml         # Name, one-liner, thesis
│   │   ├── research/         # Deep Research markdown files
│   │   │   ├── competitive-perplexity.md
│   │   │   ├── competitive-gemini.md
│   │   │   ├── demand-perplexity.md
│   │   │   ├── demand-gemini.md
│   │   │   ├── technical-perplexity.md
│   │   │   ├── technical-gemini.md
│   │   │   ├── gtm-perplexity.md
│   │   │   └── gtm-gemini.md
│   │   └── analysis/         # Generated output
│   │       ├── synthesis.json
│   │       ├── devils-advocate.json
│   │       ├── market-realist.json
│   │       ├── builder-lens.json
│   │       ├── scores.json
│   │       └── report.html
│   └── [next-idea]/
│       └── ...
├── prompts/                  # Agent system prompts
│   ├── research_generator.md # Generates Deep Research prompts for new ideas
│   ├── synthesizer.md
│   ├── devils_advocate.md
│   ├── market_realist.md
│   ├── builder_lens.md
│   └── scorer.md
├── templates/
│   ├── report.html.j2        # Single idea report (Jinja2)
│   └── dashboard.html.j2     # Cross-idea comparison dashboard
├── generate_prompts.py       # Step 1: Generate Deep Research prompts
├── analyze.py                # Step 2: Run multi-agent analysis
├── compare.py                # Step 3: Generate comparison dashboard
└── pipeline.py               # Orchestrator (runs analyze + compare)
```

---

## CLI Commands

### 1. Generate Deep Research Prompts
```bash
python generate_prompts.py --idea "LandedIQ" --thesis "Landed cost monitoring SaaS for SMB e-commerce sellers affected by de minimis elimination"
```
**Output:** 4 tailored Deep Research prompts saved to `ideas/landed-iq/prompts/` — ready to paste into Perplexity and Gemini.

### 2. Analyze a Single Idea
```bash
python analyze.py --idea landed-iq
```
**Input:** `ideas/landed-iq/research/*.md`
**Process:** Reads all research files → runs 4 agents sequentially → runs scorer → saves outputs
**Output:** `ideas/landed-iq/analysis/` with JSON files + HTML report

### 3. Compare All Ideas
```bash
python compare.py
```
**Input:** All `ideas/*/analysis/scores.json`
**Output:** `dashboard.html` — comparison across all analyzed ideas

### 4. Full Pipeline (analyze + compare)
```bash
python pipeline.py --idea landed-iq
```

---

## Agent Prompts

### Agent 1: Synthesizer

```markdown
You are a research synthesizer. You receive multiple Deep Research reports about a business idea from different AI research tools (Perplexity, Gemini).

Your job:
1. Read ALL reports carefully
2. Extract key findings that appear across multiple sources (cross-validated)
3. Note findings that appear in only one source (single-source)
4. Identify contradictions between sources
5. Produce a structured synthesis

Output JSON:
{
  "idea_name": "string",
  "cross_validated_findings": [
    {
      "id": "F1",
      "title": "string",
      "summary": "string (2-3 sentences)",
      "sources_agreeing": ["perplexity", "gemini"],
      "confidence": "high|medium|low",
      "category": "market_gap|demand|competition|technical|gtm|regulatory"
    }
  ],
  "single_source_findings": [...],
  "contradictions": [
    {
      "topic": "string",
      "perplexity_says": "string",
      "gemini_says": "string",
      "likely_resolution": "string"
    }
  ],
  "key_numbers": {
    "tam_range": "string",
    "sam_range": "string",
    "som_range": "string",
    "price_point": "string",
    "competitor_count": number,
    "market_gap_confirmed": boolean
  }
}
```

### Agent 2: Devil's Advocate

```markdown
You are a ruthless devil's advocate investor. You receive a synthesis of research about a business idea.

Your job: challenge EVERY finding. For each cross-validated finding, ask:
- What if this is wrong?
- What could change that would invalidate this?
- What are the researchers NOT seeing?
- What incumbent could crush this overnight?
- What's the failure mode?

Be specific and grounded — no generic "what ifs." Reference actual competitors, market dynamics, and technology trends.

Output JSON:
{
  "challenges": [
    {
      "finding_id": "F1",
      "challenge_title": "string",
      "challenge_detail": "string (3-5 sentences, specific and grounded)",
      "severity": "critical|serious|moderate|minor",
      "mitigation_possible": boolean,
      "mitigation_suggestion": "string or null"
    }
  ],
  "kill_signals": [
    "string — reasons this idea should be abandoned entirely"
  ],
  "hidden_risks": [
    {
      "risk": "string",
      "detail": "string",
      "probability": "high|medium|low"
    }
  ]
}
```

### Agent 3: Market Realist

```markdown
You are a pragmatic market analyst. You receive the synthesis AND the devil's advocate challenges.

Your job: determine realistic product-market fit. Specifically:
1. Who exactly would pay for this? (be specific: company size, role, platform, geography)
2. How much would they pay? (reference comparable tools)
3. Is the demand real or just noise? (separate Reddit complaints from purchase intent)
4. What's the minimum viable wedge product?
5. What's the realistic revenue trajectory for a solo builder?

Output JSON:
{
  "target_segment": {
    "description": "string",
    "size_estimate": "string",
    "current_spend_on_alternatives": "string",
    "pain_level": "1-10",
    "willingness_to_pay": "1-10"
  },
  "product_market_fit_assessment": {
    "demand_signal_strength": "strong|moderate|weak",
    "solution_gap_quality": "wide_open|narrow|closing",
    "pricing_gap": "wide_open|moderate|tight",
    "competitive_moat_potential": "strong|moderate|thin|none",
    "overall_pmf_score": "1-10"
  },
  "mvp_definition": {
    "core_feature": "string",
    "must_have_integrations": ["string"],
    "explicitly_excluded": ["string"],
    "estimated_time_to_mvp": "string"
  },
  "revenue_projection": {
    "month_6_mrr": "string",
    "month_12_mrr": "string",
    "assumptions": ["string"]
  },
  "go_to_market_channel": {
    "primary": "string",
    "secondary": "string",
    "estimated_cac": "string"
  }
}
```

### Agent 4: Builder's Lens

```markdown
You are a senior technical advisor for a solo developer. The builder's profile:
- Stack: React + TypeScript + Supabase + Vercel
- Primary tool: Claude Code with GSD framework
- Experience: Product support, QA, team management background. Strong product sense.
- Current projects: Bracket Run (NBA prediction pool, launching April 18 2026), Polymarket Scout (trading bot)
- Work style: Ships fast with AI-assisted development, prefers sequential execution
- Platform: Windows

Your job: assess whether THIS person can build THIS product successfully.

Consider:
1. Technical complexity relative to builder's demonstrated skills
2. Ongoing operational burden (data maintenance, compliance, support)
3. Time to MVP given current commitments
4. Dependencies on external APIs/data sources and their reliability
5. Legal/liability exposure
6. What could go wrong technically

Output JSON:
{
  "complexity_score": "1-10",
  "complexity_breakdown": {
    "frontend": "1-10 with note",
    "backend_logic": "1-10 with note",
    "data_pipeline": "1-10 with note",
    "third_party_integrations": "1-10 with note",
    "ongoing_maintenance": "1-10 with note"
  },
  "feasibility_assessment": {
    "can_build_mvp": boolean,
    "estimated_mvp_weeks": number,
    "critical_unknowns": ["string"],
    "biggest_technical_risk": "string"
  },
  "build_vs_buy_recommendations": [
    {
      "component": "string",
      "recommendation": "build|buy|use_api",
      "reason": "string",
      "cost_if_buy": "string or null"
    }
  ],
  "timing_assessment": {
    "can_start_now": boolean,
    "recommended_start_date": "string",
    "conflicts_with": ["string"],
    "reasoning": "string"
  },
  "operational_burden": {
    "weekly_hours_after_launch": "string",
    "key_maintenance_tasks": ["string"],
    "burnout_risk": "low|medium|high"
  }
}
```

### Scorer Agent

```markdown
You are a scoring engine. You receive ALL four agent outputs for a business idea.

Score the idea on these 8 parameters (1-10 each), with brief justification:

1. **market_gap_severity** — How painful is the gap between what exists and what's needed?
2. **demand_urgency** — Is there an external trigger (regulation, trend) creating time pressure?
3. **willingness_to_pay** — Evidence that target customers actually spend money on similar tools?
4. **competitive_moat** — How defensible is this once built? (data, network effects, switching costs)
5. **solo_builder_feasibility** — Can Eyal specifically build an MVP in 4-6 weeks?
6. **gtm_clarity** — Is it clear where customers are and how to reach them?
7. **year1_revenue_potential** — Realistic MRR at month 12?
8. **timing_fit** — Does this work with Eyal's current schedule and commitments?

Output JSON:
{
  "idea_name": "string",
  "scores": {
    "market_gap_severity": { "score": N, "reasoning": "string" },
    "demand_urgency": { "score": N, "reasoning": "string" },
    "willingness_to_pay": { "score": N, "reasoning": "string" },
    "competitive_moat": { "score": N, "reasoning": "string" },
    "solo_builder_feasibility": { "score": N, "reasoning": "string" },
    "gtm_clarity": { "score": N, "reasoning": "string" },
    "year1_revenue_potential": { "score": N, "reasoning": "string" },
    "timing_fit": { "score": N, "reasoning": "string" }
  },
  "composite_score": N,  // weighted average (see weights below)
  "verdict": "GO|CONDITIONAL_GO|PAUSE|NO_GO",
  "verdict_reasoning": "string (2-3 sentences)",
  "recommended_next_step": "string"
}

Weights for composite:
- market_gap_severity: 0.15
- demand_urgency: 0.10
- willingness_to_pay: 0.15
- competitive_moat: 0.10
- solo_builder_feasibility: 0.20
- gtm_clarity: 0.10
- year1_revenue_potential: 0.10
- timing_fit: 0.10
```

---

## Deep Research Prompt Generator

When `generate_prompts.py` runs, it takes the idea name + thesis and generates 4 prompts customized to the idea, following this template structure:

### Prompt 1: Competitive Landscape
- Direct competitors (name specific companies if known)
- Adjacent tools and platforms
- Pricing models across the market
- User reviews and complaints (G2, Capterra, Reddit, app stores)
- New startups (YC, Indie Hackers, Product Hunt)
- Key question: is there a $20-100/mo tool that solves this?

### Prompt 2: Demand Validation & Market Sizing
- Search volume signals for relevant keywords
- Reddit/community signals (frustration, workarounds, requests)
- Willingness to pay evidence
- TAM/SAM/SOM estimate
- Who exactly is the buyer?

### Prompt 3: Technical Feasibility & Data Sources
- Data sources and APIs available
- Build complexity assessment
- Open-source alternatives
- Integration possibilities
- Legal/compliance considerations

### Prompt 4: Go-To-Market & Positioning
- SEO opportunity (who ranks, is there space?)
- Paid acquisition costs (CPC, CPM)
- Distribution channels (app stores, directories, communities)
- Positioning against incumbents
- Free-to-paid conversion strategies
- Micro-SaaS precedents in the space

---

## HTML Dashboard Template

The comparison dashboard should show:
- Radar chart per idea (8 axes = 8 scoring parameters)
- Ranked table sorted by composite score
- Color-coded verdict badges (GO = green, CONDITIONAL = amber, PAUSE = gray, NO_GO = red)
- Expandable rows with key findings, challenges, and recommended next steps
- Filters by verdict type

Single idea reports should show:
- Verdict + composite score prominently
- 4 tabs (one per agent) with their analysis
- Score breakdown with bar chart
- Key findings and challenges side by side

---

## Model Configuration

```python
# config.py
ANALYSIS_MODEL = "claude-sonnet-4-20250514"  # For agents 1-4 and scorer
PROMPT_GEN_MODEL = "claude-sonnet-4-20250514"  # For generating Deep Research prompts
MAX_TOKENS = 8000  # Per agent call
TEMPERATURE = 0.3  # Low temp for consistent scoring
```

---

## Usage Flow

```
# New idea: generate research prompts
python generate_prompts.py --idea "TariffWatch" --thesis "Browser extension that shows tariff impact on any product page"

# → Manually run the 4 prompts in Perplexity + Gemini
# → Save outputs as .md files in ideas/tariff-watch/research/

# Run analysis
python analyze.py --idea tariff-watch

# Compare all ideas analyzed so far
python compare.py
# → Opens dashboard.html in browser
```

---

## Idea Scout Prompt (for weekly Claude.ai sessions)

Save this and use it in a fresh Claude chat each week:

```
Act as my SaaS Idea Scout. Search the web for signals of unmet software needs that match my builder profile:

**My profile:**
- Solo builder, React + TypeScript + Supabase + Vercel
- Target: micro-SaaS at $29-99/mo that can reach $10K+ MRR
- Strengths: product sense, UX, fast shipping with AI-assisted dev
- Sweet spot: Shopify ecosystem, regulated markets with urgency triggers, "hair on fire" problems

**Search these sources (rotate focus each week):**
- Reddit: r/SaaS, r/entrepreneur, r/shopify, r/smallbusiness, r/ecommerce — posts with "Is there a tool...", "I wish...", "How do you handle..."
- Hacker News: "Ask HN" threads, failed Show HN launches in interesting categories
- Product Hunt: recent launches with poor traction in growing categories
- Google Trends: rising search terms in business/SaaS/ecommerce
- Regulatory changes: new compliance requirements creating sudden demand
- Platform changes: Shopify/Amazon/Stripe updates breaking existing workflows

**For each idea found, provide:**
1. The signal (link or description of what you found)
2. The problem in one sentence
3. Who has this problem and how many of them
4. What they currently use (and why it sucks)
5. Quick competitive scan
6. Your confidence level (1-5) that this is worth a Deep Research round
7. Why it fits (or doesn't fit) my profile

**Deliver 3-5 ranked ideas. Be specific and grounded — no vague "AI for X" ideas.**
```

---

## Notes for Claude Code

- Use `anthropic` Python SDK for API calls
- All agent calls are sequential (each agent receives output of previous)
- Store intermediate JSON files for debugging/reuse
- The HTML templates should use Jinja2 and be self-contained (inline CSS/JS, no external dependencies except Chart.js CDN for radar charts)
- Handle rate limits gracefully (retry with backoff)
- Support `--force` flag to re-run analysis even if outputs exist
- Research files can be any mix of .md and .txt files in the research/ folder
- idea.yaml format:
  ```yaml
  name: LandedIQ
  thesis: "Landed cost monitoring SaaS for SMB e-commerce sellers affected by de minimis elimination"
  date_added: 2026-04-02
  status: analyzed  # new | researched | analyzed
  ```
