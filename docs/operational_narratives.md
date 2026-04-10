# Operational Procedures

> 操作过程知识（W6 近端丰富化）。每个 Procedure 记录一个经过实践验证的操作流程。
> 格式：触发条件 → 前置检查 → 步骤 → 已知陷阱 → 最终验证 → 历史执行
> 最后更新：2026-04-09

---

## P-000: Cowork 目录挂载（request_cowork_directory）

**触发条件**：
- 需要让 Claude 直接读写某个目录（项目文件夹、Myco 源码等）
- 当前会话中 Read/Write/Edit 工具无法访问目标路径

**前置检查**：
- 确认目标路径在本机上真实存在
- Myco repo 路径通常为 `C:\Users\{用户名}\Desktop\Myco`（Windows）

**步骤**：
1. Claude 调用 `mcp__cowork__request_cowork_directory` 工具，传入完整路径
2. Cowork 弹出确认对话框，用户点击确认
3. 目录被挂载到 `/sessions/{session-id}/mnt/{目录名}/`
4. 验证：`ls /sessions/.../mnt/{目录名}/` 确认文件可见

**已知陷阱**：
- ❌ 挂载后路径格式为 Linux 风格（`/sessions/.../mnt/Myco/`），不是 Windows 路径
- ❌ 会话结束后挂载失效，下次会话需重新挂载
- ❌ 必须用 Read/Write/Edit 工具操作挂载目录，不能用 `mcp__filesystem__*`

**最终验证**：
```bash
ls /sessions/.../mnt/{目录名}/   # 能看到文件列表即成功
```

**历史执行**：
- 2026-04-09：挂载 `C:\Users\10350\Desktop\Myco` → 成功，v0.9.0 打包 + 自我应用全程在此目录下执行

---

## P-001: Windows 环境 Myco 开发操作规范

**触发条件**：
- 在 Windows 机器上通过 Cowork 开发 Myco 框架本身
- 执行 git 操作、CLI 调试、PyPI 上传等任何需要 Windows 工具链的任务

**工具选择矩阵**：

| 操作类型 | 推荐工具 | 原因 |
|---------|---------|------|
| 快速 git status/log | `Bash`（Linux sandbox `git -C path`） | 快，输出干净 |
| git commit（含多行消息） | `desktop-commander` + `-F` 文件写法 | CMD 会截断 `-m` 里的换行符 |
| 删除 `.git/index.lock` | `mcp__Windows-MCP__PowerShell` | Linux sandbox `rm` 无权操作 Windows `.git/` |
| 长时间操作（>20s） | `desktop-commander start_process` + `read_process_output` | PowerShell MCP 有 60s 硬超时 |
| PyPI twine 上传 | CMD: `chcp 65001 && set PYTHONIOENCODING=utf-8 && twine upload dist/*` | rich 进度条含 U+2022，GBK 无法编码（v0.9.0 后 CLI 自动 UTF-8，但 twine 本身不经 myco CLI） |
| 文件重命名/移动 | `mcp__Windows-MCP__PowerShell` `Move-Item` | Linux sandbox 无写权限到 Windows git tracked 文件 |

**git commit 标准写法（Windows）**：
```
# 1. 将 commit message 写入文件
Write(commit_msg.txt, "feat: ...")

# 2. 用 -F 提交
git -C C:\path\to\repo commit -F commit_msg.txt
```

**myco CLI 不在 PATH 时的 fallback**：
```
# 检查 myco 是否在 PATH
where myco  (cmd) / which myco  (bash)

# Fallback 1: 直接调用脚本
python scripts\lint_knowledge.py --project-dir .

# Fallback 2: 确认 editable install
pip show myco  # 应显示 Location: ...src
```

**PyPI 上传完整命令**：
```cmd
chcp 65001
set PYTHONIOENCODING=utf-8
python -m twine upload dist/* --repository myco
```

**已知陷阱**：
- ❌ `PYTHONUTF8=1` 在 Python 3.13 的 CMD 里会被忽略（只接受 "1"/"0"），用 `PYTHONIOENCODING=utf-8` 代替
- ❌ `cd /d "C:\path with spaces"` 在 desktop-commander 里可能有编码问题，改用 `git -C C:\path\to\repo` 语法
- ❌ **Windows-MCP PowerShell 不稳定**：Windows-MCP PowerShell 工具有 60s hard limit 且本身调用不稳定；所有 >5s 的操作**优先用 desktop-commander**，Windows-MCP 仅作备用（2026-04-10）
- ❌ **Windows cmd/GBK 编码**：cmd 默认 GBK 编码，任何输出含中文或 emoji 的 Python 脚本都会 UnicodeEncodeError。标准 header：`import sys; sys.stdout.reconfigure(encoding='utf-8')`（2026-04-10）
- ❌ **禁止写桌面**：工作脚本绝不写到 `C:\Users\...\Desktop\`。应写到项目 `scripts/`（有复用价值）或 `C:\Users\...\AppData\Local\Temp\`（一次性临时文件）。会话结束前必须清理临时文件。（来源：ASCC g4-candidate 2026-04-09）
- ❌ **SSH ProxyJump 必须用 config alias，不要直连**：Git SSH 直连跳板机后的目标主机会在 kex 阶段断开（`kex_exchange_identification: Connection closed by remote host`）。必须用 SSH config 别名（内含 `ProxyJump + IdentityFile`）。`-F` 参数使用 MSYS 路径格式：`/c/Users/<user>/.ssh/config`（Windows 路径不被 Git SSH 识别）。（来源：ASCC g4-candidate 2026-04-10）
- ❌ **远程目录名 ≠ 代码变量名**：远程服务器上的目录命名约定可能与代码中的变量名不同（如 `td3_native` vs `td3`）。写任何远程查询脚本前**必须先 `ls` 确认实际目录名**，不要假设与本地代码一致。遇到计数为 0 的异常先验证目录名再排查其他原因。（来源：ASCC g4-candidate 2026-04-10）

**最终验证**：
- git 操作：`git -C C:\...\Myco log --oneline -3` 确认最新 commit 正确
- PyPI 上传：`pip install myco==<version>` 在干净 venv 中验证

**历史执行**：
- 2026-04-09：v0.9.0 完整发布周期，上述所有坑均踩过并记录于此

---
