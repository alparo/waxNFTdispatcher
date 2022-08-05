import os
import eospyo
from loguru import logger

import requests

from collections import Counter

ENTRYPOINT = "https://test.wax.api.atomicassets.io/atomicassets/v1"
ENTRYPOINT_ASSETS = f"{ENTRYPOINT}/assets"
KEY = os.environ["PRIVATE_KEY"]
SENDER = "pixeltycoons"
COLLECTION_WALLET = "thisismyfirs"
COLLECTION = "gen1pokemon1"
logger.add("sendoutnft.log", format="{time} {level} {message}", retention="1 week")

DICT = {
    # "Grass Tuft": "289228",
    "Grass Tuft": "64",
    # "Dried Leaf": "265138",
    "Dried Leaf": "42",
    "Pinecone": "289221",
    "Big Flat Stone": "529844",
    "Granite Stone": "265148",
}


def send_blockchain_transaction(assets: list, recipient: str, memo: str = ""):
    """
    Sends given assets from SENDER wallet to given recipient wallet
    :param assets: must be list, like [123456789, ]
    :param recipient: string with receiver wallet
    :param memo: optional self-explanatory parameter
    :return: TX ID or 'False' if TX failed.
    """
    logger.info("Creating Transaction...")
    data = [
        eospyo.Data(
            name="from",
            value=eospyo.types.Name(COLLECTION_WALLET),
        ),
        eospyo.Data(
            name="to",
            value=eospyo.types.Name(recipient),
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
    logger.info("Linking transaction to the network...")
    net = eospyo.WaxTestnet()  # this is an alias for a testnet node
    # notice that eospyo returns a new object instead of change in place
    linked_transaction = raw_transaction.link(net=net)
    logger.info("Signing transaction...")
    signed_transaction = linked_transaction.sign(key=KEY)
    logger.info("Sending transaction to the blockchain...")
    resp = signed_transaction.send()
    try:
        return resp["transaction_id"]
    except KeyError:
        logger.error(resp["error"]["details"][0]["message"])
        return False


def get_available_assets(
    collection_wallet: str,
    collection: str,
    template_list: list,
    sorting_key: str = "asset_id",
):
    """
    Make request to blockchain to get available assets with given template IDs
    :param collection_wallet: collection wallet which owns the assets
    :param collection: self-explanatory
    :param template_list: list with templates to search
    :param sorting_key: self-explanatory, default "asset_id"
    :return: API response with all found assets sorted by default by highest asset ID
    """
    # convert list to comma separated string
    template_list_string = ",".join(str(template) for template in template_list)
    payload = {
        "owner": collection_wallet,
        "collection_name": collection,
        "template_whitelist": template_list_string,
        "sort": sorting_key,
    }
    response = requests.get(ENTRYPOINT_ASSETS, params=payload)
    return response.json()


def find_assets_with_highest_mints(
    api_response, template_id: str, quantity_requested: int = 1
):
    """
    Finds in collection_wallet given quantity of assets with given template
    :param api_response: data received from blockchain
    :param template_id: only one template ID per function run
    :param quantity_requested: how many assets with given template ID must be found
    :return: list of found asset IDs
    """
    # extract asset_ids from reply data
    asset_ids = []
    asset_number = 0
    while len(asset_ids) < quantity_requested:
        try:
            if (
                api_response["data"][asset_number]["template"]["template_id"]
                == template_id
            ):
                asset_ids.append(api_response["data"][asset_number]["asset_id"])
                logger.info(
                    f"found asset with ID {api_response['data'][asset_number]['asset_id']}"
                )
            asset_number += 1
        except IndexError:
            logger.error(
                f"Not enough assets available. Have: {len(asset_ids)}; Need: {quantity_requested}"
            )
            # TO-DO here will come the logic to mint missing assets.
            break
    return asset_ids


def prepare_list_of_templates(asset_names: list):
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
            logger.error(
                f"Asset name '{err}' is not in the dictionary and will not be sent."
            )
    # Count duplicates of template IDs and create dictionary
    dict_with_counted_templates = Counter(list_of_templates)
    return dict_with_counted_templates.items()


def send_assets_to_wallet(
    asset_names: list,
    wallet: str,
    collection_wallet: str = COLLECTION_WALLET,
    memo: str = "",
):
    """
    :param wallet: recipient wallet
    :param collection_wallet: collection wallet with all the assets
    :param asset_names: list with asset names e.g. ["Grass Tuft", "Dried Leaf", "Dried Leaf", "Pinecone"]
    :param memo: transaction memo
    :return: TX ID or 'False' if TX failed.
    """
    templates_and_quantities = prepare_list_of_templates(asset_names)
    logger.info(f"*** Requested to send {templates_and_quantities}")
    # Convert dict into list with templates
    template_list = [template[0] for template in templates_and_quantities]

    # make a request to blockchain to get available assets with given template_ids
    if template_list:
        api_response = get_available_assets(
            collection_wallet, COLLECTION, template_list
        )
    else:
        logger.error("Template list is empty")
        return

    assets_to_send = []
    for template, quantity in templates_and_quantities:
        logger.info(
            f"Searching in stock for {quantity} asset(s) with template {template}"
        )
        assets_to_send.extend(
            find_assets_with_highest_mints(api_response, template, quantity)
        )

    # assets_to_send = None
    if assets_to_send:
        logger.info(
            f"Going to send following assets:{assets_to_send} to the wallet '{wallet}'"
        )
        tx_return_status = send_blockchain_transaction(assets_to_send, wallet, memo)
        if tx_return_status:
            logger.info(f"Successful: {tx_return_status}")
        else:
            logger.error(f"TX failed")
        return tx_return_status


def mint_asset(authorized_minter, collection_name, schema_name, template_id, new_asset_owner):
    """

    :param authorized_minter:
    :param collection_name:
    :param schema_name:
    :param template_id:
    :param new_asset_owner:
    :return: TX ID or 'False' if TX failed.
    """
    logger.info("Creating Transaction...")
    data = [
        eospyo.Data(
            name="authorized_minter",
            value=eospyo.types.Name(authorized_minter),
        ),
        eospyo.Data(
            name="collection_name",
            value=eospyo.types.Name(collection_name),
        ),
        eospyo.Data(
            name="schema_name",
            value=eospyo.types.Name(schema_name),
        ),
        eospyo.Data(
            name="template_id",
            value=eospyo.types.Uint32(template_id),
        ),
        eospyo.Data(
            name="new_asset_owner",
            value=eospyo.types.Name(new_asset_owner),
        ),
    ]
    auth = eospyo.Authorization(actor=COLLECTION_WALLET, permission="active")
    action = eospyo.Action(
        account="atomicassets",  # this is the contract account
        name="mintasset",  # this is the action name
        data=data,
        authorization=[auth],
    )
    raw_transaction = eospyo.Transaction(actions=[action])
    logger.info("Linking transaction to the network...")
    net = eospyo.WaxTestnet()  # this is an alias for a testnet node
    # notice that eospyo returns a new object instead of change in place
    linked_transaction = raw_transaction.link(net=net)
    logger.info("Signing transaction...")
    signed_transaction = linked_transaction.sign(key=KEY)
    logger.info("Sending transaction to the blockchain...")
    resp = signed_transaction.send()
    try:
        return resp["transaction_id"]
    except KeyError:
        logger.error(resp["error"]["details"][0]["message"])
        return False
    pass