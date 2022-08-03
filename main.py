import json
import os
import eospyo
from loguru import logger

KEY = os.environ["PRIVATE_KEY"]
# SENDER = "pixeltycoons"
SENDER = "thisismyfirs"
logger.add("debug.log")

def send_assets_to_wallet(assets: tuple, receiver: str, memo: str = ""):
    """Sends given assets from SENDER wallet to given recepient wallet.
    In:
        assets: must be tuple, like (123456789, );
        receiver: string with receiver wallet;
        memo: optional selfexplanatory parameter.
    Out:
        TO-DO: return status of request.
    """
    logger.info("Create Transaction")
    data = [
        eospyo.Data(
            name="from",
            value=eospyo.types.Name(SENDER),
        ),
        eospyo.Data(
            name="to",
            value=eospyo.types.Name(receiver),
        ),
        eospyo.Data(
            name="asset_ids",
            value=eospyo.types.Array(values=assets, type_=eospyo.types.Uint64),
        ),
        eospyo.Data(
            name="memo",
            value=eospyo.types.String(memo),
        ),
    ]

    auth = eospyo.Authorization(actor=SENDER, permission="active")

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
    resp = signed_transaction.send()

    logger.info("Printing the response")
    resp_fmt = json.dumps(resp, indent=4)

    logger.info(f"Response:\n{resp_fmt}")


assets_to_send = (1099511628040,)
send_assets_to_wallet(assets_to_send, "thisismyseco", "send pokecrops")
