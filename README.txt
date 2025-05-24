# 云平台余额自动监控与钉钉通知脚本说明

## 功能简介
本脚本支持自动采集多云平台（阿里云、火山云、腾讯云、抖店云、华为云、七牛云）多个账号的余额，并通过钉钉加签机器人推送余额通知。

## 安装与环境准备
1. **Python 3.7+**
2. 安装依赖包：
   ```shell
   pip install -r requirements.txt
   ```
   > 如需采集腾讯云、华为云余额，请取消 requirements.txt 中相关注释后再安装。

3. 配置 `config.yaml`，参考示例，填写各云平台账号的 AK/SK/Secret 等信息。

## 各云平台最小授权说明

### 阿里云
- **最小权限策略**：AliyunBSSFullAccess 或自定义策略，需包含 `bss:QueryAccountBalance` 权限。
- **说明**：建议为子账号分配最小只读权限，避免泄露风险。

### 火山云（火山引擎）
- **最小权限策略**：BillingReadOnlyAccess 或自定义策略，需包含 `Billing:QueryBalanceAcct` 权限。

### 腾讯云
- **最小权限策略**：QcloudFinanceReadOnlyAccess 或自定义策略，需包含 `finance:DescribeAccountBalance` 权限。
- **说明**：子用户需在【访问管理】中授权。

### 抖店云
- **最小权限**：需有余额查询API权限，具体以抖店云开放平台文档为准。
- **说明**：需完成应用授权，获取 app_key/app_secret。

### 华为云
- **最小权限策略**：BSS Administrator 或自定义策略，需包含 `bss:customerAccount:query` 权限。
- **说明**：仅支持 cn-north-1 区域。

### 七牛云
- **最小权限**：主账号 AK/SK，需有结算中心/账户余额API访问权限。
- **说明**：部分个人账号或未开通结算中心的账号无法API查余额。

## 钉钉机器人配置
- 需在钉钉群添加自定义机器人，开启“加签”安全设置。
- 在 `config.yaml` 填写 webhook 和 secret。

## 运行脚本
```shell
python cloud_balance_notify.py
```

## 其他说明
- 支持多账号循环采集，异常自动捕获。
- 钉钉通知内容支持表情区分各云平台。
- 若需采集更多云厂商余额或业务数据，可扩展相应采集函数。

---
如遇接口权限不足、API变更、余额字段异常等问题，请根据报错提示调整云平台授权或反馈详细信息。
