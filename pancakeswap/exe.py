import json
from web3 import Web3
import asyncio
import time
import os


web3 = Web3(Web3.HTTPProvider("https://bsc-dataseed.binance.org/"))

pancake_factory = '0xcA143Ce32Fe78f1f7019d7d551a6402fC5350c73'
pancake_router = '0x10ED43C718714eb63d5aA57B78B54704E256024E'

cwd = os.getcwd()

pair_file = open(cwd + "\\pair_abi.json", "r")
pair_abi = json.load(pair_file)
pair_file.close()
swap_file = open(cwd + "\\swap_abi.json", "r")
swap_abi = json.load(swap_file)
swap_file.close()


afile = open(cwd + "\\account.json", "r")
json_file = json.load(afile)
web3.eth.default_account = json_file["Account"]
private_key = json_file["Private_Key"]
desired_token = json_file["Token_ID"]
spend_limit = json_file["Spending_Limit"]
spend_option = json_file["Spending_Option"]
afile.close()

spend_count = 0
spend_count_total = 0

if spend_option == 1:
    spend_count_total = 1
elif spend_option == 2:
    spend_count_total = 5
elif spend_option == 3:
    spend_count_total = 10
else:
    print("Invalid spending option, defaulting to spend_option 1")
    spend_count_total = 1

pair_contract = web3.eth.contract(address=pancake_factory, abi=pair_abi)
swap_contract = web3.eth.contract(address=pancake_router, abi=swap_abi)


def handle_event(event, min, spend_count, spend_count_total):
    jso = json.loads(web3.toJSON(event))
    token_in = jso["args"]["token0"]
    token_out = jso["args"]["token1"]
    print(jso)
    if token_in == desired_token:
        
        txn = {
        'from': web3.eth.default_account,
        'value': web3.toWei(min, 'ether'),
        'gas': 650000,
        'gasPrice': web3.eth.gasPrice,
        'nonce': web3.eth.getTransactionCount(web3.eth.default_account)
        }

        amountoutmin = swap_contract.functions.getAmountsOut(int(min), [web3.toChecksumAddress(token_in), web3.toChecksumAddress(token_out)]).call()
        tx_hash = swap_contract.functions.swapExactTokensForTokens(int(min), int(amountoutmin[1] * 1e18), [web3.toChecksumAddress(token_in), web3.toChecksumAddress(token_out)], web3.eth.default_account, int(time.time() + 10 * 60)).buildTransaction(txn)
        signed_tx = web3.eth.account.sign_transaction(tx_hash, private_key=private_key)
        tx_hash = web3.eth.send_raw_transaction(signed_tx.rawTransaction)
        tx_reciept = web3.eth.wait_for_transaction_receipt(tx_hash)
        if tx_reciept["status"] == 1:
            print(tx_reciept["transactionHash"])
            spend_count += 1
            if spend_count == spend_count_total:
                quit()
        


async def log_loop(event_filter, poll_interval, amount_min, spend_count, spend_count_total):
    while True:
        for PairCreated in event_filter.get_new_entries():
            handle_event(PairCreated, amount_min, spend_count, spend_count_total)
        await asyncio.sleep(poll_interval)



def run():
    if spend_option == 1:
        amountin = int(spend_limit * 1e18)

        event_filter = pair_contract.events.PairCreated.createFilter(fromBlock="latest")
        loop = asyncio.get_event_loop()
        try:
            loop.run_until_complete(
                asyncio.gather(
                    log_loop(event_filter, 0.5, amountin, spend_count, spend_count_total)))           
        finally:
            loop.close()
    
    
    elif spend_option == 2:
        amountin = int(spend_limit * 1e18)

        event_filter = pair_contract.events.PairCreated.createFilter(fromBlock="latest")
        loop = asyncio.get_event_loop()
        try:
            loop.run_until_complete(
                asyncio.gather(
                    log_loop(event_filter, 0.5, int(amountin/5))))
        finally:
            loop.close()
    
    
    elif spend_option == 3:
        amountin = int(spend_limit * 1e18)

        event_filter = pair_contract.events.PairCreated.createFilter(fromBlock="latest")
        loop = asyncio.get_event_loop()
        try:
            loop.run_until_complete(
                asyncio.gather(
                    log_loop(event_filter, 0.5, int(amountin/10))))
        finally:
            loop.close()

if web3.eth.default_account == "" or private_key == "":
    print("Error: Go to account.json and make sure that your credentials are correct")
else:
    run()