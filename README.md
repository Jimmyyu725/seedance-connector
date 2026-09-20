# Seedance 2.5 · 火山方舟接入

供 Codex 使用的轻量 Skill＋Python 标准库调用工具；不更换 Codex 主模型，不需要安装 SDK，不运行后台 MCP 服务。

## 当前配置

- 提供商：火山方舟。
- 模型：`doubao-seedance-2-5-260628`。
- 官方接口：`https://ark.cn-beijing.volces.com/api/v3`。
- Skill：`/Users/jingtianyu/.codex/skills/seedance`。
- 密钥：`/Users/jingtianyu/.config/seedance/credentials.json`，权限 600；密钥不在本源码目录。

## 使用

在 Codex 中说：`使用 $seedance，先准备一个5秒720p视频方案并估价，暂不生成。`

命令示例：

```sh
python3 /Users/jingtianyu/.codex/skills/seedance/scripts/seedance.py check
python3 /Users/jingtianyu/.codex/skills/seedance/scripts/seedance.py prepare --prompt-file /absolute/prompt.txt --request-out /absolute/request.json --duration 5 --resolution 720p
python3 /Users/jingtianyu/.codex/skills/seedance/scripts/seedance.py submit --request /absolute/request.json --confirm-create
python3 /Users/jingtianyu/.codex/skills/seedance/scripts/seedance.py status TASK_ID
```

`prepare` 不联网；`submit` 会创建可能收费的生成任务，配置操作本身不包含该授权。此版本不上传本地媒体；先完成单独授权的素材上传，再填实际 HTTPS 地址或官方素材 ID。

鉴权检查只读任务列表，不创建任务；它不证明模型的实际生成权限或余额。POST 超时不自动重试。出现权限或余额错误，保留原始错误并核实官方控制台，勿换模型冒充 Seedance 2.5。

`VERIFICATION.txt` 记录测试和实际只读结果。`ROLLBACK.sh` 将配置恢复为禁用状态，覆盖前保存当前配置，不删除密钥或任务记录。
