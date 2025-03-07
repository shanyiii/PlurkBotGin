from plurk_oauth import PlurkAPI
from db_manager import db_addData, db_readData, db_removeData
from common import BAN_LIST, GIN_RANDOM_RESPONSES, GIN_FEEL_LIKE, GIN_WHAT_TO_EAT
import urllib.request
import re, json, random, time

APP_KEY = "Y1zrw4VROaDF"
APP_SECRET = "B5P3tzU5cugiJPt03MU0Fq1uzlCeom5x"
ACCESS_TOKEN = "w6UnyVxVLSmF"
ACCESS_TOKEN_SECRET = "2fdwHDWVPa3FTFmQdDYYQPfupwoqoX0S"

plurk = PlurkAPI(APP_KEY, APP_SECRET)
plurk.authorize(ACCESS_TOKEN, ACCESS_TOKEN_SECRET)

comet = plurk.callAPI('/APP/Realtime/getUserChannel')
comet_channel = comet.get('comet_server') + "&new_offset=%d"
jsonp_re = re.compile(r'CometChannel.scriptCallback\((.+)\);\s*');
new_offset = -1

# 阿金的uid=17637392
category_list = ["服裝", "互動"]
friend_list = list()
admin_list = {"16713667": "352533876594842"}

# 認證
def auth():
    plurk.authorize(ACCESS_TOKEN, ACCESS_TOKEN_SECRET)
    comet = plurk.callAPI('/APP/Realtime/getUserChannel')
    try:
        comet_channel = comet.get('comet_server') + "&new_offset=%d"
        jsonp_re = re.compile(r'CometChannel.scriptCallback\((.+)\);\s*');
    except Exception as e:
        print(f"[err]auth:{e}")

# 更新好友清單
def setFriendList():
    try:
        data = plurk.callAPI('/APP/FriendsFans/getCompletion')
        if data is not None:
            for user in data:
                if not user in friend_list:
                    friend_list.append(user)
                    print(f"New friend {user} added!")
    except Exception as e:
        print(f"setFriendList err: {e}")

# 認證+初始化+get data
def initApi():
    auth()
    try:
        plurk.callAPI('/APP/Alerts/addAllAsFriends')
        setFriendList()
        req = urllib.request.urlopen(comet_channel % new_offset, timeout=50)
        rawdata = req.read()
        match = jsonp_re.match(rawdata.decode('ISO-8859-1'))
        return match
    except urllib.error.URLError as e:
        print(f"Plurk API 請求失敗: {e}")
        time.sleep(5)  # 等待 5 秒後重試
    except TimeoutError as e:
        print(f"timeoyt: {e}")
        time.sleep(5)  # 等待 5 秒後重試

    return None

# 回覆
def plurkResponse(pid, bot_content):
    plurk.callAPI('/APP/Responses/responseAdd', {'plurk_id': pid, 'content': bot_content, 'qualifier': ':'})

# 檢查是否在資料庫中
def is_in_db(query):
    data = db_readData(query, True)
    print(f"data in db: {data}")
    if data:
        return True
    else:
        return False

# 把 tags 存到資料庫
def save_tags_to_db(category, options, user_nick_name, pid):
    if category in category_list:
        bot_contents = [f"@{user_nick_name}: 新增結果如下~"]
        for option in options:
            if option == "":
                continue
            if option in BAN_LIST:
                bot_contents.append("阿金抓到了敏感字詞")
                continue
            query = {"$and": [
                {"category": category},
                {"tag": option}
            ]}
            if is_in_db(query):
                print("資料庫已有相同資料")
                bot_contents.append(f"「{option}」已存在，不需要再新增啦！")
            else:
                new_tag = dict()
                new_tag['category'] = category
                new_tag['tag'] = option
                db_addData(new_tag)
                bot_contents.append(f"「{option}」新增成功！")
        bot_content = '\n'.join(bot_contents)
        plurkResponse(pid, bot_content)
    else:
        print("查無分類")
        plurkResponse(pid, f"沒有「{category}」這個分類歐[emo11]")

def start_match(pattern, user_content):
    # 進行匹配
    match = re.match(pattern, user_content)
    if match:
        category = match.group(1)  # 取得兩字詞(服裝、互動)
        options = match.group(2).split("、")  # 取得選項列表
        print("分類:", category)
        print("選項:", options)
        return category, options
    else:
        return None, None

