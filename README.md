# SmartFinance

**A financial safety net for when the banks go down.**

Built at GreatUniHack 2026 (University of Manchester) for the NatWest challenge: *AI-Powered Financial Inclusion & Resilience*.

---

## What is SmartFinance?

If a cyberattack or outage takes down banking apps and card networks, most people can't pay for food, transport or medicine. Students and people who find money hard to manage are hit the hardest, because they rarely have a cash buffer.

SmartFinance has two parts that work together:

1. **An offline emergency card.** You store money on the card while the network is working. If the network goes down, you can still spend from that balance. Payments are saved and sent automatically once you're back online.
2. **A money simulation.** You enter your bills and spending, and it works out how much you should set aside to cover an emergency, with a plain-language AI explanation.

The idea in one sentence: **predict when you could be in trouble, and keep you able to pay when the banks go down.**

---

## Demo: what it does

### 1. The offline card ("Lifeline" card screen)

- **Three cards:** an Emergency card, an Everyday card and a One-use card. Switch between them with the tabs.
- **Online / offline switch.** Press *Go offline* to simulate an outage. The status pill turns orange and the signal bars are crossed out.
- **Test payment.** Press *Pay* to make a purchase.
  - Online: the payment goes through straight away.
  - Offline: the payment is **saved in a queue** ("Waiting to send"). Press *Reconnect* and the queued payments are sent.
- **Spending limit that you control.** Each card has a daily limit you set yourself. A bar shows how much you've spent today.
- **Cooling-off prompt.** If a payment would go over your limit, the app pauses and asks you to think first. You can still go ahead by tapping again. It's a nudge, not a block.
- **Lock / unlock** a card at any time.
- **One-use card** locks itself after a single payment.

### 2. The money simulation

- Enter your income, bills and spending.
- It calculates how many days you could cover if banks went offline, and how much to set aside as an emergency fund.
- The AI explains the result in simple, non-judgemental language.

**Design choice:** the numbers come from plain Python maths, so they're reliable. The AI is only used to explain them.

> **Everything is simulated.** No real money, bank accounts or card networks are involved. See *What's real vs simulated* below.

---

## Tech stack

| Part | Technology |
|---|---|
| Backend | Python |
| AI | Claude API (Anthropic) |
| Frontend | Tkinter (Python's built-in GUI library) |
| Config | `python-dotenv` for API keys in a `.env` file |

Tkinter is the **frontend**. It draws the windows and buttons that the user sees. The Python code behind it is the backend.

---

## Getting started

### 1. Requirements

- **Python 3.10 or newer, installed from [python.org](https://www.python.org/downloads/).**
  On a Mac, the Python that comes with macOS has an old version of Tk that shows blank windows. Check yours with:
  ```
  python3 -c "import tkinter; print(tkinter.TkVersion)"
  ```
  It should print `8.6` or higher.
- A Claude API key (from the Anthropic Console).
- Git.

### 2. Clone the repository

```
git clone <repo-link>
cd SmartFinance
```

### 3. Create the virtual environment

```
python3 -m venv venv
source venv/bin/activate
```

On Windows, use `venv\Scripts\activate` instead. You should see `(venv)` at the start of your terminal line.

### 4. Install the packages

```
pip install anthropic python-dotenv
```

### 5. Add your API key

Create a file called `.env` in the main `SmartFinance` folder (next to this README) with one line:

```
ANTHROPIC_API_KEY=your-key-here
```

- No quote marks and no spaces around `=`.
- **Never commit this file.** `.gitignore` already excludes `.env` and `venv/`.
- Each team member should use their own key.

### 6. Run it

Card screen:

```
python app/virtualCard/cardPreview.py
```

Money simulation:

```
python app/simulation.py
```

AI helper (quick test that your key works):

```
python app/askAI.py
```

---

## Project structure

```
SmartFinance/

```

---

## What's real vs simulated

**Real:**
- The spending maths and emergency-fund calculation.
- The offline queue logic: payments are held while offline and settled on reconnect.
- The spending limits and cooling-off prompt.
- The AI explanations.

**Simulated:**
- The bank, the card network and the money itself.
- The "outage": a button toggles it.

**What a real version would need:** a partnership with a bank, regulatory approval, and secure signed offline payments (reserving funds in advance with a cap, so the same money can't be spent twice).

---

## Design principles

- **Inclusive.** Built for students and people who struggle to manage money, including people with ADHD or mental health difficulties. Plain language, few steps, no jargon.
- **User in control.** The user sets their own limits and can override the cooling-off prompt.
- **No shame.** The tone is supportive, never judgemental.
- **Privacy first.** Financial data stays with the user.

---

## Team

- Nina Momoko Heegaard
- Amal Ismail
- Rand Koja
- Viet Anh Xuan Ta

---

*Built in one day at GreatUniHack 2026, University of Manchester.*