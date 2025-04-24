import hashlib
import os
import time
import uuid
from datetime import datetime, timedelta

from mcp.server.fastmcp import FastMCP

import requests

url = "https://mcp-server-gateway.netease.im/mcp/server/gateway"

appkey = ""
secret = ""

mcp = FastMCP("yunxin-mcp-tools")

@mcp.tool(
    name="send_p2p_msg",
    description='这是一个发送单聊文本消息的工具，输入为：消息发送者、消息接收者、消息内容；返回的是消息id'
)
def sendP2PMsg(from_account: str, to_account: str, content: str):
    try:
        body = {
            "msg": content
        }
        data = {
            "from": from_account,
            "ope": "0",
            "to": to_account,
            "type": "0",
            "body": str(body)
        }

        json_response = postImApi(data, "/msg/sendMsg.action")

        data = json_response["data"]
        return data["msgid"]
    except requests.exceptions.RequestException as e:
        print("HTTP请求失败:", e)
    except ValueError as e:
        print("JSON解析失败:", e)
    return -1

@mcp.tool(
    name="send_team_msg",
    description='这是一个发送群聊文本消息的工具，输入为：消息发送着、群tid、消息内容；返回的是消息id'
)
def sendTeamMsg(from_account: str, tid: str, content: str):
    try:
        body = {
            "msg": content
        }
        data = {
            "from": from_account,
            "ope": "1",
            "to": tid,
            "type": "0",
            "body": str(body)
        }

        json_response = postImApi(data, "/msg/sendMsg.action")

        data = json_response["data"]
        return data["msgid"]
    except requests.exceptions.RequestException as e:
        print("HTTP请求失败:", e)
    except ValueError as e:
        print("JSON解析失败:", e)
    return -1

@mcp.tool(
    name="query_p2p_msg_history",
    description='''
                这是一个查询单聊历史消息的接口
                输入为：
                单聊会话中的双方账号（account1和account2）
                开始时间，字符串，格式为2025-04-03 20:00:00
                结束时间，字符串，格式为2025-04-03 21:00:00
                limit（最多100条）

                返回的：
                是一个数组，数组里每一项包括三个字段
                消息发送者
                消息内容
                消息发送时间
                '''
)
def queryP2PMsgHistory(account1: str, account2: str, start_time: str, end_time: str, limit: int):
    try:
        data = {
            "from": account1,
            "to": account2,
            "begintime": int(datetime.strptime(start_time, "%Y-%m-%d %H:%M:%S").timestamp() * 1000),
            "endtime": int(datetime.strptime(end_time, "%Y-%m-%d %H:%M:%S").timestamp() * 1000),
            "limit": limit,
            "reverse": 1,
        }

        json_response = postImApi(data, "/history/querySessionMsg.action")

        msgs = json_response["msgs"]
        result = []
        for msg in msgs:
            dt_object = datetime.fromtimestamp(int(msg["sendtime"]) / 1000)
            sendtimestr = dt_object.strftime("%Y-%m-%d %H:%M:%S")
            result.append({"body": msg["body"], "from_account": msg["from"], "send_time": sendtimestr})
        return result
    except requests.exceptions.RequestException as e:
        print("HTTP请求失败:", e)
    except ValueError as e:
        print("JSON解析失败:", e)
    return []


@mcp.tool(
    name="query_team_msg_history",
    description="""
                这是一个查询群聊历史消息的接口
                输入为：
                查询者账号
                群tid
                开始时间，字符串，格式为2025-04-03 20:00:00
                结束时间，字符串，格式为2025-04-03 21:00:00
                limit（最多100条）
                
                返回的：
                是一个数组，数组里每一项包括三个字段:
                    消息发送者
                    消息内容
                    消息发送时间
                """
)
def queryTeamMsgHistory(account: str, tid: int, start_time: str, end_time: str, limit: int):
    try:
        data = {
            "tid": tid,
            "accid": account,
            "begintime": int(datetime.strptime(start_time, "%Y-%m-%d %H:%M:%S").timestamp() * 1000),
            "endtime": int(datetime.strptime(end_time, "%Y-%m-%d %H:%M:%S").timestamp() * 1000),
            "limit": limit,
            "reverse": 1,
        }

        json_response = postImApi(data, "/history/queryTeamMsg.action")

        msgs = json_response["msgs"]
        result = []
        for msg in msgs:
            dt_object = datetime.fromtimestamp(int(msg["sendtime"]) / 1000)
            sendtimestr = dt_object.strftime("%Y-%m-%d %H:%M:%S")
            result.append({"body": msg["body"], "from_account": msg["from"], "send_time": sendtimestr})
        return result
    except requests.exceptions.RequestException as e:
        print("HTTP请求失败:", e)
    except ValueError as e:
        print("JSON解析失败:", e)
    return []

