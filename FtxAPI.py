import ftx
from pprint import pprint


def string_precision(price_string: str):
    return len(price_string.split(".")[1])


class FtxApi:
    def __init__(self, api_key, api_secret):
        self.ftx_cli = ftx.FtxClient(api_key=api_key, api_secret=api_secret)
        self.qty = 0

    def get_acc_balance(self):
        """
        :return: returns current balance of the futures wallet / account
        """
        return float(self.ftx_cli.get_account_info()['totalAccountValue'])

    def get_pair_curr_price(self, pair):
        """
        :param pair:  Pair which price need to be fetched --string
        :return: current price --float
        """
        return float(self.ftx_cli.get_future(future_name=pair)['last'])

    def get_pair_precision(self, pair):
        """
        Each platform has float precision dictionary which defines how many decimal points there should in coins quantity
        :param pair: Current pair --string
        :return: precision places --int
        """
        data = self.ftx_cli.get_future(future_name=pair)
        return string_precision(data['sizeIncrement'])

    def cal_quantity(self, margin, leverage, pair):
        """
        This calculates quantity needs to buy according to the given margin, leverage and pair's precision
        :param margin: Account margin need to be used
        :param leverage: Leverage for pair

        :param pair:  Current pair
        :return: Total quantity
        """
        precision = self.get_pair_precision(pair=pair)
        balance = self.get_acc_balance()
        curr_price = self.get_pair_curr_price(pair=pair)
        return round(float(((balance * (margin / 100)) * leverage) / curr_price), precision)

    def place_buy_order(self, pair, side, margin, leverage):
        self.qty = self.cal_quantity(pair=pair, margin=margin, leverage=leverage)  # Storing the used quantity for selling same later on
        return self.ftx_cli.place_order(market='{}-PERP'.format(pair), side='buy', price=self.get_pair_curr_price(pair), size=self.qty, type='market')

    def place_sell_order(self, pair, side, margin, leverage):
        """
        Function to place sell order
        :param pair: Current pair
        :return: Success or Failure Message from Binance api client
        """
        self.qty = self.cal_quantity(pair=pair, margin=margin, leverage=leverage)
        return self.ftx_cli.place_order(market='{}-PERP'.format(pair), side='buy', price=self.get_pair_curr_price(pair), size=self.qty, type='market')
