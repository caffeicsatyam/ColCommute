from google.adk.tools import FunctionTool
from typing import List, Dict, Any, Annotated

def process_payment_tool(ride_id: str, users: List[str], total_fare: float) -> Dict[str, Any]:
    """
    Processes payments for a ride, including fare splitting among multiple users.

    Args:
        ride_id (str): The unique identifier for the completed ride.
        users (List[str]): List of user identifiers whose payments are to be processed.
        total_fare (float): The total cost of the ride to be split.

    Returns:
        Dict[str, Any]: A report indicating the status of payment for each user.
    """
    if not users:
        return {"status": "error", "message": "No users provided for payment splitting."}

    share = round(total_fare / len(users), 2)
    payments_status = []
    
    for user in users:
        payments_status.append({
            "user_id": Annotated[str, "The unique identifier for the user."],
            "amount": Annotated[float, "The amount to be paid by the user."],
            "status": Literal["paid", "pending", "failed"]
        })
        print(f"Processed payment of {share} for user {user} in ride {ride_id}.")

    return {
        "status": "success",
        "ride_id": ride_id,
        "total_fare": total_fare,
        "split_share": share,
        "payment_reports": payments_status
    }

process_payment_tool = FunctionTool(func=process_payment_tool)