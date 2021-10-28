import os
from dotenv import load_dotenv
import telebot
import json
import random
import time
import re

import datetime
from requests import Session
from requests.exceptions import ConnectionError, Timeout, TooManyRedirects
import pprint as pp

from threading import Thread

load_dotenv()
TELEGRAM_API_KEY = os.getenv('TELEGRAM_API_KEY')
CMC_API_KEY = os.getenv('COINMARKETCAP_API_KEY')
ETHERSCAN_API_KEY = os.getenv('ETHERSCAN_API_KEY')

bot = telebot.TeleBot(TELEGRAM_API_KEY)

json_file = open('cryptos.json')
cryptos_json = json.load(json_file)


@bot.message_handler(commands=['coins'])
def coins(message):
    bot.reply_to(message, 'Known coins:\n' + ' ; '.join([x for x in cryptos_json.keys()]))


def usage_error(message, usage_str: str = ''):
    bot.send_message(message.chat.id, f'Usage\n{usage_str}')


def unknown_coin(message, invalid_coin_str):
    bot.send_message(message.chat.id,
                     f"Unknown coin: {invalid_coin_str}\n\nKnown coins: {' ; '.join([x for x in cryptos_json.keys()])}")


@bot.message_handler(commands=['info'])
def info(message):
    request = message.text.split()[1] if len(message.text.split()) == 2 else ''

    # Too many or too few args
    if request == '':
        usage_error(message, '/info COIN_NAME')
        return

    # Given a coin name thats not in the JSON file
    if request not in cryptos_json:
        unknown_coin(message, request)
        return

    response = ''

    requested_crypto_info = cryptos_json[request]["INFO"]

    for k, v in requested_crypto_info.items():
        response += f'{k} : {v}\n'

    if 'chain' in requested_crypto_info:
        if requested_crypto_info['chain'] == 'BSC':
            response += f"BSC Scan: https://www.bscscan.com/address/{requested_crypto_info['contract_id']}\n"
            response += f"Dextools: https://www.dextools.io/app/{requested_crypto_info['chain'].lower()}" +\
                f"/pair-explorer/{requested_crypto_info['contract_id']}"
        else:
            response += f"CMC: https://coinmarketcap.com/currencies/{cryptos_json[request]['cmc_name']}/"

    bot.send_message(message.chat.id, response)


@bot.message_handler(commands=['dextools'])
def dextools(message):
    request = message.text.split()[1] if len(message.text.split()) == 2 else ''

    if request == '':
        bot.send_message(message.chat.id, 'https://www.dextools.io/app/')
        return

    if request in cryptos_json:
        bot.send_message(message.chat.id, 'wip')


@bot.message_handler(commands=['wen', 'WEN'])
def wen(message):
    request = (message.text.split()[1] if len(message.text.split()) == 2 else '').lower()

    if request == '':
        return

    if request == 'lambo':
        lambo_models = ['https://www.lamborghini.com/en-en/models/aventador/aventador-svj',
                        'https://www.lamborghini.com/en-en/models/aventador/aventador-svj-roadster',
                        'https://www.lamborghini.com/en-en/models/aventador/aventador-lp-780-4-ultimae',
                        'https://www.lamborghini.com/en-en/models/aventador/aventador-lp-780-4-ultimae-roadster',
                        'https://www.lamborghini.com/en-en/models/huracan/huracan-evo',
                        'https://www.lamborghini.com/en-en/models/huracan/huracan-evo-spyder',
                        'https://www.lamborghini.com/en-en/models/huracan/huracan-evo-rwd',
                        'https://www.lamborghini.com/en-en/models/huracan/huracan-evo-rwd-spyder',
                        'https://www.lamborghini.com/en-en/models/huracan/huracan-evo-fluo-capsule',
                        'https://www.lamborghini.com/en-en/models/huracan/huracan-sto',
                        'https://ezgo.txtsv.com/personal/golfcarts/freedom-rxv'
                        ]

        # Reply with a link to a random lambo model from the lambo_models list
        bot.reply_to(message, lambo_models[random.randrange(len(lambo_models))])
    elif request == 'moon':
        replies = ['Ask Musk Daddy\n\nhttps://twitter.com/elonmusk',
                   'Soon',
                   'HODL',
                   'Ask Rob',
                   'WEN MOON?']

        # Reply with something stupid from the replies list
        bot.reply_to(message, replies[random.randrange(len(replies))])
        if os.path.exists('media/wen_moon.ogg'):
            bot.send_audio(message.chat.id, audio=open('media/wen_moon.ogg', 'rb'))
    elif request == 'aston':
        aston_models = ['https://www.astonmartin.com/en-us/models/aston-martin-valkyrie',
                        'https://www.astonmartin.com/en-us/models/dbx',
                        'https://www.astonmartin.com/en-us/models/new-vantage',
                        'https://www.astonmartin.com/en-us/models/db11',
                        'https://www.astonmartin.com/en-us/models/dbs-superleggera']
        bot.reply_to(message, aston_models[random.randrange(len(aston_models))])


