from binance.client import Client

class BiAPI:
    def __init__(self, api_key, api_secrete):
        """
        :param api_key: Account's api key
        :param api_secrete: Account's secrete
        """
        self.bi_client = Client(api_key=api_key, api_secret=api_secrete)  # Client for binance
        self.used_qty = 0  # Storing used quantity to later use while selling

    def get_acc_balance(self):
        """
        :return: returns current balance of the futures wallet / account
        """
        return float(self.bi_client.futures_account_balance()[6]['balance'])

    def get_pair_curr_price(self, pair):
        """
        :param pair:  Pair which price need to be fetched --string
        :return: current price --float
        """
        return float(self.bi_client.futures_symbol_ticker(symbol=pair)['price'])

    def get_pair_precision(self, pair):
        """
        Each platform has float precision dictionary which defines how many decimal points there should in coins quantity
        :param pair: Current pair --string
        :return: precision places --int
        """
        all_info = self.bi_client.futures_exchange_info()  # Fetch all coins precision
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
        precision = self.get_pair_precision(pair=pair)
        balance = self.get_acc_balance()
        curr_price = self.get_pair_curr_price(pair=pair)
        return round(float(((balance * (margin / 100)) * leverage) / curr_price), precision)

    def place_order(self, pair, side, margin, leverage):
        """
        Function to place buy order according to set margin and leverage
        :param pair: Current pair
        :param side: BUY for long entry, SELL for short entry --string
        :param margin: Account margin
        :param leverage: Leverage to be used
        :return: price at which order got placed
        """
        self.used_qty = self.cal_quantity(pair=pair, margin=margin, leverage=leverage)  # Storing the used quantity for selling same later on
        self.bi_client.futures_create_order(symbol=pair, side=side, type='MARKET', quantity=self.used_qty)
        return self.get_pair_curr_price(pair=pair)

    def place_sell_order(self, pair):
        """
        Function to place sell order
        :param pair: Current pair
        :return: Success or Failure Message from Binance api client
        """
        return self.bi_client.futures_create_order(symbol=pair, side='SELL', type='MARKET', quantity=self.used_qty)
