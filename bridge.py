from web3 import Web3
from web3.contract import Contract
from web3.providers.rpc import HTTPProvider
from web3.middleware import geth_poa_middleware  # Necessary for POA chains
import json
import sys
from pathlib import Path

source_chain = 'avax'
destination_chain = 'bsc'
contract_info = "contract_info.json"

def connectTo(chain):
    if chain == 'avax':
        api_url = f"https://api.avax-test.network/ext/bc/C/rpc"  # AVAX C-chain testnet

    if chain == 'bsc':
        api_url = f"https://data-seed-prebsc-1-s1.binance.org:8545/"  # BSC testnet

    if chain in ['avax', 'bsc']:
        w3 = Web3(Web3.HTTPProvider(api_url))
        # inject the poa compatibility middleware to the innermost layer
        w3.middleware_onion.inject(geth_poa_middleware, layer=0)
        return w3

def getContractInfo(chain):
    """
        Load the contract_info file into a dictinary
        This function is used by the autograder and will likely be useful to you
    """
    p = Path(__file__).with_name(contract_info)
    try:
        with p.open('r') as f:
            contracts = json.load(f)
    except Exception as e:
        print("Failed to read contract info")
        print("Please contact your instructor")
        print(e)
        sys.exit(1)

    return contracts[chain]

def register_token(source_w3, source_contract_address, token_address):
    """
        Register the token on the source contract.
    """
    with open('Source_contract_abi.json', 'r') as f:
        source_contract_abi = json.load(f)

    source_contract = Contract(
        address=source_contract_address,
        abi=source_contract_abi,
        w3=source_w3
    )

    # Register the token on the source contract
    tx_hash = source_contract.functions.registerToken(token_address).transact()
    source_w3.eth.wait_for_transaction_receipt(tx_hash)

def create_token(destination_w3, destination_contract_address, token_address):
    """
        Create the token on the destination contract.
    """
    with open('Destination_contract_abi.json', 'r') as f:
        destination_contract_abi = json.load(f)

    destination_contract = Contract(
        address=destination_contract_address,
        abi=destination_contract_abi,
        w3=destination_w3
    )

    # Create the token on the destination contract
    tx_hash = destination_contract.functions.createToken(token_address).transact()
    destination_w3.eth.wait_for_transaction_receipt(tx_hash)

def scanBlocks(chain):
    """
        chain - (string) should be either "source" or "destination"
        Scan the last 5 blocks of the source and destination chains
        Look for 'Deposit' events on the source chain and 'Unwrap' events on the destination chain
        When Deposit events are found on the source chain, call the 'wrap' function the destination chain
        When Unwrap events are found on the destination chain, call the 'withdraw' function on the source chain
    """

    if chain not in ['source', 'destination']:
        print(f"Invalid chain: {chain}")
        return

    # YOUR CODE HERE 

if __name__ == "__main__":
    # Connect to both chains
    source_w3 = connectTo(source_chain)
    destination_w3 = connectTo(destination_chain)

    # Get contract information
    source_contract_info = getContractInfo(source_chain)
    destination_contract_info = getContractInfo(destination_chain)

    # Register/Create the token on both chains
    token_address = "0xc677c31AD31F73A5290f5ef067F8CEF8d301e45c"  # Replace with your actual token address
    register_token(source_w3, source_contract_info['address'], token_address)
    create_token(destination_w3, destination_contract_info['address'], token_address)

    # Scan blocks for events
    scanBlocks('source')
    scanBlocks('destination')
