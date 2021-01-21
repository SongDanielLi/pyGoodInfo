import requests
from bs4 import BeautifulSoup
import re
import pandas as pd

baseurl = 'https://goodinfo.tw/StockInfo/StockDetail.asp?STOCK_ID={sid}'
headers = {'User-Agent':'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 \
        (KHTML, like Gecko) Chrome/70.0.3538.77 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
        'host': 'goodinfo.tw',
        'origin': 'https://goodinfo.tw',
        'referer': 'https://goodinfo.tw/StockInfo/StockDetail.asp?STOCK_ID=0050'}


class GoodInfoStock():
    def __init__(self, stockid):
        self.stockid = stockid
        url = baseurl.format(sid = stockid)
        # request session
        sess = requests.session()
        response = sess.get(url, headers = headers)
        response.encoding = 'utf-8'
        self.success = False
        if response.status_code == 200:
            self.__soup = BeautifulSoup(response.text, 'html.parser')
            self.success = True
        
    # Basic price info
    def BasicInfo(self):
        basictbls = self.__soup.find_all('table', attrs = {'class':'solid_1_padding_3_1_tbl'})
        content = table2list(basictbls[0])
        # to dict
        basic_dict = {}
        for i in range(2, 8, 2):
            for j in range(len(content[i])):
                basic_dict[content[i][j]] = "".join(content[i+1][j].split())

        score = content[8][0]
        score = "".join(score.split())
        scores = re.split(r'連漲連跌:|財報評分:|上市指數:', score)
        basic_dict['連漲連跌'] = scores[1]
        basic_dict['財報評分'] = scores[2]
        basic_dict['上市指數'] = scores[3]
        return basic_dict
    
    '''
    個股最新消息
    output: [list] with title and link
    '''
    def News(self):
        tbls = self.__soup.find_all('table', attrs = {'class':'solid_1_padding_4_2_tbl'})
        newstbl = tbls[0].find_all('table', attrs = {'class':'none_tbl'})
        trs = newstbl[0].find_all('tr')
        # Link example
        # https://www.ettoday.net/news/20200109/1621811.htm?from=rss
        # OpenLink.asp?LINK=https%3A%2F%2Fwww%2Eettoday%2Enet%2Fnews%2F20200109%2F1621811%2Ehtm%3Ffrom%3Drss
        transMap = {'OpenLink.asp?LINK=': '',
            '%3A%2F%2F': '://',
            '%2F': '/',
            '%2E': '.',
            '%3F': '?',
            '%3D': '='
        }
        
        allnews = []
        for tr in trs:
            tds = tr.select('td > a[href]')
            td = tds[0]
            title = td.text
            link = td['href']
            if 'OpenLink' in link:
                link = replaceWithMap(link, transMap)
            else:
                link = 'https://goodinfo.tw/StockInfo/' + link
            meta = {'title': title, 'link': link}
            allnews.append(meta)
        return allnews
    
    # 公司基本資料
    def CompanyInfo(self):
        tbls = self.__soup.find_all('table', attrs = {'class':'solid_1_padding_4_4_tbl'})
        # many tables named solid_1_padding_4_4_tbl
        # find first td called 名稱
        infoTbls = None
        for tbl in tbls:
            trs = tbl.find_all('tr')
            tds = trs[0].find_all('td')
            if(tds[0].get_text() == '名稱'):
                infoTbls = tbl
        if infoTbls:
            content = table2list(infoTbls)

        info = {}
        for i in range(len(content)-2):
            for j in range(0, len(content[i]), 2):
                info[content[i][j]] = content[i][j+1]
        info[content[len(content)-2][0]] = content[len(content)-1][0]
        return info

    '''
    output:
        risk: 風險係數 [dict]
        df: [dataframe] with (累計漲跌價/累計漲跌幅/區間振幅/成交量週轉率/均線落點/均線乖離率)
    '''
    def KLineInfo(self):
        tbls = self.__soup.find_all('table', attrs = {'class':'solid_1_padding_4_2_tbl'})
        tbl = findFirstTd(tbls, '風險係數')
        risk = {}
        if tbl:
            content = table2list(tbl)
            for i in range(1, len(content[0])):
                risk[content[0][i]] = content[1][i-1]

        tbls = self.__soup.find_all('table', attrs = {'class':'solid_1_padding_4_0_tbl'})
        tbl = findFirstTd(tbls, '統計區間')
        df = None
        if tbl:
            df = pd.read_html(str(tbl))[0]
            df.rename(columns=df.iloc[0], inplace=True)
            df = df[1:]
            df.set_index('統計區間', inplace=True)
            df.head()
        return risk, df
    
    '''
    法人買賣情況
    output:
        dataframe: index -> 外資, 投信, 自營商 
    '''
    def InstitutionalInvestors(self):
        tbls = self.__soup.find_all('table', attrs = {'class':'solid_1_padding_4_4_tbl'})
        tbl = findFirstTd(tbls, '買進(張)')
        df = None
        if tbl is None: return df
        df = pd.read_html(str(tbl))[0]
        return setDataframe(df)
    
    '''
    融資融券
    融資: margin trading
    融券: short selling
    output: 
        dict:
        key in 融資 {買進, 賣出, 現償, 餘額, 增減, 使用率, 資券互抵, 資券當沖}
        key in 融券 {買進, 賣出, 現償, 餘額, 增減, 使用率, 券資比}
    '''
    def MarginTradingShortSale(self):
        tbls = self.__soup.find_all('table', attrs = {'class':'solid_1_padding_4_0_tbl'})
        tbl = findFirstTd(tbls, '融資')
        info = {'融資': {}, '融券': {}}
        if tbl is None: return info
        content = table2list(tbl)
        md = {}
        for i in range(1, len(content[0])):
            md[content[0][i]] = content[1][i-1]
        tmp = content[2][0].split('連續增減日數:')[1]
        md['連續增減日數'] = "".join(tmp.split())
        info['融資'] = md

        ss = {}
        for i in range(1, len(content[3])):
            ss[content[3][i]] = content[4][i-1]
        tmp = content[5][0].split('連續增減日數:')[1]
        ss['連續增減日數'] = "".join(tmp.split())
        info['融券'] = ss
        return info
    
    '''
    現股當沖
    output: [dataframe]
        Example:
                    成交張數	買進金額	賣出金額	損益金額				
        張/金額(元)	3,298張	    167,887萬	168,070萬	+183萬
        當沖率	    8.12%	    8.11%	    8.12%	    NaN
    '''
    def DayTrading(self):
        tbls = self.__soup.find_all('table', attrs = {'class':'solid_1_padding_4_0_tbl'})
        tbl = findFirstTd(tbls, '成交張數')
        df = None
        if tbl is None: return df
        df = pd.read_html(str(tbl))[0]
        return setDataframe(df)

    '''
    股利
    output: [dataframe]
    '''
    def Dividend(self):
        tbls = self.__soup.find_all('table', attrs = {'class':'solid_1_padding_4_0_tbl', 'id': 'FINANCE_DIVIDEND'})
        df = pd.read_html(str(tbls[0]))[0]
        df = df[2:-1]
        return setDataframe(df)


    '''
    月營收
    output: [dataframe]
        rank_df: 歷史排名
        df: 月營收(年/月)
    '''
    def MonthReport(self):
        # rank in history
        tbls = self.__soup.find_all('table', attrs = {'class':'solid_1_padding_4_1_tbl'})
        rank_df = None
        # TODO:
        if tbls:
            rank_df = pd.read_html(str(tbls[0]))[0]
            rank_df.rename(columns= rank_df.iloc[0], inplace=True)
            rank_df = rank_df[1:]

        tbls = self.__soup.find_all('table', attrs = {'class':'solid_1_padding_4_2_tbl'})
        tbl = findFirstTd(tbls, '年/月')
        df = None
        if tbl:
            df = pd.read_html(str(tbl))[0]
            h1 = df.iloc[0]
            h2 = df.iloc[1]
            df = df[2:]
            df.set_index(df.columns[0], inplace=True)
            df.columns = pd.MultiIndex.from_tuples(list(zip(h1[1:], h2[1:])))
        return rank_df, df

    '''
    獲利狀況
    output: [dataframe]
    '''
    def Profit(self):
        tbls = self.__soup.find_all('table', attrs = {'class':'solid_1_padding_4_0_tbl'})
        tbl = findSecondTd(tbls, '營收')
        df = None
        if tbl is None: return df
        df = pd.read_html(str(tbl))[0]
        return setDataframe(df)

    '''
    資產負債
    output: [dataframe]
    '''
    def AssetLiabilities(self):
        tbls = self.__soup.find_all('table', attrs = {'class':'solid_1_padding_4_0_tbl'})
        tbl = findSecondTd(tbls, '佔 總 資 產')
        df = None
        if tbl is None: return df
        df = pd.read_html(str(tbl))[0]
        return setDataframe(df[1:])

    '''
    現金流量
    '''
    def CashFlow(self):
        tbls = self.__soup.find_all('table', attrs = {'class':'solid_1_padding_4_0_tbl'})
        tbl = findSecondTd(tbls, '營業活動')
        df = None
        if tbl is None: return df
        df = pd.read_html(str(tbl))[0]
        return setDataframe(df)





