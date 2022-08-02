import json
import os
import eospyo
from loguru import logger

KEY = os.environ["PRIVATE_KEY"]
SENDER = "pixeltycoons"


print("Create Transaction")
data = [
    eospyo.Data(
        name="from",
        value=eospyo.types.Name("thisismyfirs"),
    ),
    eospyo.Data(
        name="to",
        value=eospyo.types.Name("thisismyseco"),
    ),
    eospyo.Data(
        name="asset_ids",
        value=eospyo.types.Array(values=(1099511797168,), type_=eospyo.types.Uint64),
    ),
    eospyo.Data(
        name="memo",
        value=eospyo.types.String("catch em all"),
    ),
]

auth = eospyo.Authorization(actor="thisismyfirs", permission="active")

action = eospyo.Action(
    account="atomicassets",  # this is the contract account
    name="transfer",  # this is the action name
    data=data,
    authorization=[auth],
)

raw_transaction = eospyo.Transaction(actions=[action])

logger.info("Link transaction to the network")
net = eospyo.WaxTestnet()  # this is an alias for a testnet node
# notice that eospyo returns a new object instead of change in place
linked_transaction = raw_transaction.link(net=net)

logger.info("Sign transaction")
signed_transaction = linked_transaction.sign(key=KEY)

logger.info("Send")
#resp = signed_transaction.send()

logger.info("Printing the response")
resp_fmt = json.dumps(resp, indent=4)

logger.info(f"Response:\n{resp_fmt}")
