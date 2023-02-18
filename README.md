# waxNFTdispatcher

This library will help you to transfer or to mint NFTs on the WAX blockchain. It relies on the library 
pyntelope for blockchain interaction and on the library loguru for beautiful logs.

By default, the [EOSUSA](https://eosusa.io/) WAX API is used to post transactions to blockchain.
It can be changed while creating an object.
Due to some limitations only EOSUSA API can be used to get transaction info from blockchain.


## Installation
```poetry add waxNFTdispatcher```

or

```pip install waxNFTdispatcher```

## Usage

```python
from waxNFTdispatcher import AssetSender
import os

private_key = os.environ["PRIVATE_KEY"]
collection_wallet = "mywallet.wam"
collection = "pixeltycoons"
recipient = "recipient.wam"
INPUT = (("rawmaterials", "318738"), ("magmaterials", "416529"))

# Create object
assetsender = AssetSender(collection, collection_wallet, private_key)

# Try to find assets in the collection wallet to send them.
# If not all needed assets were in the collection wallet, the script will mint the rest.
assetsender.send_or_mint_assets(INPUT, recipient)

# Send assets with given asset ID to the given wallet
assetsender.send_assets(("1099543811405", "1099543811406"), recipient)

# Mint given number of same assets
assetsender.mint_assets("rawmaterials", "318738", "recipient.wam", 5)

# Mint given number of same assets and then try to fetch their IDs
assetsender.mint_assets_and_get_ids("rawmaterials", "318738", "recipient.wam", 5)
```

The methods return tuple or list of tuples where on the first place is the asset ID or id-schema-template tuple, and 
on the second place either hash of successful transaction or 'False' if transaction failed for some reason. For example:

```
[(('1099511811820', 'rawmaterials', '318738'), False),
(('1099511811819',), '6b80b145aa261736941583ed17802a8be0254cd21a78b6bb415c923ec64ad32c')]
```

## Contribution
Contribution is highly welcome. Please send your pull requests or create issues with found bugs and suggestions. 
In your pull requests please use Black formatting.
