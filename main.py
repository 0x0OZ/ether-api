#!/usr/bin/python3

import requests
import dotenv
import toml
import os

dotenv.load_dotenv()


class Token:
    def __init__(self, name, symbol, address):
        self.name = name
        self.symbol = symbol
        self.address = address


class Network:
    def __init__(self, network_name, api_endpoint, api_key, coin_symbol, tokens):
        self.network_name = network_name
        self.api_endpoint = api_endpoint
        self.api_key = api_key
        self.coin_symbol = coin_symbol
        self.tokens = tokens

    def handle_response(self, response, network_name):
        if response.status_code != 200:
            raise Exception(f"Error: {response.status_code}")
        data = response.json()
        if data["status"] != "1":
            raise Exception(f"Error: {data['message']}")
        return data["result"]

    def get_block_number(self):
        url = f"{self.api_endpoint}?module=proxy&action=eth_blockNumber&apikey={self.api_key}"
        return self.handle_response(requests.get(url), self.network_name)

    def get_native_balance(self, address):
        url = f"{self.api_endpoint}?module=account&action=balance&address={address}&tag=latest&apikey={self.api_key}"
        print(url)
        return self.handle_response(requests.get(url), self.network_name)

    def get_token_balance(self, address, token_address):
        url = f"{self.api_endpoint}?module=account&action=tokenbalance&contractaddress={token_address}&address={address}&tag=latest&apikey={self.api_key}"
        return self.handle_response(requests.get(url), self.network_name)

    def get_tokens_balance(self, address):
        balances = {}
        for token in self.tokens:
            balances[token.symbol] = self.get_token_balance(address, token.address)
        return balances

    def get_native_balance_multi(self, addresses):
        url = f"{self.api_endpoint}?module=account&action=balancemulti&address={','.join(addresses)}&tag=latest&apikey={self.api_key}"
        return self.handle_response(requests.get(url), self.network_name)

    def get_normal_transactions(self, address, startblock=0, endblock=-1):
        endblock = endblock if endblock != -1 else self.get_block_number()

        url = f"{self.api_endpoint}?module=account&action=txlist&address={address}&startblock={startblock}&endblock={endblock}&sort=asc&apikey={self.api_key}"
        transactions = []

        while True:
            response = self.handle_response(requests.get(url), self.network_name)
            transactions.extend(response)
            if len(response) < 10000:
                break
            url = f"{self.api_endpoint}?module=account&action=txlist&address={address}&startblock={startblock}&endblock={endblock}&sort=asc&apikey={self.api_key}&offset={len(transactions)}"
        return transactions

    def get_internal_transactions(self, address, startblock=0, endblock=-1):
        endblock = endblock if endblock != -1 else self.get_block_number()
        # This API endpoint returns a maximum of 10000 records only. So we need to handle pagination
        url = f"{self.api_endpoint}?module=account&action=txlistinternal&address={address}&startblock={startblock}&endblock={endblock}&sort=asc&apikey={self.api_key}"
        transactions = []

        while True:
            response = self.handle_response(requests.get(url), self.network_name)
            transactions.extend(response)
            if len(response) < 10000:
                break
            url = f"{self.api_endpoint}?module=account&action=txlistinternal&address={address}&startblock={startblock}&endblock={endblock}&sort=asc&apikey={self.api_key}&offset={len(transactions)}"

        return transactions

    def get_internal_transactions_by_hash(self, txhash):
        # This API endpoint returns a maximum of 10000 records only. So we need to handle pagination
        url = f"{self.api_endpoint}?module=account&action=txlistinternal&txhash={txhash}&apikey={self.api_key}"
        transactions = []

        while True:
            response = self.handle_response(requests.get(url), self.network_name)
            transactions.extend(response)
            if len(response) < 10000:
                break
            url = f"{self.api_endpoint}?module=account&action=txlistinternal&txhash={txhash}&apikey={self.api_key}&offset={len(transactions)}"
        return transactions

    def get_internal_transactions_by_blockhash(self, blockhash):
        # This API endpoint returns a maximum of 10000 records only. So we need to handle pagination
        url = f"{self.api_endpoint}?module=account&action=txlistinternal&blockhash={blockhash}&apikey={self.api_key}"
        transactions = []

        while True:
            response = self.handle_response(requests.get(url), self.network_name)
            transactions.extend(response)
            if len(response) < 10000:
                break
            url = f"{self.api_endpoint}?module=account&action=txlistinternal&blockhash={blockhash}&apikey={self.api_key}&offset={len(transactions)}"
        return transactions

    def get_internal_transactions_by_block_range(self, startblock=0, endblock=-1):
        endblock = endblock if endblock != -1 else self.get_block_number()
        url = f"{self.api_endpoint}?module=account&action=txlistinternal&startblock={startblock}&endblock={endblock}&apikey={self.api_key}"
        return self.handle_response(requests.get(url), self.network_name)

    def get_erc20_transfers_by_event(
        self, address, startblock=0, endblock=-1, topic0=None
    ):
        endblock = endblock if endblock != -1 else self.get_block_number()
        url = f"{self.api_endpoint}?module=logs&action=getLogs&fromBlock={startblock}&toBlock={endblock}&address={address}&topic0={topic0}&apikey={self.api_key}"
        return self.handle_response(requests.get(url), self.network_name)


NETWORKS = []


for file in os.listdir("networks"):
    if file.endswith(".toml"):
        data = toml.load(f"networks/{file}")
        tokens = []
        for token in data["tokens"]:
            tokens.append(Token(token["name"], token["symbol"], token["address"]))
        NETWORKS.append(
            Network(
                data["network_name"],
                data["api_endpoint"],
                data["api_key"],
                data["coin_symbol"],
                tokens,
            )
        )


def main():
    print(NETWORKS)
    for network in NETWORKS:
        # for token in network.tokens:
        #     x = network.get_native_balance(token.address)
        addr = "0xCBB379347e5ABbfd2dAdB1C20A95d58275805C91"

        z = network.get_internal_transactions(addr, 0, 99999999)
        import json

        # print(json.dumps(z, indent=4))
        x = network.get_internal_transactions_by_hash(z[0]["hash"])

        print(json.dumps(x, indent=4))


if __name__ == "__main__":
    main()