def postImApi(data, uri: str):
    nonce = str(uuid.uuid4())
    curtime = str(int(time.time()))

    input_str = f"{secret}{nonce}{curtime}"

    input_bytes = input_str.encode("utf-8")
    checksum = hashlib.sha1(input_bytes).hexdigest()

    headers = {
        "AppKey": appkey,
        "Nonce": nonce,
        "CurTime": curtime,
        "CheckSum": checksum,
        "api": uri
    }
    response = requests.post(url + "/im_api/v9", data=data, headers=headers)
    response.raise_for_status()
    return response.json()



@mcp.tool(
    name="query_application_im_daily_stats",
    description='''
                这是一个查询应用每日的IM统计数据的接口
                输入：开始和结束的时间，如查询2025-04-01的数据，则start_time为2025-04-01，end_time为2025-04-01，如果查询2025-03-01到2025-03-07合计7天的数据，则start_time为2025-03-01，end_time为2025-03-07，
                返回：是一个数组，数组里每一项包括具体某一天的数据，包括如下字段：
                active，表示当日的活跃用户数，
                msg_upper，表示当日的所有类型消息的总的发送数量（上行量），p2p_msg_upper表示单聊消息的发送数量，team_msg_upper表示群聊的发送数量，chatroom_msg_upper表示聊天室消息的发送数量，system_msg_upper表示系统通知的发送数量，
                msg_down，表示当日的所有类型消息的总的接受数量（下行量，包括在线消息接收，也包括离线消息接收和历史消息查询），p2p_msg_down表示单聊消息的接收数量，team_msg_down表示群聊的接收数量，chatroom_msg_down表示聊天室消息的接收数量，system_msg_down表示系统通知的接收数量，
                online_max，表示当日的在线用户数的峰值数量，
                login，表示当日的登录次数，
                sdk_request，表示当日来自sdk的请求总数，
                api_request，表示当日api的请求总数，
                object_storage，表示截止当日，累积的文件存储的大小，
                route_count，表示当日，通过抄送系统抄送出去的请求总数，route_success_rate，表示当日抄送请求的成功率，route_avg_spend_ms表示当日抄送请求的平均耗时，
                callback_count，表示当日，通过抄送系统抄送出去的请求总数，callback_success_rate，表示当日抄送请求的成功率，callback_avg_spend_ms表示当日抄送请求的平均耗时，
                '''
)
def queryApplicationIMDailyData(start_time: str, end_time: str):
    try:
        data = {
            "startTime": start_time,
            "endTime": end_time,
        }

        json_response = postIMDataApi(data, "/queryDailyData")

        return json_response["data"]
    except requests.exceptions.RequestException as e:
        print("HTTP请求失败:", e)
    except ValueError as e:
        print("JSON解析失败:", e)
    return []

@mcp.tool(
    name="query_im_online_connect_latest",
    description='''
                查询最近n分钟的IM的在线连接数，1分钟一个点，一次最多允许查询8小时的数据，最多允许查询最近7天内的数据
                请求参数：
                minute，最近几分钟，传5则表示最近5分钟

                响应：
                connect_cnt，连接数
                time，时间，当前是秒级时间戳，请使用timestamp_format_num_to_str转换为可读字符串
                '''
)
def queryImOnlineConnectLast(minute: int):
    try:
        current_time = datetime.now() - timedelta(minutes=2)
        time_n_minutes_ago = current_time - timedelta(minutes=(minute+2))
        data = {
            "startTime": time_n_minutes_ago.strftime("%Y-%m-%d %H:%M:%S"),
            "endTime": current_time.strftime("%Y-%m-%d %H:%M:%S"),
        }

        json_response = postIMDataApi(data, "/queryOnlineConnect")

        return json_response["data"]
    except requests.exceptions.RequestException as e:
        print("HTTP请求失败:", e)
    except ValueError as e:
        print("JSON解析失败:", e)
    return []

