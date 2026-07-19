"""
语音入口 —— ASR 适配层（Adapter）。

设计目标（面试可讲）：
- 前端录音（Web Audio / MediaRecorder）→ 后端 /api/asr → 转写为文本 → 直接喂给 Agent 编排层，
  实现「语音直达服务单入口」，对应痛点五「缺乏 AI 赋能 / 对话直达服务单」。
- ASRProvider 抽象：默认 MockASRProvider（离线演示，回显/规则映射），生产可切换 FunASRProvider。
- FunASRProvider 预留：通过 funasr 的 SenseVoice/Paraformer 模型做中文语音识别，
  仅在部署环境 `pip install funasr modelscope` 且能拉取模型权重时启用，避免开发/演示环境强依赖。

说明：真实模型权重（几十~几百 MB）需联网下载，演示环境用 Mock 即可跑通完整链路；
生产部署文档见 README「语音入口（可选）」一节。
"""

from typing import List, Optional, Protocol


class ASRProvider(Protocol):
    def transcribe(self, audio_bytes: bytes, fmt: str = "webm") -> str:
        ...


class MockASRProvider:
    """
    离线回显型识别器：演示用。
    行为与真实 ASR 一致——接收音频、返回文本——但文本由「映射规则」生成，
    便于在无 GPU / 无模型的机器上完整演示「语音→工单」链路。
    """

    # 关键词 → 意图短语映射，模拟「说一句话即生成工单」的体验
    _MAP = [
        ("ukey", "我要申请制作一个 Ukey"),
        ("邮件", "我需要开通远程邮件帐号并扩容到 5G"),
        ("会议", "我要借用一台会议终端并预约视频会议"),
        ("打印机", "我需要领用一台打印机"),
        ("巡检", "对应用系统做一次自动化巡检"),
        ("异常", "计算存储设备出现告警，请帮我生成处置工单"),
    ]

    def transcribe(self, audio_bytes: bytes, fmt: str = "webm") -> str:
        size = len(audio_bytes)
        # 用音频大小做确定性选择，让每次演示结果稳定可复现
        if size == 0:
            return "（未检测到音频输入）"
        idx = size % len(self._MAP)
        return self._MAP[idx][1]


class FunASRProvider:
    """
    预留：FunASR 真实中文语音识别。
    启用条件：部署环境安装 `funasr modelscope` 并能下载模型权重；
    通过设置 settings.asr_backend = "funasr" 启用。
    """

    def __init__(self, model_dir: str = "iic/SenseVoiceSmall"):
        try:
            from funasr import AutoModel
        except Exception as e:  # pragma: no cover
            raise RuntimeError(
                f"FunASRProvider 需要 funasr 与 modelscope，且能下载模型权重：{e}。"
                "演示环境请使用 mock 后端。"
            )
        self._model = AutoModel(
            model=model_dir,
            vad_model="fsmn-vad",
            punc_model="ct-punc",
            disable_update=True,
        )

    def transcribe(self, audio_bytes: bytes, fmt: str = "webm") -> str:
        import tempfile, os

        with tempfile.NamedTemporaryFile(suffix=f".{fmt}", delete=False) as f:
            f.write(audio_bytes)
            path = f.name
        try:
            res = self._model.generate(input=path, language="auto", use_itn=True)
            return res[0]["text"] if res else ""
        finally:
            os.remove(path)


def build_asr_provider(backend: str = "mock") -> ASRProvider:
    if backend == "funasr":
        return FunASRProvider()
    return MockASRProvider()
