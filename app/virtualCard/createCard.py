"""
createCard.py - the demo screen for the virtual offline card.

Run with:  streamlit run createCard.py        (from inside the virtualCard folder)
       or  streamlit run app/virtualCard/createCard.py   (from the project root)
"""
import streamlit as st

from bank import Bank, RealAccount
from chip import MAX_ALLOWANCE, MAX_OFFLINE_PAYMENTS, PER_TXN_LIMIT, fmt, to_pence

st.set_page_config(page_title="Offline Card", page_icon="💳")

# ---- App state (lives until you refresh the page) ----
if "account" not in st.session_state:
    st.session_state.account = RealAccount("Margaret", 500_00)  # demo: £500 on the real card
    st.session_state.bank = Bank()
    st.session_state.cards = []
    st.session_state.opened = None       # card_id of the card currently unlocked
    st.session_state.terminal = []       # signed payments stored on the "terminal", not yet settled
    st.session_state.settled_txs = []    # payments the bank has already processed (used for attacks)
    st.session_state.log = []            # bank-side log: (what happened, result)

account: RealAccount = st.session_state.account
bank: Bank = st.session_state.bank


def flash(kind: str, text: str):
    """Show a message after the next rerun (so balances at the top are fresh)."""
    st.session_state.flash = (kind, text)
    st.rerun()


# ---- Header ----
st.title("💳 Offline Card")

online = st.toggle("🌐 Network online", value=True, key="online")
if not online:
    st.warning("Network is DOWN. App and online banking are unavailable. "
               "Offline cards with an allowance still work in shops.")

c1, c2 = st.columns(2)
c1.metric("Real card balance", fmt(account.balance) if online else "Unavailable")
c2.metric("Reserved for offline cards", fmt(account.escrow) if online else "Unavailable")

if "flash" in st.session_state:
    kind, text = st.session_state.pop("flash")
    getattr(st, kind)(text)

tab_create, tab_open = st.tabs(["Create offline card", "My offline cards"])

# ---------------- CREATE ----------------
with tab_create:
    if not online:
        st.info("Cards can only be created while the network is up.")
    else:
        st.caption(f"Money is moved from your real card into escrow. Max {fmt(MAX_ALLOWANCE)} per offline card.")
        name = st.text_input("Card name", placeholder="e.g. Emergency food")
        amount = st.number_input("Amount (£)", min_value=0.0, step=5.0, format="%.2f")
        pin = st.text_input("Choose a 4-digit PIN", type="password", max_chars=4)
        pin2 = st.text_input("Confirm PIN", type="password", max_chars=4)

        if st.button("Add", type="primary"):
            try:
                card = bank.issue_card(account, name, amount, pin, pin2, source="customer")
                st.session_state.cards.append(card)
                flash("success", f"Offline card '{card.name}' created with {fmt(card.allowance)}. "
                                 "Go to 'My offline cards' and open it with your PIN.")
            except ValueError as e:
                st.error(str(e))

