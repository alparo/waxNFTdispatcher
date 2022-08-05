from sendoutnft import  prepare_list_of_templates, \
    send_assets_to_wallet, COLLECTION_WALLET

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

send_assets_to_wallet(INPUT, recipient)