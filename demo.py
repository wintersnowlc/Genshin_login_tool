import hashlib
import json
import os.path
import pickle
import random
import sys
import time
import warnings
from hashlib import md5
from typing import List

import numpy as np
import wmi
import cv2 as cv
import requests
from pyautogui import screenshot

sys.path.append(os.path.abspath('.'))


class User:
    def __init__(self, web_cookie):
        self.web_cookie = web_cookie
        web_cookie = parse_cookie(web_cookie)
        self.uid = web_cookie['login_uid']
        self.ticket = web_cookie['login_ticket']
        self.stoken = self.get_stoken(web_cookie)
        self.game_token = self.get_game_token()
        self.role = self.get_role()

    @staticmethod
    def get_stoken(web_cookie: dict):
        url = 'https://api-takumi.mihoyo.com/auth/api/getMultiTokenByLoginTicket'
        params = {
            'login_ticket': web_cookie['login_ticket'],
            'token_types': 3,
            'uid': web_cookie['login_uid']
        }
        get_url1 = requests.get(url, params)
        if get_url1.status_code == 200:
            tokens = json.loads(get_url1.text)
            if tokens.get('message') == 'OK':
                tokens = tokens['data']['list']
                for item in tokens:
                    if item.get('name') == 'stoken':
                        print('获取token成功')
                        return item['token']

    def get_game_token(self):
        url = 'https://api-takumi.mihoyo.com/auth/api/getGameToken'
        get_url = requests.get(url, {'stoken': self.stoken, 'uid': self.uid})
        if get_url.status_code == 200:
            json_loads = json.loads(get_url.text)
            if json_loads.get('message') == 'OK':
                return json_loads['data']['game_token']

    def get_role(self):
        url = 'https://api-takumi.miyoushe.com/binding/api/getUserGameRolesByStoken'
        headers['DS'] = get_DS()
        get_url = requests.get(url,
                               cookies={'stuid': self.uid,
                                        'stoken': self.stoken,
                                        'mid': '043co169fb_mhy'},
                               headers=headers)
        if get_url.status_code == 200:
            json_loads = json.loads(get_url.text)
            if json_loads.get('message') == 'OK':
                return json_loads['data']['list']

    def __str__(self):
        return f'name：{self.role[0]["nickname"]}\t{self.uid=};'


def parse_header_and_cookie(text: str):
    text = text.strip().split('\n')[1:]
    text = [item.strip().split(':', 1) for item in text if item]
    headers_ = {k.strip(): v.strip() for k, v in text}
    cookie_ = headers_.pop('cookie')
    cookie_ = parse_cookie(cookie_)
    return headers_, cookie_


def parse_cookie(text: str):
    cookie_ = [item.strip().split('=', 1) for item in text.strip().split(';') if item]
    cookie_ = {k.strip(): v.strip() for k, v in cookie_}
    return cookie_


def get_qr_code():
    """
    识别桌面二维码
    :return:
    """
    img = screenshot(region=region)
    img = np.array(img)
    # img = cv.cvtColor(img, cv.COLOR_BGR2GRAY)
    return detector.detectAndDecode(img)[0]
    # return pyzbar.decode(image, [64])


def get_qr_ticket():
    """
    获取ticket
    :return:
    """
    # barcodes = get_qr_code()
    # if barcodes:
    #     return barcodes[0].data.decode("UTF8")[-24:]
    qr_code = get_qr_code()
    if qr_code:
        return qr_code[0][-24:]


def get_DS():
    """
    获取DS
    :return:
    """
    time_now = str(int(time.time()))
    rand = str(random.randint(100001, 200000))
    m = f'salt={salt}&t={time_now}&r={rand}'.encode('u8')
    return f'{time_now},{rand},{md5(m).hexdigest()}'


def save_users():
    with open('userinfo.pickle', 'wb') as f:
        pickle.dump(users, f)


def load_users():
    try:
        with open('userinfo.pickle', 'rb') as f:
            return pickle.load(f)
    except FileNotFoundError:
        return []


def get_scan_session():
    sess = requests.Session()
    url = 'https://api-sdk.mihoyo.com/hk4e_cn/combo/panda/qrcode/scan'
    headers['DS'] = get_DS()
    data_ = {}
    sess.post(url, json=data_, headers=headers, cookies=cookies)
    return sess


def call_scan(t: str, sess: requests.Session):
    url = 'https://api-sdk.mihoyo.com/hk4e_cn/combo/panda/qrcode/scan'
    sess.headers['DS'] = get_DS()
    data_ = {
        "app_id": "4",
        "device": "d9951154-6eea-35e8-9e46-20c53f440ac7",
        "ticket": t
    }
    response = sess.post(url, json=data_)
    return response


def call_confirm(u: User, t: str, sess: requests.Session):
    # print('向服务器发送确认信息')
    url = 'https://api-sdk.mihoyo.com/hk4e_cn/combo/panda/qrcode/confirm'
    sess.headers['DS'] = get_DS()
    data_ = {"app_id": 4,
             "device": "d9951154-6eea-35e8-9e46-20c53f440ac7",
             "payload": {"proto": "Account",
                         "raw": "{\"uid\":\"%s\",\"token\":\"%s\"}" % (u.uid, u.game_token)},
             "ticket": t}
    response = sess.post(url, json=data_, cookies=cookies)
    return response


def has_auth():
    if os.path.exists('auth.auth'):
        with open('auth.auth', 'r') as f:
            return f.read() == get_true_md5()


