#!/usr/bin/python3

import requests
import toml
import os
import re
from functools import partial
import flask

app = flask.Flask(__name__)


class Token:
    def __init__(self, name, symbol, address):
        self.name = name
        self.symbol = symbol
        self.address = address


class Network:
    def __init__(self, network_name, endpoint, api_key, coin_symbol, tokens):
        self.network_name = network_name
        self.endpoint = endpoint
        self.api_key = api_key
        self.coin_symbol = coin_symbol
        self.tokens = tokens

    def load_etherscan_config(self):
        config_file = "apis/ethereum/etherscan.toml"
        config = toml.load(config_file)
        return config

    def create_function_from_config(self, config):
        funcs = {}
        for key in config["api_calls"]:
            value = config["api_calls"][key]
            matches = re.findall(r"\${network\.(.*?)\}", value)
            for match in matches:
                value = value.replace(f"${{network.{match}}}", getattr(self, match))

            funcs[key] = self.create_function(value)
        return funcs

    def create_function(self, url):

        def f(url, *args, **kwargs):
            for key in kwargs:
                url = url.replace(f"$[{key}]", kwargs[key])

            matches = re.findall(r"\$.*?\]", url)
            if matches:
                print(f"Unresolved variables in url: {matches}")
            response = requests.get(url)
            return response.json()

        return partial(f, url)


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
                data["endpoint"],
                data["api_key"],
                data["coin_symbol"],
                tokens,
            )
        )


def main():
    # for network in NETWORKS:
    #     # for token in network.tokens:
    #     #     x = network.get_native_balance(token.address)
    #     addr = "0x9dd134d14d1e65f84b706d6f205cd5b1cd03a46b"
    #     import json

    #     z = network.load_etherscan_config()
    #     y = network.create_function_from_config(z)
    #     # r = y["get_balance"](addr)
    #     r = y["get_gas_price"]()

    #     nodes_count = y["get_nodes_count"]()

    #     print(json.dumps(r, indent=4))
    #     print(json.dumps(nodes_count, indent=4))

    app.run(port=5000)


@app.route("/docs", methods=["GET"])
def docs():
    return flask.jsonify(
        {
            "endpoints": {
                f"/{network.network_name}/{api_call}": f"{api_call}"
                for network in NETWORKS
                for api_call in network.create_function_from_config(
                    network.load_etherscan_config()
                )
            }
        }
    )


@app.route("/<network_name>/<api_call>")
def api_call(network_name, api_call):
    network = next((n for n in NETWORKS if n.network_name == network_name), None)
    if network is None:
        return "Network not found", 404

    config = network.load_etherscan_config()
    functions = network.create_function_from_config(config)
    if api_call not in functions:
        return "Api call not found", 404

    return functions[api_call](**flask.request.args)


if __name__ == "__main__":
    main()
