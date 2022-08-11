from nft_hopper import Collection
import os

key = os.environ["PRIVATE_KEY"]
entrypoint = "https://test.wax.api.atomicassets.io/atomicassets/v1"
collection_wallet = "thisismyseco"
collection = "cxctestnet12"
INPUT = [
    "Dried Leaf",
]
#     "Big Flat Stone",
#     "Granite Stone",
#     "Grass Tuft",
#     "Dried Leaf",
# ]

recipient = "thisismyseco"

# send_assets_to_wallet(INPUT, recipient)

test_collection = Collection(collection, collection_wallet, key, entrypoint)
print(test_collection.get_available_assets([338280, 289221]))

