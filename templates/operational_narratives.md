# Operational Procedures

> 操作过程知识（W6 近端丰富化）。每个 Procedure 记录一个经过实践验证的操作流程。
> 格式：触发条件 → 前置检查 → 步骤 → 已知陷阱 → 最终验证 → 历史执行

---

[Procedures 在首次 ≥2 次失败后创建——不预建空条目]

---

## P-000: Cowork 目录挂载（request_cowork_directory）

**触发条件**：
- 需要让 Claude 直接读写某个目录（项目文件夹、Myco 源码、数据目录等）
- 当前会话中 Read/Write/Edit 工具无法访问目标路径
- 需要挂载 Myco 框架本身以执行 Gear 4 操作

**前置检查**：
- 确认目标路径在本机上真实存在
- 如果是 Myco 自身，路径通常为 `C:\Users\{用户名}\Desktop\Myco`（Windows）或 `~/Myco`（Mac/Linux）

**步骤**：
1. Claude 调用 `mcp__cowork__request_cowork_directory` 工具，传入完整路径
2. Cowork 弹出确认对话框，用户点击确认
3. 目录被挂载到 `/sessions/{session-id}/mnt/{目录名}/`
4. 验证：`ls /sessions/.../mnt/{目录名}/` 确认文件可见

**Cowork 本地会话（路径已知）**：
```
mcp__cowork__request_cowork_directory(path="C:\\Users\\10350\\Desktop\\Myco")
# → 挂载到 /sessions/.../mnt/Myco/
```

**已知陷阱**：
- 远程会话必须传入 path 参数；省略 path 只在本地会话弹出文件选择器
- 挂载后路径格式为 Linux 风格（`/sessions/.../mnt/Myco/`），不是 Windows 路径
- 会话结束后挂载失效，下次会话需重新挂载
- filesystem MCP 的 allowed_directories 不包含新挂载路径——必须用 Read/Write/Edit 工具，不能用 mcp__filesystem__*

**最终验证**：
```bash
ls /sessions/.../mnt/{目录名}/   # 能看到文件列表即成功
```

**历史执行**：
- 2026-04-09：ASCC 项目中挂载 `C:\Users\10350\Desktop\Myco` → 成功，Gear 4 直接用 Edit 工具写入 `docs/research_paper_craft.md`

---

## P-001: 远程服务器文件部署（Cowork → Remote, 大文件 >5KB）

**触发条件**：需要将 >5KB 文件从 Cowork Linux 沙箱部署到远程服务器（HPC/云主机）。
**前置检查**：SSH 连通性（先用 P-003 echo test 验证）。

**步骤（base64 管道模式）**：
1. Linux 沙箱：gzip 压缩 + base64 编码（减小传输体积）
2. `desktop-commander write_file` 将 base64 字符串写到 `C:\temp\deploy_b64.txt`
3. 写 Python 解码脚本 `C:\temp\decode.py`（还原文件到 `C:\temp\hpc_files\`）
4. 写部署脚本 `C:\temp\deploy.py`（subprocess → Git SSH → 远程 `cat > path`）
5. 用 P-003 模式后台执行部署脚本
6. SSH 验证：`wc -c` 确认字节数一致

**已知陷阱**：
- ❌ Cowork Linux 沙箱无 SSH 客户端——**必须从 Windows 侧**（Git SSH）发起
- ❌ `desktop-commander write_file` 单次 ~25-30 行上限——大 base64 分段写入
- ❌ Windows `\r\n` 换行符破坏 bash 脚本——传输文件必须用 `"rb"` 模式读取
- ❌ base64 字符串在 write_file 中可能截断 → gzip CRC error

**最后验证**：远程 `wc -c` 与本地一致。

---

## P-002: 远程服务器文件部署（Cowork → Remote, 小文件 ≤5KB）

**触发条件**：需要将 ≤5KB 文件部署到远程服务器。

**步骤**：
1. 写部署脚本 `C:\temp\deploy_small.py`（内含 `open(path, "rb").read()` + SSH pipe）
2. 用 P-003 模式执行

**已知陷阱**：同 P-001，必须 `"rb"` 读取文件。

**最后验证**：`head -5` 检查文件开头。

---

## P-003: Desktop-Commander 长任务标准模式

**触发条件**：任何通过 desktop-commander 执行的 SSH 命令 | 预计 >20s 的任何操作。

**核心模式（必须后台执行 + 文件读取）**：

```python
# 1. 写任务脚本到 C:\temp\task_XXX.py
# 脚本内使用 Git SSH:
SSH = r"C:\Progra~1\Git\usr\bin\ssh.exe"

# 2. desktop-commander start_process 后台执行：
cmd /c python C:\temp\task_XXX.py > C:\temp\task_XXX_out.txt 2>&1

# 3. 完成后 desktop-commander read_file 读取输出文件
```

**已知陷阱**：
- ❌ **60s 硬超时**：desktop-commander start_process 默认超时。SSH 双跳必定超时——**永远后台执行**
- ❌ **UTF-16 输出**：Windows cmd 重定向可能产生 UTF-16——用 Windows MCP FileSystem 读取（自动处理编码）
- ❌ **30 行写入限制**：长脚本分多次 write_file 或 base64 传输
- ❌ **空结果 ≠ 成功**：SSH 超时返回空——先验证 SSH 本身是否通
- ❌ **禁止写用户桌面**：工作脚本绝不写到 Desktop/。应写到项目 scripts/ 目录（有复用价值）或系统 Temp 目录（`%LOCALAPPDATA%\Temp\`，一次性临时文件）。会话结束前清理临时文件

**最后验证**：output 文件存在且内容非空，无 traceback。

---

## P-004: 会话临时文件清理

**触发条件**：会话结束前 | 临时文件 >10 个。

**步骤**：
1. 检查项目根目录（`ls *.py *.txt` — 调试残留）
2. 检查 `C:\temp`（保留核心脚本，删除本次会话产物）
3. 检查 Cowork session 目录（`/sessions/.../`）

**历史执行**：ASCC 项目曾一次清出 89 个临时文件（2026-04-03）。
