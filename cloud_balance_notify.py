import yaml
import requests
import datetime
import time
import hmac
import hashlib
import base64
import urllib.parse

def load_config(path="config.yaml"):
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)

def get_aliyun_balance(account):
    try:
        from aliyunsdkcore.client import AcsClient
        from aliyunsdkbssopenapi.request.v20171214.QueryAccountBalanceRequest import QueryAccountBalanceRequest
        client = AcsClient(account['access_key'], account['access_secret'], 'cn-hangzhou')
        request = QueryAccountBalanceRequest()
        response = client.do_action_with_exception(request)
        import json
        data = json.loads(response)
        balance_str = data['Data']['AvailableAmount']
        # 处理千分位和单位
        balance_str = balance_str.replace(',', '').replace('元', '').strip()
        balance = float(balance_str)
        return balance
    except Exception as e:
        return f"获取失败: {e}"

def get_volcengine_balance(account):
    try:
        import volcenginesdkcore
        import volcenginesdkbilling
        from volcenginesdkcore.rest import ApiException
        configuration = volcenginesdkcore.Configuration()
        configuration.ak = account['ak']
        configuration.sk = account['sk']
        configuration.region = "cn-beijing"
        volcenginesdkcore.Configuration.set_default(configuration)
        api_instance = volcenginesdkbilling.BILLINGApi()
        query_balance_acct_request = volcenginesdkbilling.QueryBalanceAcctRequest()
        try:
            resp = api_instance.query_balance_acct(query_balance_acct_request)
            # 直接取 _available_balance 字段
            balance = getattr(resp, '_available_balance', None)
            if balance is not None:
                balance_str = str(balance).replace(',', '').replace('元', '').strip()
                return float(balance_str)
            return f"获取失败: 未找到余额字段, resp={resp.__dict__}"
        except ApiException as e:
            return f"获取失败: volcengine api异常, error={e}"
    except Exception as e:
        return f"获取失败: {e}"

def get_tencent_balance(account):
    try:
        import tencentcloud.common as common
        from tencentcloud.common import credential
        from tencentcloud.common.profile.client_profile import ClientProfile
        from tencentcloud.common.profile.http_profile import HttpProfile
        from tencentcloud.billing.v20180709 import billing_client, models
        cred = credential.Credential(account['secret_id'], account['secret_key'])
        httpProfile = HttpProfile()
        httpProfile.endpoint = "billing.tencentcloudapi.com"
        clientProfile = ClientProfile()
        clientProfile.httpProfile = httpProfile
        client = billing_client.BillingClient(cred, "ap-guangzhou", clientProfile)
        req = models.DescribeAccountBalanceRequest()
        resp = client.DescribeAccountBalance(req)
        # 兼容新版/老版字段
        if hasattr(resp, "Balance"):
            balance = resp.Balance / 100.0  # 分转元
        elif hasattr(resp, "BalanceAmount"):
            balance = resp.BalanceAmount / 100.0
        else:
            balance = "未知"
        return balance
    except Exception as e:
        print(f"腾讯云余额获取异常: {e}")
        return None

def get_doudian_balance(account):
    try:
        # 伪代码：假设抖店云有类似火山云的 SDK 和调用方式
        # 实际使用时请替换为抖店云官方 SDK 或 HTTP API 调用
        import volcenginesdkcore
        import volcenginesdkbilling
        from volcenginesdkcore.rest import ApiException
        configuration = volcenginesdkcore.Configuration()
        configuration.ak = account['app_key']
        configuration.sk = account['app_secret']
        configuration.region = "cn-beijing"  # 如有抖店云专属 region 请替换
        volcenginesdkcore.Configuration.set_default(configuration)
        api_instance = volcenginesdkbilling.BILLINGApi()
        query_balance_acct_request = volcenginesdkbilling.QueryBalanceAcctRequest()
        try:
            resp = api_instance.query_balance_acct(query_balance_acct_request)
            balance = getattr(resp, '_available_balance', None)
            if balance is not None:
                balance_str = str(balance).replace(',', '').replace('元', '').strip()
                return float(balance_str)
            return f"获取失败: 未找到余额字段, resp={resp.__dict__}"
        except ApiException as e:
            return f"获取失败: doudian api异常, error={e}"
    except Exception as e:
        return f"获取失败: {e}"

def get_huaweicloud_balance(account):
    try:
        import os
        from huaweicloudsdkcore.auth.credentials import GlobalCredentials
        from huaweicloudsdkbss.v2.region.bss_region import BssRegion
        from huaweicloudsdkcore.exceptions import exceptions
        from huaweicloudsdkbss.v2 import BssClient, ShowCustomerAccountBalancesRequest
        ak = account.get('ak') or os.environ.get('CLOUD_SDK_AK')
        sk = account.get('sk') or os.environ.get('CLOUD_SDK_SK')
        # BSS服务仅支持cn-north-1
        region = 'cn-north-1'
        credentials = GlobalCredentials(ak, sk)
        client = BssClient.new_builder() \
            .with_credentials(credentials) \
            .with_region(BssRegion.value_of(region)) \
            .build()
        request = ShowCustomerAccountBalancesRequest()
        response = client.show_customer_account_balances(request)
        if hasattr(response, 'account_balances') and response.account_balances:
            balance = response.account_balances[0].amount / 100  # 分转元
            return balance
        return f"获取失败: 未找到余额字段, resp={response}" 
    except Exception as e:
        return f"获取失败: {e}"