def slotTags(category, num):
    data = db_readData({"category": category}, False)
    all_data = list(data)
    tag_list = [ad['tag'] for ad in all_data]
    slot_result = list()
    random.shuffle(tag_list)
    # print(f"random list: {tag_list}")
    for i in range(0, num):
        slot_result.append(tag_list[i])
        print(f"{i}. 抽到的 tag: {tag_list[i]}")
    return slot_result

def dealContent(pid, user_content, isAdmin, p, user_nick_name):
    print(f"reply plurk id: {pid}\nuser nick name: {user_nick_name}\ncontent: {user_content}")
    print(f"is admin: {isAdmin}")
    # plurkResponse(pid, f"@{user_nick_name}: 阿金寶貝進入新噗文留下一顆心 (heart)")

    # 新增 tags 功能
    if user_content.find("新增") != -1 and user_content.find("@gin_the_golden") != -1:
        # 正則表達式：新增<category>：<tag>、<tag>
        pattern = r"(?:.*[\n\s]*)?新增(\w{2})：(.+)"
        # 進行匹配
        category, options = start_match(pattern, user_content)
        if category is not None and options is not None:
            save_tags_to_db(category, options, user_nick_name, pid)
        else:
            print("re 未匹配成功(格式有誤)")
            plurkResponse(pid, f"@{user_nick_name}: 怎麼怪怪der~是不是格式打錯哩[emo9]")

    # 抽 tags 功能
    elif user_content.find("抽") != -1 and user_content.find("@gin_the_golden") != -1:
        # 正則表達式：新增<category><num>個
        pattern = r"(?:.*[\n\s]*)?抽(\w{2})(\d+)"
        # 進行匹配
        category, number = start_match(pattern, user_content)
        if category is not None and number is not None:
            num = int(number[0])
            if category in category_list:
                if 0 < num <= 10:
                    result = slotTags(category, num)
                    result = '、'.join(result)
                    plurkResponse(pid, f"@{user_nick_name}: 「{category}」{num}抽的抽選結果：\n{result}")
                elif num > 10:
                    plurkResponse(pid, f"@{user_nick_name}: 太貪心辣[emo4]一次最多只能抽10個")
                else:
                    plurkResponse(pid, f"@{user_nick_name}: ┌(。Д。)┐?!![emo10]")
            else:
                print("查無分類")
                plurkResponse(pid, f"沒有「{category}」這個分類歐[emo3]")
        else:
            print("re 未匹配成功(格式有誤)")
            plurkResponse(pid, f"@{user_nick_name}: 怎麼怪怪der~是不是格式打錯哩[emo9]")

    # 檢舉功能
    elif user_content.find("檢舉") != -1 and user_content.find("@gin_the_golden") != -1:
        # 正則表達式：檢舉<category>：<tag>、<tag>、......
        pattern = r"(?:.*[\n\s]*)?檢舉(\w{2})：(.+)"
        category, options = start_match(pattern, user_content)
        if category is not None and options is not None:
            report_contents = [f"@{user_nick_name}: 謝謝您的檢舉，檢舉結果："]
            report_to_admin = list()
            for option in options:
                query = {"$and": [
                    {"category": category},
                    {"tag": option}
                ]}
                if is_in_db(query):
                    report_contents.append(f"「{option}」已受理檢舉")
                    report_to_admin.append(option)
                else:
                    report_contents.append(f"「{option}」並沒有在阿金的腦袋中！")
            report_content = '\n'.join(report_contents)
            report_to_admin = '、'.join(report_to_admin)
            plurkResponse(admin_list['16713667'], f"@yf168px: 收到來自 {user_nick_name} 的檢舉：{report_to_admin}")
            plurkResponse(pid, report_content)
        else:
            print("re 未匹配成功(格式有誤)")
            plurkResponse(pid, f"@{user_nick_name}: 怎麼怪怪der~是不是格式打錯哩[emo9]")
    
    # 刪除 tag 功能(僅限管理員)
    elif user_content.find("刪除") != -1 and isAdmin and user_content.find("@gin_the_golden") != -1:
        pattern = r"(?:.*[\n\s]*)?刪除(\w{2})：(.+)"
        category, options = start_match(pattern, user_content)
        if category is not None and options is not None:
            remove_contents = [f"@{user_nick_name}: 刪除結果："]
            for option in options:
                query = {"$and": [
                    {"category": category},
                    {"tag": option}
                ]}
                if is_in_db(query):
                    db_removeData(query)
                    remove_contents.append(f"「{option}」已刪除")
                else:
                    remove_contents.append(f"「{option}」並沒有在阿金的腦袋中！")
            remove_content = '\n'.join(remove_contents)
            plurkResponse(pid, remove_content)
        else:
            print("re 未匹配成功(格式有誤)")
            plurkResponse(pid, f"@{user_nick_name}: 怎麼怪怪der~是不是格式打錯哩[emo9]")

    # 阿金乾杯!
    elif user_content.find("乾杯") != -1 and user_content.find("@gin_the_golden") != -1:
        plurkResponse(pid, f"@{user_nick_name}: 阿金準備了(dice10)杯琴酒，今天不醉不歸[emo16]")

    # 阿金吃什麼
    elif user_content.find("吃什麼") != -1 and user_content.find("@gin_the_golden") != -1:
        feel = GIN_FEEL_LIKE
        food = GIN_WHAT_TO_EAT
        random.shuffle(feel)
        random.shuffle(food)
        plurkResponse(pid, f"@{user_nick_name}: {feel[0]}{food[0]}")

    elif user_content.find("@gin_the_golden") != -1:
        res_list = GIN_RANDOM_RESPONSES
        random.shuffle(res_list)
        plurkResponse(pid, f"@{user_nick_name}: {res_list[0]}")

