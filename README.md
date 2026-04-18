# Idea Validation Pipeline

Local Python CLI that takes Deep Research outputs (markdown from Perplexity + Gemini), runs multi-agent analysis via Claude CLI (Max plan), scores ideas on 8 parameters, and generates an HTML comparison dashboard.

## Setup

```bash
pip install -r requirements.txt
```

**Requires:** Claude CLI installed and authenticated (`claude` in PATH via Max plan).

## Usage

### 1. Generate Deep Research Prompts
```bash
python generate_prompts.py --idea "LandedIQ" --thesis "Landed cost monitoring SaaS for SMB e-commerce sellers"
```
Outputs 4 prompts to `ideas/landed-iq/prompts/` — paste into Perplexity and Gemini.

### 2. Save Research
Save Perplexity/Gemini outputs as `.md` files in `ideas/<slug>/research/`:
```
competitive-perplexity.md, competitive-gemini.md
demand-perplexity.md, demand-gemini.md
technical-perplexity.md, technical-gemini.md
gtm-perplexity.md, gtm-gemini.md
```

### 3. Analyze
```bash
python analyze.py --idea landed-iq
python analyze.py --idea landed-iq --force  # re-run
```

### 4. Compare All Ideas
```bash
python compare.py
```
Opens `dashboard.html` with radar charts and ranked comparison.

### 5. Full Pipeline
```bash
python pipeline.py --idea landed-iq
```

## Analysis Agents

1. **Synthesizer** — Cross-validates findings across research sources
2. **Devil's Advocate** — Challenges every finding with specific risks
3. **Market Realist** — Assesses realistic PMF, pricing, and GTM
4. **Builder's Lens** — Technical feasibility for Eyal's specific profile
5. **Scorer** — Scores 8 parameters, produces weighted composite + verdict

## Scoring Parameters

| Parameter | Weight |
|-----------|--------|
| Solo Builder Feasibility | 20% |
| Market Gap Severity | 15% |
| Willingness to Pay | 15% |
| Demand Urgency | 10% |
| Competitive Moat | 10% |
| GTM Clarity | 10% |
| Year 1 Revenue Potential | 10% |
| Timing Fit | 10% |

**Verdicts:** GO (>=7.0) | CONDITIONAL_GO (>=5.5) | PAUSE (>=4.0) | NO_GO (<4.0)
