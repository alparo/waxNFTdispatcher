from sendoutnft import find_asset_with_highest_mint, send_assets_to_wallet, SENDER, prepare_list_of_templates
from loguru import logger

INPUT = [
    "Grass Tuft",
    "Dried Leaf",
    "Dried Leaf",
    "Pinecone",
    "Big Flat Stone",
    "Granite Stone",
    "Grass Tuft",
    "Dried Leaf",
]


print(prepare_list_of_templates(INPUT))

template_id1 = "54"
assets_to_send = None
#assets_to_send = find_asset_with_highest_mint(SENDER, template_id1, 2)
if assets_to_send:
    tx_return_status = send_assets_to_wallet(assets_to_send, "thisismyseco")
    if tx_return_status:
        logger.info(f"Successful: {tx_return_status}")
    else:
        logger.error(f"TX failed")