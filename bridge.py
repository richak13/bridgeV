from web3 import Web3
from web3.contract import Contract
from web3.providers.rpc import HTTPProvider
from web3.middleware import geth_poa_middleware #Necessary for POA chains
import json
import sys
from pathlib import Path

source_chain = 'avax'
destination_chain = 'bsc'
contract_info = "contract_info.json"

def connectTo(chain):
    if chain == 'avax':
        api_url = f"https://api.avax-test.network/ext/bc/C/rpc" #AVAX C-chain testnet

    if chain == 'bsc':
        api_url = f"https://data-seed-prebsc-1-s1.binance.org:8545/" #BSC testnet

    if chain in ['avax','bsc']:
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
        with p.open('r')  as f:
            contracts = json.load(f)
    except Exception as e:
        print( "Failed to read contract info" )
        print( "Please contact your instructor" )
        print( e )
        sys.exit(1)

    return contracts[chain]



def scanBlocks(chain):
    """
        chain - (string) should be either "source" or "destination"
        Scan the last 5 blocks of the source and destination chains
        Look for 'Deposit' events on the source chain and 'Unwrap' events on the destination chain
        When Deposit events are found on the source chain, call the 'wrap' function the destination chain
        When Unwrap events are found on the destination chain, call the 'withdraw' function on the source chain
    """

    if chain not in ['source','destination']:
        print( f"Invalid chain: {chain}" )
        return
        
    if chain == 'source':
        api_url = f"https://api.avax-test.network/ext/bc/C/rpc" #AVAX C-chain testnet
        with open("contract_info.json", "r") as f:
            d = json.load(f)
            d1 = d['source']
            address1 = '0x9c3Cc0EC58Ee8114F35e7dB98F95f6a5d0DA59be'
            abi1 = d1['abi']
            d2 = d['destination']
            address2 = '0x32de83CB410a7A1ABaB8cA6DdE381C220D051688'
            abi2 = d2['abi']

        url1 = "https://api.avax-test.network/ext/bc/C/rpc"
        url2 = "https://data-seed-prebsc-1-s1.binance.org:8545/"
        w3_1 = Web3(HTTPProvider(url1))
        w3_2 = Web3(HTTPProvider(url2))
        
        w3_1.middleware_onion.inject(geth_poa_middleware, layer=0)
        w3_2.middleware_onion.inject(geth_poa_middleware, layer=0)

        if w3_1.is_connected():
            print("Connected to Avax Testnet")
        else:
            print("Connection failed")
        contract1 = w3_1.eth.contract(address=address1, abi=abi1)
        contract2 = w3_2.eth.contract(address=address2, abi=abi2)

        start_block1 = w3_1.eth.get_block_number()
        end_block1 = start_block1 - 5

        start_block2 = w3_2.eth.get_block_number()
        end_block2 = start_block2 - 5
        print("Source")
        print("Start Block 1 = " + str(start_block1))
        print("End Block 1 = " + str(end_block1))
        print("Start Block2 = " + str(start_block2))
        print("End Block2 = " + str(end_block2))
        arg_filter = {}
        print("Destination contract address: " + address2)
        print("Source contract address: "+address1)
        print("LISTENING FOR DEPOSITS ON SOURCE CONTRACT AT BLOCKS " + str(end_block1) + " to " + str(start_block1))
        event_filter1 = contract1.events.Deposit.create_filter(fromBlock=end_block1, toBlock=start_block1, argument_filters=arg_filter)
        events1 = event_filter1.get_all_entries()
        print(str(len(events1)) + " Deposit events found on source contract")

        event_filter2 = contract2.events.Unwrap.create_filter(fromBlock=end_block2, toBlock=start_block2, argument_filters=arg_filter)
        events2 = event_filter2.get_all_entries()
        sk = '69593227abfe0f42dea95240ad20f1173618585b38a326352e1076cd0642f157'  # "YOUR SECRET KEY HERE"


        acct = w3_2.eth.account.from_key(sk)
        print("DESTINATION AND SOURCE CONTRACTS DEPLOYED FROM "+acct.address)
        if len(events1)>0:

            for event in events1:
                print("CALLING WRAP ON DESTINATION CONTRACT")
                event_dict = {'chain': chain,
                              'token': event['args']['token'],
                              'recipient': event['args']['recipient'],
                              'amount': event['args']['amount'],
                              'transactionHash': event['transactionHash'],
                              'address': event['address']}
                tx_raw = contract2.functions.wrap(event_dict['token'], event_dict['recipient'],
                                                  event_dict['amount']).build_transaction({

                    "from": acct.address,
                    "nonce": w3_2.eth.get_transaction_count(acct.address)

                })
                print("RAW WRAP TRANSACTION:")
                print(tx_raw)
                signed_tx = w3_2.eth.account.sign_transaction(tx_raw, private_key=acct.key)
                print("SIGNED WRAP TRANSACTION:")
                print(signed_tx)
                tx_hash = w3_2.eth.send_raw_transaction(signed_tx.rawTransaction)
                print("WRAP TX HASH:")
                print(type(tx_hash))
                print(tx_hash.hex())
                print("TOKEN:")
                print(event_dict['token'])

    if chain == 'destination':
        api_url = f"https://api.avax-test.network/ext/bc/C/rpc" #AVAX
        with open("contract_info.json", "r") as f:
            d = json.load(f)
            d2 = d['source']
            address2 = '0x32de83CB410a7A1ABaB8cA6DdE381C220D051688'
            abi2 = d2['abi']
            d1 = d['destination']
            address1 = '0x9c3Cc0EC58Ee8114F35e7dB98F95f6a5d0DA59be'
            abi1 = d1['abi']


        url2 = "https://api.avax-test.network/ext/bc/C/rpc"
        url1 = "https://data-seed-prebsc-1-s1.binance.org:8545/"
        w3_2 = Web3(HTTPProvider(url2))
        w3_1 = Web3(HTTPProvider(url1))
        
        w3_1.middleware_onion.inject(geth_poa_middleware, layer=0)
        w3_2.middleware_onion.inject(geth_poa_middleware, layer=0)

        if w3_1.is_connected():
            print("Connected to BSC Testnet")
        else:
            print("Connection failed")
        contract1 = w3_1.eth.contract(address=address1, abi=abi1)
        contract2 = w3_2.eth.contract(address=address2, abi=abi2)

        start_block1 = w3_1.eth.get_block_number()
        end_block1 = start_block1 - 5
        start_block2 = w3_2.eth.get_block_number()
        end_block2 = start_block2 - 5

        print("Destination")
        print("Start Block 1 = " + str(start_block1))
        print("End Block 1 = " + str(end_block1))
        print("Start Block2 = " + str(start_block2))
        print("End Block2 = " + str(end_block2))

        arg_filter = {}
        print("Listening for unwraps on blocks " + str(end_block1) + " to " + str(start_block1))
        event_filter1 = contract1.events.Unwrap.create_filter(fromBlock=end_block1, toBlock=start_block1, argument_filters=arg_filter)
        events1 = event_filter1.get_all_entries()
        print(str(len(events1))+" Unwrap events found on destination contract")

        event_filter2 = contract2.events.Deposit.create_filter(fromBlock=end_block2, toBlock=start_block2, argument_filters=arg_filter)
        events2 = event_filter2.get_all_entries()
        print(str(len(events2))+" Deposit events found on source contract")

        sk = '69593227abfe0f42dea95240ad20f1173618585b38a326352e1076cd0642f157'  # "YOUR SECRET KEY HERE"

        acct = w3_2.eth.account.from_key(sk)
        if len(events1)>0:
            for event in events1:
                print("Unwrap event from destination contract")
                print(event)
                event_dict = {'chain': chain,
                              'token': event['args']['underlying_token'],
                              'recipient': event['args']['to'],
                              'amount': event['args']['amount'],
                              'transactionHash': event['transactionHash'],
                              'address': event['address']}
                tx_raw = contract2.functions.withdraw(event_dict['token'], event_dict['recipient'],
                                                  event_dict['amount']).build_transaction({

                    "from": acct.address,
                    "nonce": w3_2.eth.get_transaction_count(acct.address),

                })
                print('withdrawn token is:')
                print(event_dict['token'])

                signed_tx = w3_2.eth.account.sign_transaction(tx_raw, private_key=sk)
                tx_hash = w3_2.eth.send_raw_transaction(signed_tx.rawTransaction)

scanBlocks('source')
