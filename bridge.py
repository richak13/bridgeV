from web3 import Web3
from web3.contract import Contract
from web3.providers.rpc import HTTPProvider
from web3.middleware import geth_poa_middleware
import json
import sys
from pathlib import Path
import time

source_chain = 'avax'
destination_chain = 'bsc'
contract_info = "contract_info.json"

def connectTo(chain):
    # ... (Existing connectTo function)

def getContractInfo(chain):
    # ... (Existing getContractInfo function)

def register_token(source_w3, source_contract_address, token_address, private_key):
    with open('Source_contract_abi.json', 'r') as f:
        source_contract_abi = json.load(f)

    source_contract = source_w3.eth.contract(address=source_contract_address, abi=source_contract_abi)
    nonce = source_w3.eth.getTransactionCount(source_w3.eth.defaultAccount)
    try:
        tx = source_contract.functions.registerToken(token_address).buildTransaction({
            'gas': 2000000,
            'gasPrice': source_w3.eth.gasPrice,
            'nonce': nonce,
        })
        signed_tx = source_w3.eth.account.signTransaction(tx, private_key)
        tx_hash = source_w3.eth.sendRawTransaction(signed_tx.rawTransaction)
        tx_receipt = source_w3.eth.wait_for_transaction_receipt(tx_hash)
        if tx_receipt['status']==1:
            print("Token registered on source chain.")
        else:
            print("Token registration on source chain failed.")
            print(tx_receipt)
    except Exception as e:
        print(f"Error registering token on source chain: {e}")
        return False
    return True

def create_token(destination_w3, destination_contract_address, token_address, private_key):
    with open('Destination_contract_abi.json', 'r') as f:
        destination_contract_abi = json.load(f)

    destination_contract = destination_w3.eth.contract(address=destination_contract_address, abi=destination_contract_abi)
    nonce = destination_w3.eth.getTransactionCount(destination_w3.eth.defaultAccount)
    try:
        tx = destination_contract.functions.createToken(token_address).buildTransaction({
            'gas': 2000000,
            'gasPrice': destination_w3.eth.gasPrice,
            'nonce': nonce,
        })
        signed_tx = destination_w3.eth.account.signTransaction(tx, private_key)
        tx_hash = destination_w3.eth.sendRawTransaction(signed_tx.rawTransaction)
        tx_receipt = destination_w3.eth.wait_for_transaction_receipt(tx_hash)
        if tx_receipt['status']==1:
            print("Token created on destination chain.")
        else:
            print("Token creation on destination chain failed.")
            print(tx_receipt)
    except Exception as e:
        print(f"Error creating token on destination chain: {e}")
        return False
    return True

def scanBlocks(chain):
    # ... (Existing scanBlocks function)

if __name__ == "__main__":
    source_w3 = connectTo(source_chain)
    destination_w3 = connectTo(destination_chain)

    source_contract_info = getContractInfo(source_chain)
    destination_contract_info = getContractInfo(destination_chain)
    
    with open('contract_info.json', 'r') as f:
        contract_data = json.load(f)
    private_key = contract_data['private_key']
    source_w3.eth.defaultAccount = source_w3.eth.account.from_key(private_key).address
    destination_w3.eth.defaultAccount = destination_w3.eth.account.from_key(private_key).address

    token_address = "0x380A72Da9b73bf597d7f840D21635CEE26aa3dCf"

    if register_token(source_w3, source_contract_info['address'], token_address, private_key):
        time.sleep(10) #wait for confirmation on the chain
        if create_token(destination_w3, destination_contract_info['address'], token_address, private_key):
            #Only scan if both are successful
            scanBlocks('source')
            scanBlocks('destination')
        else:
            print("destination token creation failed")
    else:
        print("source token registration failed")
