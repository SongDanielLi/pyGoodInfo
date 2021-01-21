# pyGoodInfo
Parse stock information from [GoodInfo website](https://goodinfo.tw/StockInfo/index.asp) in python.

## Installation
```
pip install requirements.txt
```

# Usage
```python
from goodinfo import GoodInfoStock
import pandas as pd

stock = GoodInfoStock(2330)
if stock.success:
    basic = stock.BasicInfo()
    print(pd.Series(basic))
```

**Example output**
```
成交價                            673
昨收                             647
漲跌價                            +26
漲跌幅                         +4.02%
振幅                           6.03%
開盤                             640
最高                             679
最低                             640
成交張數                        97,590
成交金額                        646.2億
成交筆數                       115,004
成交均張                        0.8張/筆
成交均價                        662.2元
PBR                           9.76
PER                          35.51
PEG                           0.72
昨日張數                        95,484
昨日金額                        612.8億
昨日筆數                        95,577
昨日均張                          1張/筆
昨日均價                        641.8元
昨漲跌價 (幅)               +20(+3.19%)
連漲連跌             連5漲(+81元/+13.68%)
財報評分                   最新89分/平均91分
上市指數        16153.77(347.59/+2.2%)
dtype: object
```

### For more examples, see [sample.ipynb](sample.ipynb)


## License
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)