import tkinter as tk

APP_NAME = "Offline Savings"

W, H = 390, 760
BG = "#f5efe6"
INK = "#1d2540"
MUTED = "#6b7280"
WHITE = "#ffffff"
TRACK = "#ddd5c6"
GREEN = "#2f9e6e"
ORANGE = "#e8892b"
RED = "#d62839"

PAY_AMOUNT = 5.00

CARDS = [
    {"short": "Emergency", "name": "Emergency card", "number": "•••• •••• •••• 4821",
     "color": "#e47cbe", "limit": 30, "balance": 150.00, "spent": 0.0,
     "pending": [], "locked": False},
    {"short": "Everyday", "name": "Everyday card", "number": "•••• •••• •••• 7390",
     "color": "#17a398", "limit": 50, "balance": 80.00, "spent": 0.0,
     "pending": [], "locked": False},
    {"short": "One-use", "name": "One-use card", "number": "•••• •••• •••• 1156",
     "color": "#6a4c93", "limit": 25, "balance": 25.00, "spent": 0.0,
     "pending": [], "locked": False},
]

state = {
    "index": 0,          # start on the Emergency card
    "offline": False,
    "warned": False,     # cooling-off: first tap warns, second tap goes ahead
    "msg": "Try a test payment, then switch to offline mode and try again.",
    "msg_color": MUTED,
}

root = tk.Tk()
root.title("Lifeline")
root.geometry("%dx%d+300+20" % (W, H))
root.minsize(W, H)
root.configure(bg=BG)

canvas = tk.Canvas(root, width=W, height=H, bg=BG, highlightthickness=0)
canvas.pack(fill="both", expand=True)

hits = []   # clickable areas: (x1, y1, x2, y2, function)


def rrect(x1, y1, x2, y2, r, fill):
    """Rounded rectangle from plain rectangles and circles."""
    canvas.create_rectangle(x1 + r, y1, x2 - r, y2, fill=fill, outline=fill)
    canvas.create_rectangle(x1, y1 + r, x2, y2 - r, fill=fill, outline=fill)
    canvas.create_oval(x1, y1, x1 + 2 * r, y1 + 2 * r, fill=fill, outline=fill)
    canvas.create_oval(x2 - 2 * r, y1, x2, y1 + 2 * r, fill=fill, outline=fill)
    canvas.create_oval(x1, y2 - 2 * r, x1 + 2 * r, y2, fill=fill, outline=fill)
    canvas.create_oval(x2 - 2 * r, y2 - 2 * r, x2, y2, fill=fill, outline=fill)


def button(x1, y1, x2, y2, label, fn, fill, ink, size=13):
    rrect(x1, y1, x2, y2, 14, fill)
    canvas.create_text((x1 + x2) // 2, (y1 + y2) // 2, text=label, fill=ink,
                       font=("Helvetica", size, "bold"))
    hits.append((x1, y1, x2, y2, fn))


def say(text, color=MUTED):
    state["msg"] = text
    state["msg_color"] = color


# ---------- actions ----------
def choose(n):
    state["index"] = n
    state["warned"] = False
    say("Showing the %s." % CARDS[n]["name"])
    draw()


def pay():
    card = CARDS[state["index"]]
    if card["locked"]:
        say("This card is locked. Unlock it to pay.", RED)
    elif card["balance"] < PAY_AMOUNT:
        say("Not enough balance on this card.", RED)
    elif card["spent"] + PAY_AMOUNT > card["limit"] and not state["warned"]:
        state["warned"] = True
        say("That goes over your £%d limit. Take a breath. Tap Pay again to "
            "go ahead, or leave it." % card["limit"], ORANGE)
    else:
        state["warned"] = False
        card["balance"] -= PAY_AMOUNT
        card["spent"] += PAY_AMOUNT
        if state["offline"]:
            card["pending"].append(PAY_AMOUNT)
            say("Offline: payment saved. It will be sent when you reconnect.", ORANGE)
        else:
            say("Paid £%.2f." % PAY_AMOUNT, GREEN)
        if card["name"] == "One-use card":
            card["locked"] = True
            say("Paid. This one-use card is now used up.", GREEN)
    draw()


def toggle_lock():
    card = CARDS[state["index"]]
    card["locked"] = not card["locked"]
    state["warned"] = False
    say("Card locked." if card["locked"] else "Card unlocked.")
    draw()


def toggle_offline():
    state["offline"] = not state["offline"]
    state["warned"] = False
    if state["offline"]:
        say("Offline mode. Payments are held until you reconnect.", ORANGE)
    else:
        count = sum(len(c["pending"]) for c in CARDS)
        total = sum(sum(c["pending"]) for c in CARDS)
        for c in CARDS:
            c["pending"] = []
        if count:
            say("Back online. %d payment%s sent (£%.2f)." %
                (count, "" if count == 1 else "s", total), GREEN)
        else:
            say("Back online.", GREEN)
    draw()


