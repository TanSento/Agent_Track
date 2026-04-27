import gradio as gr
from accounts import Account, get_share_price, InsufficientFundsError, InsufficientSharesError

# Global account instance
account = None

SYMBOLS = ["AAPL", "TSLA", "GOOGL"]


def create_account(initial_deposit):
    global account
    try:
        amount = float(initial_deposit)
        account = Account(amount)
        return get_dashboard()
    except ValueError as e:
        return str(e), "", "", "", ""


def get_dashboard():
    if account is None:
        empty = "No account created yet."
        return empty, empty, empty, empty, empty

    # Summary
    balance = account.get_balance()
    portfolio_value = account.calculate_portfolio_value()
    total_value = balance + portfolio_value
    pl_report = account.get_profit_loss()
    pl = pl_report['profit_loss']
    pl_pct = pl_report['profit_loss_percentage']
    pl_sign = "+" if pl >= 0 else ""

    summary = f"""💰 Cash Balance:      ${balance:>12,.2f}
📈 Portfolio Value:   ${portfolio_value:>12,.2f}
🏦 Total Value:       ${total_value:>12,.2f}
💹 Net Invested:      ${pl_report['net_invested']:>12,.2f}
📊 Profit / Loss:     {pl_sign}${pl:>11,.2f}  ({pl_sign}{pl_pct:.2f}%)"""

    # Holdings
    holdings = account.get_holdings()
    if holdings:
        rows = []
        rows.append(f"{'Symbol':<8} {'Qty':>6} {'Price':>10} {'Value':>12}")
        rows.append("-" * 40)
        for symbol, qty in holdings.items():
            price = get_share_price(symbol)
            value = price * qty
            rows.append(f"{symbol:<8} {qty:>6} ${price:>9,.2f} ${value:>11,.2f}")
        holdings_text = "\n".join(rows)
    else:
        holdings_text = "No shares held."

    # Share prices
    prices_lines = ["Current Prices:"]
    for sym in SYMBOLS:
        prices_lines.append(f"  {sym}: ${get_share_price(sym):,.2f}")
    prices_text = "\n".join(prices_lines)

    # Transactions
    transactions = account.get_transactions()
    if transactions:
        tx_lines = []
        for i, txn in enumerate(reversed(transactions), 1):
            ts = txn['timestamp'][11:19]  # HH:MM:SS
            t = txn['type'].upper()
            if t in ('DEPOSIT', 'WITHDRAWAL'):
                detail = f"${txn['amount']:,.2f}"
            else:
                sym = txn.get('symbol', '')
                qty = txn.get('quantity', '')
                price = txn.get('price', 0)
                detail = f"{sym} x{qty} @ ${price:,.2f}"
            tx_lines.append(f"[{ts}] {t:<12} {detail}")
        transactions_text = "\n".join(tx_lines)
    else:
        transactions_text = "No transactions yet."

    return summary, holdings_text, prices_text, transactions_text, ""


def deposit_funds(amount):
    if account is None:
        return "⚠️ Please create an account first.", "", "", "", ""
    try:
        account.deposit(float(amount))
        result = get_dashboard()
        return result[0], result[1], result[2], result[3], f"✅ Deposited ${float(amount):,.2f}"
    except ValueError as e:
        result = get_dashboard()
        return result[0], result[1], result[2], result[3], f"❌ {e}"


def withdraw_funds(amount):
    if account is None:
        return "⚠️ Please create an account first.", "", "", "", ""
    try:
        account.withdraw(float(amount))
        result = get_dashboard()
        return result[0], result[1], result[2], result[3], f"✅ Withdrew ${float(amount):,.2f}"
    except (ValueError, InsufficientFundsError) as e:
        result = get_dashboard()
        return result[0], result[1], result[2], result[3], f"❌ {e}"


def buy_shares(symbol, quantity):
    if account is None:
        return "⚠️ Please create an account first.", "", "", "", ""
    try:
        account.buy_shares(symbol, int(quantity))
        price = get_share_price(symbol)
        result = get_dashboard()
        return result[0], result[1], result[2], result[3], f"✅ Bought {int(quantity)} {symbol} @ ${price:,.2f}"
    except (ValueError, InsufficientFundsError) as e:
        result = get_dashboard()
        return result[0], result[1], result[2], result[3], f"❌ {e}"


