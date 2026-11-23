# 前线部署工程实践指南

从发现客户现场的问题，到用软件、数据与 AI 交付可运维、可接管的生产系统。

**[在 GitBook 阅读第一章 · FDE 的角色边界](https://yeasy.gitbook.io/forward_deployed_engineering_guide/di-yi-bu-fen-ru-men-pian-li-jie-fde/01_role)**

[全书目录（GitHub）](https://github.com/yeasy/forward_deployed_engineering_guide/blob/main/SUMMARY.md) · [正式 PDF 和单文件 HTML（发布页）](https://github.com/yeasy/forward_deployed_engineering_guide/releases/latest)

<img src="cover.png" width="210" alt="前线部署工程实践指南封面">

## 关于本书

Forward Deployed Engineering，简称 FDE，本书译作“前线部署工程”。它是指把工程师嵌入真实业务现场，用软件、数据、AI、平台和运营方法解决复杂组织问题的工程实践，有别于传统售前、外包实施或一次性顾问交付。FDE 的目标是把模糊问题转化为可运行、可观测、可治理、可持续演进的生产系统，交付物不止于方案文档。

FDE 已从少数公司的组织实践扩展为企业 AI 和数字化转型的重要交付模式：

- Palantir 的 FDE 实践将这一角色带入行业视野，并在 Foundry 文档中提供 [AI FDE](https://www.palantir.com/docs/foundry/ai-fde/overview)。
- OpenAI 推出 [OpenAI Deployment Company](https://openai.com/index/openai-launches-the-deployment-company/)，强调工程师嵌入组织、识别高影响场景、重构关键工作流。
- Accenture 与 Microsoft 成立面向企业 AI 规模化的 [FDE 实践](https://newsroom.accenture.com/news/2026/accenture-launches-microsoft-forward-deployed-engineering-practice-to-help-organizations-scale-ai-across-the-enterprise)。

本书面向希望系统掌握 FDE 的工程师、技术负责人、产品经理、解决方案架构师、平台工程师、AI 应用开发者和企业数字化负责人。

## 从哪里开始

- **第一次接触 FDE** · 从[第一章 · FDE 的角色边界](https://yeasy.gitbook.io/forward_deployed_engineering_guide/di-yi-bu-fen-ru-men-pian-li-jie-fde/01_role)开始，先弄清 FDE 与售前、解决方案架构师及平台团队各自负责什么。
- **即将进入客户现场** · 从[第二章 · 现场问题发现](https://yeasy.gitbook.io/forward_deployed_engineering_guide/di-yi-bu-fen-ru-men-pian-li-jie-fde/02_discovery)开始。选一条业务流程，记录现状与约束，写出第一轮试点要验证的假设。
- **准备将试点转入生产** · 从[用户上线与运营切换](https://yeasy.gitbook.io/forward_deployed_engineering_guide/di-san-bu-fen-sheng-chan-pian-ai-yuan-sheng-xi-tong/11_production/11.4_launch)开始，制定分批切换计划，用[交付证据包模板](appendix/templates.md)检查数据、安全、LLMOps 和运维证据，以及回滚和接管的条件与负责人。

想完整演练一次交付，可以用[综合实战](appendix/capstone.md)中的制造案例，从现场调研做起，交付一份可供客户接管评审的证据包。

<details>

<summary>按角色选读</summary>

- **FDE 与解决方案工程师** · 从[角色边界](01_role/README.md)读到第 4 章，形成现场发现、架构决策和交付计划。再读第 7–8、10–12 章，按附录模板准备上线证据。
- **平台与 DevOps 工程师** · 从[云原生运行底座](05_cloud_native/README.md)开始，依次读第 5–6、8、12–13 章，为同一制品设计环境提升、回滚和运维方案。
- **AI 应用工程师** · 从[数据源接入与契约](07_data/7.1_contract.md)开始，再读第 8–12 和第 16 章，为 RAG 或 Agent 定义数据权限、评测门槛和人工接管条件。
- **技术负责人和产品负责人** · 先读[角色边界](01_role/README.md)和[交付节奏与团队协作](04_delivery/README.md)，再结合第 11–12、14–16 章和附录模板，明确交付责任、接管标准和产品化机会。

</details>

## 全书结构

- **入门篇 · 理解 FDE（第 1–4 章）** · 先读[FDE 的角色边界](01_role/README.md)，再学习现场问题发现、架构取舍和交付协作。
- **工程篇 · 云原生与自动化交付（第 5–8 章）** · 从[云原生运行底座](05_cloud_native/README.md)入手，学习 Kubernetes、GitOps、基础设施即代码、数据集成和安全合规。
- **生产篇 · AI 原生系统（第 9–12 章）** · 先读[AI 原生 FDE](09_ai_native/README.md)，学习如何将 LLM、RAG 和 Agent 接入业务工作流，用评测与可观测性支持上线和现场运维。
- **实战篇 · 规模化与行业落地（第 13–16 章）** · 从[工具生态与平台化](13_tooling/README.md)入手，结合金融、制造、医疗等行业案例，理解交付能力如何通过平台和组织复用。

附录提供[术语表](appendix/glossary.md)、[参考文献](appendix/references.md)、[工具索引](appendix/tools.md)、[交付证据包模板](appendix/templates.md)、[综合实战](appendix/capstone.md)、[第十四章声明账本](appendix/claim_ledger.md)和[快变事实核验表](appendix/volatile_facts.md)。

## 延伸阅读

- **容器、镜像和 Kubernetes** · [Docker 从入门到实践](https://yeasy.gitbook.io/docker_practice/)
- **任务拆解、提示词设计和评测** · [大模型提示词工程指南](https://yeasy.gitbook.io/prompt_engineering_guide/)
- **RAG、记忆与上下文管理** · [大模型上下文工程权威指南](https://yeasy.gitbook.io/context_engineering_guide/)
- **Agent 运行时、工具层和可观测性** · [智能体 Harness 工程指南](https://yeasy.gitbook.io/harness_engineering_guide/)
- **提示注入、数据泄露和 AI 治理** · [大模型安全权威指南](https://yeasy.gitbook.io/ai_security_guide/)

## 反馈与贡献

欢迎在 [GitHub Issues](https://github.com/yeasy/forward_deployed_engineering_guide/issues) 报告勘误或提出建议，也可以[提交 Pull Request](https://github.com/yeasy/forward_deployed_engineering_guide/pulls)。

<details>

<summary>本地预览与构建</summary>

在仓库根目录安装并运行 [mdPress](https://github.com/yeasy/mdPress)，启动本地预览。

```bash
brew tap yeasy/tap
brew install mdpress
mdpress serve .
```

检查 Markdown 链接与代码块围栏，并构建静态站点、PDF 和 ePub。

```bash
python3 check_project_rules.py
mdpress build --format site,pdf,epub .
```

构建可离线阅读的单文件 HTML 需要 Pandoc 3.5、Chrome 和 Node.js。将 `CHROME_BIN` 设为本机 Chrome 可执行文件路径。

```bash
PUPPETEER_SKIP_DOWNLOAD=true npm ci --prefix tools/mermaid --ignore-scripts
export PATH="$PWD/tools/mermaid/node_modules/.bin:$PATH"
export CHROME_BIN="/path/to/chrome"
python3 tools/render_mermaid.py --book-dir . --svg-out /tmp/fde-mermaid --strict
python3 tools/build_html_reader.py --book-dir . --title "前线部署工程实践指南" \
  --svg-dir /tmp/fde-mermaid --out forward_deployed_engineering_guide.html --strict
```

</details>

<details>

<summary>预览版、持续集成与发布</summary>

默认分支的预览版随主线更新，提供 [PDF](https://github.com/yeasy/forward_deployed_engineering_guide/releases/download/preview-pdf/forward_deployed_engineering_guide.pdf)、[单文件 HTML](https://github.com/yeasy/forward_deployed_engineering_guide/releases/download/preview-pdf/forward_deployed_engineering_guide.html)和 [SHA256SUMS](https://github.com/yeasy/forward_deployed_engineering_guide/releases/download/preview-pdf/SHA256SUMS)。正式版本另带构建来源证明。

- `CI` 在推送到 `main`、提交 Pull Request 或手动触发时运行测试和项目检查，并构建、验证 PDF、单文件 HTML 和校验和。
- `Update Preview Publications` 在只读任务中构建并验证 PDF、HTML 和校验和，再由独立任务发布到 `preview-pdf`。
- `Auto Release` 在推送 `v*` 标签时构建 PDF、HTML 和校验和，再由独立任务生成构建来源证明并发布到 GitHub Releases。手动触发仅生成验证后的构建产物。
- `Dependabot auto-merge` 仅对 GitHub Actions 的低风险补丁和小版本更新启用自动合并，要求目标分支已配置必需检查。

</details>
