# app.py
# Contact: github/pokefish
# S/O : https://github.com/OKHand-Zy/Line-Bot_Module 


## pkg
from email import message
from flask import Flask, request, abort

from linebot import (
    LineBotApi, WebhookHandler
)
from linebot.exceptions import (
    InvalidSignatureError
)

from linebot.models import (
    MessageEvent, TextMessage, TextSendMessage,
)
import json ,os ,urllib

## 

# 初始化 Line BOT 
app = Flask(__name__)

## 從 json 拿到各個資訊
with open('./main/key.json') as f :
    jdata =json.load(f)
    myToken = jdata['bot_token'] 
    mySecret = jdata['bot_secret']

    client_id = jdata['NOTIFY_CLIENT_ID']
    client_secret = jdata['NOTIFY_CLIENT_SECRET']

# redirect_uri = f"https://{os.environ['YOUR_HEROKU_APP_NAME']}.herokuapp.com/callback/notify"
redirect_uri = f"https://533a-163-14-35-222.jp.ngrok.io/callback/notify"   ## 填 ngrok 的假外網


line_bot_api = LineBotApi(myToken) ## channel token
handler = WebhookHandler(mySecret) ## channel secret




def create_auth_link(user_id, client_id=client_id, redirect_uri=redirect_uri):
    
    data = {
        'response_type': 'code',
        'client_id': client_id,
        'redirect_uri': redirect_uri,
        'scope': 'notify',
        'state': user_id
    }
    query_str = urllib.parse.urlencode(data)
    
    return f'https://notify-bot.line.me/oauth/authorize?{query_str}'

## 拿取綁定的 Access_token 
def get_token(code, client_id=client_id, client_secret=client_secret, redirect_uri=redirect_uri):
    url = 'https://notify-bot.line.me/oauth/token'
    headers = { 'Content-Type': 'application/x-www-form-urlencoded' }
    data = {
        'grant_type': 'authorization_code',
        'code': code,
        'redirect_uri': redirect_uri,
        'client_id': client_id,
        'client_secret': client_secret
    }
    data = urllib.parse.urlencode(data).encode()
    req = urllib.request.Request(url, data=data, headers=headers)
    page = urllib.request.urlopen(req).read()
    res = json.loads(page.decode('utf-8'))
    return res['access_token']      #拆解後拿取 Access_Token

## 用 Notify 發出消息
def send_message(access_token, text_message):
    url = 'https://notify-api.line.me/api/notify'
    headers = {"Authorization": "Bearer "+ access_token}
    data = {'message': text_message}
    data = urllib.parse.urlencode(data).encode()
    req = urllib.request.Request(url, data=data, headers=headers)
    page = urllib.request.urlopen(req).read() #看是否成功 Ex: {"status":200,"message":"ok"}



##### 用handler處理Line觸發事件 ##### 可用此，跟資料庫做個資比對
Group_id = str   #用來紀錄群組名稱
User_id = str    #用來紀錄使用者名稱
Flag = str       #判定是否重複的值





@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
        # line_bot_api.reply_message(event.reply_token
        # , TextSendMessage(text=f"嗨嗨～ {line_bot_api.get_profile(event.source.user_id).display_name}!"))
        global Group_id , User_id
        if event.message.text == "個人訂閱" :
            url = create_auth_link(event)
            #回傳 url 給傳訊息的那 個人 or 群組
            line_bot_api.reply_message(event.reply_token,TextSendMessage(text=url) )
            #這邊是利用 event 內的 user_id 去跟 Line 拿到使用者的當前 Line 使用的名子 Ex: Zi-Yu(林子育)
            User_id = line_bot_api.get_profile(event.source.user_id).display_name
            Group_id = ''
        elif event.message.text == "群組訂閱" :
            url = create_auth_link(event)
            line_bot_api.reply_message(event.reply_token,TextSendMessage(text=url) )
            #因為 event 內只會回傳個人訊息所以無法找到 Group 的名稱,所以只能改拿 Group 的 id
            Group_id = (event.source.group_id)   #Group_id get!
            User_id = ''
###########################################
# # 學你說話
# @handler.add(MessageEvent, message=TextMessage)
# def echo(event):
    
#     if event.source.user_id != "Udeadbeefdeadbeefdeadbeefdeadbeef":
#         line_bot_api.reply_message(
#             event.reply_token,
#             TextSendMessage(text=event.message.text)
#         )


########### 各 ＣＡＬＬＢＡＣＫ ##############
## linebot 驗證回傳起手式: route 處理路由
@app.route("/callback", methods=['POST'])
def callback():
    # get X-Line-Signature header value
    signature = request.headers['X-Line-Signature']

    # get request body as text
    body = request.get_data(as_text=True)
    app.logger.info("Request body: " + body)

    # handle webhook body
    try:
        handler.handle(body, signature)

    except InvalidSignatureError:
        
        print("無法驗證，重新驗證頻道資訊")
        abort(400)

    return 'OK'


# url 回傳給 Notify 並拿 User Token
@app.route("/callback/notify", methods=['GET'])
def callback_nofity():
    #assert request.headers['referer'] == 'https://notify-bot.line.me/'
    code = request.args.get('code')
    state = request.args.get('state')
    
    # print("Code:"+code)
    # print("state:"+state)
    # print(event.source.group_id)
    
    # Get Access-Token
    access_token = get_token(code, client_id, client_secret, redirect_uri)
    
    #print("AccessToken="+access_token)
    #print("Clinet_id"+client_id)

    ### google_sheet(client_id,access_token)  ## 回傳資料庫 >> 改ragic 
    send_message(access_token,text_message="嗨～")   #發訊息
    
    return '恭喜完成 LINE Notify 連動！請關閉此視窗。'

########### 各 ＣＡＬＬＢＡＣＫ ##############


if __name__ == '__main__':
    app.run(port=6666) # 配合 ngrok
    