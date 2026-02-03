import json
import math
import time
import urllib.request
import requests

# === 修改下面为你自己的 SESSDATA 值（登录 B站网页后在 Cookie 里复制） ===
SESSDATA = "2e33657e%2C1769231297%2Cf6c38%2A71CjCrVrpdhSNBm8a_HAGPGv6hcCb6f_N9tE2yFcg494XNBTZJMDW3cExrgwF-GqIoqo0SVk9mNkxlalRTTDktbk5zOG9JZU1xRkpEQjB6MlZseGJnS1JobExHTlhoamUwOS1VenFkSzQwLWNuT2dVemJPN3N4V185TGFrb0xkNFJYbkxXQ1k2MDFnIIEC"  # 建议设置，否则某些视频评论无法访问

def check_login_status():
    url = "https://api.bilibili.com/x/web-interface/nav"
    headers = build_headers()
    try:
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req) as res:
            data = json.loads(res.read().decode("utf-8"))
            if data.get("code") == 0 and data.get("data", {}).get("isLogin"):
                name = data["data"].get("uname", "未知")
                mid = data["data"].get("mid", "未知")
                print(f"✅ 当前已登录账号：{name} (UID: {mid})")
                return True
            else:
                print("❌ 未登录或 SESSDATA 无效")
                return False
    except Exception as e:
        print(f"❌ 登录状态检测失败：{e}")
        return False

def build_headers():
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
        "Referer": "https://www.bilibili.com/",
    }
    if SESSDATA:
        headers["Cookie"] = f"SESSDATA={SESSDATA}"
    return headers

def get_csrf_token():
    """
    从SESSDATA中提取csrf_token（bili_jct）或者直接从Cookie中获得。
    这里假设csrf_token即为SESSDATA解码后字符串中bili_jct对应值。
    如果你已有更好的获取csrf_token方式，替换此函数即可。
    """
    bili_jct = "f4f7001e76840ea7299809d3857288a7"  # 需要登录后从浏览器Cookie获得，示例请替换
    return bili_jct

def get_video_info(bvid, max_retries=3):
    url = f"https://api.bilibili.com/x/web-interface/view?bvid={bvid}"
    headers = build_headers()
    for _ in range(max_retries):
        try:
            res = urllib.request.urlopen(urllib.request.Request(url, headers=headers))
            data = json.loads(res.read().decode("utf-8"))
            if data["code"] != 0:
                print("获取视频信息失败")
                return None, None
            return data["data"]["aid"], data["data"]["title"]
        except:
            time.sleep(2)
    print("重试失败，无法获取视频信息")
    return None, None

def get_comments(oid, page=1):
    url = f"https://api.bilibili.com/x/v2/reply?type=1&oid={oid}&pn={page}&ps=20&sort=2"
    headers = build_headers()
    try:
        res = urllib.request.urlopen(urllib.request.Request(url, headers=headers))
        data = json.loads(res.read().decode("utf-8"))
        if data["code"] != 0: return []
        replies = data["data"].get("replies") or []
        return [(r["member"]["uname"], r["content"]["message"], r["member"]["mid"]) for r in replies]
    except:
        return []

def post_comment(bvid, message):
    """
    发送评论到指定视频bvid下，返回True/False
    需登录态和csrf_token支持。
    """
    aid, _ = get_video_info(bvid)
    if not aid:
        print("无法获取aid，评论失败")
        return False

    url = "https://api.bilibili.com/x/v2/reply/add"
    headers = build_headers()
    csrf_token = get_csrf_token()
    if not csrf_token or csrf_token == "你的bili_jct":
        print("缺少有效的csrf_token，请填写你的bili_jct")
        return False

    data = {
        "oid": aid,
        "type": 1,  # 视频类型固定1
        "message": message,
        "csrf": csrf_token,
        "csrf_token": csrf_token,  # 部分接口可能同时需要
    }
    post_data = urllib.parse.urlencode(data).encode("utf-8")

    req = urllib.request.Request(url, data=post_data, headers=headers, method="POST")
    try:
        with urllib.request.urlopen(req) as resp:
            resp_json = json.loads(resp.read().decode("utf-8"))
            if resp_json.get("code") == 0:
                print("评论发送成功")
                return True
            else:
                print("评论发送失败:", resp_json.get("message"))
                return False
    except Exception as e:
        print("发送评论异常:", e)
        return False

