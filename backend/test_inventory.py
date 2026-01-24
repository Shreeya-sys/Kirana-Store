import requests
import time

BASE_URL = "http://127.0.0.1:8000"

def get_token():
    # Login as before (assuming testuser exists from previous test)
    login_data = {"username": "testuser", "password": "testpassword"}
    response = requests.post(f"{BASE_URL}/token", data=login_data)
    if response.status_code == 200:
        return response.json().get("access_token")
    return None

def test_inventory():
    token = get_token()
    if not token:
        print("Login failed, cannot test inventory")
        return

    headers = {"Authorization": f"Bearer {token}"}

    # 1. Create Item (Sugar Sack)
    item_data = {
        "name": "Sugar",
        "parent_unit": "Sack",
        "child_unit": "Gram",
        "conversion_factor": 10000,
        "sku": "SUG001",
        "bulk_qty": 5
    }
    response = requests.post(f"{BASE_URL}/items/", json=item_data, headers=headers)
    print(f"Create Item: {response.status_code}")
    if response.status_code != 200:
        print(f"Error: {response.text}")
        return
    
    item_id = response.json()["id"]
    print(f"Created Item ID: {item_id}")

    # 2. Add implementation shortcut: We need initial stock.
    # Since I didn't verify an 'Add Stock' endpoint (only Create Item), 
    # and Item defaults to 0, I might fail decant.
    # Wait, Models say default=0.
    # I should have added an 'Add Stock' logic or manual DB update.
    # Ah, I missed 'Purchase' or 'Add Stock' endpoint in the plan.
    # I'll update the test to fail expectedly or I just add a quick hack?
    # No, I should fix the code to allow adding stock or update the ItemCreate to allow initial stock?
    # Schema `ItemCreate` passes `ItemBase`. `ItemBase` doesn't have qty.
    # I should add 'Add Stock' endpoint or update `create_item` to accept initial stock.
    # Let's add specific endpoint for this test or just update the logic in next step.
    
    # For now, let's trying decanting 0 stock and see failure.
    
    response = requests.post(f"{BASE_URL}/inventory/decant/{item_id}", headers=headers)
    print(f"Decant (Stock 0): {response.status_code} (Expected 400)")

if __name__ == "__main__":
    test_inventory()
