from decimal import Decimal

# Simple HSN -> GST Rate mapping (Mock)
HSN_RATES = {
    "1001": 0, # Wheat, Rice (Exempt)
    "1701": 5, # Sugar
    "3304": 18, # Cosmetics
    "8517": 18 # Electronics
}

def calculate_gst(hsn_code: str, amount: float):
    rate = HSN_RATES.get(hsn_code, 18) # Default 18%
    tax_amount = (amount * rate) / 100
    total_amount = amount + tax_amount
    
    # Split CGST/SGST (intra-state assumption for now)
    cgst = tax_amount / 2
    sgst = tax_amount / 2
    
    return {
        "hsn": hsn_code,
        "rate": rate,
        "taxable_amount": amount,
        "cgst": cgst,
        "sgst": sgst,
        "igst": 0, # Assuming intra-state
        "total_tax": tax_amount,
        "total_amount": total_amount
    }