#%%
def table2list(tbl):
    trs=tbl.find_all('tr')
    content = []
    for tr in trs:
        tds = tr.find_all('td')
        row = [td.get_text() for td in tds]
        content.append(row)
    return content

def replaceWithMap(text, transMap):
    return re.sub('({})'.format('|'.join(map(re.escape, transMap.keys()))), lambda m: transMap[m.group()], text)

def getKLineURL(stockid, period = 'w'):
    # 'https://goodinfo.tw/StockInfo/image/StockPrice/PRICE_WEEK_0050.gif?'
    # DATE / WEEK / MONTH / QUAR / YEAR
    # 日線 / 周線  /  月線 / 季線  / 年線
    if period == 'd':
        ptype = 'DATE'
    elif period == 'w':
        ptype = 'WEEK'
    elif period == 'm':
        ptype = 'MONTH'
    elif period == 'q':
        ptype = 'QUAR'
    elif period == 'y':
        ptype = 'YEAR'
    else:
        ptype = 'WEEK'
    return 'https://goodinfo.tw/StockInfo/image/StockPrice/PRICE_{ptype}_{sid}.gif?'.format(ptype=ptype, sid = stockid)

def findFirstTd(tbls, firstText):
    for tbl in tbls:
        trs = tbl.find_all('tr')
        tds = trs[0].find_all('td')
        td = "".join(tds[0].get_text().split())
        td = td if len(td) > 0 else tds[1].get_text()
        if firstText in td:
            return tbl
    return None

def findSecondTd(tbls, secondText):
    for tbl in tbls:
        trs = tbl.find_all('tr')
        tds = trs[0].find_all('td')
        if len(tds) < 2: continue
        td = tds[1].get_text()
        if secondText in td:
            return tbl
    return None 

def setDataframe(df):
    df.rename(columns= df.iloc[0], inplace=True)
    df = df[1:]
    df.set_index(df.columns[0], inplace=True)
    return df