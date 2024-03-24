#!/usr/bin/python3

import requests, toml, os, re, flask
from functools import partial
from dotenv import load_dotenv


app = flask.Flask(__name__)
NETWORKS = []

apis_dir = "config/apis/"
networks_dir = "config/networks/"


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

    def load_config(self, config_file):
        config = toml.load(config_file)
        return config

    def create_functions_from_apis_config(self, config):
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


"""
{
            "endpoints": {
                f"/{network.network_name}/{api_call}": f"{api_call}"
                for network in NETWORKS
                for api_call in network.create_functions_from_apis_config(
                    network.load_config(f"{apis_dir}/{network.network_name}.toml")
                )
            }
        }
        """


@app.route("/<network_name>/<api_call>")
def api_call(network_name, api_call):
    # init_networks()

    network = next((n for n in NETWORKS if n.network_name == network_name), None)
    if network is None or not os.path.exists(f"{networks_dir}/{network_name}.toml"):
        return "Network not found", 404

    explorers = os.listdir(apis_dir)

    for explorer in explorers:
        if not os.path.exists(f"{apis_dir}/{explorer}"):
            print("not exist")
            continue
        config = network.load_config(f"{apis_dir}/{explorer}")

    if api_call not in config["api_calls"].keys():
        return "Api call not found", 404

    functions = network.create_functions_from_apis_config(config)

    return functions[api_call](**flask.request.args)


@app.route("/docs", methods=["GET"])
def docs():

    endpoints = []
    for network in NETWORKS:
        explorers = os.listdir(apis_dir)
        print("Z")

        for explorer in explorers:
            if not os.path.exists(f"{apis_dir}/{explorer}"):
                print("not exist")
                continue
            config = network.load_config(f"{apis_dir}/{explorer}")
        for key in config["api_calls"]:
            endpoints.append(
                {
                    "network": network.network_name,
                    "explorer": explorer,
                    "api_call": key,
                    "url": config["api_calls"][key],
                }
            )

    return flask.jsonify(endpoints)


def init_networks():
    load_dotenv()

    for file in os.listdir(networks_dir):
        data = toml.load(f"{networks_dir}/{file}")
        tokens = []
        for token in data["tokens"]:
            tokens.append(Token(token["name"], token["symbol"], token["address"]))
        data["api_key"] = os.getenv(data["api_key"])
        NETWORKS.append(
            Network(
                data["network_name"],
                data["endpoint"],
                data["api_key"],
                data["coin_symbol"],
                tokens,
            )
        )


init_networks()


def main():
    # init_networks()
    app.run(port=5000)


if __name__ == "__main__":
    main()