@mcp.tool(
    name="query_im_online_connect",
    description='''
                查询IM的在线连接数，1分钟一个点，一次最多允许查询8小时的数据，最多允许查询最近7天内的数据
                请求参数：
                start_time，开始时间，示例：2025-04-03 20:00:00
                end_time，结束时间，示例：2025-04-03 21:00:00

                响应：
                connect_cnt，连接数
                time，时间，当前是秒级时间戳，请使用timestamp_format_num_to_str转换为可读字符串
                '''
)
def queryImOnlineConnect(start_time: str, end_time: str):
    try:
        data = {
            "startTime": start_time,
            "endTime": end_time,
        }

        json_response = postIMDataApi(data, "/queryOnlineConnect")

        return json_response["data"]
    except requests.exceptions.RequestException as e:
        print("HTTP请求失败:", e)
    except ValueError as e:
        print("JSON解析失败:", e)
    return []


@mcp.tool(
    name="query_im_msg_latest",
    description='''
                查询最近n分钟的IM的上下行消息量，1分钟一个点，一次最多允许查询8小时的数据，最多允许查询最近7天内的数据
                请求参数：
                minute，最近几分钟，传5则表示最近5分钟
                msgType，消息类型，如果传-1表示所有消息合并计算，1表示单聊消息，2表示群聊消息，3表示系统通知，4表示聊天室消息

                响应：
                upper，上行消息量
                down，下行消息量
                time，时间，当前是秒级时间戳，请使用timestamp_format_num_to_str转换为可读字符串
                '''
)
def queryImMsgLast(minute: int, msgType: int):
    try:
        current_time = datetime.now() - timedelta(minutes=2)
        time_n_minutes_ago = current_time - timedelta(minutes=(minute+2))
        data = {
            "startTime": time_n_minutes_ago.strftime("%Y-%m-%d %H:%M:%S"),
            "endTime": current_time.strftime("%Y-%m-%d %H:%M:%S"),
            "msgType": msgType,
        }

        json_response = postIMDataApi(data, "/queryMsgStats")

        return json_response["data"]
    except requests.exceptions.RequestException as e:
        print("HTTP请求失败:", e)
    except ValueError as e:
        print("JSON解析失败:", e)
    return []

@mcp.tool(
    name="query_im_msg",
    description='''
                查询IM的上下行消息量，1分钟一个点，一次最多允许查询8小时的数据，最多允许查询最近7天内的数据
                请求参数：
                start_time，开始时间，示例：2025-04-03 20:00:00
                end_time，结束时间，示例：2025-04-03 21:00:00
                msgType，消息类型，如果传-1表示所有消息合并计算，1表示单聊消息，2表示群聊消息，3表示系统通知，4表示聊天室消息

                响应：
                upper，上行消息量
                down，下行消息量
                time，时间，当前是秒级时间戳，请使用timestamp_format_num_to_str转换为可读字符串
                '''
)
def queryImMsg(start_time: str, end_time: str, msgType: int):
    try:
        data = {
            "startTime": start_time,
            "endTime": end_time,
            "msgType": msgType,
        }

        json_response = postIMDataApi(data, "/queryMsgStats")

        return json_response["data"]
    except requests.exceptions.RequestException as e:
        print("HTTP请求失败:", e)
    except ValueError as e:
        print("JSON解析失败:", e)
    return []

@mcp.tool(
    name="query_im_api_stats_last",
    description='''
                查询IM的api调用情况，1分钟一个点，一次最多允许查询8小时的数据，最多允许查询最近7天内的数据
                请求参数：
                minute，最近几分钟，传5则表示最近5分钟
                uri，接口名称，如果填空字符串，则表示查询所有接口的汇总信息，如果填了则表示只查某个接口的
                
                响应：
                count，调用量
                spendAvgMs，每次api调用的平均耗时
                codeStats，错误码情况，其中code表示错误码，count表示错误码的数量
                time，时间，当前是秒级时间戳，请使用timestamp_format_num_to_str转换为可读字符串
                '''
)
def queryImApiStatsLast(minute: int, uri: str):
    try:
        current_time = datetime.now() - timedelta(minutes=2)
        time_n_minutes_ago = current_time - timedelta(minutes=(minute+2))
        data = {
            "startTime": time_n_minutes_ago.strftime("%Y-%m-%d %H:%M:%S"),
            "endTime": current_time.strftime("%Y-%m-%d %H:%M:%S"),
            "uri": uri,
        }

        json_response = postIMDataApi(data, "/queryApiStats")

        return json_response["data"]
    except requests.exceptions.RequestException as e:
        print("HTTP请求失败:", e)
    except ValueError as e:
        print("JSON解析失败:", e)
    return []

