CUSTOMERS = {
    "C001": {"name": "Asha Rao", "account_no": "1234567890", "balance": 50000},
}

def read_masked_customer(customer_id):
    c = CUSTOMERS[customer_id]
    return {"name": c["name"], "account_no": "******" + c["account_no"][-4:]}

def initiate_transfer(from_id, to_id, amount):
    return f"Transferred {amount} from {from_id} to {to_id}"

TOOLS = {
    "read_masked_customer": read_masked_customer,
    "initiate_transfer": initiate_transfer,
}