def sell_shares(symbol, quantity):
    if account is None:
        return "⚠️ Please create an account first.", "", "", "", ""
    try:
        account.sell_shares(symbol, int(quantity))
        price = get_share_price(symbol)
        result = get_dashboard()
        return result[0], result[1], result[2], result[3], f"✅ Sold {int(quantity)} {symbol} @ ${price:,.2f}"
    except (ValueError, InsufficientSharesError) as e:
        result = get_dashboard()
        return result[0], result[1], result[2], result[3], f"❌ {e}"


css = """
.status-box { font-size: 1.05em; }
.mono { font-family: monospace; }
#create-btn { background: #2563eb; color: white; }
#deposit-btn { background: #16a34a; color: white; }
#withdraw-btn { background: #dc2626; color: white; }
#buy-btn { background: #7c3aed; color: white; }
#sell-btn { background: #ea580c; color: white; }
"""

with gr.Blocks(css=css, title="Trading Simulator") as demo:
    gr.Markdown("# 📊 Trading Simulation Platform")
    gr.Markdown("A simple account management demo. Available symbols: **AAPL** ($150), **TSLA** ($250), **GOOGL** ($2800)")

    with gr.Row():
        # Left column: controls
        with gr.Column(scale=1):
            gr.Markdown("## 🏦 Account Setup")
            with gr.Group():
                initial_deposit_input = gr.Number(label="Initial Deposit ($)", value=10000, minimum=0)
                create_btn = gr.Button("Create Account", variant="primary", elem_id="create-btn")

            gr.Markdown("## 💵 Funds")
            with gr.Group():
                deposit_input = gr.Number(label="Deposit Amount ($)", value=1000, minimum=0)
                deposit_btn = gr.Button("Deposit", elem_id="deposit-btn")
                withdraw_input = gr.Number(label="Withdraw Amount ($)", value=500, minimum=0)
                withdraw_btn = gr.Button("Withdraw", elem_id="withdraw-btn")

            gr.Markdown("## 📈 Trade Shares")
            with gr.Group():
                symbol_dropdown = gr.Dropdown(choices=SYMBOLS, value="AAPL", label="Symbol")
                quantity_input = gr.Number(label="Quantity", value=1, minimum=1, precision=0)
                with gr.Row():
                    buy_btn = gr.Button("Buy", elem_id="buy-btn")
                    sell_btn = gr.Button("Sell", elem_id="sell-btn")

            status_msg = gr.Textbox(label="Status", interactive=False, elem_classes=["status-box"])

        # Right column: dashboard
        with gr.Column(scale=2):
            gr.Markdown("## 📋 Dashboard")
            summary_box = gr.Textbox(
                label="Account Summary",
                lines=6,
                interactive=False,
                elem_classes=["mono"],
                value="Create an account to get started."
            )

            with gr.Row():
                with gr.Column():
                    holdings_box = gr.Textbox(
                        label="Holdings",
                        lines=8,
                        interactive=False,
                        elem_classes=["mono"]
                    )
                with gr.Column():
                    prices_box = gr.Textbox(
                        label="Market Prices",
                        lines=5,
                        interactive=False,
                        elem_classes=["mono"]
                    )

            transactions_box = gr.Textbox(
                label="Transaction History (most recent first)",
                lines=10,
                interactive=False,
                elem_classes=["mono"]
            )

    outputs = [summary_box, holdings_box, prices_box, transactions_box, status_msg]

    create_btn.click(
        fn=create_account,
        inputs=[initial_deposit_input],
        outputs=outputs
    )
    deposit_btn.click(
        fn=deposit_funds,
        inputs=[deposit_input],
        outputs=outputs
    )
    withdraw_btn.click(
        fn=withdraw_funds,
        inputs=[withdraw_input],
        outputs=outputs
    )
    buy_btn.click(
        fn=buy_shares,
        inputs=[symbol_dropdown, quantity_input],
        outputs=outputs
    )
    sell_btn.click(
        fn=sell_shares,
        inputs=[symbol_dropdown, quantity_input],
        outputs=outputs
    )

if __name__ == "__main__":
    demo.launch()