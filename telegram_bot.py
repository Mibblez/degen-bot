import os
import sys
from dotenv import load_dotenv
import telebot
import json
import random
import time
import re
import sqlite3

from requests import Session
from requests.exceptions import ConnectionError, Timeout, TooManyRedirects
import pprint as pp

from threading import Thread

load_dotenv()
TELEGRAM_API_KEY = os.getenv('TELEGRAM_API_KEY')
CMC_API_KEY = os.getenv('COINMARKETCAP_API_KEY')
ETHERSCAN_API_KEY = os.getenv('ETHERSCAN_API_KEY')

if None in [TELEGRAM_API_KEY, CMC_API_KEY, ETHERSCAN_API_KEY]:
    print('ERROR: Missing API key(s)\n'
          'API keys for the following APIs must be present in the .env file: '
          'TELEGRAM, Coinmarketcap, Etherscan\n'
          'These API keys must be named TELEGRAM_API_KEY, COINMARKETCAP_API_KEY and ETHERSCAN_API_KEY')
    sys.exit()

if not os.path.exists('cryptos.json'):
    print('ERROR: cryptos.json not found\n'
          'Create a cryptos.json according to the template named cryptos_example.json')

json_file = open('cryptos.json')
cryptos_json = json.load(json_file)

bot = telebot.TeleBot(TELEGRAM_API_KEY)


@bot.message_handler(commands=['coins'])
def coins(message):
    bot.reply_to(message, 'Known coins:\n' + ' ; '.join([x for x in cryptos_json.keys()]))


def usage_error(message, usage_str: str = ''):
    bot.send_message(message.chat.id, f'Usage\n{usage_str}')


def unknown_coin(message, invalid_coin_str):
    bot.send_message(message.chat.id,
                     f"Unknown coin: {invalid_coin_str}\n\nKnown coins: {' ; '.join([x for x in cryptos_json.keys()])}")


# TODO: add has_dextools in each json entry. show dextools url if has_dextools is set to true
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


def initialize_db():
    connection = sqlite3.connect('notifications.db')
    cursor = connection.cursor()

    command1 = 'CREATE TABLE IF NOT EXISTS ' +\
               'users(user_id INTEGER PRIMARY KEY, name TEXT)'

    command2 = 'CREATE TABLE IF NOT EXISTS ' +\
               'price_notifications(' +\
               'notification_id INTEGER PRIMARY KEY AUTOINCREMENT, coin TEXT, user_id INTEGER, ' +\
               'notify_at FLOAT, direction CHAR,' +\
               'FOREIGN KEY(user_id) REFERENCES users(user_id))'

    cursor.execute(command1)
    cursor.execute(command2)

    connection.commit()
    connection.close()


@bot.message_handler(commands=['start'])
def start_bot(message):
    user_id = message.from_user.id

    connection = sqlite3.connect('notifications.db')
    cursor = connection.cursor()

    # Create new user in user db if not already present
    cursor.execute(f"SELECT user_id FROM users WHERE user_id={user_id}")
    if cursor.fetchone() is None:
        cursor.execute('INSERT INTO users VALUES '
                       f"({user_id}, '{message.from_user.first_name} {message.from_user.last_name}')")

    connection.commit()
    connection.close()

    bot.reply_to(message, "Henlo")


@bot.message_handler(commands=['price_notify'])
def notify(message):
    request = message.text.split()[1:3] if len(message.text.split()) == 3 else ''

    if request == '':
        # Too many or too few args
        usage_error(message, '/price_notify COIN_NAME PRICE_TARGET')
        return

    coin = request[0].upper()
    if coin not in cryptos_json:
        # Given a coin name thats not in the JSON file
        unknown_coin(message, request)
        return

    # Make sure price_target arg can be converted to a float
    price_target = 0.0
    try:
        price_target = float(request[1].strip('$'))
    except ValueError:
        usage_error(message, '/price_notify COIN_NAME PRICE_TARGET\n'
                    'Ensure that PRICE_TARGET is a number')
        return

    user_id = message.from_user.id

    connection = sqlite3.connect('notifications.db')
    cursor = connection.cursor()

    # Make sure user is in the database
    cursor.execute(f"SELECT user_id FROM users WHERE user_id={user_id}")
    if cursor.fetchone() is None:
        bot.reply_to(message, "Cannot set price notification. You must DM the bot /start first.")
        return

    coin_id = cryptos_json[coin]["cmc_id"]
    coin_data = get_coin_data(coin_id)

    if coin_data is None:
        bot.send_message(message.chat.id, "Could not get the latest price. Try again later.")
        return

    latest_price = float("{:.10f}".format(
        coin_data['data'][coin_id]['quote']['USD']['price']))

    desired_price_movement = '+' if latest_price < price_target else '-'

    # See if user already has a notification for this coin. Overwrite the old notification if so
    cursor.execute(f"SELECT notification_id from price_notifications WHERE user_id={user_id} AND coin='{coin}'")
    price_notification_id = 'NULL'
    if (fetch := cursor.fetchone()) is not None:
        price_notification_id = fetch[0]

    cursor.execute('REPLACE INTO price_notifications VALUES '
                   f"({price_notification_id}, '{coin}', {user_id}, {price_target}, '{desired_price_movement}')")

    connection.commit()
    connection.close()

    bot.reply_to(message, f"Created notification for {coin} at ${price_target}")


