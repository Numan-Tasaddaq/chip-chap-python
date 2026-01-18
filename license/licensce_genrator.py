# generate_license.py
import hashlib
import json

LICENSE_SECRET = "license"

license_key = "ABCDEF-123456"

signature = hashlib.sha256(
    f"{license_key}|{LICENSE_SECRET}".encode("utf-8")
).hexdigest()

license_data = {
    "license_key": license_key,
    "signature": signature,
}

with open("license.json", "w") as f:
    json.dump(license_data, f, indent=2)

print("license.json generated")
