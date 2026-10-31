from datetime import datetime


class TokenTracker:
    """Records every AI call: tokens used, time taken, and estimated cost."""

    def __init__(self, input_price=0.30, output_price=2.50):
        # Prices in US dollars per 1 million tokens.
        # Check Google's current pricing page and update these two numbers.
        self.input_price = input_price
        self.output_price = output_price
        self.calls = []

    def record(self, feature, input_tokens, output_tokens, seconds):
        cost = (
            input_tokens * self.input_price + output_tokens * self.output_price
        ) / 1_000_000
        self.calls.append({
            "time": datetime.now().isoformat(timespec="seconds"),
            "feature": feature,         
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
            "seconds": round(seconds, 2),
            "cost_usd": round(cost, 6),
        })

    def summary(self):
        by_feature = {}
        for call in self.calls:
            item = by_feature.setdefault(
                call["feature"], {"calls": 0, "tokens": 0, "seconds": 0, "cost_usd": 0}
            )
            item["calls"] += 1
            item["tokens"] += call["input_tokens"] + call["output_tokens"]
            item["seconds"] += call["seconds"]
            item["cost_usd"] += call["cost_usd"]

        for item in by_feature.values():
            item["avg_seconds"] = round(item["seconds"] / item["calls"], 2)
            item["cost_usd"] = round(item["cost_usd"], 6)
            del item["seconds"]

        return {
            "total_calls": len(self.calls),
            "total_input_tokens": sum(c["input_tokens"] for c in self.calls),
            "total_output_tokens": sum(c["output_tokens"] for c in self.calls),
            "total_cost_usd": round(sum(c["cost_usd"] for c in self.calls), 6),
            "by_feature": by_feature,
        }

    def reset(self):
        self.calls = []


# One shared tracker used by the whole app
tracker = TokenTracker()