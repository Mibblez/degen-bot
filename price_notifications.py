import sqlite3
import time

import functools

import globals
from bot_utilities import get_coin_data, usage_error, unknown_coin


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


# Wrapper that creates a cursor for notifications.db and passes it down to func
# Closes the connection to the db and commits any changes once func returns
def uses_notification_db(func):
    @functools.wraps(func)
    def wrapped(*args, **kwargs):
        connection = sqlite3.connect('notifications.db')
        cursor = connection.cursor()

        # Call func with cursor, passing along any other args to it as well
        func(cursor, *args, **kwargs)

        connection.commit()
        connection.close()

    return wrapped


@globals.bot.message_handler(commands=['price_notify', 'pnot'])
@uses_notification_db
def notify(cursor, message):
    request = message.text.split()[1:3] if len(message.text.split()) == 3 else ''

    if request == '':
        # Too many or too few args
        usage_error(message, '/price_notify COIN_NAME PRICE_TARGET')
        return

    coin = request[0].upper()
    if coin not in globals.cryptos_json:
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

    # Make sure user is in the database
    cursor.execute(f"SELECT user_id FROM users WHERE user_id={user_id}")
    if cursor.fetchone() is None:
        globals.bot.reply_to(message, "Cannot set price notification. You must DM the bot /start first.")
        return

    coin_id = globals.cryptos_json[coin]["cmc_id"]
    coin_data = get_coin_data(coin_id, globals.CMC_API_KEY)

    if coin_data is None:
        globals.bot.send_message(message.chat.id, "Could not get the latest price. Try again later.")
        return

    latest_price = float("{:.10f}".format(
        coin_data['data'][coin_id]['quote']['USD']['price']))

    desired_price_movement = '+' if latest_price < price_target else '-'

    # See if user already has a notification for this coin. Overwrite the old notification if so
    cursor.execute(f"SELECT notification_id from price_notifications WHERE user_id={user_id} AND coin='{coin}'")
    # If NULL is used for the notification ID, the db will replace it with a unique ID
    price_notification_id = 'NULL'
    if (fetch := cursor.fetchone()) is not None:
        price_notification_id = fetch[0]

    cursor.execute('REPLACE INTO price_notifications VALUES '
                   f"({price_notification_id}, '{coin}', {user_id}, {price_target}, '{desired_price_movement}')")

    globals.bot.reply_to(message, f"Created notification for {coin} at ${price_target}")


@globals.bot.message_handler(commands=['check_notifications', 'cnot'])
@uses_notification_db
def check_notifications(cursor, message):
    cursor.execute(f"SELECT coin, notify_at FROM price_notifications WHERE user_id={message.from_user.id}")
    result = cursor.fetchall()

    if result == []:
        # No notifications are set
        globals.bot.reply_to(message, "No notifications set")
        return

    response = ""

    for coin, notify_at in result:
        response += f"{coin} at ${notify_at}\n"

    globals.bot.reply_to(message, response)


@globals.bot.message_handler(commands=['delete_notification', 'dnot'])
@uses_notification_db
def delete_notification(cursor, message):
    request = message.text.split()[1:2] if len(message.text.split()) == 2 else ''

    if request == '':
        # Too many or too few args
        usage_error(message, '/delete_notification COIN_NAME')
        return

    coin = request[0].upper()
    if coin not in globals.cryptos_json:
        # Given a coin name thats not in the JSON file
        unknown_coin(message, request)
        return

    user_id = message.from_user.id

    cursor.execute(f"SELECT notification_id from price_notifications WHERE user_id={user_id} AND coin='{coin}'")
    if (cursor.fetchone() is None):
        globals.bot.reply_to(message, f"You don't have a notification set for {coin}")
        return

    cursor.execute(f"DELETE FROM price_notifications WHERE user_id={user_id} AND coin='{coin}'")
    globals.bot.reply_to(message, f"Notification for {coin} deleted")


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

        coin_ids = list(map(lambda coin_name: globals.cryptos_json[coin_name]["cmc_id"], coin_names))

        # Convert coin_ids list to a string so it can be passed to the CMC api
        coin_string = ",".join(coin_ids)

        coin_data = get_coin_data(coin_string, globals.CMC_API_KEY)

        for coin_id, coin_name in zip(coin_ids, coin_names):
            current_price = float("{:.10f}".format(coin_data['data'][coin_id]['quote']['USD']['price']))

            cursor.execute("SELECT notification_id, user_id, notify_at, direction FROM price_notifications "
                           f"WHERE coin='{coin_name}'")

            result = cursor.fetchall()

            # Check if the price for each coin is high or low enough to trigger a notification
            # If so, DM the user and remove the notification entry from the database
            for notification_id, user_id, notification_price, direction in result:
                if direction == '+' and current_price > notification_price:
                    globals.bot.send_message(user_id, 'HEY FELLOW 🦍!\n'
                                             f'{coin_name} has risen above {notification_price} and is at {current_price}.')
                    cursor.execute(f"DELETE FROM price_notifications WHERE notification_id={notification_id}")
                elif direction == '-' and current_price < notification_price:
                    globals.bot.send_message(user_id, 'HEY 🌈🐻!\n'
                                             f'{coin_name} has fallen below {notification_price} and is at {current_price}.')
                    cursor.execute(f"DELETE FROM price_notifications WHERE notification_id={notification_id}")

        connection.commit()
        connection.close()
        time.sleep(900)
