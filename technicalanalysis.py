import pandas as pd


class TechnicalAnalysis:
    def __init__(self):
        pass

    def add_NR7_flag(self, data: pd.DataFrame):
        data["Range"] = round(100 * (data.high - data.low) / data.close, 2)
        data["NR7"] = data["Range"].rolling(7).min() == data["Range"]
        return data

    # Function to calculate Fibonacci Pivot Points
    def calculate_fibonacci_pivots(self, data: pd.DataFrame, cash: int | float):
        data = self.add_NR7_flag(data)

        pivot_levels = {"PP": (data["high"] + data["low"] + data["close"]) / 3}
        pivot_levels["R1"] = pivot_levels["PP"] + 0.382 * (data["high"] - data["low"])
        pivot_levels["S1"] = pivot_levels["PP"] - 0.382 * (data["high"] - data["low"])
        pivot_levels["R2"] = pivot_levels["PP"] + 0.618 * (data["high"] - data["low"])
        pivot_levels["S2"] = pivot_levels["PP"] - 0.618 * (data["high"] - data["low"])
        pivot_levels["R3"] = pivot_levels["PP"] + 1.0 * (data["high"] - data["low"])
        pivot_levels["S3"] = pivot_levels["PP"] - 1.0 * (data["high"] - data["low"])

        # Calculate Top Central (TC) and Bottom Central (BC) Pivot Points
        pivot_levels["TC"] = (
            data["high"] + data["low"] + data["open"] + 2 * data["close"]
        ) / 5
        pivot_levels["BC"] = (
            data["high"] + data["low"] + 2 * data["open"] + data["close"]
        ) / 5

        # Determine if it's an RB candidate
        rb_candidate = data["NR7"].values[-1] and data["close"].values[-1] < 0.25 * cash

        # Return the levels and RB candidate status
        return {
            "Symbol": data.symbol.values[-1],
            "PP": round(pivot_levels["PP"].values[-1], 2),
            "R1": round(pivot_levels["R1"].values[-1], 2),
            "S1": round(pivot_levels["S1"].values[-1], 2),
            "R2": round(pivot_levels["R2"].values[-1], 2),
            "S2": round(pivot_levels["S2"].values[-1], 2),
            "R3": round(pivot_levels["R3"].values[-1], 2),
            "S3": round(pivot_levels["S3"].values[-1], 2),
            "TC": round(pivot_levels["TC"].values[-1], 2),
            "BC": round(pivot_levels["BC"].values[-1], 2),
            "PDL": round(data["low"].values[-1], 2),
            "PDH": round(data["high"].values[-1], 2),
            "RB_Candidate": rb_candidate,
        }
