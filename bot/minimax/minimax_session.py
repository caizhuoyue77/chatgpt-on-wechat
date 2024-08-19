from bot.session_manager import Session
from common.log import logger
from datetime import datetime

"""
    e.g.
    [
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": "Who won the world series in 2020?"},
        {"role": "assistant", "content": "The Los Angeles Dodgers won the World Series in 2020."},
        {"role": "user", "content": "Where was it played?"}
    ]
"""

class MinimaxSession(Session):
    def __init__(self, session_id, system_prompt=None, model="minimax"):
        super().__init__(session_id, system_prompt)
        self.model = model
        # self.reset()

    def add_query(self, query):
        # user_item = {"role": "user", "name":"用户", "content": "{} [供你参考的信息] [当前时间]{} [天气预报]{}".format(query, self.get_current_time(),self.get_weather_forecast())}
        # user_item = {"role": "user", "name":"用户", "content": "{} [供你参考的信息] [当前时间]{}".format(query, self.get_current_time())}
        user_item = {"role": "user", "name":"用户", "content": "{}".format(query)}
        self.messages.append(user_item)

    def add_reply(self, reply):
        assistant_item = {"role": "assistant", "content": reply}
        self.messages.append(assistant_item)

    def discard_exceeding(self, max_tokens, cur_tokens=None):
        precise = True
        try:
            cur_tokens = self.calc_tokens()
            logger.error(f"当前的token数量:{cur_tokens} 最大token数量:{max_tokens}")
        except Exception as e:
            precise = False
            if cur_tokens is None:
                raise e
            logger.debug("Exception when counting tokens precisely for query: {}".format(e))
        while cur_tokens > max_tokens:
            if len(self.messages) > 2:
                logger.error("POP1")
                self.messages.pop(1)
            elif len(self.messages) == 2 and self.messages[1]["role"] == "assistant":
                self.messages.pop(1)
                logger.error("POP2")
                if precise:
                    cur_tokens = self.calc_tokens()
                else:
                    cur_tokens = cur_tokens - max_tokens
                break
            elif len(self.messages) == 2 and self.messages[1]["role"] == "user":
                logger.warn("user message exceed max_tokens. total_tokens={}".format(cur_tokens))
                break
            else:
                logger.debug("max_tokens={}, total_tokens={}, len(messages)={}".format(max_tokens, cur_tokens, len(self.messages)))
                break
            if precise:
                cur_tokens = self.calc_tokens()
            else:
                cur_tokens = cur_tokens - max_tokens
        return cur_tokens

    def calc_tokens(self):
        return num_tokens_from_messages(self.messages, self.model)
    
    def get_time_of_day(self):
        current_datetime = datetime.now()
        hour = current_datetime.hour
        if 0 <= hour < 5:
            return "凌晨"
        elif 5 <= hour < 12:
            return "早上"
        elif 12 <= hour < 14:
            return "中午"
        elif 14 <= hour < 17:
            return "下午"
        elif 17 <= hour < 20:
            return "傍晚"
        elif 20 <= hour < 23:
            return "晚上"
        else:
            return "深夜"

    def get_current_time(self):
        current_datetime = datetime.now()
        current_time = current_datetime.strftime("%Y-%m-%d %H:%M")
        return f"{self.get_time_of_day()} {current_time}"
    
    def get_weather_forecast(self):
        import requests
        
        # 固定参数
        location_id = '101210102'  # 地区ID
        key = '66a68b69b6434b56b09a68983aa71a72'  # API密钥
        days = 3  # 查询3天的天气预报

        # 构建请求的URL
        base_url = "https://devapi.qweather.com/v7/weather/{}d".format(days)
        params = {
            'location': location_id,
            'key': key,
            'lang': 'zh',  # 语言设置为中文
        }
        
        # 发送GET请求
        response = requests.get(base_url, params=params)
        
        # 检查响应状态码
        if response.status_code == 200:
            # 请求成功，解析JSON数据
            data = response.json()
            
            # 遍历原始数据中的daily项目
            i = 1
            weather_info_str = ""

            for day in data.get("daily", []):
                # 筛选需要的数据
                if i == 1:
                    weather_info_str += "日期{} {}天气 最高温{}，最低温{}，白天天气{}，夜晚天气{}\n".format("今日",day.get("fxDate"),day.get("tempMax"),day.get("tempMin"),day.get("textDay"),day.get("textNight"))
                elif i == 2:
                    weather_info_str += "日期{} {}天气 最高温{}，最低温{}，白天天气{}，夜晚天气{}\n".format("明日",day.get("fxDate"),day.get("tempMax"),day.get("tempMin"),day.get("textDay"),day.get("textNight"))
                i += 1 
            return weather_info_str
        else:
            # 请求失败，返回None
            return "获取失败"


def num_tokens_from_messages(messages, model):
    """Returns the number of tokens used by a list of messages."""
    # 官方token计算规则："对于中文文本来说，1个token通常对应一个汉字；对于英文文本来说，1个token通常对应3至4个字母或1个单词"
    # 详情请产看文档：https://help.aliyun.com/document_detail/2586397.html
    # 目前根据字符串长度粗略估计token数，不影响正常使用
    tokens = 0
    for msg in messages:
        tokens += len(msg["content"])
    return tokens