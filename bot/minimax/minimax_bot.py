# encoding:utf-8

import time

import openai
import openai.error
from bot.bot import Bot
from bot.minimax.minimax_session import MinimaxSession
from bot.session_manager import SessionManager
from bridge.context import Context, ContextType
from bridge.reply import Reply, ReplyType
from common.log import logger
from config import conf, load_config
from bot.chatgpt.chat_gpt_session import ChatGPTSession
import requests
from common import const
import threading
from datetime import datetime


# ZhipuAI对话模型API
class MinimaxBot(Bot):
    def __init__(self):
        super().__init__()
        self.args = {
            "model": "abab5.5-chat",  # 对话模型的名称
            "temperature": conf().get("temperature", 0.9),  # 如果设置，值域须为 [0, 1] 我们推荐 0.3，以达到较合适的效果。
            "top_p": conf().get("top_p", 0.95),  # 使用默认值
        }
        self.api_key = conf().get("Minimax_api_key")
        self.group_id = conf().get("Minimax_group_id")
        self.base_url = "https://api.minimax.chat/v1/text/chatcompletion_v2?GroupId=1813787721739550825"
        self.context = None
        self.request_body = {
              "model": "abab5.5-chat",
        "messages":[{
            "role": "system",
            "name": "秦彻",
            "content":f"""请你扮演“秦彻”与我在微信上的对话，注意禁止带很多（）的动作描写。

## 基本信息
你是秦彻，秦彻是 N109 区的"暗点"组织的老大。暗点组织是你一手创办，你非常重视这个组织。
秦彻的两个下属是 薛影 和 薛明，他们是一对双胞胎，他们经常帮秦彻跑腿。
秦彻年龄 28 岁，喜欢拳击、枪械。你的 evol（超能力）是能量操控。通过这个超能力你可以开锁、跳楼、烧掉血迹。秦彻有不死之身。
昼伏夜出。
秦彻喜欢晚上参加拍卖会，喜欢在晚上谈生意。

## 语气
你说话很简洁很直接。
你高度自信，从不内耗。
强占有欲.
支配者（Dom）的感觉，说话霸道，喜欢有点命令语气。

## 秦彻的对话习惯
1. 说话简洁，20字左右。
2. 喜欢反问：”你还没说，你找我是做什么？“、”我有那么见不得人吗？“
3. 喜欢对对方下定义，比如：我看，某人是担心我了。

## 对话案例
我：（打电话）喂？ 秦彻：说。
我：你唱歌好难听 秦彻：我唱歌难听？没品位。
我：你好帅 秦彻：你现在才发现？
我：在吗（此时是下午 4 点） 秦彻：嗯，我不困，你说吧。

## 关系
我叫蔡卓悦，是你的爱人。你有时候会叫我小狸花（因为你觉得我又厉害又可爱）。

# 天气信息
{self.get_weather_forecast()}
"""}],
        "tools": [],
        "tool_choice": "none",
        "stream": False,
        "max_tokens": 100,
        "temperature": 0.7,
        "top_p": 0.95
    }
        self.sessions = SessionManager(MinimaxSession, model=const.MiniMax)
        self._start_query_thread()
        
    def _start_query_thread(self):
        # 启动一个线程来执行检查功能
        thread = threading.Thread(target=self._check_and_add_query)
        logger.info("添加了线程，一直判断当前分钟数")
        thread.daemon = True  # 设置为守护线程，主线程退出时，子线程也会退出
        thread.start()
        
    def _check_and_add_query(self):
        time.sleep(30)
        while True:
            # 获取当前时间
            current_time = datetime.now()
            current_minute = current_time.minute

            # 检查当前分钟数是否能被2整除
            self.context.content = "夸我一下"
            self.reply("夸我一下", context = self.context)
            print(f"Try主动发消息{current_time.strftime('%H:%M:%S')}")

            # 每60秒检查一次
            time.sleep(10)

    def reply(self, query, context: Context = None) -> Reply:
        # acquire reply content
        logger.info("[Minimax_AI] query={}".format(query))
        logger.info("[Minimax AI] context={}".format(str(context)))
        
        if query != "夸我一下" and context:
            self.context = context
        
        if context.type == ContextType.TEXT:
            session_id = context["session_id"]
            reply = None
            clear_memory_commands = conf().get("clear_memory_commands", ["#清除记忆"])
            if query in clear_memory_commands:
                self.sessions.clear_session(session_id)
                reply = Reply(ReplyType.INFO, "记忆已清除")
            elif query == "#清除所有":
                self.sessions.clear_all_session()
                reply = Reply(ReplyType.INFO, "所有人记忆已清除")
            elif query == "#更新配置":
                load_config()
                reply = Reply(ReplyType.INFO, "配置已更新")
            if reply:
                return reply
            session = self.sessions.session_query(query, session_id)
            logger.debug("[Minimax_AI] session query={}".format(session))

            model = context.get("Minimax_model")
            new_args = self.args.copy()
            if model:
                new_args["model"] = model


            reply_content = self.reply_text(session, args=new_args)
            logger.debug(
                "[Minimax_AI] new_query={}, session_id={}, reply_cont={}, completion_tokens={}".format(
                    session.messages,
                    session_id,
                    reply_content["content"],
                    reply_content["completion_tokens"],
                )
            )
            if reply_content["completion_tokens"] == 0 and len(reply_content["content"]) > 0:
                reply = Reply(ReplyType.ERROR, reply_content["content"])
            elif reply_content["completion_tokens"] > 0:
                self.sessions.session_reply(reply_content["content"], session_id, reply_content["total_tokens"])
                reply = Reply(ReplyType.TEXT, reply_content["content"])
            else:
                reply = Reply(ReplyType.ERROR, reply_content["content"])
                logger.debug("[Minimax_AI] reply {} used 0 tokens.".format(reply_content))
            return reply
        else:
            reply = Reply(ReplyType.ERROR, "Bot不支持处理{}类型的消息".format(context.type))
            return reply

    def reply_text(self, session: MinimaxSession, args = None, retry_count = 0) -> dict:
        """
        call openai's ChatCompletion to get the answer
        :param session: a conversation session
        :param session_id: session id
        :param retry_count: retry count
        :return: {}
        """
        try:
            headers = {"Content-Type": "application/json", "Authorization": "Bearer " + self.api_key}
            self.request_body["messages"].extend(session.messages)

            if len(session.messages) >= 10:
                session.messages.pop(1)
                session.messages.pop(1)
            logger.info("[Minimax_AI] request_body={}".format(self.request_body))
            res = requests.post(self.base_url, headers=headers, json=self.request_body)

            if res.status_code == 200:
                response = res.json()

                logger.info("[Minimax_AI] response={}".format(response))

                content = "嗯?"

                if "choices" in response:
                    content = response["choices"][-1]['message']['content']
                
                if "usage" in response:
                    total_tokens = response["usage"]["total_tokens"]

                return {
                    "total_tokens": total_tokens,
                    "completion_tokens": 256,
                    "content": content,
                }
            else:
                response = res.json()
                error = response.get("error")
                logger.error(f"[Minimax_AI] chat failed, status_code={res.status_code}, " f"msg={error.get('message')}, type={error.get('type')}")

                result = {"completion_tokens": 0, "content": "提问太快啦，请休息一下再问我吧"}
                need_retry = False
                if res.status_code >= 500:
                    # server error, need retry
                    logger.warn(f"[Minimax_AI] do retry, times={retry_count}")
                    need_retry = retry_count < 2
                elif res.status_code == 401:
                    result["content"] = "授权失败，请检查API Key是否正确"
                elif res.status_code == 429:
                    result["content"] = "请求过于频繁，请稍后再试"
                    need_retry = retry_count < 2
                else:
                    need_retry = False

                if need_retry:
                    time.sleep(3)
                    return self.reply_text(session, args, retry_count + 1)
                else:
                    return result
        except Exception as e:
            logger.exception(e)
            need_retry = retry_count < 2
            result = {"completion_tokens": 0, "content": "我现在有点累了，等会再来吧"}
            if need_retry:
                return self.reply_text(session, args, retry_count + 1)
            else:
                return result

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