# NeuroVerse AI — complete Tkinter desktop application

A bright, interactive **fictional** financial resilience simulator for a hackathon about financial fairness, forecasting, neurodiversity and accessible banking. This is an **original UI**, not affiliated with a bank.

## Run

Requires Python 3.10+ with Tkinter and a graphical desktop.

```bash
python3 run.py
```

Everything except online Gemini works **without third-party packages**. To enable Gemini:

```bash
python3 -m pip install -r requirements-ai.txt
export GEMINI_API_KEY='your-google-ai-studio-api-key'
python3 run.py
```

macOS/Linux use `export`. Windows PowerShell use `$env:GEMINI_API_KEY="your-key"`. Optionally set `GEMINI_MODEL` if that model is unavailable to your account. Do not commit API keys. Gemini calls require internet. The default model is `gemini-2.5-flash`.

## Screens

- **Dashboard:** animated gradient balance hero, interactive quick actions, future-risk alert, trend sparkline and transactions.
- **My Finances:** editable fictional current balance, scheduled income and expenses; remove entries; persistent local demo state.
- **Time Travel:** three scenarios (baseline, emergency cost, bill-date shift subject to provider agreement), responsive forecast chart, mouse-based point inspection.
- **Future-Self Coach:** actual Gemini via optional SDK, prompt suggestions, user questions, multi-turn visual history; nonblocking worker thread and offline fallback.
- **Action Plan:** personalised checklist with persistent progress and editable emergency savings goal.
- **Accessibility:** plain language, focus navigation, default larger text, reduced motion, one-click demo reset.
- **Virtual Card:** deliberately **EMPTY placeholder**. No card actions or card implementation are provided.

## Team ownership / integration

The card team's existing event integration interface is left at `neuroverse/integrations/card_bridge.py`; they can work in a separate branch. Only one integrator should alter `neuroverse/app.py` and `core/state.py`.

```python
# Called on Tk's main thread, using the existing app EventBus
from neuroverse.integrations.card_bridge import CardBridge
bridge = CardBridge(bus)
bridge.record_practice_purchase('Groceries', 1250)  # -£12.50 practice only
```

No card numbers, PINs, actual banking tokens or real transactions should be sent. Worker threads should queue card events and have the main Tk thread apply them via `after()`. Events are deduplicated. The card placeholder has **no simulated spending button**.

## Persistence

The app stores fictional balance, scheduled entries, action progress and preferences locally in `~/.neuroverse_ai/demo_state.json`. Reset via Accessibility. Delete that file if necessary to restore the starting state. No database server is required.

## Design & constraints

Financial projections use **integer pence** and scheduled events, not a trained future predictor. It assumes no unspecified spending or income. It illustrates the financial-time-travel idea, but it does not establish actual credit risk, benefit eligibility, or investment advice. Gemini receives the *fictional* account summary, up to 12 upcoming events, and user text; never use real sensitive financial information or submit account credentials. The AI cannot move money. Its numeric context comes from the deterministic forecast service. AI responses should still be reviewed for factual correctness.

Accessibility modes are implementation aids, not a clinical assessment or evidence of usability for all disabilities. Test with participants and assistive technologies before claiming full accessibility.

## Tests

```bash
python3 -m unittest discover -s tests -v
python3 -m compileall -q neuroverse run.py
```

## File layout

- `neuroverse/app.py` — app shell, routes and navigation
- `neuroverse/ui/screens/` — one independent Tkinter class per page
- `neuroverse/ui/widgets.py` and `theme.py` — shared styling
- `neuroverse/core/state.py` — persistent state and updates
- `neuroverse/services/forecast.py` — deterministic scenarios
- `neuroverse/services/gemini_agent.py` — optional Gemini client and grounded context
- `neuroverse/integrations/card_bridge.py` — teammate-owned integration boundary
