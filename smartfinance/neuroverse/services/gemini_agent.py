import os
from pathlib import Path
from dotenv import load_dotenv

from neuroverse.services.forecast import project, money, SCENARIO_LABELS

# Locate the smartfinance project root
BASE_DIR = Path(__file__).resolve().parents[2]

# Load Gemini credentials from .env
load_dotenv(BASE_DIR / ".env")

MODEL = os.getenv('GEMINI_MODEL','gemini-2.5-flash')

class GeminiUnavailable(Exception):
    pass

def model_ready():
    return bool(os.getenv('GEMINI_API_KEY','').strip())

def offline_reply(question, store):
    state=store.state
    result=project(state.balance_pence,state.transactions,scenario=state.selected_scenario)
    low=result['lowest']
    return (f"Offline guide · Your lowest projected balance is {money(low['balance_pence'])} "
            f"on {low['date']} in the {SCENARIO_LABELS[state.selected_scenario]} scenario. "
            "This is a fictional calculation based on listed future payments. "
            "You could review your upcoming bills, explore the Time Travel scenarios, or ask a provider about possible arrangements. "
            "For a conversational AI response, add GEMINI_API_KEY to your environment.")

def build_context(store):
    s=store.state
    result=project(s.balance_pence,s.transactions,scenario=s.selected_scenario)
    baseline=project(s.balance_pence,s.transactions)
    upcoming=sorted((t for t in s.transactions if t.source!='card' and t.date>=result['timeline'][0]['date']),key=lambda t:t.date)[:12]
    return {
        'practice_balance':money(s.balance_pence),
        'scenario':SCENARIO_LABELS[s.selected_scenario],
        'lowest_balance':money(result['lowest']['balance_pence']),
        'lowest_date':result['lowest']['date'],
        'first_negative_day':result['shortfall']['date'] if result['shortfall'] else None,
        'day_30_balance':money(result['end_balance_pence']),
        'baseline_low':money(baseline['lowest']['balance_pence']),
        'known_upcoming_transactions':[{'date':t.date,'description':t.description,'amount':money(t.amount_pence)} for t in upcoming],
        'preferences':s.preferences,
        'disclaimer':'All information is fictional. Forecast is a deterministic scenario, not a validated predictive model.'
    }

def ask_gemini(question, context):
    if not model_ready():
        raise GeminiUnavailable('Missing GEMINI_API_KEY')
    try:
        from google import genai
    except ImportError as exc:
        raise GeminiUnavailable('Install Gemini support: pip install -r requirements-ai.txt') from exc
    import json
    client=genai.Client(api_key=os.environ['GEMINI_API_KEY'])
    instruction=(
        'You are NeuroVerse, an inclusive financial learning guide for a fictional banking simulator. '
        'Answer the question using ONLY the verified context provided. Do not invent numbers, benefit eligibility, bill changes, or factual predictions. '
        'All forecasts are scenario calculations, not certain outcomes. Do not recommend risky borrowing, pretend to make payments, '
        'give regulated personal investment advice, or infer disabilities or diagnoses. '
        'Use non-judgmental clear language, an encouraging but non-patronising tone and short actionable steps. '
        'For possible financial hardship, consider essential expenses and payment support rather than merely saying spend less. '
        'If a requested number cannot be established from the context, say so. '
        'Prefer 2–5 short sentences, especially when simple or focus preference is enabled. '
        'Never ask for or output real banking credentials.'
    )
    prompt=f'{instruction}\n\nVerified fictional financial context:\n{json.dumps(context,ensure_ascii=False)}\n\nLearner question: {question[:1200]}'
    try:
        response=client.models.generate_content(model=MODEL, contents=prompt)
    except Exception as exc:
        raise GeminiUnavailable('Gemini request failed. Check the API key, model and internet connection.') from exc
    answer=(getattr(response,'text',None) or '').strip()
    if not answer:
        raise GeminiUnavailable('Gemini returned no response.')
    return answer[:4000]
