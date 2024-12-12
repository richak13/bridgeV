from web3 import Web3
from web3.middleware import geth_poa_middleware
import json
from pathlib import Path
import time

source_chain = 'avax'
destination_chain = 'bsc'
contract_info_file = "contract_info.json"
private_key = "69593227abfe0f42dea95240ad20f1173618585b38a326352e1076cd0642f157"
token_address = "0xc677c31AD31F73A5290f5ef067F8CEF8d301e45c"  # Replace if incorrect

# Connect to blockchain
def connectTo(chain):
    if chain == 'avax':
        api_url = "https://api.avax-test.network/ext/bc/C/rpc"  # AVAX C-chain testnet
    elif chain == 'bsc':
        api_url = "https://data-seed-prebsc-1-s1.binance.org:8545/"  # BSC testnet
    else:
        raise ValueError("Invalid chain name")

    w3 = Web3(Web3.HTTPProvider(api_url))
    w3.middleware_onion.inject(geth_poa_middleware, layer=0)
    if not w3.isConnected():
        raise ConnectionError(f"Failed to connect to {chain} chain")
    print(f"Connected to {chain} chain")
    return w3

# Load contract information
def getContractInfo(chain):
    p = Path(__file__).with_name(contract_info_file)
    with p.open('r') as f:
        contracts = json.load(f)
    return contracts[chain]

# Get contract instance
def get_contract(w3, address, abi):
    return w3.eth.contract(address=address, abi=abi)

def registerToken():
    try:
        # Connect to source chain
        w3_source = connectTo('avax')

        # Load contract info
        source_info = getContractInfo("source")
        source_contract = get_contract(w3_source, source_info['address'], source_info['abi'])

        # Warden address
        warden_address = w3_source.eth.account.from_key(private_key).address

        # Register token on source chain
        nonce = w3_source.eth.get_transaction_count(warden_address)
        tx_register = source_contract.functions.registerToken(token_address).build_transaction({
            "chainId": w3_source.eth.chain_id,
            "gas": 300000,
            "gasPrice": w3_source.toWei("10", "gwei"),
            "nonce": nonce,
        })
        signed_tx_register = w3_source.eth.account.sign_transaction(tx_register, private_key=private_key)
        tx_hash_register = w3_source.eth.send_raw_transaction(signed_tx_register.rawTransaction)
        print(f"RegisterToken Transaction Hash: {tx_hash_register.hex()}")
        receipt_register = w3_source.eth.wait_for_transaction_receipt(tx_hash_register)
        print(f"RegisterToken Transaction Receipt: {receipt_register}")

    except Exception as e:
        print(f"Error during registerToken: {e}")

def createToken():
    try:
        # Connect to destination chain
        w3_destination = connectTo('bsc')

        # Load contract info
        destination_info = getContractInfo("destination")
        destination_contract = get_contract(w3_destination, destination_info['address'], destination_info['abi'])

        # Warden address
        warden_address = w3_destination.eth.account.from_key(private_key).address

        # Create token on destination chain
        nonce = w3_destination.eth.get_transaction_count(warden_address)
        tx_create = destination_contract.functions.createToken(
            token_address, "WrappedToken", "WTKN"
        ).build_transaction({
            "chainId": w3_destination.eth.chain_id,
            "gas": 300000,
            "gasPrice": w3_destination.toWei("10", "gwei"),
            "nonce": nonce,
        })
        signed_tx_create = w3_destination.eth.account.sign_transaction(tx_create, private_key=private_key)
        tx_hash_create = w3_destination.eth.send_raw_transaction(signed_tx_create.rawTransaction)
        print(f"CreateToken Transaction Hash: {tx_hash_create.hex()}")
        receipt_create = w3_destination.eth.wait_for_transaction_receipt(tx_hash_create)
        print(f"CreateToken Transaction Receipt: {receipt_create}")

    except Exception as e:
        print(f"Error during createToken: {e}")

def scanBlocks(chain_name, other_chain_name):
    try:
        w3_source = connectTo(chain_name)
        w3_destination = connectTo(other_chain_name)

        source_info = getContractInfo("source")
        destination_info = getContractInfo("destination")

        source_contract = get_contract(w3_source, source_info['address'], source_info['abi'])
        destination_contract = get_contract(w3_destination, destination_info['address'], destination_info['abi'])

        warden_address = w3_source.eth.account.from_key(private_key).address

        while True:
            latest_block = w3_source.eth.block_number
            for block_num in range(latest_block - 5, latest_block + 1):
                block = w3_source.eth.get_block(block_num, full_transactions=True)
                for tx in block.transactions:
                    try:
                        receipt = w3_source.eth.get_transaction_receipt(tx.hash)
                        logs = source_contract.events.Deposit().process_receipt(receipt)

                        for event in logs:
                            token = event["args"]["token"]
                            recipient = event["args"]["recipient"]
                            amount = event["args"]["amount"]

                            nonce = w3_destination.eth.get_transaction_count(warden_address)
                            tx = destination_contract.functions.wrap(
                                token, recipient, amount
                            ).build_transaction({
                                "chainId": w3_destination.eth.chain_id,
                                "gas": 300000,
                                "gasPrice": w3_destination.toWei("10", "gwei"),
                                "nonce": nonce,
                            })

                            signed_tx = w3_destination.eth.account.sign_transaction(tx, private_key=private_key)
                            tx_hash = w3_destination.eth.send_raw_transaction(signed_tx.rawTransaction)
                            print(f"Wrap Transaction Hash: {tx_hash.hex()}")
                    except Exception as e:
                        print(f"Error processing transaction {tx.hash.hex()}: {e}")

            latest_block_dest = w3_destination.eth.block_number
            for block_num in range(latest_block_dest - 5, latest_block_dest + 1):
                block = w3_destination.eth.get_block(block_num, full_transactions=True)
                for tx in block.transactions:
                    try:
                        receipt = w3_destination.eth.get_transaction_receipt(tx.hash)
                        logs = destination_contract.events.Unwrap().process_receipt(receipt)

                        for event in logs:
                            wrapped_token = event["args"]["wrapped_token"]
                            recipient = event["args"]["to"]
                            amount = event["args"]["amount"]

                            nonce = w3_source.eth.get_transaction_count(warden_address)
                            tx = source_contract.functions.withdraw(
                                wrapped_token, recipient, amount
                            ).build_transaction({
                                "chainId": w3_source.eth.chain_id,
                                "gas": 300000,
                                "gasPrice": w3_source.toWei("10", "gwei"),
                                "nonce": nonce,
                            })

                            signed_tx = w3_source.eth.account.sign_transaction(tx, private_key=private_key)
                            tx_hash = w3_source.eth.send_raw_transaction(signed_tx.rawTransaction)
                            print(f"Withdraw Transaction Hash: {tx_hash.hex()}")
                    except Exception as e:
                        print(f"Error processing transaction {tx.hash.hex()}: {e}")

            time.sleep(10)
    except Exception as e:
        print(f"Error during block scanning: {e}")

if __name__ == "__main__":
    try:
        print("Calling registerToken...")
        registerToken()
        print("registerToken completed.")

        print("Calling createToken...")
        createToken()
        print("createToken completed.")

        print("Starting block scanning...")
        scanBlocks(source_chain, destination_chain)
    except Exception as e:
        print(f"An error occurred: {e}")