# ---------------- OPEN ----------------
with tab_open:
    cards = st.session_state.cards
    if not cards:
        st.info("No offline cards yet. Create one first.")
    else:
        labels = {f"{c.name}  ({c.card_id})" + ("  [closed]" if c.closed else ""): c for c in cards}
        choice = labels[st.selectbox("Choose a card", list(labels))]

        if choice.closed:
            st.info("This card is closed. Its unused allowance was returned to your real card.")
        elif choice.locked:
            st.error("🔒 This card is locked after 3 wrong PINs.")
        elif st.session_state.opened != choice.card_id:
            entered = st.text_input("Enter PIN to open", type="password", max_chars=4, key="open_pin")
            if st.button("Open card"):
                if choice.verify_pin(entered):
                    st.session_state.opened = choice.card_id
                    st.rerun()
                elif choice.locked:
                    flash("error", "🔒 Too many wrong PINs. Card locked.")
                else:
                    flash("error", f"Wrong PIN. {choice.attempts_left} attempts left.")
        else:
            st.success("Card unlocked")
            st.markdown(f"### {choice.name}")
            st.code(choice.card_id)

            m1, m2 = st.columns(2)
            m1.metric("Offline allowance left", fmt(choice.allowance))
            m2.metric("Offline payments left", f"{choice.offline_payments_left} of {MAX_OFFLINE_PAYMENTS}")
            st.caption(f"Per-payment limit {fmt(PER_TXN_LIMIT)}. "
                       f"Held in escrow by the bank: {fmt(bank.escrow_for(choice.card_id))}.")

            b1, b2 = st.columns(2)
            if b1.button("Lock card"):
                st.session_state.opened = None
                st.rerun()

            pending = [t for t in st.session_state.terminal if t["card_id"] == choice.card_id]
            can_release = online and not pending
            if b2.button("Release unused allowance", disabled=not can_release,
                         help="Needs the network back and all stored payments settled first."):
                returned = bank.release_unused(account, choice)
                st.session_state.opened = None
                flash("success", f"{fmt(returned)} returned to your real card. This card is now closed.")

            st.divider()
            st.subheader("Test: pay at an offline terminal")
            if online:
                st.info("The network is up, so a shop would authorise this online. "
                        "Switch the network off above to test offline payments.")
            else:
                merchant = st.text_input("Shop", value="Corner Shop")
                pay_amt = st.number_input("Payment (£)", min_value=0.0, step=1.0, format="%.2f", key="pay_amt")
                pay_pin = st.text_input("PIN", type="password", max_chars=4, key="pay_pin")

                p1, p2 = st.columns(2)
                if p1.button("Pay"):
                    try:
                        tx = choice.pay(pay_pin, to_pence(pay_amt), merchant)
                        st.session_state.terminal.append(tx)
                        flash("success", f"Approved offline. {fmt(choice.allowance)} left.")
                    except ValueError as e:
                        flash("error", f"Declined: {e}")
                if p2.button("Attack: try to overspend"):
                    try:
                        choice.pay(pay_pin, choice.allowance + 1, merchant)  # one penny too much
                        flash("error", "Overspend went through. This should never happen!")
                    except ValueError as e:
                        flash("warning", f"Chip refused the overspend: {e}")

# ---------------- TERMINAL / SETTLEMENT ----------------
st.divider()
st.subheader("Terminal (offline) → Bank settlement")
stored = st.session_state.terminal
st.write(f"{len(stored)} payment(s) stored on the terminal.")
if stored:
    st.table({
        "Shop": [t["merchant"] for t in stored],
        "Amount": [fmt(t["amount"]) for t in stored],
        "Payment #": [t["counter"] for t in stored],
        "Card": [t["card_id"] for t in stored],
    })

s1, s2, s3 = st.columns(3)

if s1.button("Reconnect and settle", disabled=not online or not stored,
             help="Switch the network back on first."):
    for tx in stored:
        result = bank.settle(account, tx)
        st.session_state.log.append((f"{fmt(tx['amount'])} at {tx['merchant']} (#{tx['counter']})", result))
        if result.startswith("ACCEPTED"):
            st.session_state.settled_txs.append(tx)
    for c in st.session_state.cards:
        c.sync()                          # chips reset their offline payment count
    st.session_state.terminal = []
    flash("success", "Settlement complete.")

attacks_ready = online and bool(st.session_state.settled_txs)
attack_help = "Settle at least one payment first (with the network on)."

if s2.button("Attack: replay last payment", disabled=not attacks_ready, help=attack_help):
    tx = dict(st.session_state.settled_txs[-1])
    result = bank.settle(account, tx)
    st.session_state.log.append((f"REPLAY of {fmt(tx['amount'])} at {tx['merchant']} (#{tx['counter']})", result))
    flash("warning", f"Replay attempt → {result}")

if s3.button("Attack: tamper with amount", disabled=not attacks_ready, help=attack_help):
    tx = dict(st.session_state.settled_txs[-1])
    tx["amount"] = 1                      # change the amount but keep the old signature
    tx["counter"] += 1                    # and a fresh counter so it isn't just a replay
    result = bank.settle(account, tx)
    st.session_state.log.append((f"TAMPERED payment of {fmt(tx['amount'])} at {tx['merchant']}", result))
    flash("warning", f"Tamper attempt → {result}")

if st.session_state.log:
    st.markdown("**Bank settlement log**")
    st.table({
        "Payment": [row[0] for row in st.session_state.log],
        "Result": [row[1] for row in st.session_state.log],
    })

if bank.merchant_totals:
    st.markdown("**Merchants paid from escrow**")
    st.table({
        "Shop": list(bank.merchant_totals),
        "Paid": [fmt(v) for v in bank.merchant_totals.values()],
    })