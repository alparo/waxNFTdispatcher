import eospyo
from loguru import logger
import requests
from collections import Counter

logger.add("sendoutnft.log", format="{time} {level} {message}", retention="1 week")


class Collection:
    def __init__(
        self,
        collection: str,
        collection_wallet: str,
        private_key: str,
        api_entrypoint: str,
    ):
        """
        Constructor
        :param collection: Collection which assets are going to be transferred or minted
        :param collection_wallet: wallet which holds the assets
        :param private_key: private key from the collection_wallet
        :param api_entrypoint: API URL address
        """
        self.collection = collection
        self.collection_wallet = collection_wallet
        self.private_key = private_key
        self.entrypoint_assets = f"{api_entrypoint}/assets"

    def get_available_assets(
        self,
        schema_template_list: list,
        sorting_key: str = "asset_id",
    ):
        """
        Make request to blockchain to get available assets in collection wallet with given template IDs
        :param schema_template_list: list of (schema, template) tuples.
                E.g. [("rawmaterials", 318738), ("magmaterials", 416529)]
        :param sorting_key: self-explanatory, default "asset_id"
        :return: API response with all found assets sorted by default by the highest asset ID
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
        response = requests.get(self.entrypoint_assets, params=payload)
        return response.json()

    @staticmethod
    def collapse_identical_schemas_templates(schema_template_list: list):
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
    def find_assets_with_highest_mints(
        api_response, template_id: str, quantity_requested: int = 1
    ):
        """
        Finds in collection wallet given quantity of assets with given template
        :param api_response: data received from blockchain
        :param template_id: self-explanatory. Only one template ID per function run
        :param quantity_requested: how many assets with given template ID must be found
        :return: list of found asset IDs
        """
        # extract asset_ids from reply data
        asset_ids = []
        asset_number = 0
        quantity_to_mint = 0
        while len(asset_ids) < quantity_requested:
            try:
                if (
                    api_response["data"][asset_number]["template"]["template_id"]
                    == template_id
                ):
                    asset_ids.append(api_response["data"][asset_number]["asset_id"])
                    logger.info(
                        f"found asset with ID {api_response['data'][asset_number]['asset_id']}"
                    )
                asset_number += 1
            except IndexError:
                quantity_available = len(asset_ids)
                logger.warning(
                    f"Not enough assets available. Have: {quantity_available}; Need: {quantity_requested}"
                )
                quantity_to_mint = quantity_requested - quantity_available
                break
        return asset_ids, quantity_to_mint

    def prepare_transfer_transaction(
        self, asset_ids: list, to: str, from_wallet: str, memo: str = ""
    ):
        """
        Sends given assets from SENDER wallet to given recipient wallet
        :param asset_ids: must be list, like [123456789, ]
        :param to: string with recipient wallet
        :param from_wallet: collection wallet
        :param memo: optional self-explanatory parameter
        :return: TX ID or 'False' if TX failed.
        """
        logger.info("Creating Transaction...")
        data = [
            eospyo.Data(
                name="from",
                value=eospyo.types.Name(from_wallet),
            ),
            eospyo.Data(
                name="to",
                value=eospyo.types.Name(to),
            ),
            eospyo.Data(
                name="asset_ids",
                value=eospyo.types.Array(values=asset_ids, type_=eospyo.types.Uint64),
            ),
            eospyo.Data(
                name="memo",
                value=eospyo.types.String(memo),
            ),
        ]
        auth = eospyo.Authorization(actor=self.collection_wallet, permission="active")
        action = eospyo.Action(
            account="atomicassets",  # this is the contract account
            name="transfer",  # this is the action name
            data=data,
            authorization=[auth],
        )
        return action

    def prepare_mint_transaction(
        self,
        authorized_minter: str,
        collection_name: str,
        schema_name: str,
        template_id: str,
        new_asset_owner: str,
        immutable_data: list = [],
        mutable_data: list = [],
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
        :return: TX ID or 'False' if TX failed.
        """
        logger.info("Creating Transaction...")
        data = [
            eospyo.Data(
                name="authorized_minter",
                value=eospyo.types.Name(authorized_minter),
            ),
            eospyo.Data(
                name="collection_name",
                value=eospyo.types.Name(collection_name),
            ),
            eospyo.Data(
                name="schema_name",
                value=eospyo.types.Name(schema_name),
            ),
            eospyo.Data(
                name="template_id",
                value=eospyo.types.Uint32(template_id),
            ),
            eospyo.Data(
                name="new_asset_owner",
                value=eospyo.types.Name(new_asset_owner),
            ),
            eospyo.Data(
                name="immutable_data",
                value=eospyo.types.Array(
                    values=immutable_data, type_=eospyo.types.Array
                ),
            ),
            eospyo.Data(
                name="mutable_data",
                value=eospyo.types.Array(values=mutable_data, type_=eospyo.types.Array),
            ),
            eospyo.Data(
                name="tokens_to_back",
                value=eospyo.types.Asset(tokens_to_back),
            ),
        ]
        auth = eospyo.Authorization(actor=self.collection_wallet, permission="active")
        action = eospyo.Action(
            account="atomicassets",  # this is the contract account
            name="mintasset",  # this is the action name
            data=data,
            authorization=[auth],
        )
        return action

    def send_transaction(self, action):
        raw_transaction = eospyo.Transaction(actions=[action])
        logger.debug("Linking transaction to the network...")
        net = eospyo.WaxTestnet()  # this is an alias for a testnet node
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
        pass

    def send_or_mint_assets_to_wallet(
        self,
        schema_template_list: list,
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
        schemas_templates_quantities = self.collapse_identical_schemas_templates(
            schema_template_list
        )
        logger.info(
            f"*** Requested to send {schemas_templates_quantities} to wallet '{wallet}'"
        )
        # make a request to blockchain to get available assets with given template_ids
        if schema_template_list:
            api_response = self.get_available_assets(schema_template_list)
        else:
            logger.error("Schema-template list is empty")
            return

        assets_to_send = []
        for schema_template, quantity in schemas_templates_quantities:
            schema = schema_template[0]
            template = str(schema_template[1])
            logger.info(
                f"Searching in stock for {quantity} asset(s) with template '{template}'"
            )
            found_assets, need_to_mint = self.find_assets_with_highest_mints(
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
                    minting_tx = self.send_transaction(
                        self.prepare_mint_transaction(
                            self.collection_wallet,
                            self.collection,
                            schema,
                            template,
                            wallet,
                        )
                    )
                    if minting_tx:
                        minted_quantity += 1
                        logger.info(f"Successfully minted: {minting_tx}")
                    else:
                        logger.critical(
                            f"Failed to mint asset with schema, template '{schema_template}'. Manual intervention is needed!"
                        )
                        break

        if assets_to_send:
            logger.info(
                f"Going to send following assets: {assets_to_send} to the wallet '{wallet}'"
            )
            tx_return_status = self.send_transaction(
                self.prepare_transfer_transaction(
                    assets_to_send, wallet, self.collection_wallet, memo
                )
            )
            if tx_return_status:
                logger.info(f"Successfully sent: {tx_return_status}")
            else:
                logger.error(f"TX failed")
            return tx_return_status
