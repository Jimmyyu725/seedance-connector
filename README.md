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

## Mac 当前用户全局默认

- 主变量：`ARK_API_KEY`；兼容别名：`SEEDANCE_API_KEY`、`VIDEO_API_KEY`。
- 默认服务变量：`VIDEO_API_PROVIDER`、`VIDEO_API_BASE_URL`、`VIDEO_API_MODEL`。
- Shell 默认载入：`/Users/jingtianyu/.zshenv` 和 `/Users/jingtianyu/.profile`。
- 私有环境文件：`/Users/jingtianyu/.config/video-generation/default.env`（600）。
- 用户登录启动项：`/Users/jingtianyu/Library/LaunchAgents/com.jingtianyu.video-api-env.plist`。
- 新终端生效；已经运行的图形应用需退出后重新启动以继承新环境。程序仍需支持相应环境变量；不是所有视频软件自动切换供应商。
- 显式设置的进程环境变量优先，不覆盖项目自己的非空变量。此凭据默认仅用于火山方舟，不用于其他平台。
- 全局回退：`/Users/jingtianyu/Documents/Codex/seedance-connector/global-env/ROLLBACK.sh`，会保留恢复前副本，不删除原始密钥文件。
