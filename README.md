# astrbot_plugin_newapi_qq_group_verify

AstrBot 插件：群成员在群里发送 `/获取验证码`，为 **NewAPI** 的「QQ 群验证」签发验证码。

---

##  先决条件（必读）

**本插件只是"发码端"，必须先在 NewAPI 上安装配套补丁，否则调用接口会 404。**

 **NewAPI 补丁（含逐步安装说明）**：
**https://github.com/7985200/newapi-qq-group-verification**

装完补丁后，NewAPI 才会有 `POST /api/qq-group/verification/code` 这个接口，本插件才能工作。

---

## 它做什么

1. 群成员发送 `/获取验证码`，插件调用 NewAPI 的
   `POST /api/qq-group/verification/code`（请求头 `X-QQ-Bot-Secret`）
   为该 QQ 号签发一个 **6 位验证码**（10 分钟有效、60 秒冷却）；
2. 用户到 NewAPI **个人资料 → 绑定QQ群** 弹窗里填入验证码；
3. NewAPI 校验：
   - 账号邮箱必须是该 QQ 号的 QQ 邮箱（前缀与 QQ 号一致）；
   - 一个 QQ 号只能绑定一个账号；
4. 未完成验证的用户调用模型会被拦截。

## 安装

**方式一（推荐）**：把本仓库整个目录放进 AstrBot 的 `data/plugins/` 下，重载插件。

**方式二**：在 AstrBot 插件页上传本仓库的 zip 包。

## 配置项（AstrBot 插件配置页）

| 配置 | 说明 |
|---|---|
| `newapi_base_url` | 你的 NewAPI 站点地址，如 `https://your-domain.com`（不要带末尾斜杠） |
| `bot_secret` | 与 NewAPI 后台「QQ群验证」里的 **Bot 密钥**一致（建议 48 位随机十六进制） |
| `allowed_groups` | 允许获取验证码的群号列表，留空表示所有群都允许 |

## 使用步骤

1. 在 NewAPI 后台：**系统设置 → 安全与限制 → QQ群验证**，配置群号和 Bot 密钥，开启验证开关；
2. 在本插件配置里填上对应的 `newapi_base_url` 与 `bot_secret`；
3. 把机器人拉进群，群成员发送 `/获取验证码` 即可。

> 提示：本插件只负责发码，**验证与绑定逻辑全部在 NewAPI 侧完成**。

## 相关仓库

- **NewAPI 补丁（必装）**：https://github.com/7985200/newapi-qq-group-verification