def search_videos(keyword, page=1, page_size=30):
    import urllib.parse
    url = (f"https://api.bilibili.com/x/web-interface/search/all/v2?"
           f"keyword={urllib.parse.quote(keyword)}&page={page}&page_size={page_size}")
    headers = build_headers()
    try:
        req = urllib.request.Request(url, headers=headers)
        res = urllib.request.urlopen(req)
        data = json.loads(res.read().decode("utf-8"))
        if data["code"] != 0:
            return []
        for sec in data["data"]["result"]:
            if sec.get("result_type") == "video":
                return [
                    (v["bvid"], v["title"], f"https://www.bilibili.com/video/{v['bvid']}")
                    for v in sec.get("data", [])
                ]
    except Exception as e:
        print("搜索异常：", e)
    return []

def get_user_info(mid):
    info = {}
    # 获取基本信息
    url1 = f"https://api.bilibili.com/x/space/acc/info?mid={mid}"
    url2 = f"https://api.bilibili.com/x/relation/stat?vmid={mid}"
    for url in (url1, url2):
        try:
            res = urllib.request.urlopen(urllib.request.Request(url, headers=build_headers()))
            data = json.loads(res.read().decode("utf-8"))
            if data["code"] == 0:
                info.update(data["data"])
        except:
            pass
    return info

def get_user_videos(mid):
    vids = []
    pn = 1
    while True:
        url = f"https://api.bilibili.com/x/space/arc/search?mid={mid}&pn={pn}&ps=30"
        try:
            headers = build_headers()
            req = urllib.request.Request(url, headers=headers)
            with urllib.request.urlopen(req) as res:
                data = json.loads(res.read().decode("utf-8"))

            if data.get("code") != 0:
                print(f"接口返回错误 code={data.get('code')}")
                break

            page_data = data.get("data", {})
            vlist = page_data.get("list", {}).get("vlist", [])
            if not vlist:
                break

            for v in vlist:
                bvid = v.get("bvid") or f"av{v.get('aid')}"
                title = v.get("title", "无标题")
                vids.append((bvid, title))

            total = page_data.get("page", {}).get("count", 0)
            ps = page_data.get("page", {}).get("size", 30)
            total_pages = math.ceil(total / ps)
            if pn >= total_pages:
                break

            pn += 1
            time.sleep(0.5)

        except Exception as e:
            print(f"获取用户视频出错: {e}")
            break
    return vids

def get_user_favorites(mid):
    favs = []
    pn = 1
    while True:
        url = f"https://api.bilibili.com/x/space/favourite?mid={mid}&pn={pn}&ps=30"
        try:
            res = urllib.request.urlopen(urllib.request.Request(url, headers=build_headers()))
            data = json.loads(res.read().decode("utf-8"))
            if data["code"] != 0:
                break
            fav_list = data["data"]["list"]
            if not fav_list:
                break
            favs.extend([(fav["title"], fav["id"]) for fav in fav_list])
            page_num = data["data"]["page"]["num"]
            page_count = data["data"]["page"]["count"]
            if page_num >= page_count:
                break
            pn += 1
            time.sleep(0.5)
        except Exception as e:
            print(f"获取收藏夹出错: {e}")
            break
    return favs

def crawl_bilibili_comments(bvid, max_pages=30):
    oid, title = get_video_info(bvid)
    if not oid:
        print("❌ 无法获取视频信息")
        return []
    print(f"爬取视频《{title}》的评论…")
    all_comments = []
    for p in range(1, max_pages+1):
        cmts = get_comments(oid, p)
        if not cmts: break
        all_comments.extend(cmts)
        time.sleep(1)
    fname = f"{''.join(c for c in title if c.isalnum())}_comments.txt"
    with open(fname, "w", encoding="utf-8") as f:
        for u,msg,mid in all_comments:
            f.write(f"{u}\t{mid}\t{msg}\n")
    print(f"共爬取 {len(all_comments)} 条评论，已保存到 {fname}")
    return all_comments

