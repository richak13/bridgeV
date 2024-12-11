from web3 import Web3
import json
import sys
import time

source_chain = 'avax'
destination_chain = 'bsc'
contract_info = "contract_info.json"

def connectTo(chain):
    """
    Connect to the Avalanche or BNB chain testnet
    """
    if chain == 'avax':
        api_url = f"https://api.avax-test.network/ext/bc/C/rpc"  # AVAX C-chain testnet

    if chain == 'bsc':
        api_url = f"https://data-seed-prebsc-1-s1.binance.org:8545/"  # BSC testnet

    if chain in ['avax', 'bsc']:
        w3 = Web3(Web3.HTTPProvider(api_url))
        if not w3.isConnected():
            print(f"Failed to connect to {chain} chain")
            sys.exit(1)
        return w3

def getContractInfo(chain):
    """
    Load the contract_info file into a dictionary
    """
    try:
        with open(contract_info, 'r') as f:
            contracts = json.load(f)
    except Exception as e:
        print(f"Error reading contract_info.json: {e}")
        sys.exit(1)

    return contracts[chain]

def registerSourceToken():
    w3 = connectTo("avax")
    contract_info = getContractInfo("source")
    source_contract = w3.eth.contract(address=contract_info["address"], abi=contract_info["abi"])

    source_token_address = "0xc677c31AD31F73A5290f5ef067F8CEF8d301e45c"
    txn = source_contract.functions.registerToken(source_token_address).buildTransaction({
        'from': w3.eth.defaultAccount,
        'gas': 2000000,
        'gasPrice': w3.toWei('5', 'gwei'),
        'nonce': w3.eth.getTransactionCount(w3.eth.defaultAccount),
    })

    signed_txn = w3.eth.account.signTransaction(txn, private_key="your_private_key")
    tx_hash = w3.eth.sendRawTransaction(signed_txn.rawTransaction)
    print(f"Registered token {source_token_address} on source chain, tx hash: {tx_hash.hex()}")
    w3.eth.waitForTransactionReceipt(tx_hash)
    print("Token registration confirmed on source chain")

def registerDestinationToken():
    w3 = connectTo("bsc")
    contract_info = getContractInfo("destination")
    destination_contract = w3.eth.contract(address=contract_info["address"], abi=contract_info["abi"])

    destination_token_address = "0xc677c31AD31F73A5290f5ef067F8CEF8d301e45c" 
    txn = destination_contract.functions.createToken(destination_token_address, "WrappedToken", "WT").buildTransaction({
        'from': w3.eth.defaultAccount,
        'gas': 2000000,
        'gasPrice': w3.toWei('5', 'gwei'),
        'nonce': w3.eth.getTransactionCount(w3.eth.defaultAccount),
    })

    signed_txn = w3.eth.account.signTransaction(txn, private_key="your_private_key")
    tx_hash = w3.eth.sendRawTransaction(signed_txn.rawTransaction)
    print(f"Created token {destination_token_address} on destination chain, tx hash: {tx_hash.hex()}")
    w3.eth.waitForTransactionReceipt(tx_hash)
    print("Token creation confirmed on destination chain")

# Main function: Register tokens and listen for events
if __name__ == "__main__":
    print("Registering tokens...")
    registerSourceToken()  # Register tokens on source chain
    registerDestinationToken()  # Register tokens on destination chain

    while True:
        print("Scanning source chain for Deposit events...")
        scanBlocks("source")  # Listen for Deposit events on the source chain
        
        print("Scanning destination chain for Unwrap events...")
        scanBlocks("destination")  # Listen for Unwrap events on the destination chain

        # Wait a bit before scanning again to avoid hitting rate limits
        time.sleep(10)
