import gradio as gr
from share_price_service import SharePriceService, get_share_price
from transaction import Transaction
from portfolio import Portfolio
from account import Account

# ---------------------------------------------------------------------------
# Since the provided source modules have several inconsistencies (method names
# differ between what's implemented and what's called), we wire everything up
# manually using the classes as they are actually implemented (based on the
# source code supplied).  We bypass TradingService / PortfolioValuation /
# ReportingService because those modules call non-existent methods
# (add_transaction, get_balance, get_initial_deposit, add_shares, etc.).
# Instead we drive the Account directly, which IS consistent in its source.
# ---------------------------------------------------------------------------

# Global state – single user
share_price_service = SharePriceService()

# Patch Portfolio so Account can use it (Account calls add_shares / remove_shares / has_shares
# but Portfolio only exposes buy / sell / has_sufficient_shares)
_orig_portfolio_init = Portfolio.__init__

def _patched_portfolio_init(self):
    _orig_portfolio_init(self)

Portfolio.__init__ = _patched_portfolio_init

def _add_shares(self, symbol, quantity):
    self.buy(symbol, quantity)

def _remove_shares(self, symbol, quantity):
    self.sell(symbol, quantity)

def _has_shares(self, symbol, quantity):
    return self.has_sufficient_shares(symbol, quantity)

Portfolio.add_shares = _add_shares
Portfolio.remove_shares = _remove_shares
Portfolio.has_shares = _has_shares

# Now we can safely create an Account
account = Account()

FIXED_PRICES = {"AAPL": 150.00, "TSLA": 700.00, "GOOGL": 2800.00}
SYMBOLS = list(FIXED_PRICES.keys())


# ---------------------------------------------------------------------------
# Helper to build the full status string shown in reports
# ---------------------------------------------------------------------------

def _holdings_text():
    holdings = account.portfolio.get_holdings()
    lines = ["=== Current Holdings ==="]
    if not holdings:
        lines.append("  No shares currently held.")
    else:
        for sym, qty in holdings.items():
            price = FIXED_PRICES.get(sym, 0)
            lines.append(f"  {sym}: {qty} share(s)  @ ${price:.2f} each  = ${qty * price:.2f}")
    lines.append(f"\nCash Balance: ${account.balance:.2f}")
    portfolio_value = sum(
        qty * FIXED_PRICES.get(sym, 0) for sym, qty in holdings.items()
    )
    total = account.balance + portfolio_value
    lines.append(f"Portfolio Market Value: ${portfolio_value:.2f}")
    lines.append(f"Total Account Value: ${total:.2f}")
    return "\n".join(lines)


def _pl_text():
    holdings = account.portfolio.get_holdings()
    portfolio_value = sum(
        qty * FIXED_PRICES.get(sym, 0) for sym, qty in holdings.items()
    )
    total = account.balance + portfolio_value
    pl = total - account.initial_deposit
    direction = "Profit" if pl >= 0 else "Loss"
    lines = [
        "=== Profit / Loss Report ===",
        f"Initial Deposit:        ${account.initial_deposit:.2f}",
        f"Cash Balance:           ${account.balance:.2f}",
        f"Portfolio Market Value: ${portfolio_value:.2f}",
        f"Total Account Value:    ${total:.2f}",
        f"{direction}:                 ${abs(pl):.2f}",
    ]
    return "\n".join(lines)


def _tx_text():
    txns = account.get_transactions()
    lines = ["=== Transaction History ==="]
    if not txns:
        lines.append("  No transactions recorded.")
    else:
        for t in txns:
            lines.append(f"  {t}")
    return "\n".join(lines)


def _full_report():
    return "\n\n".join([_holdings_text(), _pl_text(), _tx_text()])


# ---------------------------------------------------------------------------
# Action functions called by Gradio
# ---------------------------------------------------------------------------

def create_account(initial_deposit):
    global account
    try:
        amount = float(initial_deposit)
        account = Account(initial_deposit=amount)
        return f"✅ Account created with initial deposit of ${amount:.2f}", _full_report()
    except Exception as e:
        return f"❌ {e}", _full_report()


def deposit(amount):
    try:
        account.deposit(float(amount))
        return f"✅ Deposited ${float(amount):.2f}", _full_report()
    except Exception as e:
        return f"❌ {e}", _full_report()


def withdraw(amount):
    try:
        account.withdraw(float(amount))
        return f"✅ Withdrew ${float(amount):.2f}", _full_report()
    except Exception as e:
        return f"❌ {e}", _full_report()


