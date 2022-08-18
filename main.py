from nft_hopper import AssetSender
import os

# Example usage
private_key = os.environ["PRIVATE_KEY"]
entrypoint = "https://wax.api.atomicassets.io/atomicassets/v1"
collection_wallet = "thisismyfirs"
collection = "cxctestnet12"
recipient = "thisismyseco"
INPUT = [("123", 338280), ("123", 338280)]


test_assetsender = AssetSender(collection, collection_wallet, private_key, entrypoint)
test_assetsender.send_or_mint_assets_to_wallet(INPUT, recipient)
