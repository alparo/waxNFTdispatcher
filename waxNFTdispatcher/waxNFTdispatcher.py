import time
from typing import Iterable, Tuple
import pyntelope
from loguru import logger
import requests
from collections import Counter

ATOMICASSETS_MAIN_API = "https://wax.api.atomicassets.io/atomicassets/v1"
ATOMICASSETS_TEST_API = "https://test.wax.api.atomicassets.io/atomicassets/v1"
TIMEOUT = 0


class AssetSender:
    def __init__(
        self,
        collection: str,
        collection_wallet: str,
        private_key: str,
        api_endpoint: str = '',
        testnet: bool = False,
    ):
        """
        Constructor
        :param collection: Collection which assets are going to be transferred or minted
        :param collection_wallet: wallet which holds the assets
        :param private_key: private key from the collection_wallet
        :param api_endpoint: API URL address
        :param testnet: if True, will interact with Wax Test Net through Test endpoint.
        """
        self.collection = collection
        self.collection_wallet = collection_wallet
        self.private_key = private_key
        self.testnet = testnet
        # Set the default API endpoint
        if self.testnet and not api_endpoint:
            api_endpoint = ATOMICASSETS_TEST_API
        elif not self.testnet and not api_endpoint:
            api_endpoint = ATOMICASSETS_MAIN_API
        self.endpoint_assets = f"{api_endpoint}/assets"

    def _get_available_assets(
        self,
        schema_template_list: Iterable[Tuple[str, int]],
        sorting_key: str = "asset_id",
    ) -> list:
        """
        Make request to blockchain to get available assets in collection wallet with given template IDs
        :param schema_template_list: list or tuple of (schema, template) tuples.
                E.g. [("rawmaterials", 318738), ("magmaterials", 416529)]
        :param sorting_key: self-explanatory, default "asset_id"
        :return: list with all found assets (with other info from API) sorted by default by the highest asset ID
        """
        # Build comma separated string of templates
        template_list_string = ",".join(
            str(template[1]) for template in schema_template_list
        )
        logger.info(
            f"Making request to blockchain to find in the collection wallet "
            f"following templates: {template_list_string}"
        )
        payload = {
            "owner": self.collection_wallet,
            "template_whitelist": template_list_string,
            "sort": sorting_key,
        }
        response = requests.get(self.endpoint_assets, params=payload)
        return response.json()["data"]

    @staticmethod
    def _collapse_identical_schemas_templates(
        schema_template_list: Iterable[Tuple[str, int]]
    ):
        """
        :param schema_template_list: list with (schema, template) tuples.
                E.g. [("rawmaterials", 318738), ("magmaterials", 416529)]
        :return: class dict_items (list of tuples) with schemas-templates and their quantities.
                 E.g. dict_items([(("rawmaterials", 318738), 2), (("magmaterials", 416529), 1)])
        """
        # Count duplicates of tuples with schema and template and create dictionary
        dict_with_counted_schemas_templates = Counter(schema_template_list)
        return dict_with_counted_schemas_templates.items()

    @staticmethod
    def _find_assets_with_highest_mints(
        api_response, template_id: str, quantity_requested: int = 1
    ):
        """
        Finds in collection wallet given quantity of assets with given template
        :param api_response: list with found assets received from blockchain
        :param template_id: self-explanatory. Only one template ID per function run
        :param quantity_requested: how many assets with given template ID must be found
        :return: list of found asset IDs, quantity needed to mint if any.
        """
        # extract asset_ids from reply data
        asset_ids = []
        asset_number = 0
        quantity_to_mint = 0
        while len(asset_ids) < quantity_requested:
            try:
                asset_data = api_response[asset_number]
                if asset_data["template"]["template_id"] == template_id:
                    asset_ids.append(asset_data["asset_id"])
                    logger.info(f'found asset with ID {asset_data["asset_id"]}')
                asset_number += 1
            except IndexError:
                quantity_available = len(asset_ids)
                logger.warning(
                    f"Not enough assets available. Have: {quantity_available}; Need: {quantity_requested}"
                )
                quantity_to_mint = quantity_requested - quantity_available
                break
        return asset_ids, quantity_to_mint

    def _prepare_transfer_transaction(
        self, asset_ids: list, to: str, from_wallet: str, memo: str = ""
    ):
        """
        Sends given assets from SENDER wallet to given recipient wallet
        :param asset_ids: must be list, like [123456789, ]
        :param to: string with recipient wallet
        :param from_wallet: collection wallet
        :param memo: optional self-explanatory parameter
        :return: Ready Action object.
        """
        logger.info("Creating Transaction...")
        data = [
            pyntelope.Data(
                name="from",
                value=pyntelope.types.Name(from_wallet),
            ),
            pyntelope.Data(
                name="to",
                value=pyntelope.types.Name(to),
            ),
            pyntelope.Data(
                name="asset_ids",
                value=pyntelope.types.Array(values=asset_ids, type_=pyntelope.types.Uint64),
            ),
            pyntelope.Data(
                name="memo",
                value=pyntelope.types.String(memo),
            ),
        ]
        auth = pyntelope.Authorization(actor=self.collection_wallet, permission="active")
        action = pyntelope.Action(
            account="atomicassets",  # this is the contract account
            name="transfer",  # this is the action name
            data=data,
            authorization=[auth],
        )
        return action

    def _prepare_mint_transaction(
        self,
        authorized_minter: str,
        collection_name: str,
        schema_name: str,
        template_id: str,
        new_asset_owner: str,
        immutable_data: list = None,
        mutable_data: list = None,
        tokens_to_back: str = "0.00000000 WAX",
    ):
        """
        :param authorized_minter: wallet with authorisation to mint collection assets
        :param collection_name: self-explanatory
        :param schema_name: self-explanatory
        :param template_id: self-explanatory
        :param new_asset_owner: the recipient wallet
        :param immutable_data: better to leave it unfilled
        :param mutable_data: better to leave it unfilled
        :param tokens_to_back: amount of tokens with token symbol. Like that "0.00000000 WAX".
                Always 8 digits after period and one space before the token symbol.
        :return: Ready Action object.
        """
        # workaround for passing mutable default argument
        if immutable_data is None:
            immutable_data = []
        if mutable_data is None:
            mutable_data = []

        logger.info("Creating Transaction...")
        data = [
            pyntelope.Data(
                name="authorized_minter",
                value=pyntelope.types.Name(authorized_minter),
            ),
            pyntelope.Data(
                name="collection_name",
                value=pyntelope.types.Name(collection_name),
            ),
            pyntelope.Data(
                name="schema_name",
                value=pyntelope.types.Name(schema_name),
            ),
            pyntelope.Data(
                name="template_id",
                value=pyntelope.types.Uint32(template_id),
            ),
            pyntelope.Data(
                name="new_asset_owner",
                value=pyntelope.types.Name(new_asset_owner),
            ),
            pyntelope.Data(
                name="immutable_data",
                value=pyntelope.types.Array(
                    values=immutable_data, type_=pyntelope.types.Array
                ),
            ),
            pyntelope.Data(
                name="mutable_data",
                value=pyntelope.types.Array(values=mutable_data, type_=pyntelope.types.Array),
            ),
            pyntelope.Data(
                name="tokens_to_back",
                value=pyntelope.types.Asset(tokens_to_back),
            ),
        ]
        auth = pyntelope.Authorization(actor=self.collection_wallet, permission="active")
        action = pyntelope.Action(
            account="atomicassets",     # this is the contract account
            name="mintasset",           # this is the action name
            data=data,
            authorization=[auth],
        )
        return action

    def _send_transaction(self, action):
        """
        Sends transaction into blockchain.
        :param action: Action object.
        :return: TX ID or 'False' if TX failed.
        """
        raw_transaction = pyntelope.Transaction(actions=[action])
        logger.debug("Linking transaction to the network...")
        if self.testnet:
            net = pyntelope.WaxTestnet()  # this is an alias for WAX testnet node
        else:
            net = pyntelope.WaxMainnet()  # this is an alias for WAX mainnet node
        linked_transaction = raw_transaction.link(net=net)
        logger.debug("Signing transaction...")
        signed_transaction = linked_transaction.sign(key=self.private_key)
        logger.debug("Sending transaction to the blockchain...")
        resp = signed_transaction.send()
        try:
            return resp["transaction_id"]
        except KeyError:
            logger.error(resp["error"]["details"][0]["message"])
            return False

    def send_or_mint_assets_to_wallet(
        self,
        schema_template_list: Iterable[Tuple[str, int]],
        wallet: str,
        memo: str = "",
    ):
        """
        :param schema_template_list: list of tuples containing schema names and template IDs
         e.g. [("rawmaterials", 318738), ("magmaterials", 416529)]
        :param wallet: recipient wallet
        :param memo: transaction memo
        :return: TX ID or 'False' if TX failed.
        """
        if not schema_template_list:
            logger.error("Schema-template list is empty!")
            raise ValueError("Schema-template can't be empty!")
        if not wallet:
            logger.error("Wallet is empty!")
            raise ValueError("The wallet can't be empty!")

        schemas_templates_quantities = self._collapse_identical_schemas_templates(
            schema_template_list
        )
        logger.info(
            f"*** Requested to send {schemas_templates_quantities} to the wallet '{wallet}'"
        )
        # Make a request to blockchain to get available assets with given template_ids
        api_response = self._get_available_assets(schema_template_list)

        assets_to_send = []
        successful_tx = []
        for schema_template, quantity in schemas_templates_quantities:
            schema = schema_template[0]
            template = str(schema_template[1])
            logger.info(
                f"Searching in stock for {quantity} asset(s) with template '{template}'"
            )
            found_assets, need_to_mint = self._find_assets_with_highest_mints(
                api_response, template, quantity
            )
            if found_assets:
                assets_to_send.extend(found_assets)
            if need_to_mint > 0:
                logger.info(
                    f"Going to mint {need_to_mint} assets with template '{template}' to the wallet '{wallet}'"
                )
                minted_quantity = 0
                while minted_quantity < need_to_mint:
                    minting_tx = self._send_transaction(
                        self._prepare_mint_transaction(
                            self.collection_wallet,
                            self.collection,
                            schema,
                            template,
                            wallet,
                        )
                    )
                    if minting_tx:
                        minted_quantity += 1
                        successful_tx.append(minting_tx)
                        logger.info(f"Successfully minted: {minting_tx}")
                    else:
                        logger.critical(
                            f"Failed to mint asset with schema, template '{schema_template}'. "
                            f"Manual intervention is needed! "
                        )
                        break
                    # Sleep in order to get rig of "duplicate transaction" error
                    time.sleep(TIMEOUT)

        if assets_to_send:
            logger.info(
                f"Going to send following assets: {assets_to_send} to the wallet '{wallet}'"
            )
            tx_return_status = self._send_transaction(
                self._prepare_transfer_transaction(
                    assets_to_send, wallet, self.collection_wallet, memo
                )
            )
            if tx_return_status:
                successful_tx.append(tx_return_status)
                logger.info(f"Successfully sent: {tx_return_status}")
            else:
                logger.critical(
                    f"Failed to send assets: {assets_to_send} to the wallet '{wallet}'!"
                )
        return successful_tx

    def send_assets_to_wallet(
        self,
        asset_id: Iterable[str],
        wallet: str,
        memo: str = "",
    ):
        pass

    def mint_assets_to_wallet(
        self,
        schema_template_list: Iterable[Tuple[str, int]],
        wallet: str,
        memo: str = "",
    ):
        pass