import time
from apollox.rest_api import Client
from pprint import pprint
import ConfigTest

class apolloxAPI:
    def __init__(self, api_key, api_secrete):
        self.client = Client(key=api_key, secret=api_secrete)
        self.qty = 0

    def get_pair_curr_price(self, pair):
        """
        :param pair:  Pair which price need to be fetched --string
        :return: current price --float
        """
        return float(self.client.ticker_price(symbol=pair)['price'])

    def get_pair_precision(self, pair):
        """
        Each platform has float precision dictionary which defines how many decimal points there should in coins quantity
        :param pair: Current pair --string
        :return: precision places --int
        """
        all_info = self.client.exchange_info()  # Fetch all coins precision
        for i in all_info['symbols']:  # Search for current coin
            try:
                if i['pair'] == pair:
                    return int(i['quantityPrecision'])
            except Exception as e:
                print(e)
                pass

    def cal_quantity(self, margin, leverage, pair, acc_bl):
        """
        This calculates quantity needs to buy according to the given margin, leverage and pair's precision
        :param acc_bl:
        :param margin: Account margin need to be used
        :param leverage: Leverage for pair

        :param pair:  Current pair
        :return: Total quantity
        """
        precision = self.get_pair_precision(pair=pair)
        curr_price = self.get_pair_curr_price(pair=pair)
        return round(float(((acc_bl * (margin / 100)) * leverage) / curr_price), precision)

    def place_order(self, pair, side, margin, leverage, acc_bal):
        self.qty = self.cal_quantity(margin, leverage, pair, acc_bal)
        params = {
            'symbol': pair,
            'side': side,
            'type': 'MARKET',
            'quantity': self.qty
        }

        return self.client.new_order(**params)

    def place_sell_order(self, pair):
        """
        Function to place sell order
        :param pair: Current pair
        :return: Success or Failure Message from Binance api client
        """
        params = {
            'symbol': pair,
            'side': "SELL",
            'type': 'MARKET',
            'quantity': self.qty
        }
        return self.client.new_order(**params)



