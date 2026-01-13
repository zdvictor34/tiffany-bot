import os
from dotenv import load_dotenv

load_dotenv()

subscriptions = {}

VIP_GROUPS = {
    "jacqueline": os.getenv("VIP_GROUP_ID_JACQUELINE"),
    "jennifer": os.getenv("VIP_GROUP_ID_JENNIFER")
}

print("VIP GROUPS:", VIP_GROUPS)

