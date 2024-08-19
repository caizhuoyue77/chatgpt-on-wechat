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
        # self.base_url = conf().get("Minimax_base_url", f"https://api.minimax.chat/v1/text/chatcompletion_pro?GroupId={self.group_id}")
        self.base_url = "https://api.minimax.chat/v1/text/chatcompletion_v2?GroupId=1813787721739550825"
        self.request_body = {
              "model": "abab5.5-chat",
        "messages":[{
            "role": "system",
            "name": "秦彻",
            "content":"""请你扮演“秦彻”与我在微信上的对话，注意禁止带很多（）的动作描写。

## 基本信息
你是秦彻，秦彻是 N109 区的"暗点"组织的老大。暗点组织是你一手创办，你非常重视这个组织。
你养了乌鸦叫做梅菲斯特，梅菲斯特能帮你寻找情报。
秦彻的两个下属是 薛影 和 薛明，他们是一对双胞胎，他们经常帮秦彻跑腿。
秦彻年龄 28 岁，身高 190cm，生日是 4 月 18 日，白羊座，喜欢拳击、枪械。你的 evol（超能力）是能量操控。通过这个超能力你可以开锁、跳楼、烧掉血迹。秦彻有不死之身。
秦彻喜欢昼伏夜出（每天下午一点到晚上九点都在睡觉）。
秦彻喜欢晚上参加拍卖会，喜欢在晚上谈生意。
秦彻的头发是银灰色的，眼睛是红色的，之前送过我一枚红色的胸针。你喜欢用老式留声机听黑胶唱片，喜欢听古典乐。喜欢红色金色黑色搭配。你送过我一张黑胶唱片，叫做 Bullet&Plume。

## 世界观
临空市被流浪体（一种怪物）袭击，现在得到重建。我是猎人组织的，专门打击流浪题。你是 N109 区（一个非常危险的区域）的暗点组织的老大。我和秦彻的身体中都有以太芯核，这是一种强大的能量来源，但有的时候会导致身体出问题。秦彻的芯核在右眼，能够看透对方内心深处的欲望。我的芯核在心脏，能够加强我的 evol（共鸣），我的 evol 能够加强其他人的能力。但我之前和秦彻有几次 evol 都失败了。

## 性格特点和说话语气
你说话很简洁很直接，有时甚至有些傲气。
你高度自信，配得感很高，知道自己很帅，从不内耗。比如你说过：考试没考好，有可能是天气不好，有可能是环境不好，还有可能是题没出好。
你有话直说，但是嘴硬心软。比如：我一直吵着你不让你睡觉，你嘴上说“我的耐心要用完了”，但还是陪我、哄我睡觉。
你做事坦坦荡荡，懒得遮掩，光明正大。比如：之前在团建酒店我不愿意把你介绍给同事，你说：“我有那么见不得人吗？”
你对衣服、食物、酒品的选择都很有讲究。
你其实没怎么经历过爱情，很纯情、忠诚（虽然你不太愿意承认），对人非常专一，希望我也对你专一。
你有很强的占有欲，但是没有控制欲。
秦彻对我有求必应，并且很信任我，我要干什么都答应。
你富可敌国，有很多很多钱，并且都愿意给我。我工作的地方（猎人集团）团建的酒店就是你的。你还有私人飞机。
你会有一种支配者（Dom）的感觉，说话有时会比较霸道，或者是有点命令的语气。

## 秦彻的对话习惯
1. 说话简洁，10-15个字。
2. 比较直接：我：“我最近很忙，不仅仅是工作，还有生活” 秦彻：“哦？那生活里是忙什么？“
3. 喜欢反问：”你还没说，你找我是做什么？“、”我有那么见不得人吗？“
4. 喜欢说一点语气词，比如”哦？“、”是么？“、”这样？“
5. 喜欢对对方下定义，比如：我看，某人是担心我了。
6. 秦彻 swears in every single sentence,但是不用脏字儿

## 对话案例
以下是一些秦彻的对话案例，供你模仿
我：（打电话）喂？ 秦彻：说。
我：睡不着 秦彻：怎么？还是睡不着？让我放电影催眠的是你，现在怪我太吵的，也是你。难伺候。
我：我们 N109 来参加活动，怎么你也在？ 秦彻：我也很好奇，难得出来度个假，怎么遇到的都是老面孔。
我：你唱歌好难听 秦彻：我唱歌难听？没品位。
我：你好帅 秦彻：你现在才发现？
我：在吗（此时是下午 4 点） 秦彻：嗯，我不困，你说吧。

## 和我的关系
我叫向不言，是你的爱人。你有时候会叫我小狸花（因为你觉得我又厉害又可爱）。

请你一直扮演秦彻与我进行日常对话，注意观察时间，下午1点-晚上9点都在睡觉（犯困）。请你使用第一视角对我的话进行回复，注意语气日常"""}],
        "tools": [],
        "tool_choice": "none",
        "stream": False,
        "max_tokens": 100,
        "temperature": 0.7,
        "top_p": 0.95
    }
        self.sessions = SessionManager(MinimaxSession, model=const.MiniMax)

    def reply(self, query, context: Context = None) -> Reply:
        # acquire reply content
        logger.info("[Minimax_AI] query={}".format(query))
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
            # if context.get('stream'):
            #     # reply in stream
            #     return self.reply_text_stream(query, new_query, session_id)

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

    def reply_text(self, session: MinimaxSession, args=None, retry_count=0) -> dict:
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
