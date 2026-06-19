from typing import Dict, List

DEFAULT_HISTORY = {
    "user_id": "",
    "past_claim_count": "0",
    "accept_claim": "0",
    "manual_review_claim": "0",
    "rejected_claim": "0",
    "last_90_days_claim_count": "0",
    "history_flags": "none",
    "history_summary": "",
}


def get_user_history(user_id: str, history_df) -> Dict[str, str]:
    if user_id in history_df.index:
        return history_df.loc[user_id].fillna("").to_dict()
    return DEFAULT_HISTORY.copy()


def get_history_risk_flags(history: Dict[str, str]) -> List[str]:
    flags = []
    rejected = int(history.get("rejected_claim", "0") or "0")
    history_flags = history.get("history_flags", "")
    if rejected > 1 or (history_flags and history_flags.lower() not in {"", "none"}):
        flags.append("user_history_risk")
    return flags
