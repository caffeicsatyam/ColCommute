from google.adk.tools import FunctionTool
from typing import List, Dict, Any

def process_payment(ride_id: str, users: List[str], total_fare: float) -> Dict[str, Any]:
    """
    Processes payments for a ride, including fare splitting among multiple users.
    """
    if not users:
        return {"status": "error", "message": "No users provided for payment splitting."}

    share = round(total_fare / len(users), 2)
    payment_reports = []

    for user in users:
        # Simulate processing; integrate with a payment gateway in production.
        report = {
            "user_id": user,
            "amount": share,
            "status": "paid"
        }
        payment_reports.append(report)
        print(f"Processed payment of {share} for user {user} in ride {ride_id}.")

    return {
        "status": "success",
        "ride_id": ride_id,
        "total_fare": total_fare,
        "split_share": share,
        "payment_reports": payment_reports
    }

process_payment_tool = FunctionTool(func=process_payment)