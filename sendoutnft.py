import os
import eospyo
from loguru import logger

import requests


ENTRYPOINT = "https://test.wax.api.atomicassets.io/atomicassets/v1"
ENTRYPOINT_ASSETS = f"{ENTRYPOINT}/assets"
#KEY = os.environ["PRIVATE_KEY"]
# SENDER = "pixeltycoons"
SENDER = "thisismyfirs"
COLLECTION = "gen1pokemon1"
logger.add("debug.log")


DICT = {
    "Grass Tuft": 289228,
    "Dried Leaf": 265138,
    "Pinecone": 289221,
    "Big Flat Stone": 529844,
    "Granite Stone": 265148,
}


def send_assets_to_wallet(assets: list, receiver: str, memo: str = ""):
    """
    Sends given assets from SENDER wallet to given recipient wallet.
    In:
        assets: must be tuple, like (123456789, );
        receiver: string with receiver wallet;
        memo: optional self-explanatory parameter.
    Out:
        returns TX ID or 'False' if TX failed.
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

    try:
        return resp["transaction_id"]
    except KeyError:
        logger.error(resp["error"]["details"][0]["message"])
        return False


def get_assets(wallet, collection, template, limit, sorting_key="template_mint"):
    """
    Make request to blockchain to get available assets with given template_id.
    wallet - is the collection wallet with alle the assets.
    Result is by default sorted by highest template mint.
    """
    payload = {
        "owner": wallet,
        "collection_name": collection,
        "template_id": template,
        "limit": limit,
        "sort": sorting_key,
    }
    response = requests.get(ENTRYPOINT_ASSETS, params=payload)
    return response.json()


def find_asset_with_highest_mint(wallet, template_id, quantity_requested: int = 1):
    # make a request to blockchain to get available assets with given template_id
    assets = get_assets(wallet, COLLECTION, template_id, quantity_requested)
    # check if enough assets are available in collection wallet
    quantity_available = len(assets["data"])
    if quantity_available < quantity_requested:
        logger.error(
            f"Not enough assets available.\n"
            f"you have: {quantity_available}\n"
            f"you need: {quantity_requested}"
        )
        # TO-DO here will come the logic to mint more assets.
        return
    # extract asset_ids from reply data
    asset_ids = [data["asset_id"] for data in assets["data"]]
    return asset_ids


def prepare_list_of_templates(asset_names):
    list_of_templates = [DICT[asset] for asset in asset_names]
    return list_of_templates