def get_user_followings(mid, pn=1, max_pages=10):
    """获取用户关注的用户列表（昵称和UID），最多爬取max_pages页"""
    followings = []
    while pn <= max_pages:
        url = f"https://api.bilibili.com/x/relation/followings?vmid={mid}&pn={pn}&ps=50"
        try:
            res = urllib.request.urlopen(urllib.request.Request(url, headers=build_headers()))
            data = json.loads(res.read().decode("utf-8"))
            if data["code"] != 0:
                break
            lst = data["data"].get("list", [])
            if not lst:
                break
            followings.extend([(u["uname"], u["mid"]) for u in lst])
            total_count = data["data"]["total"]
            if pn * 50 >= total_count:
                break
            pn += 1
            time.sleep(0.5)
        except Exception as e:
            print(f"获取关注列表出错: {e}")
            break
    return followings

def filter_comments_by_keyword(input_filename, keyword):
    out=[]
    with open(input_filename, "r",encoding="utf-8") as f:
        for line in f:
            if keyword in line: out.append(line.strip())
    if out:
        of=f"{keyword}_comments.txt"
        with open(of,"w",encoding="utf-8") as w:
            w.write("\n".join(out))
        print(f"筛选结果：{len(out)} 条，保存至 {of}")
    else:
        print("未筛选出匹配评论")

# 新增搜索用户昵称的接口（B站官方未公开搜索接口，改用bilibili搜索api）
def search_users_by_name(keyword, page=1, page_size=20):
    url = (f"https://api.bilibili.com/x/web-interface/search/type?"
           f"keyword={urllib.request.quote(keyword)}&search_type=bili_user&page={page}&pagesize={page_size}")
    headers = build_headers()
    try:
        res = urllib.request.urlopen(urllib.request.Request(url, headers=headers))
        data = json.loads(res.read().decode("utf-8"))
        if data["code"] != 0:
            return []
        users = data["data"]["result"]
        return [(u["uname"], u["mid"]) for u in users]
    except:
        return []

def crawl_users_by_keyword(keyword):
    users = search_users_by_name(keyword)
    if not users:
        print("❌ 未找到相关用户")
        return
    print(f"共找到 {len(users)} 位昵称包含“{keyword}”的用户：")
    for i, (uname, mid) in enumerate(users, 1):
        print(f"{i}. 昵称: {uname}, UID: {mid}")
    sel = input("选择用户编号查看详细信息（输入数字查看/exit返回上一级）：").strip()
    if not sel.isdigit() or not (1 <= int(sel) <= len(users)):
        print("无效选择，退出。")
        return
    if sel == "exit":
        return
    uname, mid = users[int(sel) - 1]

    # 定义递归查看用户详情及关注列表的函数
    def view_user_detail_and_followings(mid):
        info = get_user_info(mid)
        print(f"\n用户详细信息：")
        print(f"昵称: {info.get('name')}")
        print(f"UID: {mid}")
        print(f"性别: {info.get('sex')}")
        print(f"生日: {info.get('birthday')}")
        print(f"常住地: {info.get('place')}")
        print(f"关注数: {info.get('following')}")
        print(f"粉丝数: {info.get('follower')}")

        vids = get_user_videos(mid)
        print("\n用户视频：")
        if vids:
            for bvid, title in vids:
                print(f"- {title} ({bvid})")
        else:
            print("无公开视频")

        favs = get_user_favorites(mid)
        print("\n用户收藏夹：")
        if favs:
            for title, fid in favs:
                print(f"- {title} (收藏夹ID: {fid})")
        else:
            print("无公开收藏夹或获取失败")

        # 查看关注列表循环
        while True:
            choice_follow = input("\n是否查看该用户关注的用户列表？(y查看，exit退出)：").strip().lower()
            if choice_follow == 'exit':
                crawl_users_by_keyword(keyword)
                break
            elif choice_follow == 'y':
                followings = get_user_followings(mid)
                if not followings:
                    print("该用户没有关注公开用户或获取失败。")
                    break
                print(f"\n该用户关注了 {len(followings)} 位用户：")
                for i, (uname_f, mid_f) in enumerate(followings, 1):
                    print(f"{i}. {uname_f} (UID: {mid_f})")
                sel_follow = input("输入关注用户编号查看详细信息，或输入'exit'返回上一级：").strip()
                if sel_follow.lower() == 'exit':
                    continue
                if not sel_follow.isdigit() or not (1 <= int(sel_follow) <= len(followings)):
                    print("无效选择，返回上一级。")
                    continue
                _, mid = followings[int(sel_follow) - 1]
                # 递归查看新选用户详情及关注列表
                view_user_detail_and_followings(mid)
                # 返回后继续循环询问关注列表
            else:
                print("输入无效，请输入'y'或'exit'。")

    # 初始查看选择的用户详情
    view_user_detail_and_followings(mid)