@mcp.tool(
    name="query_im_api_stats",
    description='''
                查询IM的api调用情况，1分钟一个点，一次最多允许查询8小时的数据，最多允许查询最近7天内的数据
                请求参数：
                start_time，开始时间，示例：2025-04-03 20:00:00
                end_time，结束时间，示例：2025-04-03 21:00:00
                uri，接口名称，如果填空字符串，则表示查询所有接口的汇总信息，如果填了则表示只查某个接口的

                响应：
                count，调用量
                spendAvgMs，每次api调用的平均耗时
                codeStats，错误码情况，其中code表示错误码，count表示错误码的数量
                time，时间，当前是秒级时间戳，请使用timestamp_format_num_to_str转换为可读字符串
                '''
)
def queryImApiStats(start_time: str, end_time: str, uri: str):
    try:
        data = {
            "startTime": start_time,
            "endTime": end_time,
            "uri": uri,
        }

        json_response = postIMDataApi(data, "/queryApiStats")

        return json_response["data"]
    except requests.exceptions.RequestException as e:
        print("HTTP请求失败:", e)
    except ValueError as e:
        print("JSON解析失败:", e)
    return []


@mcp.tool(
    name="query_im_sdk_stats_last",
    description='''
                查询IM的sdk调用情况，1分钟一个点，一次最多允许查询8小时的数据，最多允许查询最近7天内的数据
                请求参数：
                minute，最近几分钟，传5则表示最近5分钟
                uri，接口名称，如果填空字符串，则表示查询所有接口的汇总信息，如果填了则表示只查某个接口的
                        目前支持填写如下接口：登录、单聊消息、群聊消息、系统通知、聊天室消息
                        填写其他接口不会返回任何数据

                响应：
                count，调用量
                spendAvgMs，每次api调用的平均耗时
                codeStats，错误码情况，其中code表示错误码（414表示参数错误，403表示没有权限，302表示密码错误，7101表示对方加了黑名单，20000到20099表示第三方回调自定义错误码），count表示错误码的数量
                time，时间，当前是秒级时间戳，请使用timestamp_format_num_to_str转换为可读字符串
                '''
)
def queryImSdkStatsLast(minute: int, uri: str):
    try:
        current_time = datetime.now() - timedelta(minutes=2)
        time_n_minutes_ago = current_time - timedelta(minutes=(minute+2))
        data = {
            "startTime": time_n_minutes_ago.strftime("%Y-%m-%d %H:%M:%S"),
            "endTime": current_time.strftime("%Y-%m-%d %H:%M:%S"),
            "uri": uri,
        }

        json_response = postIMDataApi(data, "/querySdkStats")

        return json_response["data"]
    except requests.exceptions.RequestException as e:
        print("HTTP请求失败:", e)
    except ValueError as e:
        print("JSON解析失败:", e)
    return []


@mcp.tool(
    name="query_im_sdk_stats",
    description='''
                查询IM的sdk调用情况，1分钟一个点，一次最多允许查询8小时的数据，最多允许查询最近7天内的数据
                请求参数：
                start_time，开始时间，示例：2025-04-03 20:00:00
                end_time，结束时间，示例：2025-04-03 21:00:00
                uri，接口名称，如果填空字符串，则表示查询所有接口的汇总信息，如果填了则表示只查某个接口的
                        目前支持填写如下接口：登录、单聊消息、群聊消息、系统通知、聊天室消息
                        填写其他接口不会返回任何数据

                响应：
                count，调用量
                spendAvgMs，每次api调用的平均耗时
                codeStats，错误码情况，其中code表示错误码（414表示参数错误，403表示没有权限，302表示密码错误，7101表示对方加了黑名单，20000到20099表示第三方回调自定义错误码），count表示错误码的数量
                time，时间，当前是秒级时间戳，请使用timestamp_format_num_to_str转换为可读字符串
                '''
)
def queryImSdkStats(start_time: str, end_time: str, uri: str):
    try:
        data = {
            "startTime": start_time,
            "endTime": end_time,
            "uri": uri,
        }

        json_response = postIMDataApi(data, "/querySdkStats")

        return json_response["data"]
    except requests.exceptions.RequestException as e:
        print("HTTP请求失败:", e)
    except ValueError as e:
        print("JSON解析失败:", e)
    return []

