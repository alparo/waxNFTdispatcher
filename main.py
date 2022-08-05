from sendoutnft import  prepare_list_of_templates, \
    send_nfts_to_user, COLLECTION_WALLET

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

send_nfts_to_user(recipient, COLLECTION_WALLET, INPUT)