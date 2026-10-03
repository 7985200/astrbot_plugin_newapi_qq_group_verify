# astrbot_plugin_newapi_qq_group_verify

NewAPI QQ 群验证插件的 AstrBot 端：群成员在群里发送 `/获取验证码`，插件调用 NewAPI 的
`POST /api/qq-group/verification/code`（请求头 `X-QQ-Bot-Secret`）为该 QQ 号签发一个 6 位验证码（10 分钟有效、60 秒冷却）。

用户拿到验证码后，在 NewAPI **个人资料 → 绑定QQ群** 弹窗里提交。NewAPI 会校验：

- 账号邮箱必须是该 QQ 号的 QQ 邮箱（前缀与 QQ 号一致）；
- 一个 QQ 号只能绑定一个账号。

## 配置项（AstrBot 插件配置页）

| 配置 | 说明 |
|---|---|
| `newapi_base_url` | NewAPI 站点地址，如 `https://your-domain.com`（不要带末尾斜杠） |
| `bot_secret` | 与 NewAPI 后台「QQ群验证」里的 Bot 密钥一致（建议 48 位随机十六进制） |
| `allowed_groups` | 允许获取验证码的群号列表，留空表示所有群都允许 |

## 使用步骤

1. 在 NewAPI 后台：系统设置 → 安全与限制 → QQ群验证，配置群号和 Bot 密钥，开启验证开关；
2. 在 AstrBot 插件配置里的 `newapi_base_url` 与 `bot_secret` 填上对应值；
3. 把机器人拉进群，群成员发送 `/获取验证码` 即可。

> 提示：本插件只负责发码，验证与绑定逻辑在 NewAPI 侧完成。
