import os
import eospyo
from loguru import logger

import requests

from collections import Counter

ENTRYPOINT = "https://test.wax.api.atomicassets.io/atomicassets/v1"
ENTRYPOINT_ASSETS = f"{ENTRYPOINT}/assets"
# KEY = os.environ["PRIVATE_KEY"]
# SENDER = "pixeltycoons"
COLLECTION_WALLET = "thisismyfirs"
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
            value=eospyo.types.Name(COLLECTION_WALLET),
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

    auth = eospyo.Authorization(actor=COLLECTION_WALLET, permission="active")

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


def get_available_assets(collection_wallet, collection, template, limit, sorting_key="template_mint"):
    """
    Make request to blockchain to get available assets with given template_id.
    collection_wallet - is the collection wallet with all the assets.
    Result is by default sorted by highest template mint.
    """
    payload = {
        "owner": collection_wallet,
        "collection_name": collection,
        "template_id": template,
        "limit": limit,
        "sort": sorting_key,
    }
    response = requests.get(ENTRYPOINT_ASSETS, params=payload)
    return response.json()


def find_asset_with_highest_mint(collection_wallet, template_id, quantity_requested: int = 1):
    """
    Finds in collection_wallet given quantity of assets with given template.
    :param collection_wallet:
    :param template_id:
    :param quantity_requested:
    :return: list of found asset IDs
    """
    # make a request to blockchain to get available assets with given template_id
    assets = get_available_assets(collection_wallet, COLLECTION, template_id, quantity_requested)
    # check if enough assets are available in collection wallet
    quantity_available = len(assets["data"])
    if quantity_available < quantity_requested:
        logger.error(
            f"Not enough assets available. Have: {quantity_available}; Need: {quantity_requested}"
        )
        # TO-DO here will come the logic to mint missing assets.
        return
    # extract asset_ids from reply data
    asset_ids = [data["asset_id"] for data in assets["data"]]
    return asset_ids


def prepare_list_of_templates(asset_names):
    """
    :param asset_names: list with asset names e.g. ["Grass Tuft", "Dried Leaf", "Dried Leaf", "Pinecone"]
    :return: class dict_items (list of tuples) with templates and their quantities.
             E.g. [(289228, 2), (289221, 1), (529844, 1)]
    """
    # Translate asset names into template IDs
    list_of_templates = []
    for asset in asset_names:
        try:
            list_of_templates.append(DICT[asset])
        except KeyError as err:
            logger.error(f"Asset name '{err}' is not in the dictionary and will not be sent.")
    # Count duplicates of template IDs and creates dictionary
    dict_with_counted_templates = Counter(list_of_templates)
    return dict_with_counted_templates.items()


def send_nfts_to_user(wallet: str, collection_wallet: str, asset_names: list):
    """
    :param collection_wallet: collection wallet with all the assets
    :param wallet: recipient wallet
    :param asset_names: list with asset names e.g. ["Grass Tuft", "Dried Leaf", "Dried Leaf", "Pinecone"]
    :return: TX ID or 'False' if TX failed.
    """
    templates = prepare_list_of_templates(asset_names)
    assets_to_send = []
    for template, quantity in templates:
        logger.info(f"Trying to send {quantity} asset(s) of template {template}")
        try:
            assets_to_send.extend(find_asset_with_highest_mint(COLLECTION_WALLET, template, quantity))
        except:
            logger.error(f"Can't send asset with template '{template}'")

    assets_to_send = None
    if assets_to_send:
        logger.error("not here")
        tx_return_status = send_assets_to_wallet(assets_to_send, wallet)
        if tx_return_status:
            logger.info(f"Successful: {tx_return_status}")
        else:
            logger.error(f"TX failed")
    pass
