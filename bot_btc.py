import json
import time
from datetime import datetime

import pymongo
import requests
# import BinanceAPI
from kucoin_futures.client import Market

import ConfigTest
# import FtxAPI
import KuCoinAPI


def cal_trail_sl(price, percent, side):
    """
    Calculate trailing stop loss according to trade side
    :param price: Price --float
    :param percent: Trail sl percentage --int
    :param side: 0--> BUY and 1--> SELL --int
    :return:
    """
    # 1000->1100
    if side == 0:
        return price - (price * (percent / 100))
    elif side == 1:
        return price + (price * (percent / 100))


def cal_per_chg(old, new):
    return round(((new - old) / old) * 100, 2)


class Process:
    def __init__(self):
        """
        This is constructor for the class
        Here I am setting target point, stop loss, trail stop loss, stop loss time because we don't have database from which we gonna fetch this
        """
        # # These are the settings for testing single trade
        self.target_point = 2.5  # Target point
        self.stop_loss = 1  # Stop loss after stop loss timer
        self.trail_stop_loss = 1.1  # Trailing stop loss percentage
        self.stop_loss_time = 120  # Stop loss timer
        self.entry_price = 0
        self.leverage = 20

        self.symbol_full = 'XBTUSDTM'
        self.symbol = 'BTC'
        self.symbol_spot_signal = 'BTC_binance_spot'
        self.symbol_perp_signal = 'BTC_binance_perp'

        # These are the settings for testing single trade

        # Below are some variables for dynamic working
        self.trade_time = None
        self.monitoring_stock = {}
        self.watch_stock = {}
        self.curr_pair = ""
        self.run = True
        self.used_api = None

    def update_settings(self):
        myclient = pymongo.MongoClient("mongodb://localhost:27017/")
        mydb = myclient["trdr"]
        trade_settings_col = mydb["trade_settings"]
        current_user_email = 'cocbaz@gmail.com'
        myquery = {
            'user_email': current_user_email,
            'crypto': self.symbol
        }
        trade_setting = trade_settings_col.find_one(myquery)
        if trade_setting is None:
            self.target_point = 2.5  # Target point
            self.stop_loss = 1  # Stop loss after stop loss timer
            self.trail_stop_loss = 1.1  # Trailing stop loss percentage
            self.stop_loss_time = 120  # Stop loss timer
            self.leverage = 20
        else:
            self.target_point = trade_setting['target_point']  # Target point
            self.stop_loss = trade_setting['stop_loss']  # Stop loss after stop loss timer
            self.trail_stop_loss = trade_setting['trail_stop_loss']  # Trailing stop loss percentage
            self.stop_loss_time = trade_setting['stop_loss_time']  # Stop loss timer
            self.leverage = 20

    def trigger(self, leverage, side, pair, acc_margin, platform):
        """
        This will be the trigger function where tp, sl, trail_sl, sl_time will be set and trade will take place
        With account ID we can fetch API-KEY and API-SECRETE
        :param leverage: leverage for trade ( User must know leverage per coin with respect to his account balance ) --integer
        :param side: BUY-->0 or SELL(SHORT)-->1 --integer
        :param pair: Name of the coin (BTCUSDT) --string
        :param acc_margin: Margin percentage being used from account --integer
        :param acc_id: account ID to look up api key and secrete in the database --integer
        :param platform: Platform on which the trade will be taken 0->Apollox, 1->Binance, 2->FTX --Integer
        :return: Success response
        """
        if platform == 0:
            # todo Apollox automation still in progress
            pass
        # elif platform == 1:
        # # Right now we are using api key from ConfigTest.py file later we'll integrate database
        # # todo implement database read function
        # self.used_api = BinanceAPI.BiAPI(api_key=ConfigTest.bi_api_key, api_secrete=ConfigTest.bi_api_secrete)
        # base_price = None
        # if side == 0:  # If long
        #     base_price = self.used_api.place_order(pair=pair, side='BUY', margin=acc_margin, leverage=leverage)
        #     print("Placed BUY order at:", base_price)
        # elif side == 1:  # If Short
        #     base_price = self.used_api.place_order(pair=pair, side='SELL', margin=acc_margin, leverage=leverage)
        #     print("Placed SELL order at:", base_price)
        # """
        # As soon as we place order on either BUY or SELL side we need to add it to watch list to check if it hits target point
        # or went down.
        # Thus pair gets add to watch list and kline socket for same pair get started.
        # """
        # self.curr_pair = pair
        # self.trade_time = datetime.now()
        # self.watch_stock[pair] = {'base_price': base_price, 'side': side,
        #                           'base_stop_loss': cal_trail_sl(price=base_price, percent=self.stop_loss,
        #                                                          side=side)}
        # self.start_kline_socket(pair=pair)

        # elif platform == 2:
        #     self.used_api = FtxAPI.FtxApi(api_key=ConfigTest.bi_api_key, api_secret=ConfigTest.bi_api_secrete)
        #     base_price = None
        #     if side == 0:  # If long
        #         base_price = self.used_api.place_buy_order(pair=pair, side='BUY', margin=acc_margin, leverage=leverage)
        #         print("Placed BUY order at:", base_price)
        #     elif side == 1:  # If Short
        #         base_price = self.used_api.place_sell_order(pair=pair, side='SELL', margin=acc_margin,
        #                                                     leverage=leverage)
        #         print("Placed SELL order at:", base_price)
        #     """
        #     As soon as we place order on either BUY or SELL side we need to add it to watch list to check if it hits target point
        #     or went down.
        #     Thus pair gets add to watch list and kline socket for same pair get started.
        #     """
        #     self.curr_pair = pair
        #     self.trade_time = datetime.now()
        #     self.watch_stock[pair] = {'base_price': base_price, 'side': side,
        #                               'base_stop_loss': cal_trail_sl(price=base_price, percent=self.stop_loss,
        #                                                              side=side)}

        elif platform == 3:
            # Right now we are using api key from ConfigTest.py file later we'll integrate database
            # todo implement database read function
            self.used_api = KuCoinAPI.KuCoinAPI(api_key=ConfigTest.api_key, api_secret=ConfigTest.api_secret,
                                                api_passphrase=ConfigTest.api_passphrase)
            kucoin_client_market = Market()
            base_price = float(kucoin_client_market.get_ticker(symbol=self.symbol_full)['price'])
            print("Base price: ", base_price)
            # url = 'http://127.0.0.1:5000/candlesticklimit'
            # data = {'api_key': 'u2:(vyaVDU6%N*rH', 'symbol': 'BTC'}
            # x = requests.post(url, json=data)
            # result = json.loads(x.text)
            # base_price = float(result[0]['price']['close'])
            # proc.update_stock(price_close_0)
            # time.sleep(1)
            if side == 0:  # If long
                try:
                    order_id = self.used_api.place_order(pair=pair, side='BUY', margin=acc_margin, leverage=leverage)
                    self.entry_price = base_price
                    print("Placed BUY order: ", order_id)
                    print("Entry price: ", base_price)
                    self.curr_pair = pair
                    self.trade_time = datetime.now()
                    self.watch_stock[pair] = {'base_price': base_price, 'side': side, 'leverage': leverage,
                                              'size': acc_margin,
                                              'platform': platform,
                                              'base_stop_loss': cal_trail_sl(price=base_price, percent=self.stop_loss,
                                                                             side=side), 'stop_loss_trigger': False,
                                              'target_trigger': 0, 'limit_order_id': None}
                    print(self.watch_stock)
                    time.sleep(5)
                except:
                    print("An exception occurred...")
                    time.sleep(5)
                    self.trigger(leverage=leverage, side=side, pair=pair, acc_margin=acc_margin, platform=platform)

            elif side == 1:  # If Short
                try:
                    order_id = self.used_api.place_order(pair=pair, side='SELL', margin=acc_margin, leverage=leverage)
                    print("Placed SELL order: ", order_id)
                    print("Entry price: ", base_price)
                    self.curr_pair = pair
                    self.trade_time = datetime.now()
                    print(self.watch_stock)
                    self.watch_stock[pair] = {'base_price': base_price, 'side': side, 'leverage': leverage,
                                              'size': acc_margin,
                                              'platform': platform,
                                              'base_stop_loss': cal_trail_sl(price=base_price, percent=self.stop_loss,
                                                                             side=side), 'stop_loss_trigger': False,
                                              'target_trigger': 0, 'limit_order_id': None}
                    time.sleep(5)
                except:
                    print("An exception occurred...")
                    time.sleep(5)
                    self.trigger(leverage=leverage, side=side, pair=pair, acc_margin=acc_margin, platform=platform)
            """
            As soon as we place order on either BUY or SELL side we need to add it to watch list to check if it hits target point
            or went down.
            Thus pair gets add to watch list and kline socket for same pair get started. 
            """
            # self.start_kline_socket(pair=pair)

    def update_stock(self, close: float):
        """
        This is main function which checks target point, stop loss and stop loss timer
        :param close: current price for the pair
        :return: Nothing
        """

        self.update_settings()
        print("Monitoring Stock...")
        # If the position is a long position
        if self.watch_stock[self.curr_pair]['side'] == 0:
            target = self.entry_price * (1 + self.target_point / 100)
            stop_loss = self.entry_price * (1 - self.stop_loss / 100)

            leverage = self.leverage
            acc_margin = "1"
            platform = 3
            print("Position: LONG")
            print("Entry price: ", self.entry_price)
            print("Potential target: ", self.entry_price * (1 + self.target_point / 100))
            print("Potential sl: ", self.entry_price * (1 - self.stop_loss / 100))
            print("Current price: ", close)
            print("% of current profit: ", self.leverage * ((close / self.entry_price) - 1) * 100)

            if close < stop_loss:
                print("Stop loss triggered...")
                # Check if stoploss is already triggered
                if self.watch_stock['stop_loss_trigger']:
                    print('Closing position...')
                    self.trigger(leverage=leverage, side=1, pair=self.symbol_full, acc_margin=acc_margin,
                                 platform=platform)
                else:
                    print('Starting stop loss timer...')
                    self.watch_stock['stop_loss_trigger'] = True
                    time.sleep(self.stop_loss_time)
            if close > stop_loss:
                print('Price is above stop loss')
                self.watch_stock['stop_loss_trigger'] = False

            if close > target:
                print('Price is above the target')
                max_price = self.watch_stock['target_trigger']
                last_limit_order_id = self.watch_stock['limit_order_id']
                if close > max_price:
                    print('Price is above the highest price above the target')
                    if last_limit_order_id is None:
                        print('Placing a new limit order...')
                        stop_price = close - (self.trail_stop_loss * close / 100)
                        self.watch_stock['target_trigger'] = close
                        order_id = self.used_api.place_limit_order(pair=self.symbol_full, side="SELL",
                                                                   margin=acc_margin,
                                                                   price=stop_price, leverage=self.leverage)
                        self.watch_stock['limit_order_id'] = order_id
                    else:
                        print('Replacing the limit order...')
                        self.used_api.cancel_limit_order(self.watch_stock['limit_order_id'])
                        stop_price = close - (self.trail_stop_loss * close / 100)
                        self.watch_stock['target_trigger'] = close
                        order_id = self.used_api.place_limit_order(pair=self.symbol_full, side="SELL",
                                                                   margin=acc_margin,
                                                                   price=stop_price, leverage=self.leverage)
                        self.watch_stock['limit_order_id'] = order_id
        if self.watch_stock[self.curr_pair]['side'] == 1:
            target = self.entry_price * (1 - self.target_point / 100)
            stop_loss = self.entry_price * (1 + self.stop_loss / 100)

            leverage = self.watch_stock['leverage']
            acc_margin = self.watch_stock['size']
            platform = self.watch_stock['platform']
            print("Position: SHORT")
            print("Entry price: ", self.entry_price)
            print("Potential target: ", target)
            print("Potential sl: ", stop_loss)
            print("Current price: ", close)

            print("% of current profit: ", self.leverage * (1 - (close / self.entry_price)) * 100)

            if close > stop_loss:
                print("Stop loss triggered...")
                # Check if stoploss is already triggered
                if self.watch_stock['stop_loss_trigger']:
                    print('Closing position...')
                    self.trigger(leverage=leverage, side=0, pair=self.symbol_full, acc_margin=acc_margin,
                                 platform=platform)
                else:
                    print('Starting stop loss timer...')
                    self.watch_stock['stop_loss_trigger'] = True
                    time.sleep(self.stop_loss_time)
            if close < stop_loss:
                print('Price is below the stop loss')
                self.watch_stock['stop_loss_trigger'] = False

            if close < target:
                print('Price is below the target')
                min_price = self.watch_stock['target_trigger']
                last_limit_order_id = self.watch_stock['limit_order_id']
                if close < min_price:
                    print('Price is below the lowest price after the target')
                    if last_limit_order_id is None:
                        print('Placing a new limit order...')
                        stop_price = close + (self.trail_stop_loss * close / 100)
                        self.watch_stock['target_trigger'] = close
                        order_id = self.used_api.place_limit_order(pair=self.symbol_full, side="BUY",
                                                                   margin=acc_margin,
                                                                   price=stop_price, leverage=self.leverage)
                        self.watch_stock['limit_order_id'] = order_id
                    else:
                        print('Replacing the limit order...')
                        self.used_api.cancel_limit_order(self.watch_stock['limit_order_id'])
                        stop_price = close + (self.trail_stop_loss * close / 100)
                        self.watch_stock['target_trigger'] = close
                        order_id = self.used_api.place_limit_order(pair=self.symbol_full, side="BUY",
                                                                   margin=acc_margin,
                                                                   price=stop_price, leverage=self.leverage)
                        self.watch_stock['limit_order_id'] = order_id
        # if self.curr_pair in self.watch_stock and self.curr_pair not in self.monitoring_stock:
        #     print("Monitoring Stock...")
        #     per_chg = cal_per_chg(self.watch_stock[self.curr_pair]['base_price'],
        #                           close)  # Calculate roc (Rate of change)
        #
        #     if self.watch_stock[self.curr_pair]['side'] == 0:  # If trade taken at BUY side
        #         if per_chg >= self.target_point:  # If current price percent increase is greater than target point
        #
        #             curr_sl = cal_trail_sl(price=close, percent=self.trail_stop_loss,
        #                                    side=0)  # Calculate trailing stop loss price
        #             print("current sl: ", curr_sl)
        #             self.monitoring_stock[self.curr_pair] = {"base_price": close, "curr_price": close, "side": 0,
        #                                                      "curr_sl": curr_sl}  # Store pair and stop loss
        #
        #             print("SL started: {}:: At price: {}:: Brought at: {}".format(curr_sl, close,
        #                                                                           self.watch_stock[self.curr_pair][
        #                                                                               'base_price']))
        #             self.watch_stock.pop(self.curr_pair)  # Remove pair from watch list as it hit the target point
        #
        #         elif (
        #                 self.trade_time - datetime.now()).total_seconds() > self.stop_loss_time:  # Else if trade time and current time difference is above set stop loss time
        #             if close <= self.watch_stock[self.curr_pair][
        #                 'base_stop_loss']:  # Check if price lower than base stop loss price
        #                 print("Stock exit due to stop loss hit at price: ", close)
        #                 self.used_api.place_sell_order(pair=self.curr_pair)  # Exit position
        #                 self.run = False  # Stop the while for updating kline data
        #
        #     elif self.watch_stock[self.curr_pair]['side'] == 1:  # If trade taken at SELL side
        #         if per_chg < 0:  # As it is sell side, price down means trade is going in our favour but price decreasing thus percent change will be negative
        #             if abs(per_chg) >= self.target_point:  # Thus check with absolute percentage
        #
        #                 curr_sl = cal_trail_sl(price=close, percent=self.trail_stop_loss,
        #                                        side=1)  # Calculate trailing stop loss price
        #                 self.monitoring_stock[self.curr_pair] = {"base_price": close, "curr_price": close, "side": 1,
        #                                                          "curr_sl": curr_sl}  # Store pair and stop loss
        #
        #                 print("SL started: {}:: At price: {}:: Brought at: {}".format(curr_sl, close,
        #                                                                               self.watch_stock[self.curr_pair][
        #                                                                                   'base_price']))
        #                 self.watch_stock.pop(self.curr_pair)  # Remove pair from watch list as it hit the target point
        #
        #         elif (self.trade_time - datetime.now()).total_seconds() > self.stop_loss_time:
        #             if close >= self.watch_stock[self.curr_pair][
        #                 'base_stop_loss']:  # Check if price greater than base stop loss price
        #                 print("Stock exit due to stop loss hit at price: ", close)
        #                 self.used_api.place_sell_order(pair=self.curr_pair)  # Exit position
        #                 self.run = False  # Stop the while for updating kline data
        #
        # elif self.curr_pair in self.monitoring_stock:  # Checking trail stop loss if target point already hit
        #
        #     if self.monitoring_stock[self.curr_pair]['side'] == 0:  # If it is buy side
        #
        #         if self.monitoring_stock[self.curr_pair][
        #             'curr_sl'] >= close:  # As it's long side if current close is lower than calculated stop_loss previously
        #             print("Stock exit due to stop loss hit at price: ", close)
        #             self.used_api.place_sell_order(self.curr_pair)  # Close the position
        #             self.run = False  # Close the loop
        #
        #         elif self.monitoring_stock[self.curr_pair]['base_price'] < close and \
        #                 self.monitoring_stock[self.curr_pair][
        #                     'curr_price'] < close:  # If current price is greater than target point hit price and previous price
        #             curr_sl = cal_trail_sl(price=close, percent=self.trail_stop_loss, side=0)  # Calculate new stop loss
        #             self.monitoring_stock[self.curr_pair]['curr_price'] = close  # Update current price
        #             self.monitoring_stock[self.curr_pair]['curr_sl'] = curr_sl  # Update stop loss as well
        #             print("Updated sl :{}:: At price :{}".format(curr_sl, close))
        #
        #         else:  # Else update price only
        #             self.monitoring_stock[self.curr_pair]['curr_price'] = close
        #
        #     elif self.monitoring_stock[self.curr_pair]['side'] == 1:  # If it is SELL side
        #
        #         if self.monitoring_stock[self.curr_pair][
        #             'curr_sl'] <= close:  # As it's sell side if current price is greater than calculated stop_loss previously
        #             print("Stock exit due to stop loss hit at price: ", close)
        #             self.used_api.place_sell_order(self.curr_pair)  # Close the position
        #             self.run = False  # Terminate main loop
        #
        #         elif self.monitoring_stock[self.curr_pair]['base_price'] > close and \
        #                 self.monitoring_stock[self.curr_pair][
        #                     'curr_price'] > close:  # If current price is lower than target point price and previously updated price
        #             curr_sl = cal_trail_sl(price=close, percent=self.trail_stop_loss,
        #                                    side=1)  # Calculate new stop loss for updated price
        #             self.monitoring_stock[self.curr_pair]['curr_price'] = close  # Update current price
        #             self.monitoring_stock[self.curr_pair]['curr_sl'] = curr_sl  # Update current stop loss price
        #             print("Updated sl :{}:: At price :{}".format(curr_sl, close))
        #
        #         else:  # Update price only
        #             self.monitoring_stock[self.curr_pair]['curr_price'] = close

    # def start_kline_socket(self, pair):
    #     """
    #     This function updates price for the coin using unicorn-binance library
    #     :param pair: Current pair
    #     :return: nothing
    #     """
    #     bwm = BinanceWebSocketApiManager(exchange="binance.com-futures")
    #     bwm.create_stream(channels=['kline_1m'], markets=[pair])
    #     while self.run:
    #         stream = bwm.pop_stream_data_from_stream_buffer()
    #         if stream:
    #             jsonstream = json.loads(stream)
    #             data = jsonstream.get('data')
    #             if data:
    #                 self.update_stock(float(data['k']['c']))  # Whenever we get data update the pair status


