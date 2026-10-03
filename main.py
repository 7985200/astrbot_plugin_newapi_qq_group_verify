import re
import time

import httpx

from astrbot.api.all import *
from astrbot.api.event import AstrMessageEvent, filter

RESEND_INTERVAL = 60  # 与服务端一致的获取间隔(秒)，避免触发服务端限流


def _parse_groups(raw) -> list:
    """把 allowed_groups 解析成群号列表。

    兼容三种写法，避免因配置类型不一致而误判：
      - 列表：["123", "456"]
      - 逗号/空格/换行分隔的字符串："123, 456"
      - 空值/None：返回 []（表示不限制）
    """
    if raw is None:
        return []
    if isinstance(raw, (list, tuple, set)):
        items = [str(x) for x in raw]
    else:
        items = re.split(r"[,，;；\s]+", str(raw))
    return [s.strip() for s in items if s and s.strip()]


def _to_int(value, default: int) -> int:
    """宽松转 int：失败就返回默认值，绝不让它抛异常。"""
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


@register(
    "astrbot_plugin_newapi_qq_group_verify",
    "NewAPI QQ群验证",
    "在QQ群中发送 /获取验证码 生成验证码，用于 NewAPI 个人资料的 QQ 群绑定验证",
    "v1.0.0",
)
class NewApiQqGroupVerify(Star):
    def __init__(self, context: Context, config: dict = None):
        super().__init__(context)
        self.config = config if isinstance(config, dict) else {}
        self.last_request = {}  # qq_id -> 上次请求时间戳，本地 60 秒冷却

    @filter.command("获取验证码")
    async def get_verification_code(self, event: AstrMessageEvent):
        """在QQ群中生成 NewAPI 绑定用验证码。

        注意：整个方法体都兜在 try/except 里。插件抛异常有可能被 AstrBot
        的钩子链路放大（历史上有插件因未捕获异常把整个 AstrBot 进程带崩），
        所以这里保证「无论如何都给用户一句可读的回复，绝不向上抛」。
        """
        try:
            base = str(self.config.get("newapi_base_url") or "").strip().rstrip("/")
            secret = str(self.config.get("bot_secret") or "").strip()
            if not base or not secret:
                yield event.plain_result("管理员尚未完成插件配置，暂时无法获取验证码。")
                return

            group_id = str(event.get_group_id() or "").strip()
            allowed = _parse_groups(self.config.get("allowed_groups"))
            # 仅当「配置了白名单」且「能拿到群号」且「不在白名单里」时才拦截
            if allowed and group_id and group_id not in allowed:
                yield event.plain_result("本群不支持获取验证码，请到官方群操作。")
                return

            qq_id = str(event.get_sender_id() or "").strip()
            if not qq_id:
                yield event.plain_result("无法识别你的 QQ 号，请稍后再试。")
                return

            now = time.time()
            last = self.last_request.get(qq_id, 0)
            if now - last < RESEND_INTERVAL:
                remain = int(RESEND_INTERVAL - (now - last)) + 1
                yield event.plain_result(f"获取过于频繁，请 {remain} 秒后再试。")
                return

            try:
                async with httpx.AsyncClient(timeout=15) as client:
                    resp = await client.post(
                        f"{base}/api/qq-group/verification/code",
                        headers={
                            "X-QQ-Bot-Secret": secret,
                            "Content-Type": "application/json",
                        },
                        json={"qq_id": qq_id},
                    )
                try:
                    data = resp.json()
                except Exception:
                    data = {}
            except Exception as exc:
                logger.error(f"newapi qq verify: request to {base} failed: {exc}")
                yield event.plain_result("验证码服务暂时不可用，请稍后再试。")
                return

            if not isinstance(data, dict):
                data = {}
            if resp.status_code != 200 or not data.get("success"):
                msg = data.get("message") or f"获取失败（HTTP {resp.status_code}）"
                yield event.plain_result(msg)
                return

            # 成功后才记冷却，失败不占用额度（用户可立刻重试）
            self.last_request[qq_id] = now

            payload = data.get("data")
            if not isinstance(payload, dict):
                payload = {}
            code = payload.get("code")
            if not code:
                yield event.plain_result("验证码获取失败：服务端未返回验证码，请稍后再试。")
                return
            expires_in = _to_int(payload.get("expires_in"), 600)
            minutes = max(1, expires_in // 60)
            yield event.plain_result(
                f"你的验证码：{code}\n"
                f"有效期 {minutes} 分钟，请在有效期内完成绑定：\n"
                f"登录 NewAPI → 个人资料 → 点击「绑定QQ群」→ 输入验证码。\n"
                f"注意：账号邮箱需为本人QQ邮箱（与当前QQ号一致），否则无法通过验证。"
            )
        except Exception as exc:  # 最后一道防线：绝不让异常冒泡
            logger.error(f"newapi qq verify: unexpected error: {exc}")
            try:
                yield event.plain_result("验证码获取失败，请稍后再试。")
            except Exception:
                pass

    async def terminate(self):
        self.last_request.clear()