def buy_shares(symbol, quantity):
    try:
        qty = int(quantity)
        account.buy_shares(symbol.upper(), qty, share_price_service.get_price)
        price = share_price_service.get_price(symbol.upper())
        return (
            f"✅ Bought {qty} share(s) of {symbol.upper()} @ ${price:.2f} each "
            f"(Total: ${price * qty:.2f})",
            _full_report(),
        )
    except Exception as e:
        return f"❌ {e}", _full_report()


def sell_shares(symbol, quantity):
    try:
        qty = int(quantity)
        account.sell_shares(symbol.upper(), qty, share_price_service.get_price)
        price = share_price_service.get_price(symbol.upper())
        return (
            f"✅ Sold {qty} share(s) of {symbol.upper()} @ ${price:.2f} each "
            f"(Total: ${price * qty:.2f})",
            _full_report(),
        )
    except Exception as e:
        return f"❌ {e}", _full_report()


def get_prices():
    lines = ["=== Current Share Prices ==="]
    for sym, price in FIXED_PRICES.items():
        lines.append(f"  {sym}: ${price:.2f}")
    return "\n".join(lines)


def refresh_report():
    return _full_report()


# ---------------------------------------------------------------------------
# Build the Gradio UI
# ---------------------------------------------------------------------------

with gr.Blocks(title="Trading Simulation Platform", theme=gr.themes.Soft()) as demo:
    gr.Markdown(
        """
        # 📈 Trading Simulation Platform
        A demo of the account management & trading system.  
        Available symbols: **AAPL** ($150), **TSLA** ($700), **GOOGL** ($2800)
        """
    )

    status_box = gr.Textbox(
        label="Last Action Status", interactive=False, lines=2
    )

    with gr.Row():
        # Left column – actions
        with gr.Column(scale=1):

            # --- Account Setup ---
            with gr.Group():
                gr.Markdown("### 🏦 Account Setup")
                init_deposit_input = gr.Number(
                    label="Initial Deposit ($)", value=10000, minimum=0
                )
                create_btn = gr.Button("Create / Reset Account", variant="primary")

            # --- Deposit / Withdraw ---
            with gr.Group():
                gr.Markdown("### 💵 Cash Management")
                with gr.Row():
                    dep_amount = gr.Number(label="Amount ($)", value=1000, minimum=0)
                with gr.Row():
                    dep_btn = gr.Button("Deposit")
                    wd_btn = gr.Button("Withdraw")

            # --- Buy / Sell Shares ---
            with gr.Group():
                gr.Markdown("### 📊 Trade Shares")
                trade_symbol = gr.Dropdown(
                    choices=SYMBOLS, value="AAPL", label="Symbol"
                )
                trade_qty = gr.Number(label="Quantity", value=1, minimum=1, precision=0)
                with gr.Row():
                    buy_btn = gr.Button("Buy", variant="primary")
                    sell_btn = gr.Button("Sell", variant="stop")

            # --- Share Prices ---
            with gr.Group():
                gr.Markdown("### 🔍 Share Prices")
                prices_btn = gr.Button("Show Current Prices")
                prices_out = gr.Textbox(
                    label="Prices", interactive=False, lines=5
                )
                prices_btn.click(fn=get_prices, inputs=[], outputs=prices_out)

        # Right column – report
        with gr.Column(scale=2):
            gr.Markdown("### 📋 Account Report")
            refresh_btn = gr.Button("🔄 Refresh Report")
            report_out = gr.Textbox(
                label="Full Report",
                interactive=False,
                lines=28,
                value=_full_report(),
            )

    # Wire up buttons
    create_btn.click(
        fn=create_account,
        inputs=[init_deposit_input],
        outputs=[status_box, report_out],
    )
    dep_btn.click(
        fn=deposit,
        inputs=[dep_amount],
        outputs=[status_box, report_out],
    )
    wd_btn.click(
        fn=withdraw,
        inputs=[dep_amount],
        outputs=[status_box, report_out],
    )
    buy_btn.click(
        fn=buy_shares,
        inputs=[trade_symbol, trade_qty],
        outputs=[status_box, report_out],
    )
    sell_btn.click(
        fn=sell_shares,
        inputs=[trade_symbol, trade_qty],
        outputs=[status_box, report_out],
    )
    refresh_btn.click(
        fn=refresh_report,
        inputs=[],
        outputs=[report_out],
    )

if __name__ == "__main__":
    demo.launch()