def start_trade():
    symbols = ['BTC', 'BNB', 'SOL', 'SHIB', 'BCH', 'ETH']
    # symbols_full = ['XBTUSDTM', 'BNBUSDTM', 'SOLUSDTM', 'SHIBUSDTM', 'BCHUSDTM', 'ETHUSDTM']
    spot_signals = {
        'BTC': 'btc_binance_spot',
        'BNB': 'bnb_binance_spot',
        'SOL': 'sol_binance_spot',
        'SHIB': 'shib_binance_spot',
        'BCH': 'bch_binance_spot',
        'ETH': 'eth_binance_spot'
    }
    symbols_full = {
        'BTC': 'XBTUSDTM',
        'BNB': 'BNBUSDTM',
        'SOL': 'SOLUSDTM',
        'SHIB': 'SHIBUSDTM',
        'BCH': 'BCHUSDTM',
        'ETH': 'ETHUSDTM'
    }
    perp_signals = {
        'BTC': 'btc_binance_perp',
        'BNB': 'bnb_binance_perp',
        'SOL': 'sol_binance_perp',
        'SHIB': 'shib_binance_perp',
        'BCH': 'bch_binance_perp',
        'ETH': 'eth_binance_perp'
    }
    # Get signals data
    url_signal = 'http://127.0.0.1:80/signaltest'
    data = {'api_key': 'u2:(vyaVDU6%N*rH'}
    proc = Process()
    while True:
        time.sleep(1)
        # if len(proc.watch_stock[symbols_full[symbol]]) != 0:
        if proc.symbol_full in proc.watch_stock:
            # url = 'http://127.0.0.1:5000/candlesticklimit'
            # data = {'api_key': 'u2:(vyaVDU6%N*rH', 'symbol': 'BTC'}
            # x = requests.post(url, json=data)
            # result = json.loads(x.text)
            kucoin_client_market = Market()
            price_close_0 = float(kucoin_client_market.get_ticker(symbol=proc.symbol_full)['price'])
            proc.update_stock(price_close_0)
            time.sleep(5)
            print("-----------------------------------------------------------------------------------------------")
        else:
            x_signal = requests.post(url_signal, json=data)
            print(x_signal.reason)
            # Check if request has returned data successfully
            if x_signal.reason == "OK":
                result = json.loads(x_signal.text)
                print("======================================================")
                print(x_signal.text)
                print("======================================================")
                result_signal = result['result']
                print("Checking for signals BTC")
                # print("Result: ", result)
                # print("Available signals:")
                # Check if signals are available
                print(result_signal)
                if proc.symbol_spot_signal in result_signal and proc.symbol_perp_signal in result_signal:

                    print("Spot: ", int(result_signal[proc.symbol_spot_signal]))
                    print("Perp: ", int(result_signal[proc.symbol_perp_signal]))
                    # Check for buy signal
                    if int(result_signal[proc.symbol_spot_signal]) > 0 and int(
                            result_signal[proc.symbol_perp_signal]) > 0:
                        # Get open interest and ls ratio and price data
                        url = 'http://127.0.0.1:80/candlesticklimit'
                        data = {'api_key': 'u2:(vyaVDU6%N*rH', 'symbol': proc.symbol}
                        x = requests.post(url, json=data)
                        result = json.loads(x.text)
                        open_interest_0 = float(result[0]['open_interest']['close'][:-1])
                        open_interest_9 = float(result[9]['open_interest']['close'][:-1])
                        ls_ratio_0 = float(result[0]['ls_ratio'])
                        ls_ratio_9 = float(result[9]['ls_ratio'])
                        price_close_0 = float(result[0]['price']['close'])
                        price_close_9 = float(result[9]['price']['close'])

                        print("ls: ", ls_ratio_0, "    ", ls_ratio_9)
                        print("oi: ", open_interest_0, "    ", open_interest_9)
                        print("price: ", price_close_0, "    ", price_close_9)

                        if price_close_0 > price_close_9 and open_interest_0 > open_interest_9 and ls_ratio_0 < ls_ratio_9:
                            print("Executing buy position 1")
                            proc.trigger(leverage=20, side=0, pair=proc.symbol_full, acc_margin=25,
                                         platform=3)
                        elif price_close_0 < price_close_9 and open_interest_0 < open_interest_9 and ls_ratio_0 > ls_ratio_9:
                            print("Executing buy position 2")
                            proc.trigger(leverage=20, side=0, pair=proc.symbol_full, acc_margin=25,
                                         platform=3)

                    # Check for sell signal
                    elif int(result_signal[proc.symbol_spot_signal]) < 0 and int(
                            result_signal[proc.symbol_spot_signal]) < 0:
                        # Get open interest and ls ratio and price data
                        url = 'http://127.0.0.1:80/candlesticklimit'
                        data = {'api_key': 'u2:(vyaVDU6%N*rH', 'symbol': proc.symbol}
                        x = requests.post(url, json=data)
                        result = json.loads(x.text)
                        print(result)
                        print(len(result))
                        open_interest_0 = float(result[0]['open_interest']['close'][:-1])
                        open_interest_9 = float(result[9]['open_interest']['close'][:-1])
                        ls_ratio_0 = float(result[0]['ls_ratio'])
                        ls_ratio_9 = float(result[9]['ls_ratio'])
                        price_close_0 = float(result[0]['price']['close'])
                        price_close_9 = float(result[9]['price']['close'])

                        print("ls: ", ls_ratio_0, "    ", ls_ratio_9)
                        print("oi: ", open_interest_0, "    ", open_interest_9)
                        print("price: ", price_close_0, "    ", price_close_9)

                        if price_close_0 > price_close_9 and open_interest_0 > open_interest_9 and ls_ratio_0 < ls_ratio_9:
                            print("Executing sell position")
                            proc.trigger(leverage=proc.leverage, side=0, pair=proc.symbol_full, acc_margin=25,
                                         platform=3)
                        elif price_close_0 < price_close_9 and open_interest_0 < open_interest_9 and ls_ratio_0 > ls_ratio_9:
                            print("Executing sell position")
                            proc.trigger(leverage=proc.leverage, side=0, pair=proc.symbol_full, acc_margin=25,
                                         platform=3)


