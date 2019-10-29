# ERC-20 <-> Waves Platform Gateway Framework
This framework allows to easily establish a gateway between any ERC-20 token and the
Waves Platform.
## Installation
Clone this repository and edit the config.json file according to your needs. Install the following dependencies:
```
web3
pywaves
flask
ethtoken
```
via pip and run the gateway by
```
python gateway.py
```
## Configuration of the config file
The config.json file includes all necessary settings that need to be connfigured in order to run a proper gateway:
```
{
    "erc20": {
        "name": "<name of the token>",
        "endpoint": "<http url of your node provider | empty if you want to connect to a local node via IPC>",
        "contract": {
            "address": "<contract address of your token that you want to establish the gateway for>",
            "decimals": <number of decimals of the token>
        },
        "fee": <the fee you want to collect on the gateway, calculated in your token, e.g., 0.1>,
        "confirmations": <number of confirmations necessary in order to accept a transaction>,
        "timeInBetweenChecks": <seconds in between a check for a new block>,
        "gatewayAddress": "<ETH address of the gateway>",
        "privateKey": "<private key to the ETH address definend above>"
    },
    "waves": {
        "gatewayAddress": "<Waves address of the gateway>",
        "gatewaySeed": "<seed of the above devined address>",
        "fee": <the fee you want to collect on the gateway, calculated in the proxy token, e.g., 0.1>,
        "assetId": "<the asset id of the proxy token on the Waves platform>",
        "decimals": <number of decimals of the token>,
        "network": "<Waves network you want to connect to (testnet|stagenent|mainnet)>",
        "node": "<the waves node you want to connect to>",
        "timeInBetweenChecks": <seconds in between a check for a new block>,
        "confirmations": <number of confirmations necessary in order to accept a transaction>
    }
}
```

## Running the gateway
After starting the gateway, it will provide a webpage on port 8080 on which tunnels can be established.

## Usage of the gateway
This is a simple gateway for ERC-20 tokens to the Waves Platform. It is based on tunnels. Users can define a tunnel between a source ETH address and a target Waves address. Whenever an ERC-20 token is send from the defined source ETH address to the gateway address, the corresponding amount of tokens are send to the defined Waves address on the Waves Platform. It is important to notice that tunnels will be removed after they are used. Therefore, if more than one transfer should be done via a tunnel, this tunnel needs to be re-established!

For sending tokens from the Waves Platform to the Ethereum blockchain, just add the ETH address that should receive the tokens as the description of the transfer and send the tokens to the Waves address of the gateway.

# Disclaimer
USE THIS FRAMEWORK AT YOUR OWN RISK!!! FULL RESPONSIBILITY FOR THE SECURITY AND RELIABILITY OF THE FUNDS TRANSFERRED IS WITH THE OWNER OF THE GATEWAY!!!