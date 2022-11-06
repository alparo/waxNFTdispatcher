from waxNFTdispatcher import AssetSender
import os

# Example usage
private_key = os.environ["PRIVATE_KEY"]
collection_wallet = "thisismyfirs"
collection = "cxctestnet12"
recipient = "thisismyseco"
INPUT = (("123", 338280), ("123", 338280), ("123", 338280))
#INPUT = (("gen1pokemon1", 54), )


test_assetsender = AssetSender(collection, collection_wallet, private_key, testnet=True)
test_assetsender.send_or_mint_assets_to_wallet(INPUT, recipient)