API_KEY = "APIKey-20250708224356"        # 你的API Key
SECRET_KEY = "bce-v3/ALTAK-JtlfLWCe1YrXLevcLdv1i/cbd86a6e4ec9119d1ceb81490d756a3d02d8fea5"  # 你的Secret Key

def get_access_token(api_key, secret_key):
    url = "https://aip.baidubce.com/oauth/2.0/token"
    params = {
        "grant_type": "client_credentials",
        "client_id": api_key,
        "client_secret": secret_key
    }
    resp = requests.get(url, params=params)
    if resp.status_code == 200:
        token = resp.json().get("access_token")
        if token:
            return token
        else:
            raise Exception(f"获取access_token失败，响应内容：{resp.text}")
    else:
        raise Exception(f"请求access_token失败，状态码：{resp.status_code}")

def chat_with_baidu_new_api(user_message):
    url = "https://qianfan.baidubce.com/v2/chat/completions"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {API_KEY}"  # 新模型使用Bearer Token形式
    }
    data = {
        "model": "ernie-bot-turbo",
        "messages": [
            {"role": "user", "content": user_message}
        ]
    }
    resp = requests.post(url, headers=headers, json=data, timeout=10)
    resp.encoding = 'utf-8'  # 防止编码问题
    if resp.status_code == 200:
        resp_json = resp.json()
        return resp_json['choices'][0]['message']['content']
    else:
        raise Exception(f"调用聊天接口失败，状态码：{resp.status_code}，内容：{resp.text}")

if __name__ == "__main__":
    if not check_login_status():
        print("请检查 SESSDATA 是否正确，或尝试重新登录获取 Cookie")
        exit()
    print("1. 搜评论\n2. 筛评论\n3. 搜用户\n4. 搜视频并发评论")
    choice = input("选择：").strip()
    if choice=="1":
        kw=input("输入搜索关键词爬视频评论：")
        res=search_videos(kw,page_size=5)
        if not res:
            print("未找到相关视频")
        else:
            for i,(b,t,_) in enumerate(res,1):
                print(f"{i}. {t} ({b})")
            sel=input("选视频编号：").strip()
            if sel.isdigit() and 1 <= int(sel) <= len(res):
                crawl_bilibili_comments(res[int(sel)-1][0])
            else:
                print("无效选择")
    elif choice=="2":
        fn=input("评论文件名："); kw=input("筛选关键词：")
        filter_comments_by_keyword(fn,kw)
    elif choice=="3":
        kw=input("输入昵称关键词搜索用户：")
        crawl_users_by_keyword(kw)
    elif choice=="4":
        kw = input("输入搜索视频关键词：")
        res = search_videos(kw, page_size=5)
        if not res:
            print("未找到相关视频")
            exit()

        print("搜索到以下视频：")
        for i, (bvid, title, url) in enumerate(res, 1):
            print(f"{i}. {title} ({bvid}) - {url}")
        sel = input("选择视频编号发评论：").strip()

        if not sel.isdigit() or not (1 <= int(sel) <= len(res)):
            print("无效选择")
            exit()
        bvid = res[int(sel) - 1][0]
        msg = input("请输入评论内容：").strip()
        if not msg:
            print("评论内容不能为空")
            exit()
        success = post_comment(bvid, msg)
        if success:
            print("评论发送成功！")
        else:
            print("评论发送失败！")
    else:
        print("退出")
