import time

from kucoin.client import Client
from kucoin_futures.client import User, Market, Trade


class KuCoinAPI:
    def __init__(self, api_key, api_secret, api_passphrase):
        """
        :param api_key: Account's api key
        :param api_secret: Account's secret
        :param api_passphrase: API's pass phrase
        """
        self.kucoin_client = Client(api_key, api_secret, api_passphrase)  # Client for binance
        self.kucoin_client_user = User(api_key, api_secret, api_passphrase)  # Client for binance
        self.kucoin_client_trade = Trade(api_key, api_secret, api_passphrase)  # Client for binance
        self.kucoin_client_market = Market()
        self.used_qty = 0  # Storing used quantity to later use while selling

    def get_acc_balance(self):
        """
        :return: returns current balance of the futures wallet / account
        """

        return float(self.kucoin_client_user.get_account_overview("USDT")['marginBalance'])

    def get_pair_curr_price(self, pair):
        """
        :param pair:  Pair which price need to be fetched --string
        :return: current price --float
        """
        return float(self.kucoin_client_market.get_ticker(symbol=pair)['price'])

    def get_pair_multiplier(self, pair):
        """
        :param pair:  Pair which multiplier need to be fetched --string
        :return: pair multiplier --float
        """
        return float(self.kucoin_client_market.get_contract_detail(pair)["multiplier"])

    def get_pair_precision(self, pair):
        """
        Each platform has float precision dictionary which defines how many decimal points there should in coins quantity
        :param pair: Current pair --string
        :return: precision places --int
        """
        all_info = self.kucoin_client.get_markets()  # Fetch all coins precision
        for i in all_info['symbols']:  # Search for current coin
            try:
                if i['pair'] == pair:
                    return int(i['quantityPrecision'])
            except Exception as e:
                print(e)
                pass

    def cal_quantity(self, margin, leverage, pair):
        """
        This calculates quantity needs to buy according to the given margin, leverage and pair's precision
        :param margin: Account margin need to be used
        :param leverage: Leverage for pair
        :param pair:  Current pair
        :return: Total quantity
        """
        multiplier = self.get_pair_multiplier(pair=pair)
        balance = self.get_acc_balance()
        curr_price = self.get_pair_curr_price(pair=pair)
        return int((leverage * margin) / (curr_price * multiplier))

    def place_order(self, pair, side, margin, leverage):
        """
        Function to place buy order according to set margin and leverage
        :param pair: Current pair
        :param side: BUY for long entry, SELL for short entry --string
        :param margin: Account margin
        :param leverage: Leverage to be used
        :return: price at which order got placed
        """

        # self.order_size = self.cal_quantity(pair=pair, margin=margin,
        #                                     leverage=leverage)  # Storing the used quantity for selling same later on
        # self.kucoin_client_trade.futures_create_order(symbol=pair, side=side, type='MARKET', quantity=self.used_qty)
        try:
            order_id = self.kucoin_client_trade.create_market_order(pair, side.lower(), leverage,
                                                                    trade_volume="1")
            return order_id
        except:
            while True:
                time.sleep(5)
                return self.place_order(pair=pair, side=side, margin=margin, leverage=leverage)

    def place_sell_order(self, pair, side, margin, leverage):
        """
        Function to place sell order
        :param pair: Current pair
        :return: Success or Failure Message from Binance api client
        """
        return self.kucoin_client_trade.create_market_order(pair, 'sell', 20,
                                                            trade_volume="1")

    def close_order(self, order_id):
        self.kucoin_client_trade.cancel_order(order_id)

    def place_limit_order(self, pair, side, margin, price, leverage):
        try:
            self.kucoin_client_trade.cancel_all_limit_order(pair)
            return self.kucoin_client_trade.create_limit_order(pair, side, leverage, margin, price)
        except:
            while True:
                time.sleep(5)
                return self.place_limit_order(pair=pair, side=side, margin=margin, price=price, leverage=leverage)

    def cancel_limit_order(self, order_id):
        return self.kucoin_client_trade.cancel_order(order_id)

    def get_current_pair_price(self, pair):
        try:
            return float(self.kucoin_client_market.get_ticker(symbol=pair)['price'])
        except:
            while True:
                time.sleep(5)
                return self.get_current_pair_price(pair=pair)

    def is_position_open(self, pair):
        try:
            open_positions = self.kucoin_client_trade.get_all_position()
            if 'code' in open_positions:
                return False
            else:
                for pos in open_positions:
                    if pos['symbol'] == pair:
                        return True

            return False
        except:
            while True:
                time.sleep(5)
                return self.is_position_open(pair=pair)
