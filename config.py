import os

# Model settings — Claude CLI model names (Max plan)
SCAN_MODEL = "sonnet"   # Synthesizer, Market Realist, Builder's Lens, Prompt Gen
DEEP_MODEL = "opus"     # Devil's Advocate, Scorer (benefit from deeper reasoning)
TIMEOUT = 300           # 5 min per agent call

# Scoring weights for composite score
SCORE_WEIGHTS = {
    "market_gap_severity": 0.15,
    "demand_urgency": 0.10,
    "willingness_to_pay": 0.15,
    "competitive_moat": 0.10,
    "solo_builder_feasibility": 0.20,
    "gtm_clarity": 0.10,
    "year1_revenue_potential": 0.10,
    "timing_fit": 0.10,
}

# Directories
IDEAS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "ideas")
PROMPTS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "prompts")
TEMPLATES_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "templates")
