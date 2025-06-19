import base64

with open("sklearn170.py", "rb") as f:
    encoded = base64.b85encode(f.read()).decode()

print(f"ENCRYPTED_CODE = \"\"\"\n{encoded}\n\"\"\"")