@bot.message_handler(commands=['price'])
def price(message):
    request = message.text.split()[1] if len(message.text.split()) == 2 else ''

    # Too many or too few args
    if request == '':
        usage_error(message, '/price COIN_NAME')
        return

    # Given a coin name thats not in the JSON file
    if request not in cryptos_json:
        unknown_coin(message, request)
        return

    coin_id = cryptos_json[request]["cmc_id"]
    coin_data = get_latest_price(request, coin_id)

    if coin_data is None:
        bot.send_message(message.chat.id, "Could not get the latest price. Try again later.")
        return

    latest_price = "{:.10f}".format(
        coin_data['data'][coin_id]['quote']['USD']['price'])

    percent_change_24h = float("{:.2f}".format(
        coin_data['data'][coin_id]['quote']['USD']['percent_change_24h']))

    movement_direction = '⬆️' if percent_change_24h > 0.0 else '⬇️'

    bot.send_message(message.chat.id, f"{request} Price: ${latest_price}\n" +
                     f"{movement_direction} {percent_change_24h}% (24H)")


def get_latest_price(coin_name, coin_id):
    url = 'https://pro-api.coinmarketcap.com/v1/cryptocurrency/quotes/latest'
    headers = {
        'Accepts': 'application/json',
        'X-CMC_PRO_API_KEY': CMC_API_KEY,
    }

    parameters = {
        'id': coin_id
    }

    session = Session()
    session.headers.update(headers)

    try:
        response = session.get(url, params=parameters)
        data = json.loads(response.text)
        return data
    except (ConnectionError, Timeout, TooManyRedirects) as e:
        data = json.loads(response.text)
        pp.pprint(data)
        print(e)
        return None


# TODO: implement me https://etherscan.io/apidocs https://etherscan.io/apidocs#gastracker
# Show in USD https://etherscan.io/apidocs#stats
# Different things with cubcommands(normal transaction, uniswap, erc20, etc)
@bot.message_handler(commands=['ethgas'])
def ethgas(message):
    gas_url = 'https://api.etherscan.io/api'
    gas_parameters = {
        'module': 'gastracker',
        'action': 'gasoracle',
        'apikey': ETHERSCAN_API_KEY
    }

    stats_url = 'https://api.etherscan.io/api'
    stats_parameters = {
        'module': 'stats',
        'action': 'ethprice',
        'apikey': ETHERSCAN_API_KEY
    }

    session = Session()

    try:
        gas_response = session.get(gas_url, params=gas_parameters)
        gas_data = json.loads(gas_response.text)['result']

        stats_response = session.get(stats_url, params=stats_parameters)
        stats_data = json.loads(stats_response.text)['result']
    except (ConnectionError, Timeout, TooManyRedirects) as e:
        bot.send_message(message.chat.id, "Could not reach API. Try again later.")
        print("/ethgas API failure")
        print(e)
        return

    gwei_to_usd = 0.000000001 * float(stats_data['ethusd'])
    uniswap_gas_limit = 152000

    safe_gas_usd = round(float(gas_data['SafeGasPrice']) * gwei_to_usd * uniswap_gas_limit, 4)
    proposed_gas_usd = round(float(gas_data['ProposeGasPrice']) * gwei_to_usd * uniswap_gas_limit, 4)
    fast_gas_usd = round(float(gas_data['FastGasPrice']) * gwei_to_usd * uniswap_gas_limit, 4)

    bot_message = f"Uniswap Gas ({format(uniswap_gas_limit, ',')} gas limit)\n" +\
        f"Safe: {gas_data['SafeGasPrice']} gwei (${safe_gas_usd})\n" +\
        f"Proposed: {gas_data['ProposeGasPrice']} gwei (${proposed_gas_usd})\n" +\
        f"Fast: {gas_data['FastGasPrice']} gwei (${fast_gas_usd})"

    bot.send_message(message.chat.id, bot_message)


@bot.message_handler(commands=['list_commands', 'lc'])
def list_commands_in_file(message):
    request = message.text.split()[1] if len(message.text.split()) == 2 else ''

    # Given a command file that does not exist or too many or too few args
    if (request + '.py') not in os.listdir('misc_commands') or request == '':
        response = 'Usage: /list_commands COMMANDS_FILE\nKnown command files: '

        # Iterate over directories containing command files and strip the file extension from them
        python_files = list(filter(lambda file: file.endswith('.py'), os.listdir('misc_commands')))
        python_files = [os.path.splitext(x)[0] for x in python_files]

        response += ' | '.join(python_files)
        bot.send_message(message.chat.id, response)

        return

    with open(f'misc_commands/{request}.py', 'r') as f:
        commands = ""

        # Iterate over every bot command line
        for line in (x for x in f if x.startswith('@bot.')):
            matches = re.findall(r"['|\"](.*?)['|\"]", line)
            commands += (' | '.join(matches)) + " /// "

    bot.send_message(message.chat.id, f"Known commands in {request}:\n{commands}")


# Load bot commands from each python file in misc_commands directory
for command_file in filter(lambda file: file.endswith('.py'), os.listdir('misc_commands')):
    exec(open(f"misc_commands/{command_file}").read())


def message_polling():
    print('Starting...')
    while True:
        try:
            bot.polling()
        except Exception as e:
            print(type(e))
            print(e)

        time.sleep(1)


# Workaround to stop the bot from failing when HTTP timeout happens bit still allow for CTRL-C to close it
telegram_polling_thread = Thread(target=message_polling)
telegram_polling_thread.start()
