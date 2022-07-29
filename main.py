import json
import os
import eospyo


KEY = os.environ["PRIVATE_KEY"]


print("Create Transaction")
data=[
    eospyo.Data(
        name="from",
        value=eospyo.types.Name("thisismyfirs"),
    ),
    eospyo.Data(
        name="message",
        value=eospyo.types.String("hello from eospyo"),
    ),
]

auth = eospyo.Authorization(actor="thisismyfirs", permission="active")

action = eospyo.Action(
    account="thisismyfirs", # this is the contract account
    name="sendmsg", # this is the action name
    data=data,
    authorization=[auth],
)

raw_transaction = eospyo.Transaction(actions=[action])

print("Link transaction to the network")
net = eospyo.WaxTestnet()  # this is an alias for a testnet node
# notice that eospyo returns a new object instead of change in place
linked_transaction = raw_transaction.link(net=net)


print("Sign transaction")
#key = "a_very_secret_key"
signed_transaction = linked_transaction.sign(key=KEY)


print("Send")
resp = signed_transaction.send()

print("Printing the response")
resp_fmt = json.dumps(resp, indent=4)
print(f"Response:\n{resp_fmt}")