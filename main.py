import time

import httpx

from astrbot.api.all import *
from astrbot.api.event import filter, AstrMessageEvent


@register(
    "astrbot_plugin_newapi_qq_group_verify",
    "NewAPI QQ群验证",
    "在QQ群中发送 /获取验证码 生成验证码，用于 NewAPI 个人资料的 QQ 群绑定验证",
    "v1.0.0",
)
class NewApiQqGroupVerify(Star):
    def __init__(self, context: Context, config: dict = None):
        super().__init__(context)
        self.config = config or {}
        self.last_request = {}  # qq_id -> 上次请求时间戳，本地 60 秒冷却

    @filter.command("获取验证码")
    async def get_verification_code(self, event: AstrMessageEvent):
        """在QQ群中生成 NewAPI 绑定用验证码"""
        base = str(self.config.get("newapi_base_url") or "").strip().rstrip("/")
        secret = str(self.config.get("bot_secret") or "").strip()
        if not base or not secret:
            yield event.plain_result("管理员尚未完成插件配置，暂时无法获取验证码。")
            return

        group_id = str(event.get_group_id() or "")
        allowed = [
            str(g).strip()
            for g in (self.config.get("allowed_groups") or [])
            if str(g).strip()
        ]
        if allowed and group_id and group_id not in allowed:
            yield event.plain_result("本群不支持获取验证码，请到官方群操作。")
            return

        qq_id = str(event.get_sender_id() or "").strip()
        if not qq_id:
            yield event.plain_result("无法识别你的 QQ 号，请稍后再试。")
            return

        now = time.time()
        last = self.last_request.get(qq_id, 0)
        if now - last < 60:
            remain = int(60 - (now - last)) + 1
            yield event.plain_result(f"获取过于频繁，请 {remain} 秒后再试。")
            return
        self.last_request[qq_id] = now

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
        except Exception:
            self.last_request.pop(qq_id, None)
            logger.error(f"newapi qq verify: request to {base} failed")
            yield event.plain_result("验证码服务暂时不可用，请稍后再试。")
            return

        try:
            data = resp.json()
        except Exception:
            data = {}
        if resp.status_code != 200 or not data.get("success"):
            msg = data.get("message") or f"获取失败（HTTP {resp.status_code}）"
            yield event.plain_result(msg)
            return

        payload = data.get("data") or {}
        code = payload.get("code")
        expires_in = int(payload.get("expires_in") or 600)
        yield event.plain_result(
            f"你的验证码：{code}\n"
            f"有效期 {expires_in // 60} 分钟，请在有效期内完成绑定：\n"
            f"登录 NewAPI → 个人资料 → 点击「绑定QQ群」→ 输入验证码。\n"
            f"注意：账号邮箱需为本人QQ邮箱（与当前QQ号一致），否则无法通过验证。"
        )

    async def terminate(self):
        self.last_request.clear()