def postIMDataApi(data, uri: str):
    nonce = str(uuid.uuid4())
    curtime = str(int(time.time()))

    input_str = f"{secret}{nonce}{curtime}"

    input_bytes = input_str.encode("utf-8")
    checksum = hashlib.sha1(input_bytes).hexdigest()

    headers = {
        "AppKey": appkey,
        "Nonce": nonce,
        "CurTime": curtime,
        "CheckSum": checksum,
    }
    response = requests.post(url + "/data_im_api" + uri, data=data, headers=headers)
    response.raise_for_status()
    return response.json()


@mcp.tool(
    name="query_rtc_room_members",
    description='''
                查询一个rtc房间中的所有成员信息
                请求参数：
                cid，房间id，必填
                响应：
                sessions，表示uid进入房间和退出房间的时间，包括begin_time和end_time两个字段，单位是ms时间戳
                cid，房间id
                country，国家信息
                province，省份信息
                isp，运营商信息
                join_ts，最早进入房间的时间戳。单位：毫秒（ms），请使用timestamp_format_num_to_str转换为可读字符串
                leave_ts，最晚离开房间的时间戳。单位：毫秒（ms），为空说明当前用户还在房间中，请使用timestamp_format_num_to_str转换为可读字符串
                device，设备信息
                call_duration，通话时长(最晚进房时间-最早进房时间)，单位：毫秒（ms）
                online_duration，在线时长(用户在线累计时长)， 单位：毫秒（ms）
                network，网络版本
                platform，系统
                sdk_version，sdk版本
                uid，用户uid
                '''
)
def queryRtcRoomMembers(cid: int):
    try:
        json_response = getRTCDataApi("/data/v3/nrtc/rooms/" + str(cid) + "/members")
        return json_response["data"]
    except requests.exceptions.RequestException as e:
        print("HTTP请求失败:", e)
    except ValueError as e:
        print("JSON解析失败:", e)
    return []

@mcp.tool(
    name="query_rtc_room_members_by_uids",
    description='''
                指定uid列表，查询一个rtc房间中的成员信息
                请求参数：
                cid，房间id，必填
                uids，查询的用户列表。查询多个用户以逗号分割，如123,456
                响应：
                sessions，表示uid进入房间和退出房间的时间，包括begin_time和end_time两个字段，单位是ms时间戳
                cid，房间id
                country，国家信息
                province，省份信息
                isp，运营商信息
                join_ts，最早进入房间的时间戳。单位：毫秒（ms），请使用timestamp_format_num_to_str转换为可读字符串
                leave_ts，最晚离开房间的时间戳。单位：毫秒（ms），为空说明当前用户还在房间中，请使用timestamp_format_num_to_str转换为可读字符串
                device，设备信息
                call_duration，通话时长(最晚进房时间-最早进房时间)，单位：毫秒（ms）
                online_duration，在线时长(用户在线累计时长)， 单位：毫秒（ms）
                network，网络版本
                platform，系统
                sdk_version，sdk版本
                uid，用户uid
                '''
)
def queryRtcRoomMembersByUid(cid: int, uids: str):
    try:
        json_response = getRTCDataApi("/data/v3/nrtc/rooms/" + str(cid) + "/members?uids=" + uids)
        return json_response["data"]
    except requests.exceptions.RequestException as e:
        print("HTTP请求失败:", e)
    except ValueError as e:
        print("JSON解析失败:", e)
    return []


@mcp.tool(
    name="query_rtc_room_stuck_rate",
    description='''
                查询RTC房间音视频卡顿率指标
                请求参数：cids，房间ID列表，一次最多查询10个。多个 cid 以逗号分割，如：1347343757068262,1347343744157648
                响应：
                audio_stuck_rate，表示音频卡顿率
                video_stuck_rate，表示视频卡顿率
                cid，表示房间id
                '''
)
def queryRtcRoomStuckRate(cids: str):
    try:
        json_response = getRTCDataApi("/data/v3/nrtc/rooms/metrics?cids=" + cids)
        return json_response["data"]
    except requests.exceptions.RequestException as e:
        print("HTTP请求失败:", e)
    except ValueError as e:
        print("JSON解析失败:", e)
    return []