@bot.message_handler(commands=['check_notifications'])
def check_notifications(message):
    connection = sqlite3.connect('notifications.db')
    cursor = connection.cursor()

    cursor.execute(f"SELECT coin, notify_at FROM price_notifications WHERE user_id={message.from_user.id}")
    result = cursor.fetchall()

    if result == []:
        # No notifications are set
        bot.reply_to(message, "No notifications set")
        connection.close()
        return

    response = ""

    for coin, notify_at in result:
        response += f"{coin} at ${notify_at}\n"

    bot.reply_to(message, response)
    connection.close()


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
    coin_data = get_coin_data(coin_id)

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


def get_coin_data(coin_id):
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


# TODO:  Different gas amounts with subcommands(normal transaction, uniswap, erc20, etc)
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
def list_commands_in_file(message, dir='misc_commands'):
    if not os.path.exists(dir):
        return

    request = message.text.split()[1] if len(message.text.split()) == 2 else ''

    # Given a command file that does not exist or too many or too few args
    if (request + '.py') not in os.listdir(dir) or request == '':
        response = 'Usage: /list_commands COMMANDS_FILE\nKnown command files: '

        # Iterate over directories containing command files and strip the file extension from them
        python_files = list(filter(lambda file: file.endswith('.py'), os.listdir(dir)))
        python_files = [os.path.splitext(x)[0] for x in python_files]

        response += ' | '.join(python_files)
        bot.send_message(message.chat.id, response)

        return

    with open(f'{dir}/{request}.py', 'r') as f:
        commands = ""

        # Iterate over every bot command line
        for line in (x for x in f if x.startswith('@bot.')):
            matches = re.findall(r"['|\"](.*?)['|\"]", line)
            commands += (' | '.join(matches)) + " /// "

    bot.send_message(message.chat.id, f"Known commands in {request}:\n{commands}")


if os.path.exists('misc_commands'):
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


def check_price_notifications():
    while True:
        connection = sqlite3.connect('notifications.db')
        cursor = connection.cursor()

        # Get a list of coins that have notifications set
        cursor.execute("SELECT DISTINCT coin FROM price_notifications")
        coin_names = [item for t in cursor.fetchall() for item in t]

        # Only check notifications if someone has a notification set
        if coin_names is None:
            connection.close()
            time.sleep(900)
            continue

        coin_ids = list(map(lambda coin_name: cryptos_json[coin_name]["cmc_id"], coin_names))

        # Convert coin_ids list to a string so it can be passed to the CMC api
        coin_string = ",".join(coin_ids)

        coin_data = get_coin_data(coin_string)

        for coin_id, coin_name in zip(coin_ids, coin_names):
            current_price = float("{:.10f}".format(coin_data['data'][coin_id]['quote']['USD']['price']))

            cursor.execute("SELECT notification_id, user_id, notify_at, direction FROM price_notifications "
                           f"WHERE coin='{coin_name}'")

            result = cursor.fetchall()

            # Check if the price for each coin is high or low enough to trigger a notification
            # If so, DM the user and remove the notification entry from the database
            for notification_id, user_id, notification_price, direction in result:
                if direction == '+' and current_price > notification_price:
                    bot.send_message(user_id, 'HEY FELLOW APE!\n'
                                     f'{coin_name} has risen above {notification_price} and is at {current_price}.')
                    cursor.execute(f"DELETE FROM price_notifications WHERE notification_id={notification_id}")
                elif direction == '-' and current_price < notification_price:
                    bot.send_message(user_id, 'HEY GAY BEAR!\n'
                                     f'{coin_name} has fallen below {notification_price} and is at {current_price}.')
                    cursor.execute(f"DELETE FROM price_notifications WHERE notification_id={notification_id}")

        connection.commit()
        connection.close()
        time.sleep(900)


initialize_db()

# Workaround to stop the bot from failing when HTTP timeout happens but still allow CTRL-C to close it
telegram_polling_thread = Thread(target=message_polling)
telegram_polling_thread.start()

price_checker_thread = Thread(target=check_price_notifications)
price_checker_thread.start()