def register():
    true_md5 = get_true_md5()
    for _ in range(3):
        p = input('请输入激活码激活本软件：')
        if p == true_md5:
            with open('auth.auth', 'w') as f:
                f.write(get_true_md5())
                return True


def get_true_md5():
    true_str = 'salt=20230209' + get_CPU_info()
    true_md5 = hashlib.md5(true_str.encode('u8')).hexdigest()[8:16]
    return true_md5


def get_CPU_info():
    cpu = []
    cp = wmi.WMI().Win32_Processor()
    for u in cp:
        cpu.append([u.Name, u.ProcessorId, u.NumberOfCores])
    return hashlib.md5(json.dumps(cpu).encode('u8')).hexdigest()


def main():
    while True:
        order = input('\n-----------------\n'
                      '1. 显示用户信息\n'
                      '2. 添加用户\n'
                      '3. 删除用户\n'
                      '4. 开始扫码\n'
                      '0. 退出\n'
                      '请输入：')
        if order == '0':
            sys.exit(0)
        elif order == '1':
            for i, user in enumerate(users):
                print(i + 1, user, sep='\t')
        elif order == '2':
            cookie_new_user = input('请输入cookie：')
            try:
                user = User(cookie_new_user)
            except ValueError:
                print('解析失败，请检查cookie格式')
            else:
                if user.stoken:
                    users.append(user)
                    save_users()
                    print('添加成功')
                else:
                    print('添加失败，请检查cookie正确性')
        elif order == '3':
            idx = input('请输入待删除的用户编号：')
            if idx.isdigit() and 0 < int(idx) < len(users) + 1:
                idx = int(idx)
                users.pop(idx - 1)
                save_users()
                print('删除成功')
            else:
                print('你输入的数字不对')
        elif order == '4':
            while True:
                try:
                    idx = int(input('请选择你要使用的账号的序号：'))
                    if not 0 < idx < len(users) + 1:
                        raise ValueError
                    else:
                        break
                except ValueError:
                    print('请输入正确的序号')
            login_sleep = bool(input('默认使用急速模式，输1使用慢登模式'))
            user = users[idx - 1]
            cookies['stuid'] = user.uid
            cookies['stoken'] = user.stoken
            print(f'开始使用【{user.role[0]["nickname"]}】连续扫码')
            session = get_scan_session()
            for i in range(10000):
                # 识别
                t0 = time.time()
                ticket = get_qr_ticket()
                if not ticket:
                    continue
                # 扫码
                t1 = time.time()
                res = call_scan(ticket, sess=session)
                print(f'第{i}次识别成功：{ticket}，用时：{t1 - t0:.4f}')
                t2 = time.time()
                # 确认
                res = json.loads(res.text)
                if login_sleep:
                    time.sleep(random.random() + 1)
                if res['retcode'] == 0:
                    print(f'抢码成功：{t2 - t1:.4f}')
                    res = call_confirm(user, ticket, session)
                    t3 = time.time()
                    res = json.loads(res.text)
                    if res['retcode'] == 0:
                        print(f'登录成功，耗时：{t3 - t2:.4f}')
                    else:
                        print(f'登录失败：{res}')
                else:
                    print(f'抢码失败')


def check_the_authorization():
    authed = has_auth()
    while not authed:
        print('检查授权失败，请联系金鱼获取激活码')
        print(f'你的机器码为:\n{get_CPU_info()}\n请将此码提供给金鱼获取激活码')
        if register():
            print('激活成功，软件目录下auth.auth文件保存激活码，请勿删除此文件，否则激活生效，需重新激活，'
                  '但同一电脑激活码相同，拷贝此文件到其他电脑是无法激活的。')
            authed = has_auth()
            input('回车继续')
        else:
            print('密码错误次数过多！！！')
            sys.exit(0)


if __name__ == '__main__':
    # 检查授权
    # if time.time() - 1676096147 > 2 * 24 * 60 * 60:
    #     sys.exit(0)
    check_the_authorization()
    # 变量
    users: List[User] = load_users()
    cookies = {
        'stuid': '',
        'stoken': '',
        'mid': '043co169fb_mhy'
    }
    warnings.filterwarnings("ignore")
    salt = 'PVeGWIZACpxXZ1ibMVJPi9inCY4Nd4y2'
    app_version = '2.38.1'
    detector = cv.wechat_qrcode_WeChatQRCode()
    headers = {
        'DS': '',
        'x-rpc-client_type': '2',
        'x-rpc-app_version': app_version,
        'x-rpc-sys_version': '7.1.2',
        'x-rpc-channel': 'miyousheluodi',
        'x-rpc-device_id': 'd9951154-6eea-35e8-9e46-20c53f440ac7',
        'x-rpc-device_fp': '38d7ed301ed62',
        'x-rpc-device_name': 'HUAWEI LIO-AN00',
        'x-rpc-device_model': 'LIO-AN00',
        'Referer': 'https://app.mihoyo.com',
        'Content-Type': 'application/json; charset=UTF-8',
        'Host': 'api-sdk.mihoyo.com',
        'Connection': 'Keep-Alive',
        'User-Agent': 'okhttp/4.9.3'
    }
    with open('region.txt', 'r', encoding='u8') as f:
        region = tuple(json.load(f))
    print(f'\n二维码识别范围: {region}\n如需修改此范围，请开启“二维码定位”软件定位后（关闭软件保存定位），重启本软件。\n')
    # 主函数
    main()
