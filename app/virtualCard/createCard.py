"""
createCard.py - the demo screen.
Run with:  streamlit run createCard.py
"""
import streamlit as st

from chip import (
    MAX_ALLOWANCE, PER_TXN_LIMIT, RealAccount, create_offline_card,
    fmt, to_pence, verify_transaction,
)

st.set_page_config(page_title="Offline Card", page_icon="💳")

# ---- App state (lives until you refresh the page) ----
if "account" not in st.session_state:
    st.session_state.account = RealAccount("Margaret", 500_00)  # demo: £500 on the real card
    st.session_state.cards = []
    st.session_state.opened = None       # card_id of the card currently unlocked
    st.session_state.terminal = []       # signed payments stored on the "terminal"
    st.session_state.seen = set()

account = st.session_state.account

st.title("💳 Offline Card")
c1, c2 = st.columns(2)
c1.metric("Real card balance", fmt(account.balance))
c2.metric("Reserved for offline cards", fmt(account.escrow))

if "msg" in st.session_state:
    st.success(st.session_state.pop("msg"))

tab_create, tab_open = st.tabs(["Create offline card", "My offline cards"])

# ---------------- CREATE ----------------
with tab_create:
    st.caption(f"Money is moved from your real card. Max {fmt(MAX_ALLOWANCE)} per offline card.")
    name = st.text_input("Card name", placeholder="e.g. Emergency food")
    amount = st.number_input("Amount (£)", min_value=0.0, step=5.0, format="%.2f")
    pin = st.text_input("Choose a 4-digit PIN", type="password", max_chars=4)
    pin2 = st.text_input("Confirm PIN", type="password", max_chars=4)

    if st.button("Add", type="primary"):
        try:
            card = create_offline_card(account, name, amount, pin, pin2)
            st.session_state.cards.append(card)
            st.session_state.msg = (f"Offline card '{card.name}' created with {fmt(card.allowance)}. "
                                    "Go to 'My offline cards' and open it with your PIN.")
            st.rerun()  # refresh so the balances at the top update
        except ValueError as e:
            st.error(str(e))

# ---------------- OPEN ----------------
with tab_open:
    cards = st.session_state.cards
    if not cards:
        st.info("No offline cards yet. Create one first.")
    else:
        labels = {f"{c.name}  ({c.card_id})": c for c in cards}
        choice = labels[st.selectbox("Choose a card", list(labels))]

        if choice.locked:
            st.error("🔒 This card is locked after 3 wrong PINs.")
        elif st.session_state.opened != choice.card_id:
            entered = st.text_input("Enter PIN to open", type="password", max_chars=4, key="open_pin")
            if st.button("Open card"):
                if choice.verify_pin(entered):
                    st.session_state.opened = choice.card_id
                    st.rerun()
                elif choice.locked:
                    st.error("🔒 Too many wrong PINs. Card locked.")
                else:
                    st.error(f"Wrong PIN. {choice.attempts_left} attempts left.")
        else:
            st.success("Card unlocked")
            st.markdown(f"### {choice.name}")
            st.code(choice.card_id)
            st.metric("Offline allowance left", fmt(choice.allowance))
            st.caption(f"Per-payment limit {fmt(PER_TXN_LIMIT)}")

            if st.button("Lock card"):
                st.session_state.opened = None
                st.rerun()

            st.divider()
            st.subheader("Test: pay at an offline terminal")
            merchant = st.text_input("Shop", value="Corner Shop")
            pay_amt = st.number_input("Payment (£)", min_value=0.0, step=1.0, format="%.2f", key="pay_amt")
            pay_pin = st.text_input("PIN", type="password", max_chars=4, key="pay_pin")
            if st.button("Pay"):
                try:
                    tx = choice.pay(pay_pin, to_pence(pay_amt), merchant)
                    st.session_state.terminal.append((choice, tx))
                    st.success(f"Approved offline. {fmt(choice.allowance)} left.")
                except ValueError as e:
                    st.error(f"Declined: {e}")

# ---------------- TERMINAL / SETTLEMENT ----------------
st.divider()
st.subheader("Terminal (offline) → Bank settlement")
stored = st.session_state.terminal
st.write(f"{len(stored)} payment(s) stored on the terminal.")

cs1, cs2 = st.columns(2)
if cs1.button("Reconnect and settle"):
    for card, tx in stored:
        st.write(f"{fmt(tx['amount'])} at {tx['merchant']} (#{tx['counter']}): "
                 f"{verify_transaction(card.public_key, tx, st.session_state.seen)}")
if cs2.button("Attack: replay last payment") and stored:
    card, tx = stored[-1]
    st.write("Replay attempt → " + verify_transaction(card.public_key, tx, st.session_state.seen))