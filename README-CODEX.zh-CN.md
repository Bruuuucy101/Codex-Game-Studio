# Claude Code Game Studios 的 Codex 适配版

这是基于 [Donchitos/Claude-Code-Game-Studios](https://github.com/Donchitos/Claude-Code-Game-Studios) 制作的项目级适配，不是官方 Codex 移植版。目标是完整保留原工作室的内容、流程和质量关卡，并适配 Codex 的工具与协作机制。

基线为原版 v1.0.0，提交 `984023ddac0d5e27624f2baacde6105e45de375f`。原版 417 个受版本控制的文件全部保留：原始字节或逐项记录的修正均可验证，原 LICENSE 和基线锁均未改动。修正的原始与当前哈希、问题链接及原因见[补丁记录](.codex/upstream-patches.json)。公开版是可追溯到该上游提交的源码快照；不声称保留上游 Git 历史。可以继续在同一项目使用原版 Claude Code 入口。

**此前 v0.1.1-beta 验收记录：完整保留工作流与角色范围，并修正已确认的继承问题；73 项确定性测试、6 个真实 Git 更新场景和当时 3 个行为抽测已通过。尚不能称为所有引擎、所有工作流都已验证的 100% 运行等价版本。** 详细证据见 [验证报告](docs/codex-adapter/validation.md)。

**当前 v0.2.0-beta：74 个工作流、57 个角色。候选版本 CI 的五个必需任务通过，包含 128 项适配器测试、每个 Web 模板 10 项单元 + 4 项 Chromium 测试、libGDX 7 项纯逻辑 + 3 项真实无界面测试与桌面打包。另有 5 个新的配置/咨询行为抽测。最终 main CI、发布标签和下载 ZIP 验证是独立关卡，此处不提前宣告完成。** 见[本次功能证据](docs/codex-adapter/feature-validation-2026-09-21.md)。

## 保留了什么

| 原版内容 | Codex 接入方式 |
|---|---|
| 73 个原工作流 + setup-tool | 当前 74 个 `ccgs-*` 入口，每次读取完整原工作流；没有用摘要替代 |
| 49 个原角色 + 2 个 Web 引擎负责人 + 工具流水线开发者 + 5 个 libGDX 专家 | 当前 57 个角色配置，嵌入完整规范；原 49 个身份保留 |
| 11 组路径规则 | 保留原文与适用路径；编辑前加载，受支持的工具事件额外自动注入 |
| 12 个钩子脚本 | 全部保留；11 个脚本接入事件桥接，通知脚本有明确平台差异 |
| 40 个模板文件 | 包括嵌套目录，按实际文件清点；原 README 的数字不是此处验收依据 |
| 126 份测试框架 Markdown 文件 | 保留原测试规范、说明和管理文档；文件数量不代表已执行 126 项测试 |
| Godot、Unity、Unreal 分支 | 原引擎资料、专家分工和路由保持完整 |
| full / lean / solo 审查模式 | 保留原有含义、批准关卡、阻塞和恢复流程 |

逐项对应关系见 [能力清单](docs/codex-adapter/capabilities.md)。原版角色记忆仍会读取，后续 Codex 记忆写在项目内的 `production/agent-memory/`。

## 开始使用

1. 在 Codex 中将**克隆或解压后的仓库根目录（包含 `AGENTS.md`）**打开为项目，并在该项目中新建任务。其他目录中的任务不会自动取得本项目的技能和钩子。
2. 环境需要 Python 3.10+、Git、Bash。从 GitHub 克隆后会带有 Git 仓库；如果使用压缩包，需要先在解压后的项目根目录运行 `git init`，供钩子定位项目。不要直接把整套文件覆盖到已有游戏项目。
3. 按 Codex 的正常流程信任项目，在 `/hooks` 中检查并启用项目钩子。这是 Codex 的钩子信任要求；适配器不会替你修改信任记录。未启用时，技能与规则指令仍可读取，但不能声称自动校验已运行。
4. 输入 `使用 ccgs-help 查看工作室工作流`。要开始新游戏，输入 `使用 ccgs-start，按原版流程引导我开始`；也可以在支持技能选择的界面使用 `$ccgs-start`。

框架会按原流程询问游戏方向、引擎等必要信息。项目尚未初始化，交付文件中没有擅自填入游戏设定。

后续示例：

```text
使用 ccgs-dev-story，实现 production/epics/里的指定故事，保留原有前置检查和测试要求。
使用 ccgs-story-done，审查该故事；缺少要求的证据时不得标记完成。
使用 ccgs-team-qa，对当前 sprint 做原版完整 QA 流程。
```

原文中的 `/dev-story` 等名称映射到相应 `ccgs-*` 技能；它们不是要在终端执行的命令。命名空间用于避免与你已有技能重名。

## 已知的平台差异

- **角色启动：**本机 CLI 0.150.1 的测试会话不能按自定义角色类型直接启动，但已验证通过真实子代理读取完整角色指令的兼容方式。历史测试解析了原 49 个配置；当前 CI 解析全部 57 个配置。这不等于该主机原生加载了所有角色。需要多个角色时按宿主并发限制分批执行；没有真实委派工具时必须报告阻塞。
- **模型：**角色默认不指定模型或推理强度，按宿主启动默认值、父任务模型的顺序继承；显式配置的覆盖值优先。Claude 的 opus / sonnet / haiku 元数据保留，不直接当成 Codex 模型名。本机旧 CLI 不能调用当前桌面使用的 `gpt-6-astra`；只读抽测临时指定 `gpt-5.5` 成功，未改你的默认配置。应使用支持所选模型的 CLI/桌面版本。
- **通知与状态栏：**Codex 没有相同的 Notification 钩子；原 Windows 通知脚本保留，提醒使用宿主通知设置。原自定义状态栏由项目状态查询替代，不能复制同一界面或上下文占用统计。
- **权限、回合和记忆：**原角色工具限制与回合预算作为角色指令保留，不能承诺与 Claude 相同的强制执行机制。跨项目记忆需要另行明确配置。原始项目记忆会加载，新的记忆保存在本项目。
- **自动检查的范围：**文件补丁可逐文件验证；任意脚本、外部编辑器或 MCP 写入不能保证收到同样事件，需要显式加载规则并验证受影响文件。依赖原提交/推送钩子时，在仓库根目录直接运行相应 Git 操作。原脚本本身也有校验范围限制，详见 [钩子说明](docs/codex-adapter/hooks.md)。
- **平台与引擎：**适配器实测包括 macOS；Linux CI 已运行两个 Web 模板的 Chromium 测试和 libGDX 无界面测试/桌面打包。Windows 原生注册、Godot/Unity/Unreal 游戏验收、libGDX GPU/输入/音频仍未验证。

## 自检与维护

在项目根目录执行：

```sh
python3 tools/ccgs_codex.py doctor
python3 tools/ccgs_codex.py check --strict-upstream
python3 -m unittest discover -s tests/codex_adapter -v
```

`doctor` 会区分结构、已审阅补丁、原始字节一致性和运行验证范围。`--strict-upstream` 接受原始字节或补丁记录中的精确哈希；额外的 `check --pristine-upstream` 要求完全等于原版，因此会按预期报告补丁记录中的修正文件。开始游戏后填写文档、状态或偏好，也会产生需要审阅的差异，不能直接丢弃。更新方法见[源码维护](docs/codex-adapter/source-maintenance.md)，本轮处理范围见[全部 34 个问题的审计](docs/codex-adapter/upstream-issues-2026-09-21.md)。

修改原技能、角色、规则或运行时适配说明后执行：

```sh
python3 tools/ccgs_codex.py generate
python3 tools/ccgs_codex.py check
```

生成器管理的文件可以重新生成，请在原始定义中维护内容，不要把独有修改写进生成文件。生成器拒绝覆盖未归它管理的冲突文件、通过符号链接重定向的输出，以及未审阅的源条目删除。缺失运行时契约时不会生成一个假成功版本。

可选命令：`status` 查看项目状态；`rules <文件路径>` 查看对应原规则；`role <原角色名>` 输出完整角色指令；`workflow <原技能名>` 输出完整工作流与适配约定。

公开仓库使用 `main` 分支；原作者仓库和基线提交已记录在能力清单中。将来可以读取上游更新，先审阅差异和适配影响，再引入、重新生成并测试。不要只更新基线哈希来掩盖未审阅的变更；也不要用新的模板覆盖已有游戏内容。本项目不会自动安装全局技能。

## 进一步验收

建议在你实际选定的引擎上，走完一个小功能的完整流程：需求 → ADR → 故事 → 实现与测试 → 独立审查 → 结案 → 阶段 QA。之后使用保留的 `ccgs-skill-test` 测试规范扩大覆盖。通过这一轮才有依据评价你的实际开发环境，而不仅是适配层本身。

## Web 引擎扩展

现可选择 Phaser 3（phaser/phaser3）和 Three.js（threejs/three/three.js），
使用新增的两个引擎角色和完整的配置、审查、测试路由。原 73 个工作流、49 个角色身份和
Godot 三种语言模式、Unity、Unreal 分支保留；加入工具流水线和 libGDX 专家后当前共 57 个角色。

`templates/web/` 提供收集小游戏、锁定依赖和复制工具。先用
`python3 tools/ccgs_codex.py scaffold-web phaser --target "你的项目目录"` 预览，
确认清单后加 `--write` 复制；工具不会覆盖文件或安装依赖。浏览器验收与构建结果分别
记录在 [验证说明](docs/codex-adapter/validation.md)，不能把角色或配置存在当作运行验证通过。版本为 Phaser 3.90.0 和
Three.js 0.186.0/r186，已有项目的锁定版本优先。参见 [Web 开发说明](.claude/docs/web-game-development.md)。

## 独立工具项目

`ccgs-start` 的 E 路径和 `ccgs-setup-tool` 可建立、更新或从代码整理
`tools/TOOL_SPEC.md`。独立工具使用 `tooling` 标记与 `Tooling Project` 阶段；
游戏里的导出器保持原游戏阶段、引擎配置和审查模式。纯 CSV/JSON 工具无需安装引擎。
实现由 lead-programmer 分派给 game-pipeline-developer，再由独立角色与 QA 审查。
详见 [工具项目约定](.claude/docs/tooling-projects.md) 和
[可运行 CSV 转 JSON 示例](examples/tooling/level-exporter/README.md)。示例验证文本文件处理，
不代表已验证 Unity/Godot/Unreal 原生二进制转换或导入。


libGDX 使用 `/setup-engine libgdx [版本]`。Java 模板包含 core、lwjgl3、headless，
通过 `python3 tools/ccgs_codex.py scaffold-libgdx --target PATH` 预览，添加 `--write`
才复制；不会覆盖原文件或自动安装依赖。实际无界面生命周期测试与桌面打包分别记录，
GPU、移动端、GWT、Kotlin/KTX 验证范围见[libGDX 开发说明](.claude/docs/libgdx-development.md)。

## 新增功能的运行步骤与边界

在 Codex 对话中输入 `使用 ccgs-setup-tool level-exporter author --review lean`；
已有工具可用 `update` 或 `adopt`。这是编写工具契约，不能算作已实现或已独立审查。
引擎配置可输入 `使用 ccgs-setup-engine phaser 3.90.0`、
`使用 ccgs-setup-engine threejs 0.186.0` 或 `使用 ccgs-setup-engine libgdx 1.14.2`。
已有项目的锁定版本优先，保留 full / lean / solo 的原审查要求。

从工作室根目录预览（目标为当前目录下的子目录），再仅为选定命令追加 `--write`：

```sh
python3 tools/ccgs_codex.py scaffold-web phaser --target my-web-game
python3 tools/ccgs_codex.py scaffold-web threejs --target my-three-game
python3 tools/ccgs_codex.py scaffold-libgdx --target my-java-game
```

复制拒绝碰撞和符号链接，保留现有文件，不安装依赖。后续在**对应目标目录**运行：

- Web 需要 Node >=22.12.0 和 npm（CI 使用 22.14.0）。依次运行 `npm ci`、`npm run typecheck`、`npm test`、`npm run build`；`npm run dev` 启动本地游戏。浏览器验证先运行 `npx playwright install --with-deps chromium`，再运行 `npm run test:browser`。这些安装步骤会下载依赖。
- libGDX 需要 JDK 21，使用内置 Gradle 8.14.3 wrapper 和严格依赖锁。运行 `./gradlew :core:test :headless:test :lwjgl3:installDist --no-daemon`，再运行 `./gradlew :headless:run --no-daemon`。首次执行下载 Gradle/Maven 依赖；Windows 对应 `gradlew.bat`，该平台未实测。GPU、音频和手感不能由无界面测试或打包结果替代。
- 示例 CSV 转换器只需 Python 3.10+ 标准库，无需游戏引擎或外部供应商。

board-sync #82 只有设计，未实现；本版没有任何 board snapshot/setup/sync 命令或依赖。
创意 MCP #40、付费素材后端 #23、NPC TTS #14 也继续延后。移动端、Kotlin/KTX/GWT、
WebGPU 和供应商执行未验证。第三方依赖沿用各自许可，官方 Gradle wrapper 为 Apache-2.0；
见[第三方声明](templates/libgdx/THIRD-PARTY-NOTICES.md)及[升级说明](UPGRADING.md)。