def get_qiniu_balance(account):
    """
    获取七牛云账户余额概览（新版API，支持所有账户类型）
    文档：https://developer.qiniu.com/fusion/api/4246/account-balance
    需在 config.yaml 配置 qiniu_accounts: - name/ak/sk
    """
    try:
        import requests
        import hmac
        import hashlib
        import base64
        ak = account['ak']
        sk = account['sk']
        path = "/billing-api/v1/account/balance-overview"
        host = "api.qiniu.com"
        method = "GET"
        url = f"https://{host}{path}"
        # 签名
        signingStr = f"{method.upper()} {path}\nHost: {host}\n\n"
        sign = hmac.new(sk.encode('utf-8'), signingStr.encode('utf-8'), hashlib.sha1).digest()
        encodedSign = base64.urlsafe_b64encode(sign).decode('utf-8')
        authorization = f"Qiniu {ak}:{encodedSign}"
        headers = {
            "Host": host,
            "Authorization": authorization,
        }
        resp = requests.get(url, headers=headers)
        try:
            data = resp.json()
        except Exception:
            return f"获取失败: 返回内容非JSON, resp={resp.text}"
        # 提取关键余额信息
        available_balance = data.get('data', {}).get('available_balance')
        # currency = data.get('data', {}).get('currency', 'CNY')  # 不再拼接币种
        if available_balance is not None:
            # 七牛新版余额单位为“分厘”，需除以1e8
            return available_balance/100000000
        return f"获取失败: {data}"
    except Exception as e:
        return f"获取失败: {e}"

def send_dingtalk(webhook, secret, content):
    url = get_signed_url(webhook, secret)
    headers = {"Content-Type": "application/json"}
    data = {
        "msgtype": "markdown",
        "markdown": {
            "title": "云平台余额通知",
            "text": content
        }
    }
    try:
        resp = requests.post(url, json=data, headers=headers)
        print("钉钉响应：", resp.status_code, resp.text)  # 增加响应输出
    except Exception as e:
        print("钉钉推送异常：", e)

def get_signed_url(webhook, secret):
    timestamp = str(round(time.time() * 1000))
    string_to_sign = f'{timestamp}\n{secret}'
    hmac_code = hmac.new(secret.encode('utf-8'), string_to_sign.encode('utf-8'), digestmod=hashlib.sha256).digest()
    sign = urllib.parse.quote_plus(base64.b64encode(hmac_code))
    return f"{webhook}&timestamp={timestamp}&sign={sign}"

def wrap_color(text, color):
    # 钉钉markdown仅支持部分HTML标签，span+style可用
    return f'<span style="color:{color}">{text}</span>'

def wrap_icon(text, icon):
    return f'{icon}{text}'

def cloud_icon(cloud):
    # 使用更有趣的emoji区分各云平台
    icons = {
        '阿里云': '🐪',      # 骆驼
        '火山云': '🌋',      # 火山
        '腾讯云': '🐧',      # 企鹅
        '抖店云': '🛒',      # 购物车
        '华为云': '🌸',      # 樱花
        '七牛云': '🦒',      # 长颈鹿
    }
    return icons.get(cloud, '☁️')

def main():
    config = load_config()
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
    msg = f"### 云平台余额通知\n\n> 时间：{now}\n\n"
    # 阿里云
    for acc in config.get("aliyun_accounts", []):
        balance = get_aliyun_balance(acc)
        msg += f"- {wrap_icon('阿里云', cloud_icon('阿里云'))}【{acc['name']}】：{balance} 元\n"
    # 火山云
    for acc in config.get("volcengine_accounts", []):
        balance = get_volcengine_balance(acc)
        msg += f"- {wrap_icon('火山云', cloud_icon('火山云'))}【{acc['name']}】：{balance} 元\n"
    # 腾讯云
    for acc in config.get("tencent_cloud_accounts", []):
        balance = get_tencent_balance(acc)
        msg += f"- {wrap_icon('腾讯云', cloud_icon('腾讯云'))}【{acc['name']}】：{balance} 元\n"
    # 抖店云
    for acc in config.get("doudian_accounts", []):
        balance = get_doudian_balance(acc)
        msg += f"- {wrap_icon('抖店云', cloud_icon('抖店云'))}【{acc['name']}】：{balance} 元\n"
    # 华为云
    for acc in config.get("huaweicloud_accounts", []):
        balance = get_huaweicloud_balance(acc)
        msg += f"- {wrap_icon('华为云', cloud_icon('华为云'))}【{acc['name']}】：{balance} 元\n"
    # 七牛云
    for acc in config.get("qiniu_accounts", []):
        balance = get_qiniu_balance(acc)
        msg += f"- {wrap_icon('七牛云', cloud_icon('七牛云'))}【{acc['name']}】：{balance} 元\n"
    send_dingtalk(config["dingtalk_webhook"], config["dingtalk_secret"], msg)

if __name__ == "__main__":
    main()