# 透過 response_id 找到噗文內的回應
def findTargetResponse(res_list, res_id):
    for res in res_list:
        if res['id'] == res_id:
            return res['content_raw']
    return "not found"

def responseMentioned():
    plurks = plurk.callAPI('/APP/Alerts/getActive')
    if plurks is not None:
        for p in plurks:
            if p is not None:
                if p['type'] == "mentioned":
                    if str(p["from_user"]["id"]) not in friend_list:
                        print("Not in friend list.")
                        continue
                    print(f"[responseMentioned]: plurk id = {p['plurk_id']}\n")
                    isAdmin = False
                    # plurkResponse(p['plurk_id'], f"@{p["from_user"]["nick_name"]}: 阿金寶貝回應 mention (p-wave)")
                    
                    res_id = p['response_id']
                    pid = p['plurk_id']
                    res_json = plurk.callAPI('/APP/Responses/get', {'plurk_id': pid})
                    if res_json is None:
                        pass
                    else:
                        res_list = res_json['responses']
                        target = findTargetResponse(res_list, res_id)
                        if str(p["from_user"]["id"]) == "16713667":
                            isAdmin = True
                        dealContent(pid, target, isAdmin, p, p['from_user']["nick_name"])

while True:
    match = initApi()
    print("Auth success!")
    if match:
        rawdata = match.group(1)
    else:
        continue
    data = json.loads(rawdata)
    new_offset = data.get('new_offset', -1)
    msgs = data.get('data')

    responseMentioned()
    print("=====阿金在線中=====")
    
    if not msgs:
        continue
    for msg in msgs:
        # print(f"msg get:\n{msg}")
        isAdmin = False

        pid = msg.get('plurk_id')
        try:
            user_id = msg['response']['user_id']
            user_data = msg['user'].get(str(user_id), {})
            user_nick_name = user_data.get('nick_name', 'Unknown') 
            print(f"user id: {user_id}\nuser nick name: {user_nick_name}")
        except Exception as e:
            print("get error: \n" + str(e))
            continue

        if str(user_id) == "17637392":
            print("阿金抓到自己")
            continue
            # try:
            #     pid = msg['plurk']['plurk_id']
            #     user_id = msg['plurk']['user_id']
            # except Exception as e:
            #     print("get error: \n" + str(e))
            #     continue

        # 檢查是否為好友
        if str(user_id) not in friend_list:
            print("Not in friend list.")
            continue

        if msg.get('type') == 'new_plurk':
            print(f"reply now user:{user_id} msg: {msg.get('content')}")
            user_content = msg.get('content_raw')
            if str(user_id) == "16713667":
                isAdmin = True
            dealContent(pid, user_content, isAdmin, "", user_nick_name)
    
    time.sleep(5)


# print(plurk.callAPI('/APP/Profile/getOwnProfile'))
# print(plurk.callAPI('/APP/Profile/getPublicProfile', options={'user_id': 4203050}))
# print(plurk.callAPI('/APP/Timeline/uploadPicture', files={'image': '../testimg.jpg'}))