#!/usr/bin/python3

import toml
import os
import re
import flask
import functools
import requests
from dotenv import load_dotenv

app = flask.Flask(__name__)

apis_dir = "config/apis/"
networks_dir = "config/networks/"


class Token:
    def __init__(self, name, symbol, address):
        self.name = name
        self.symbol = symbol
        self.address = address


def load_config(config_file):
    config = toml.load(config_file)
    return config


def create_function(url, method):

    def f(url, *args, **kwargs):

        for key in kwargs:
            url = url.replace(f"$[{key}]", kwargs[key])

        headers = {
            "Content-Type": "application/json",
        }
        if method == "POST":
            matches = re.findall(r"<%.*?%>", url)
            for match in matches:
                url = url.replace(match, "")
            matches = [match[2:-2] for match in matches]
            kwargs = flask.json.loads([match for match in matches][0])

            response = requests.post(url, headers=headers, json=kwargs)
        else:
            print("url", url)
            response = requests.get(url)
        return response.json()

    return functools.partial(f, url, method)


def create_function_from_apis_config(network, config):
    funcs = {}
    for key in config["api_calls"]:
        value = config["api_calls"][key]
        matches = re.findall(r"\${network\.(.*?)\}", value)
        for match in matches:
            value = value.replace(
                f"${{network.{match}}}",
                network.get(match),
            )
        method = config["metadata"]["method"]

        funcs[key] = create_function(value, method)

    return funcs


@app.route("/<network_name>/<api_call>")
def api_call(network_name, api_call):

    load_dotenv()

    networks_config = load_config(f"{networks_dir}/{network_name}.toml")

    explorers = networks_config["explorers"]

    tokens = networks_config["tokens"]

    for explorer in explorers:
        explorer_config = load_config(f"{apis_dir}/{explorer['explorer_name']}.toml")

        network_config = {
            "explorer": explorer,
            "tokens": tokens,
            "api_calls": explorer_config["api_calls"],
            "api_key": os.getenv(explorer["api_key"]),
            "coin_symbol": explorer["coin_symbol"],
            "endpoint": explorer["endpoint"],
        }

        funcs = create_function_from_apis_config(network_config, explorer_config)
        if api_call in funcs:
            return funcs[api_call](**flask.request.args)
            # return funcs[api_call](**flask.request.args.to_dict())

    return flask.jsonify({"error": "API call not found"})


@app.route("/docs", methods=["GET"])
def docs():

    networks = os.listdir(networks_dir)
    networks = [
        flask.request.base_url + "/docs/" + network.split(".")[0]
        for network in networks
    ]

    return flask.jsonify(networks)


@app.route("/docs/<network_name>", methods=["GET"])
def docs_network(network_name):

    networks_config = load_config(f"{networks_dir}/{network_name}.toml")

    explorers = networks_config["explorers"]

    endpoints = []
    for explorer in explorers:
        explorer_config = load_config(f"{apis_dir}/{explorer['explorer_name']}.toml")
        for key in explorer_config["api_calls"]:
            params = re.findall(r"\$\[(.*?)\]", explorer_config["api_calls"][key])
            endpoints.append(
                {
                    "network": network_name,
                    "explorer": explorer["explorer_name"],
                    "api_call": key,
                    "url": explorer_config["api_calls"][key],
                    "params": params,
                }
            )

    return flask.jsonify(endpoints)


@app.route("/docs/<network_name>/<api_call>", methods=["GET"])
def docs_network_api_call(network_name, api_call):

    networks_config = load_config(f"{networks_dir}/{network_name}.toml")

    explorers = networks_config["explorers"]

    endpoints = []
    for explorer in explorers:
        explorer_config = load_config(f"{apis_dir}/{explorer['explorer_name']}.toml")
        if api_call in explorer_config["api_calls"]:
            params = re.findall(r"\$\[(.*?)\]", explorer_config["api_calls"][api_call])
            endpoints.append(
                {
                    "network": network_name,
                    "explorer": explorer["explorer_name"],
                    "api_call": api_call,
                    "url": explorer_config["api_calls"][api_call],
                    "params": params,
                }
            )

    return flask.jsonify(endpoints)


def main():
    print("Server started on port 5000")
    app.run(port=5000)
    

if __name__ == "__main__":
