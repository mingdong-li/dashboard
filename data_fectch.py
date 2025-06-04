import requests

from solders.keypair import Keypair
from solders.pubkey import Pubkey
from solana.rpc.async_api import AsyncClient
from anchorpy import Provider, Wallet
from driftpy.drift_client import DriftClient
from driftpy.math.spot_balance import calculate_borrow_rate, calculate_deposit_rate
from driftpy.constants.spot_markets import mainnet_spot_market_configs
from driftpy.accounts import get_spot_market_account, get_perp_market_account
import datetime
import pandas as pd


def get_market_index_by_symbol(symbol: str):
    for cf in mainnet_spot_market_configs:
        if cf.symbol == symbol:
            return cf.market_index
    raise ValueError(f"Symbol {symbol} not found in spot market configs.")


async def fetch_rate_cur(btc_name:str):
    # 连接 Solana RPC（建议使用付费节点，如 QuickNode）
    kp = Keypair()  # random wallet
    wallet = Wallet(kp)
    
    connection = AsyncClient("https://api.mainnet-beta.solana.com")
    drift_client = DriftClient(connection,wallet)

    # drift_user = DriftUser(drift_client)


    try:
        # get sol market info
        # sol_market_index = 0
        # sol_market = await get_perp_market_account(drift_client.program, sol_market_index)
        
        # token_market_pubkey = Pubkey("J1toso1uCk3RLmjorhTtrVwY9HJ7X8V9yYac6Y7kGCPn")  # 替换为目标 Token 的市场地址
        # market = await drift_client.get_spot_market_account(token_market_pubkey)

        # get spot market info using symbol
        spot_market_index = get_market_index_by_symbol(btc_name)
        my_market = await get_spot_market_account(drift_client.program, spot_market_index)

        # 怎么看到底是多少的decimal
        cur_deposit_rate = calculate_deposit_rate(my_market)/(10**6)
        cur_borrow_rate = calculate_borrow_rate(my_market)/(10**6)   

        # Calculate APY for deposit and borrow rates (assuming rates are per annum in decimal form)
        cur_deposit_apy = (1 + cur_deposit_rate / 365) ** 365 - 1
        cur_borrow_apy = (1 + cur_borrow_rate / 365) ** 365 - 1

        # now = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        now = (datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(hours=8)).strftime('%Y-%m-%d %H:%M')

        cur_deposit = pd.DataFrame([{"date": now, "deposit_rate":cur_deposit_rate ,"deposit_apy": cur_deposit_apy}])
        cur_borrow = pd.DataFrame([{"date": now, "borrow_rate": cur_borrow_rate,"borrow_apy": cur_borrow_apy}])

        return cur_deposit, cur_borrow

    except Exception as e:
        print(f"An error occurred: {e}")




def fetch_rate_history(token_name='SOL', day_fetch=30):
    rates =  {'deposit': [], 'borrow': []}  # 示例数据
    for x in ['deposit', 'borrow']:
        print(f"Fetching {x} rate history...")

        url = "https://data.api.drift.trade/stats/{name}/rateHistory/{mode}".format(name=token_name, mode=x) 

        response = requests.get(url)        
        if response.status_code == 200:
            data = response.json()
            # df = pd.DataFrame(data)

            for entry in data['rates'][max(-day_fetch, -len(data['rates'])):]:
                # 计算每日复利的 APY
                
                apy = (1 + float(entry[1]) / 365) ** 365 - 1

                format = '%Y-%m-%d %H:%M:%S'
                # value为传入的值为时间戳(整形)，如：1332888820
                
                # dt = datetime.datetime.fromtimestamp(entry[0]).strftime('%Y-%m-%d %H:%M:%S')
                dt = (datetime.datetime.utcfromtimestamp(entry[0]) + datetime.timedelta(hours=8)).strftime('%Y-%m-%d %H:%M')

                ## 经过localtime转换后变成
                ## time.struct_time(tm_year=2012, tm_mon=3, tm_mday=28, tm_hour=6, tm_min=53, tm_sec=40, tm_wday=2, tm_yday=88, tm_isdst=0)
                # 最后再经过strftime函数转换为正常日期格式。

                rates[x].append({
                    "date": dt,
                    x: float(entry[1]),
                    x+"_apy": apy  # 有些数据可能没有 borrowRate
                })

            print(f"{x.capitalize()} rate history fetched successfully.")

                
        else:
            print("Error:", response.status_code)

    deposit_rates = pd.DataFrame(rates['deposit'])
    borrow_rates = pd.DataFrame(rates['borrow'])

    # res = pd.concat([deposit_rates, borrow_rates], axis=1, sort=False)
    # res = pd.merge(deposit_rates, borrow_rates, on='date', how='outer')
    # res.dropna(axis=0,subset = ["deposit_apy", "borrow_apy"], how='any')
    return deposit_rates, borrow_rates
