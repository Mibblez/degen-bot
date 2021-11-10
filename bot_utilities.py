import json
import pprint as pp
from requests import Session
from requests.exceptions import ConnectionError, Timeout, TooManyRedirects

import globals


def usage_error(message, usage_str: str = ''):
    globals.bot.send_message(message.chat.id, f'Usage\n{usage_str}')


def unknown_coin(message, invalid_coin_str):
    globals.bot.send_message(message.chat.id,
                             f"Unknown coin: {invalid_coin_str}\n\nKnown coins:" +
                             f"{' ; '.join([x for x in globals.cryptos_json.keys()])}")


def get_coin_data(coin_id, cmc_api_key):
    url = 'https://pro-api.coinmarketcap.com/v1/cryptocurrency/quotes/latest'
    headers = {
        'Accepts': 'application/json',
        'X-CMC_PRO_API_KEY': cmc_api_key,
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