def change_limit():
    card = CARDS[state["index"]]
    card["limit"] = card["limit"] + 10 if card["limit"] < 100 else 10
    state["warned"] = False
    say("Daily limit set to £%d. Only you can change this." % card["limit"])
    draw()


# ---------- drawing ----------
def draw():
    canvas.delete("all")
    hits.clear()
    i = state["index"]
    card = CARDS[i]
    offline = state["offline"]

    canvas.create_rectangle(0, 0, 2000, 2000, fill=BG, outline=BG)

    # header
    canvas.create_text(24, 50, text=APP_NAME, fill=INK,
                       font=("Helvetica", 26, "bold"), anchor="w")
    rrect(W - 124, 34, W - 24, 66, 16, ORANGE if offline else GREEN)
    canvas.create_text(W - 74, 50, text="OFFLINE" if offline else "ONLINE",
                       fill=WHITE, font=("Helvetica", 11, "bold"))

    # tabs
    for n, c in enumerate(CARDS):
        x1 = 24 + n * 114
        x2 = x1 + 108
        selected = (n == i)
        rrect(x1, 100, x2, 136, 18, INK if selected else TRACK)
        canvas.create_text((x1 + x2) // 2, 118, text=c["short"],
                           fill=WHITE if selected else INK,
                           font=("Helvetica", 13, "bold"))
        hits.append((x1, 100, x2, 136, lambda n=n: choose(n)))

    # the card
    color = "#8b919c" if card["locked"] else card["color"]
    rrect(30, 160, 360, 340, 24, color)
    title = card["name"] + ("  (locked)" if card["locked"] else "")
    canvas.create_text(54, 192, text=title, fill=WHITE,
                       font=("Helvetica", 14, "bold"), anchor="w")
    # signal bars, crossed out when offline
    for k, h in enumerate((6, 11, 16)):
        bx = 316 + k * 9
        canvas.create_rectangle(bx, 200 - h, bx + 6, 200, fill=WHITE, outline=WHITE)
    if offline:
        canvas.create_line(312, 204, 344, 182, fill=INK, width=3)
    canvas.create_text(54, 228, text="Available", fill=WHITE,
                       font=("Helvetica", 12), anchor="w")
    canvas.create_text(54, 266, text="£%.2f" % card["balance"], fill=WHITE,
                       font=("Helvetica", 34, "bold"), anchor="w")
    canvas.create_text(54, 318, text=card["number"], fill=WHITE,
                       font=("Helvetica", 12), anchor="w")
    canvas.create_text(336, 318, text="debit", fill=WHITE,
                       font=("Helvetica", 12, "bold"), anchor="e")

    # spending bar
    canvas.create_text(30, 372, text="Spent today", fill=INK,
                       font=("Helvetica", 13, "bold"), anchor="w")
    canvas.create_text(360, 372, text="£%.2f of £%d" % (card["spent"], card["limit"]),
                       fill=MUTED, font=("Helvetica", 13), anchor="e")
    rrect(30, 390, 360, 406, 8, TRACK)
    frac = min(card["spent"] / float(card["limit"]), 1.0)
    if card["spent"] > 0:
        bar = GREEN if frac < 0.8 else (ORANGE if frac < 1.0 else RED)
        rrect(30, 390, 30 + max(int(330 * frac), 16), 406, 8, bar)

    # waiting-to-send panel
    count = len(card["pending"])
    total = sum(card["pending"])
    rrect(30, 428, 360, 486, 16, WHITE)
    canvas.create_text(48, 446, text="Waiting to send", fill=MUTED,
                       font=("Helvetica", 11), anchor="w")
    if count:
        txt = "%d payment%s  ·  £%.2f" % (count, "" if count == 1 else "s", total)
    else:
        txt = "Nothing waiting"
    canvas.create_text(48, 468, text=txt, fill=INK,
                       font=("Helvetica", 14, "bold"), anchor="w")

    # pay button
    button(30, 506, 360, 562, "Pay £%.2f  ·  test purchase" % PAY_AMOUNT, pay,
           INK, WHITE, size=16)

    # small buttons
    button(30, 578, 132, 622, "Unlock" if card["locked"] else "Lock",
           toggle_lock, TRACK, INK)
    button(144, 578, 246, 622, "Reconnect" if offline else "Go offline",
           toggle_offline, TRACK, INK)
    button(258, 578, 360, 622, "Limit +£10", change_limit, TRACK, INK)

    # message
    canvas.create_text(W // 2, 670, text=state["msg"], fill=state["msg_color"],
                       font=("Helvetica", 13), width=330, justify="center")
    canvas.create_text(W // 2, 738, text="Prototype  ·  simulated money",
                       fill=MUTED, font=("Helvetica", 10))


def on_click(event):
    for x1, y1, x2, y2, fn in list(hits):
        if x1 <= event.x <= x2 and y1 <= event.y <= y2:
            fn()
            return


canvas.bind("<Button-1>", on_click)

draw()
root.update_idletasks()
root.lift()
root.mainloop()