if __name__ == '__main__':
    """
    This is entry function for program, Basic Python
    """
    # proc = Process()  # Creating class object
    # # This is to demo single trade....It'll go under trigger function
    # proc.trigger(leverage=proc.leverage, side=0, pair="ETHUSDTM", acc_margin=25, acc_id=None,
    #              platform=3)  # Change leverage, margin, pair according to your needs
    # while len(proc.watch_stock) != 0:
    #     print("Checking exit conditions...")
    #     # url = 'http://127.0.0.1:5000/candlesticklimit'
    #     # data = {'api_key': 'u2:(vyaVDU6%N*rH', 'symbol': 'BTC'}
    #     # x = requests.post(url, json=data)
    #     # result = json.loads(x.text)
    #     # price_close_0 = float(result[0]['price']['close'])
    #     # print("price: ", price_close_0)
    #     kucoin_client_market = Market()
    #     # kucoin_client_market.get_ticker(symbol == 'ETHUSDTM')['price']
    #     price_close_0 = kucoin_client_market.get_ticker(symbol='ETHUSDTM')['price']
    #     print("price: ", price_close_0)
    #     proc.update_stock(float(price_close_0), "ETH")
    #     print('---------------------------------------------------------------------------------')
    #     time.sleep(1)

    start_trade()

    """
    Notes:--
    Change Config test with your api-key and secrete
    """
    # todo database connections and info, logging...
