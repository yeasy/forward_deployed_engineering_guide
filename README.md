<div align="center">

# 前线部署工程实践指南

[![GitHub stars](https://img.shields.io/github/stars/yeasy/forward_deployed_engineering_guide?style=social)](https://github.com/yeasy/forward_deployed_engineering_guide)
[![Release](https://img.shields.io/github/release/yeasy/forward_deployed_engineering_guide.svg)](https://github.com/yeasy/forward_deployed_engineering_guide/releases)
[![Online Reading](https://img.shields.io/badge/在线阅读-GitBook-brightgreen)](https://yeasy.gitbook.io/forward_deployed_engineering_guide/)
[![PDF](https://img.shields.io/badge/PDF-下载-orange)](https://github.com/yeasy/forward_deployed_engineering_guide/releases/latest)

> 从现场问题发现到 AI 原生生产交付，系统掌握前线部署工程的方法、工具与实践。

<img src="cover.png" width="360" alt="前线部署工程实践指南封面配图">

</div>

---

## 本书定位

Forward Deployed Engineering，简称 FDE，本书译作“前线部署工程”。它不是传统售前、外包实施或一次性顾问交付，而是一种把工程师嵌入真实业务现场，用软件、数据、AI、平台和运营方法解决复杂组织问题的工程实践。FDE 的目标不是完成一份方案文档，而是把模糊问题转化为可运行、可观测、可治理、可持续演进的生产系统。

FDE 已从少数公司的组织实践扩展为企业 AI 和数字化转型的重要交付模式：

- Palantir 的 FDE 实践将这一角色带入行业视野，并在 Foundry 文档中提供 [AI FDE](https://www.palantir.com/docs/foundry/ai-fde/overview)。
- OpenAI 推出 [OpenAI Deployment Company](https://openai.com/index/openai-launches-the-deployment-company/)，强调工程师嵌入组织、识别高影响场景、重构关键工作流。
- Accenture 与 Microsoft 成立面向企业 AI 规模化的 [FDE 实践](https://newsroom.accenture.com/news/2026/accenture-launches-microsoft-forward-deployed-engineering-practice-to-help-organizations-scale-ai-across-the-enterprise)。

本书面向希望系统掌握 FDE 的工程师、技术负责人、产品经理、解决方案架构师、平台工程师、AI 应用开发者和企业数字化负责人。

## 目标读者

本书适合以下读者阅读：

1. 已具备软件工程基础，希望进入 FDE、解决方案工程、AI 交付、平台工程或企业技术咨询领域的工程师。
2. 正在把 AI、数据平台、云原生平台或业务自动化系统落地到企业现场的技术负责人。
3. 需要理解 FDE 与售前、咨询、SRE、平台工程、客户成功之间边界的管理者。
4. 希望用开源工具构建可复制交付能力的团队，包括 Kubernetes、GitOps、IaC、OpenTelemetry、Backstage、Temporal、Dagster、LangGraph、LlamaIndex、MLflow 等生态使用者。
5. 正在负责高安全、高合规、高复杂度现场交付的团队，例如金融、制造、医疗、能源、公共部门和供应链场景。

## 将学到什么

读完整书后，读者应能够形成四类能力。

第一，理解 FDE 的角色本质。读者将能区分 FDE、售前工程师、解决方案架构师、专业服务、平台工程师、SRE、AI 工程师之间的责任边界，理解为什么 FDE 的核心是现场发现、工程交付、生产价值和产品反哺。

第二，掌握从问题到系统的交付方法。书中将讲解如何进入客户现场，识别真实瓶颈，建立领域语言，设计成功指标，拆分原型、试点和生产系统，并管理范围、风险、变更和知识转移。

第三，建立生产级工程底座。读者将学习容器与 Kubernetes、GitOps、基础设施即代码、CI/CD、软件供应链安全、数据产品、语义层、零信任、可观测性、SLO、事件响应等核心能力，并理解它们在 FDE 项目中的实际作用。

第四，掌握 AI 原生 FDE 实践。书中将覆盖 LLM、RAG、Agent、评测、LLMOps、提示工程、工具调用、模型部署、安全防护和人机协同边界，重点解释如何把 AI 能力接入客户数据、系统、权限和真实工作流。

## 阅读路径

下表是快速路径，不是可跳过依赖的许可。真实项目进入生产前，应回查数据、安全、LLMOps、运维和[交付证据包模板](appendix/templates.md)，确认关键证据、owner、回滚和接管条件齐全。

| 读者 | 建议章节 | 阅读重点 |
|---|---|---|
| FDE / 解决方案工程师 | 1 -> 2 -> 3 -> 4 -> 7 -> 8 -> 10 -> 11 -> 12 -> 附录模板 | 角色边界、现场发现、架构取舍、数据与安全、生产上线、运维闭环 |
| 平台 / DevOps 工程师 | 5 -> 6 -> 8 -> 12 -> 13 | 云原生、GitOps、供应链安全、可观测性、平台化 |
| AI 应用工程师 | 7 -> 8 -> 9 -> 10 -> 11 -> 12 -> 16 -> 附录模板 | 数据接入、权限与安全、RAG、Agent、评测、LLMOps、AI FDE |
| 技术负责人 / 产品负责人 | 1 -> 4 -> 11 -> 12 -> 14 -> 15 -> 16 -> 附录模板 | 交付模式、接管标准、行业案例、组织能力、长期价值 |

## 相关图书

- [Docker 从入门到实践](https://yeasy.gitbook.io/docker_practice/)：补齐容器、镜像、Compose、Kubernetes 等运行底座。
- [大模型提示词工程指南](https://yeasy.gitbook.io/prompt_engineering_guide/)：补齐提示设计、任务拆解和提示评测基础。
- [大模型上下文工程权威指南](https://yeasy.gitbook.io/context_engineering_guide/)：补齐 RAG、记忆、工具调用和上下文管理。
- [智能体 Harness 工程指南](https://yeasy.gitbook.io/harness_engineering_guide/)：补齐 Agent 运行时、工具层、记忆、安全和可观测性。
- [大模型安全权威指南](https://yeasy.gitbook.io/ai_security_guide/)：补齐提示注入、数据泄露、模型滥用和 AI 系统治理。

## 全书结构

全书分为四部分，共十六章，另设附录。

第一部分“理解 FDE”建立基本概念。它解释 FDE 的来源、角色边界、现场问题发现、架构取舍和交付协作。

第二部分“工程底座”讲生产化所需的基础能力。它覆盖云原生运行环境、自动化交付、数据集成、安全合规和治理。

第三部分“AI 原生实践”聚焦企业 AI 落地。它讲解 LLM 应用、RAG、Agent、评测、LLMOps、从原型到生产系统以及现场运维。

第四部分“规模化与生态”讨论如何把一次交付变成可复用能力。它包括工具生态、行业案例、组织能力、职业发展和未来趋势。

附录包括术语表、参考文献、工具索引和交付证据包模板，便于读者在阅读、审校和项目实践中快速查阅与复用。

## 在线阅读

可通过 GitBook 阅读在线版本：[前线部署工程实践指南](https://yeasy.gitbook.io/forward_deployed_engineering_guide/)。

## 下载离线版本

正式 PDF 版本可前往 [GitHub Releases](https://github.com/yeasy/forward_deployed_engineering_guide/releases/latest) 页面下载。

默认分支自动更新的预览版可直接下载 [forward_deployed_engineering_guide.pdf](https://github.com/yeasy/forward_deployed_engineering_guide/releases/download/preview-pdf/forward_deployed_engineering_guide.pdf)。该文件会随主线更新覆盖，不代表正式发布版本。

## 本地阅读与构建

安装 mdPress：

```bash
brew tap yeasy/tap
brew install mdpress
```

本地预览：

```bash
mdpress serve .
```

检查 Markdown 链接和代码块围栏：

```bash
python3 check_project_rules.py
```

构建静态站点、PDF 和 ePub：

```bash
mdpress build --format site,pdf,epub .
```

生成单文件 HTML：

```bash
mdpress build --format html .
```

## CI 与发布

本仓库配置 GitHub Actions：

- `CI`：在 `main` 分支推送、Pull Request 和手动触发时运行 Markdown 项目检查并构建 PDF artifact。
- `Update Preview PDF`：在 `main` 分支推送和手动触发时更新 `preview-pdf` 预览版 Release。
- `Auto Release`：在 `v*` tag 推送时构建正式 PDF 并上传到 GitHub Release；手动触发主要用于验证和生成 artifact，不会自动写入正式 Release 资产。
- `Dependabot auto-merge`：仅对 GitHub Actions 的低风险补丁和小版本更新启用自动合并，且要求目标分支已配置必需检查。
