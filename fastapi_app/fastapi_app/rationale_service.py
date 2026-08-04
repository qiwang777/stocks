class RationaleService:
    def __init__(self, client=None):
        self.client = client

    def explain(self, symbol, horizon, p_up, move, recent):
        # Placeholder: simple template
        return f"Model probability={p_up:.2f} suggests {move} for {symbol} over {horizon}."
