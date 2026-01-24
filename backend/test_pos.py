import requests
import json

BASE_URL = "http://127.0.0.1:8000"

def get_token():
    login_data = {"username": "testuser", "password": "testpassword"}
    response = requests.post(f"{BASE_URL}/token", data=login_data)
    if response.status_code == 200:
        return response.json().get("access_token")
    return None

def test_pos_and_credit():
    token = get_token()
    if not token:
        print("Login failed")
        return

    headers = {"Authorization": f"Bearer {token}"}

    # 1. Create Invoice (Credit Sale)
    # Need an item first (assuming ID 1 exists from previous test, else create)
    # Retry create item just in case
    item_data = {
        "name": "Rice",
        "parent_unit": "Sack",
        "child_unit": "Kg",
        "conversion_factor": 25,
        "sku": "RICE001",
        "bulk_qty": 10
    }
    item_res = requests.post(f"{BASE_URL}/items/", json=item_data, headers=headers)
    item_id = item_res.json().get("id") if item_res.status_code == 200 else 1 

    invoice_data = {
        "customer_name": "Ramesh",
        "customer_phone": "9876543210",
        "status": "CREDIT",
        "items": [
            {
                "item_id": item_id,
                "quantity": 5, # 5 Kg
                "unit_price": 40 # 40 Rs/Kg
            }
        ]
    }
    
    print("\n--- Creating Invoice (Credit) ---")
    response = requests.post(f"{BASE_URL}/invoices/", json=invoice_data, headers=headers)
    print(f"Status: {response.status_code}")
    print(f"Response: {response.text}")
    
    if response.status_code == 200:
        inv = response.json()
        print(f"Invoice ID: {inv['id']}, Total: {inv['total_amount']}")
        
        # 2. Check Ledger
        print("\n--- Checking Ledger ---")
        ledger_res = requests.get(f"{BASE_URL}/ledger/9876543210", headers=headers)
        print(f"Status: {ledger_res.status_code}")
        ledger = ledger_res.json()
        print(f"Ledger Entries: {len(ledger)}")
        if len(ledger) > 0:
            entry = ledger[0]
            print(f"Balance: {entry['balance']} | Debit: {entry['debit_amount']}")
            if entry['balance'] == 200:
                print("SUCCESS: Balance matches Invoice Total (5*40=200)")
            else:
                print("FAILURE: Balance Mismatch")

if __name__ == "__main__":
    test_pos_and_credit()
