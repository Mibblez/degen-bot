# degen-bot 

### Telegram Cryptocurrency Bot

The purpose of this project is to provide information through telegram for cryptocurrencies.

# Setup

## Environment File

`.env` file contains the api keys to retrieve crytocurrency info and to connect to the telegram API.
This file is not included in the project. You will need to make it yourself.

- Telegram: https://core.telegram.org/api/obtaining_api_id
- CoinMarketCap: https://coinmarketcap.com/api/
- Etherscan: https://info.etherscan.com/api-keys/

Telegram users can obtain their user ID from this [bot](https://botostore.com/c/getmyid_bot/). This ID is used to designate admins.

### Sample .env

```.env
TELEGRAM_API_KEY = XXXXXX
COINMARKETCAP_API_KEY = XXXXXX
ETHERSCAN_API_KEY = XXXXXX

ADMIN_IDS = [1, 2, 3]
```

## Cryptocurrency JSON File

## Telegram Bot Setup

# General Commands

## New Cryptocurrency (Admin only)

Enters a new cryptocurrency into the bot. The contract ID this command requires can be found by visiting [CoinMarketCap](https://coinmarketcap.com/) and searching for the cryptocurrency. Once a cryptocurrency has been added to the bot, all commands that interact with cryptocurrencies will work (`/price`, `/price_notify`, etc.).

### Usage

```
/new_crypto CONTRACT_ID
```

## Update Cryptocurrency (Admin only)

Updates into for a cryptocurrency that is known to the bot.

### Usage

```
/update_crypto COIN_SYMBOL
```

## Price

Gets the price of the specified cryptocurrency and displays 24H price movement.

### Usage 

```
/price COIN_SYMBOL
```

### Example
```
/price BTC

BTC Price: $48,992.267342
⬇️ -6.23% (24H)
```

## Ethereum Gas

Gets the current gas price for Ethereum in gwei and shows the cost of a Uniswap transfer in USD.

### Usage

```
/ethgas
```

### Example
```
/ethgas

Uniswap Gas (152,000 gas limit)
Safe: 109 gwei ($68.0022)
Proposed: 110 gwei ($68.6261)
Fast: 112 gwei ($69.8738)
```

# Price Notification Commands

# Misc Commands

## wen

### Usage 

```

```

### Example

```
/wen
```

## List Commands

Gives a list of availble commands the user has access to.

### Usage

```
/list_commands
```

