---
name: seedance
description: 使用已配置的火山方舟 Seedance 2.5 API 检查连接、准备视频生成请求、经确认提交任务并查询结果。用于用户要求 Seedance 视频或接续其任务；不更换 Codex 对话模型，也不用于普通 Blender 渲染。
---

# 火山方舟 Seedance 2.5

调用脚本：`/Users/jingtianyu/.codex/skills/seedance/scripts/seedance.py`，使用 `python3`。这是本地 CLI 接入，不是 MCP 服务。

- 默认模型为 `doubao-seedance-2-5-260628`。接口固定为火山方舟北京官方域名；不用此凭据访问其他平台。
- 密钥由脚本读取 `/Users/jingtianyu/.config/seedance/credentials.json`。不要通过 cat、日志、截图或回复展示密钥；项目源码不包含密钥。
- `check --offline` 只检查本地配置；`check` 只查询一项视频任务列表，不生成视频。鉴权成功不证明 Seedance 2.5 已开通生成权限、余额充足或视频已生成。
- 用 `prepare --prompt-file /absolute/prompt.txt --request-out /absolute/request.json --duration 5 --resolution 720p` 准备请求；它不联网、不覆盖已有请求。音频默认开启，可加 `--silent`。
- 图像、视频、音频参考可在请求 JSON 中明确列出，使用当前官方接口支持的 HTTPS 地址或 asset:// 标识。本地路径不等于素材已上传；此工具不负责上传。外发前明确实际素材和目的地。
- 生成前向用户说明提示词、素材、时长、分辨率、预计费用及本次任务数量。配置/鉴权请求不授权收费生成。用户批准该具体任务后才用 `submit --request /absolute/request.json --confirm-create`。
- POST 不自动重试。超时可能已经创建任务，先检查已有任务记录或控制台；没有任务 ID 时不要重复提交。
- 用 `status TASK_ID` 查询已有任务。返回视频地址后，按用户要求下载至项目目录；不要把临时签名地址作为永久交付链接。
- 费用按成功生成计；生成成功但不满意，再生成一版仍可能计费。20秒、720p、16:9、24fps、不含参考视频，官方公式估算约人民币30.24元；该值核实于2026-09-21，不是账户报价。含视频有最低token用量，实际以usage及账单为准。

只有用户要求时才提交生成；普通查询直接执行。Seedance 的生成状态与 Blender 工程、参考视频导出状态分别报告。

需要新增参数、上传流程或更新价格时查看官方文档：
- https://docs.volcengine.com/docs/ark/model-pricing?lang=zh
- https://docs.volcengine.com/docs/ark/model-release-announcement?lang=zh
- https://docs.volcengine.com/docs/ark/seedance-2-5-prompt-guide?lang=zh
