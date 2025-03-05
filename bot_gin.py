from plurk_oauth import PlurkAPI
from db_manager import db_addData, db_readData
import urllib.request
import re, json, random

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

category_list = ["服裝", "互動"]
friend_list = list()

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
    plurk.callAPI('/APP/Alerts/addAllAsFriends')
    setFriendList()
    req = urllib.request.urlopen(comet_channel % new_offset, timeout=80)
    rawdata = req.read()
    match = jsonp_re.match(rawdata.decode('ISO-8859-1'))
    return match

# 回覆
def plurkResponse(pid, bot_content):
    plurk.callAPI('/APP/Responses/responseAdd', {'plurk_id': pid, 'content': bot_content, 'qualifier': ':'})

# 把 tags 存到資料庫
def save_tags_to_db(category, options, user_nick_name, pid):
    if category in category_list:
        bot_contents = [f"@{user_nick_name}: 新增結果如下~"]
        for option in options:
            if option == "":
                continue
            query = {"$and": [
                {"category": category},
                {"tag": option}
            ]}
            data = db_readData(query, True)
            print(f"data in db: {data}")
            if data is None:
                new_tag = dict()
                new_tag['category'] = category
                new_tag['tag'] = option
                db_addData(new_tag)
                bot_contents.append(f"「{option}」成功新增")
            else:
                print("資料庫已有相同資料")
                bot_contents.append(f"「{option}」已存在，不需要再新增啦！")
        bot_content = '\n'.join(bot_contents)
        plurkResponse(pid, bot_content)
    else:
        print("查無分類")
        plurkResponse(pid, f"沒有「{category}」這個分類歐！")

def slotTags(category, num):
    data = db_readData({"category": category}, False)
    all_data = list(data)
    i = 0
    # print(f"data:\n{all_data}")
    maximum = len(all_data)
    print(f"Length of data list: {maximum}")
    slot_result = list()
    while i < num:
        ran = random.randrange(maximum)
        tag = all_data[ran]['tag']
        if tag not in slot_result:
            print(f"{i}. 抽到的 tag: {tag}")
            slot_result.append(tag)
            i = i + 1
    return slot_result

def dealContent(pid, user_content, isCmd, p, user_nick_name):
    print(f"reply plurk id:{pid}\ncontent:{user_content}")
    # plurkResponse(pid, f"@{user_nick_name}: 阿金寶貝進入新噗文留下一顆心 (heart)")

    # 新增 tags 功能
    if user_content.find("新增") != -1:
        # 正則表達式：新增<category>：<tag>、<tag>
        pattern = r"(?:.*[\n\s]*)?新增(\w{2})：(.+)"
        # 進行匹配
        match = re.match(pattern, user_content)
        if match:
            category = match.group(1)  # 取得兩字詞(服裝、互動)
            options = match.group(2).split("、")  # 取得選項列表
            print("分類:", category)
            print("選項:", options)
            save_tags_to_db(category, options, user_nick_name, pid)
        else:
            print("re 未匹配成功(格式有誤)")
            plurkResponse(pid, f"@{user_nick_name}: 怎麼怪怪der~是不是格式打錯哩")

    # 抽 tag 功能
    if user_content.find("抽") != -1:
        # 正則表達式：新增<category><num>個
        pattern = r"(?:.*[\n\s]*)?抽(\w{2})(\d+)"
        # 進行匹配
        match = re.match(pattern, user_content)
        if match:
            category = match.group(1)  # 取得兩字詞(服裝、互動)
            number = match.group(2).split("、")  # 取得抽取數量
            num = int(number[0])
            print("分類:", category)
            print("數量:", num)
            if 0 < num <= 10:
                result = slotTags(category, num)
                result = '、'.join(result)
                plurkResponse(pid, f"@{user_nick_name}: 「{category}」{num}抽的抽選結果：\n{result}")
            elif num > 10:
                plurkResponse(pid, f"@{user_nick_name}: 太貪心辣！一次最多只能抽10個")
            else:
                plurkResponse(pid, f"@{user_nick_name}: ┌(。Д。)┐?!![emo4]")
        else:
            print("re 未匹配成功(格式有誤)")
            plurkResponse(pid, f"@{user_nick_name}: 怎麼怪怪der~是不是格式打錯哩[emo5]")

    # if content.find("進村") != -1 or content.find("開村") != -1:
    #     plurkResponse(pid, ' 進村拉～')
    # if content.find("鴨鴨") != -1:
    #     response = requests.get(duck_url)
    #     if response.status_code == 200:
    #         plurkResponse(pid, '呱呱！' + response.json()['url'])
    # else:
    #     if content.find("謝謝") != -1:
    #         plurkResponse(pid, "不客氣拉！[emo9]")
    #     elif content.find("喜歡") != -1 or content.find("棒") != -1:
    #         plurkResponse(pid, "謝謝你的喜歡！也記得要這麼喜歡自己喔！[emo9]")
    #     else:
    #         random.shuffle(random_list)
    #         plurkResponse(pid, random_list[0])

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
                    print(f"[responseMentioned]: plurk id = {p['plurk_id']}")
                    # plurkResponse(p['plurk_id'], f"@{p["from_user"]["nick_name"]}: 阿金寶貝回應 mention (p-wave)")
                    
                    res_id = p['response_id']
                    pid = p['plurk_id']
                    res_json = plurk.callAPI('/APP/Responses/get', {'plurk_id': pid})
                    if res_json is None:
                        pass
                    else:
                        res_list = res_json['responses']
                        target = findTargetResponse(res_list, res_id)
                        dealContent(pid, target, True, p, p['from_user']["nick_name"])

while True:
    match = initApi()
    print("Auth success!")
    if match:
        rawdata = match.group(1)
    data = json.loads(rawdata)
    new_offset = data.get('new_offset', -1)
    msgs = data.get('data')

    responseMentioned()
    print("=====阿金在線中=====")
    
    if not msgs:
        continue
    for msg in msgs:
        # print(f"msg get:\n{msg}")
        pid = msg.get('plurk_id')
        try:
            user_id = msg['response']['user_id']
            user_data = msg['user'].get(str(user_id), {})
            user_nick_name = user_data.get('nick_name', 'Unknown') 
            print(f"user id: {user_id}\nuser nick name: {user_nick_name}")
        except Exception as e:
            print("get error: \n" + str(e))
            continue
        
        if user_id is None:
            try:
                pid = msg['plurk']['plurk_id']
                user_id = msg['plurk']['user_id']
            except Exception as e:
                print("get error: \n" + str(e))
                continue

        # 檢查是否為好友
        if str(user_id) not in friend_list:
            print("Not in friend list.")
            continue

        if msg.get('type') == 'new_plurk':
            print(f"reply now user:{user_id} msg: {msg.get('content')}")
            user_content = msg.get('content_raw')
            dealContent(pid, user_content, False, "", user_nick_name)


# print(plurk.callAPI('/APP/Profile/getOwnProfile'))
# print(plurk.callAPI('/APP/Profile/getPublicProfile', options={'user_id': 4203050}))
# print(plurk.callAPI('/APP/Timeline/uploadPicture', files={'image': '../testimg.jpg'}))