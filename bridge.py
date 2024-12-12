from web3 import Web3
from web3.middleware import geth_poa_middleware
import json
from pathlib import Path
import time

source_chain = 'avax'
destination_chain = 'bsc'
contract_info_file = "contract_info.json"

# Connect to blockchain

def connect_to_chain(chain):
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
    return w3

# Load contract information
def get_contract_info(chain):
    p = Path(__file__).with_name(contract_info_file)
    with p.open('r') as f:
        contracts = json.load(f)
    return contracts[chain]

# Get contract instance
def get_contract(w3, address, abi):
    return w3.eth.contract(address=address, abi=abi)

# Main scanning logic
def scan_blocks(chain_name, other_chain_name):
    w3_source = connect_to_chain(chain_name)
    w3_destination = connect_to_chain(other_chain_name)

    source_info = get_contract_info("source")
    destination_info = get_contract_info("destination")

    source_contract = get_contract(w3_source, source_info['address'], source_info['abi'])
    destination_contract = get_contract(w3_destination, destination_info['address'], destination_info['abi'])

    # Warden private key
    warden_private_key = "69593227abfe0f42dea95240ad20f1173618585b38a326352e1076cd0642f157"
    warden_address = w3_source.eth.account.from_key(warden_private_key).address

    while True:
        # Get the latest block
        latest_block = w3_source.eth.block_number

        # Scan the last 5 blocks
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

                        # Call wrap() on the destination chain
                        nonce = w3_destination.eth.get_transaction_count(warden_address)
                        tx = destination_contract.functions.wrap(
                            token, recipient, amount
                        ).build_transaction({
                            "chainId": w3_destination.eth.chain_id,
                            "gas": 300000,
                            "gasPrice": w3_destination.toWei("10", "gwei"),
                            "nonce": nonce,
                        })

                        signed_tx = w3_destination.eth.account.sign_transaction(tx, private_key=warden_private_key)
                        w3_destination.eth.send_raw_transaction(signed_tx.rawTransaction)
                        print(f"Called wrap() on destination chain for token {token} and recipient {recipient}")

                except Exception as e:
                    print(f"Error processing transaction {tx.hash.hex()}: {e}")

        # Repeat for Unwrap events on the destination chain
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

                        # Call withdraw() on the source chain
                        nonce = w3_source.eth.get_transaction_count(warden_address)
                        tx = source_contract.functions.withdraw(
                            wrapped_token, recipient, amount
                        ).build_transaction({
                            "chainId": w3_source.eth.chain_id,
                            "gas": 300000,
                            "gasPrice": w3_source.toWei("10", "gwei"),
                            "nonce": nonce,
                        })

                        signed_tx = w3_source.eth.account.sign_transaction(tx, private_key=warden_private_key)
                        w3_source.eth.send_raw_transaction(signed_tx.rawTransaction)
                        print(f"Called withdraw() on source chain for token {wrapped_token} and recipient {recipient}")

                except Exception as e:
                    print(f"Error processing transaction {tx.hash.hex()}: {e}")

        time.sleep(10)  # Delay to avoid spamming requests

if __name__ == "__main__":
    scan_blocks(source_chain, destination_chain)
