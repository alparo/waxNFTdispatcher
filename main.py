from nft_hopper import send_assets_to_wallet, send_mint_transaction

INPUT = [
    "Grass Tuft",
    "Dried Leaf",
    "Dried Leaf",
    "Pinecone",]
#     "Big Flat Stone",
#     "Granite Stone",
#     "Grass Tuft",
#     "Dried Leaf",
# ]

recipient = "thisismyseco"

#send_assets_to_wallet(INPUT, recipient)
send_mint_transaction("thisismyfirs", "cxctestnet12", "123", "338280", "thisismyseco")
