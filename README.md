# 前言

## 本书定位

Forward Deployed Engineering，简称 FDE，本书译作“前线部署工程”。它不是传统售前、外包实施或一次性顾问交付，而是一种把工程师嵌入真实业务现场，用软件、数据、AI、平台和运营方法解决复杂组织问题的工程实践。FDE 的目标不是完成一份方案文档，而是把模糊问题转化为可运行、可观测、可治理、可持续演进的生产系统。

Palantir 的 Forward Deployed Engineering 实践将 FDE 广泛带入行业视野。随着企业 AI 落地进入生产化阶段，FDE 被重新推到前台。OpenAI 宣布推出 [OpenAI Deployment Company](https://openai.com/index/openai-launches-the-deployment-company/)，强调让专门从事前沿 AI 部署的工程师嵌入组织，识别高影响场景，重构关键工作流，并把收益沉淀为可持续运行的系统。Palantir 也在 Foundry 文档中提供 [AI FDE](https://www.palantir.com/docs/foundry/ai-fde/overview)，用自然语言执行 Foundry 操作。Accenture 与 Microsoft 也宣布成立面向企业 AI 规模化的 [FDE 实践](https://newsroom.accenture.com/news/2026/accenture-launches-microsoft-forward-deployed-engineering-practice-to-help-organizations-scale-ai-across-the-enterprise)，说明 FDE 已从少数公司的组织实践扩展为企业 AI 和数字化转型的重要交付模式。

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

## 全书结构

全书分为四部分，共十六章，另设附录。

第一部分“理解 FDE”建立基本概念。它解释 FDE 的来源、角色边界、现场问题发现、架构取舍和交付协作。

第二部分“工程底座”讲生产化所需的基础能力。它覆盖云原生运行环境、自动化交付、数据集成、安全合规和治理。

第三部分“AI 原生实践”聚焦企业 AI 落地。它讲解 LLM 应用、RAG、Agent、评测、LLMOps、从原型到生产系统以及现场运维。

第四部分“规模化与生态”讨论如何把一次交付变成可复用能力。它包括工具生态、行业案例、组织能力、职业发展和未来趋势。

附录包括术语表、参考文献和工具索引，便于读者在阅读过程中快速查阅。

## 本地阅读与构建

本书使用 mdPress 支持本地阅读。安装 mdPress 后，在项目根目录执行：

```bash
mdpress serve .
```

浏览器打开 `http://127.0.0.1:9000` 即可实时预览。需要生成便携离线文件时执行：

```bash
mdpress build --format html .
```

需要同时生成静态站点、PDF、HTML 和 ePub 时执行：

```bash
mdpress build --format site,pdf,html,epub .
```

mdPress 会读取 `book.yaml` 中的书籍元数据、主题和输出设置；正文阅读顺序由 `SUMMARY.md` 维护。

## 资料原则

本书资料以写作和修订时可公开获取的信息为准。事实性内容优先引用官方文档、标准组织资料、开源项目文档、公司公开材料和综述论文。工具生态部分优先采用官方资料，例如 [Kubernetes 文档](https://kubernetes.io/docs/)、[OpenGitOps](https://opengitops.dev/)、[Argo CD 文档](https://argo-cd.readthedocs.io/)、[OpenTelemetry 文档](https://opentelemetry.io/docs/)、[NIST SSDF](https://csrc.nist.gov/pubs/sp/800/218/final)、[NIST 零信任架构](https://csrc.nist.gov/pubs/sp/800/207/final)、[SLSA](https://slsa.dev/spec/latest/)、[CISA SBOM](https://www.cisa.gov/sbom)、[OWASP 大语言模型应用安全风险](https://owasp.org/www-project-top-10-for-large-language-model-applications/) 等。

对招聘趋势、公司案例和行业观点，本书会标注来源边界，避免把未经证实的市场叙事写成事实。招聘页、营销页、厂商价格页和 SaaS 文档属于高漂移来源，应以官方最新页面为准。对金融、国防、医疗等高敏行业案例，本书只引用公开可核验资料，并明确安全、合规和数据权限假设。
