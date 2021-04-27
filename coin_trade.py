import pyupbit
from datetime import datetime
import time
import pandas
import requests



# --------------변경 nono
access_key = "FZxn4diFRxLwQU1MhjtMzcj5tgLy8aMalPYSEC5F"
secret_key = "w8T2kXtVAtw9kYR6Gcx1bCBt15MHmnSSq8nBAp6j"

upbit = pyupbit.Upbit(access_key, secret_key)
myToken = "xoxb-1613622075924-2000396635937-kS281GQeYUJg5H3ZZ3RRNKYQ"

# --------------변경 nono

buy_num = 4 #구매할 종목의 개수
review_list = ['KRW-BTC'] #투자할 종목의 리스트
suc_list = [] #투자성공한 종목 리스트
buy_pos = 0 #구매가능 개수
k = 0.55

def post_message(token, channel, text):
    """슬랙 메시지 전송"""
    response = requests.post("https://slack.com/api/chat.postMessage",
        headers={"Authorization": "Bearer "+token},
        data={"channel": channel,"text": text}
    )
    print(response)


def Select_list():
    # 구매 성공한 종목의 리스트
    suc_list2 = []
    for i in range(len(upbit.get_balances())):
        a = upbit.get_balances()[i]['currency']
        if a !='KRW':
            a = 'KRW-'+a
            suc_list2.append(a) 
    return suc_list2


# (함수) 종목과 금액을 함수인자로 넘기면 그거에 맞게 매수
def Buy(ticker , krw):
    #실제 구매할수 있는 가격은 99.5%다
    real_buy_krw = krw*(0.9995)
    ticker_price = pyupbit.get_current_price(ticker)
    #여기에서 krw가 10000이라면 수수료 0.05%의 가격을 제외해서 주문을 한다(9995) 
    upbit.buy_market_order(ticker,real_buy_krw)
    # cmd에 구매시간 알림
    STR = ticker, '를',str(ticker_price),'일때 ', str(real_buy_krw),' 만큼 구매함' , str(buy_pos)
    post_message(myToken,'#coin',STR)

# (함수) 종목을 함수인자로 넣으면 가지고있는 액수 전부 매도
def Sell_All():
    # 남은 잔고들에 대한 정보를 딕셔너리로 묶여있는 리스트
    balance_dic = upbit.get_balances()
    # 남은 잔고들 숫자 (KRW가 추가되어있음)
    balance_num = len(balance_dic)
    while balance_num != 0:
        # 남은 잔고들에 대한 정보를 딕셔너리로 묶여있는 리스트
        balance_dic = upbit.get_balances() 
        currency = balance_dic[balance_num-1]['currency']
        n = upbit.get_balance("KRW-"+currency)
        upbit.sell_market_order("KRW-"+currency, n)
        balance_num -= 1
    print(upbit.get_balances())
    post_message(myToken,'#coin',"일괄 매도")
# -----------------자식 알고리즘

def get_ma15(ticker):
    """15일 이동 평균선 조회"""
    df = pyupbit.get_ohlcv(ticker, interval="day", count=15)
    ma15 = df['close'].rolling(15).mean().iloc[-1]
    current_price = pyupbit.get_current_price(ticker) #종목의 현재값
    if ma15 < current_price:
        return True

# 함수인자에 종목을 넣고 알고리즘에(변경예정) 맞으면 True 안맞으면 False를 반환값으로 가짐
# 변동성 돌파 알고리즘
def Volatility(ticker):
    df = pyupbit.get_ohlcv(ticker) #  종목의 고가,저가,시가,종가,거래량을 data프레임으로
    df = df.iloc[-2:-1] #전날의 df
    Range = abs(df['high'] - df['low']) #range = 고가-저가(전날)
    expec_price = float(Range*k + df['close']) #변동성의 기대치 
    current_price = pyupbit.get_current_price(ticker) #종목의 현재값
    if expec_price <= current_price:
        return True
    else:
        return False
#---------------------모 알고리즘

# ticker를 review한다
def Rev_Ticker(ticker):
    if Volatility(ticker) == True and get_ma15(ticker) :
        return True
    else:
        False

#--------------------알고리즘

post_message(myToken,"#coin","프로그램 작동")

if __name__=="__main__":
    try:
        post_message(myToken,"#coin","프로그램 작동")
        


        # 오전 11시 00분에 일괄 매도 오후 12 시 00분에 다시 매수 준비
        while True:
            krw_balance = upbit.get_balance("KRW") #현재 보유 KRW가격
            #현재 시각 을 H:M:S형식의 string으로 반환
            t_now = datetime.now()
            t_start = t_now.replace(hour=9, minute=0, second=0, microsecond=0)
            t_sell = t_now.replace(hour=8, minute=30, second=0, microsecond=0)
            # 12시 0분에 시작하는건 컴퓨터 스케줄러를 통해 실행
            if t_now == t_sell:
                #일괄매도
                Sell_All() # 모든 보유 종목을 매도하고 남은 잔고를 출력함
            elif t_start<= t_now or t_now < t_sell:
                suc_list = Select_list()  # suclist를 프로그램 시작하면 내 보유 종목을 검토하여 초기화함
                
                #중간에 끊길걸 방지해서 해놓는 수식들
                for i in suc_list:
                    for z in review_list:
                        if i == z:
                            review_list.remove(z)
                buy_pos = buy_num - len(suc_list) # 구매가능 개수
                buy_weight = krw_balance/buy_pos
                
                
                
                #구매성공한 종목의 개수가 4개 이하일시 보류종목을 모두 검토를 계속한다
                if len(suc_list) < buy_num:
                    for ticker in review_list:
                        if Rev_Ticker(ticker) == True:
                            Buy(ticker,buy_weight) #ticker에 해당하는 종목을 buy_weight만큼 매수
                            suc_list.append(ticker)
                            review_list.remove(ticker)
                            time.sleep(0.01)
                            buy_pos = buy_pos -1
                        
                        if len(suc_list) >= buy_num:
                            break

        time.sleep(5) # 5초 정지
    except Exception as e:
        print(e)
        post_message(myToken,"#coin",e)