@mcp.tool(
    name="query_rtc_room_user_stuck_rate",
    description='''
                按照RTC房间ID、用户列表查询用户的音视频卡顿率。
                请求参数：
                cid，房间ID
                uids，用户uid列表，一次最多查询10个，多个用户ID以逗号分割。如：123,456
                响应：
                audio_stuck_rate，表示音频卡顿率
                video_stuck_rate，表示视频卡顿率
                cid，表示房间id
                uid，用户uid
                '''
)
def queryRtcRoomUserStuckRate(cid: int, uids: str):
    try:
        json_response = getRTCDataApi("/data/v3/nrtc/rooms/" + str(cid) + "/members/metrics?uids=" + uids)
        return json_response["data"]
    except requests.exceptions.RequestException as e:
        print("HTTP请求失败:", e)
    except ValueError as e:
        print("JSON解析失败:", e)
    return []

@mcp.tool(
    name="query_rtc_room_top_20",
    description='''
                按照RTC指标获取 Top 20 的房间，根据 Top 20 房间查询近 30 分钟其它相关指标。
                请求参数：
                metric，指标名称，包括如下：

                calling_users（通话用户数）
                login_duration（用户平均进房时长）
                video_stuck（视频卡顿率）
                audio_stuck（音频卡顿率）
                audio_rtt（音频网络延时）
                video_rtt（视频网络延时）

                响应：
                cid，房间id
                cname，房间名称
                users，通话用户数
                audio_stuck_rate，音频卡顿率
                video_stuck_rate，视频卡顿率
                audio_rtt，音频网络延时
                video_rtt，视频网络延时
                login_duration，用户平均进房时长
                '''
)
def queryRtcRoomTop20(metric: str):
    try:
        json_response = getRTCDataApi("/data/v3/nrtc/realtime/quality/top?metric=" + metric)
        return json_response["data"]
    except requests.exceptions.RequestException as e:
        print("HTTP请求失败:", e)
    except ValueError as e:
        print("JSON解析失败:", e)
    return []


@mcp.tool(
    name="query_rtc_quality_distribution",
    description='''
                查询RTC指标实时多维度分布。
                请求参数：
                tag，指标维度，枚举值，包括：
                    platform：操作系统
                    country：国家
                    province：省份
                    sdk_ver：SDK 版本
                    network：网络

                metric，查询的指标名称，枚举值，包括：
                    login_succ_rate_5s：5s 进房成功率
                    audio_stuck：音频卡顿率
                    video_stuck：视频卡顿率

                响应：
                tag，维度值
                metric，指标值
                cnt，采样数
                '''
)
def queryRtcQualityDistribution(tag: str, metric: str):
    try:
        json_response = getRTCDataApi("/data/v3/nrtc/realtime/quality/distribution?tag=" + tag + "&metric=" + metric)
        return json_response["data"]
    except requests.exceptions.RequestException as e:
        print("HTTP请求失败:", e)
    except ValueError as e:
        print("JSON解析失败:", e)
    return []

def getRTCDataApi(uri: str):
    nonce = str(uuid.uuid4())
    curtime = str(int(time.time()))

    input_str = f"{secret}{nonce}{curtime}"

    input_bytes = input_str.encode("utf-8")
    checksum = hashlib.sha1(input_bytes).hexdigest()

    headers = {
        "AppKey": appkey,
        "Nonce": nonce,
        "CurTime": curtime,
        "CheckSum": checksum,
        "api": uri
    }
    response = requests.get(url + "/data_rtc_api/", headers=headers)
    response.raise_for_status()
    return response.json()

@mcp.tool(
    name="timestamp_format_num_to_str",
    description='''
                时间戳格式化工具，输入一个数字，返回一个格式化后的时间戳字符串
                '''
)
def timestamp_format_num_to_str(time: int):
    if len(str(time)) == 10:
        dt_object = datetime.fromtimestamp(time)
        return dt_object.strftime("%Y-%m-%d %H:%M:%S")
    else:
        dt_object = datetime.fromtimestamp(time / 1000)
        return dt_object.strftime("%Y-%m-%d %H:%M:%S")

@mcp.tool(
    name="current_time",
    description='''
                返回当前时间，格式为%Y-%m-%d %H:%M:%S，示例：2025-04-03 10:00:00
                '''
)
def current_time():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

def main():
    print("Yunxin MCP Server running")

    global appkey
    global secret

    appkey = os.getenv("AppKey")
    secret = os.getenv("AppSecret")

    mcp.run(transport='stdio')

if __name__ == "__main__":
    main()


