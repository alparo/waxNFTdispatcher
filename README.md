# waxNFTDispatcher

This library will help you to transfer or to mint NFTs in the WAX blockchain. The library relies on the library 
pyntelope from FACINGS and on the module loguru for beautiful logs.


## Installation
```poetry add waxNFTDispatcher```

or

```pip install waxNFTDispatcher```

## Usage
```python
from waxNFTDispatcher import AssetSender
import os

private_key = os.environ["PRIVATE_KEY"]
collection_wallet = "mywallet.wam"
collection = "pixeltycoons"
recipient = "recipient.wam"
INPUT = (("rawmaterials", 318738), ("magmaterials", 416529))


assetsender = AssetSender(collection, collection_wallet, private_key)
assetsender.send_or_mint_assets_to_wallet(INPUT, recipient)
```

## Contribution
Contribution is highly welcome. Please send your pull requests or create issues with found bugs or suggestions.