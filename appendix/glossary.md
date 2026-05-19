## 术语表

### FDE

FDE 是 Forward Deployed Engineering 的缩写，本书译作“前线部署工程”。它指工程师深入客户或业务现场，围绕真实工作流完成问题发现、系统设计、代码实现、数据接入、部署上线、运行治理和产品反馈的工程实践。FDE 的关键边界是“对生产价值负责”，不是只交付方案文档或演示原型。

### FDSE

FDSE 是 Forward Deployed Software Engineer 的缩写，常见于 Palantir 等公司的岗位描述。FDSE 更强调软件工程师身份，通常需要直接编写代码、处理数据、构建应用、参与客户沟通，并把现场发现反馈给核心产品和工程团队。

### 现场嵌入

现场嵌入指工程师进入客户真实业务环境，理解人员、流程、系统、数据、权限、审批和失败路径。它不是简单驻场，也不是被动接需求，而是在业务现场发现系统性约束，并把约束转化为可执行的工程设计。

### 业务工作流

业务工作流指组织为了完成某个业务目标而执行的一系列活动、决策、数据流转和系统操作。FDE 关注的不是单个页面或接口，而是端到端工作流是否更快、更准、更稳、更可审计。

### 成功指标

成功指标是用于判断 FDE 交付是否产生真实价值的可衡量标准。它通常包括业务结果指标、用户行为指标和工程健康指标。例如处理时长、错误率、采用率、人工绕行比例、部署频率、恢复时间和支持负担。

### 原型

原型是为验证价值假设和技术可行性而构建的最小系统。原型的目标是学习，不是伪装成生产系统。进入生产前，原型必须经过安全、权限、可靠性、可观测性、数据治理、变更管理和运维交接等硬化。

### 试点

试点是在受控范围内验证系统是否能在真实用户、真实数据和真实流程中产生稳定结果。试点应有明确边界、验收标准、退出条件和扩展决策，避免长期停留在“永远试运行”的状态。

### 生产化

生产化指把可用原型变成可长期运行、可维护、可审计、可扩展的系统。生产化通常涉及代码质量、配置管理、发布流程、身份权限、数据保护、监控告警、容量规划、运行手册和责任交接。

### GitOps

GitOps 是一种以 Git 作为声明式期望状态来源的交付方法。按照 [OpenGitOps](https://opengitops.dev/) 原则，系统状态应声明式描述、版本化且不可变，由自动化代理拉取并持续调和。FDE 中 GitOps 的价值在于让客户环境变更可审查、可回放、可审计。

### CI/CD

CI/CD 是 Continuous Integration 与 Continuous Delivery/Deployment 的缩写。持续集成强调频繁集成代码并通过自动构建和测试快速反馈；持续交付强调已验证代码随时可部署；持续部署则在门禁通过后自动部署到生产。FDE 使用 CI/CD 时，应把制品 digest、测试结果、SBOM、provenance 和发布审批证据一起纳入交付链路。

### IaC / 基础设施即代码

基础设施即代码是用代码或声明式配置管理云资源、网络、权限、数据库和运行环境的方法。Terraform、OpenTofu、Pulumi、Crossplane 都属于相关生态。FDE 使用基础设施即代码，不是为了追求形式统一，而是为了减少手工变更、控制漂移、保留审批证据。

### 可观测性

可观测性指通过指标、日志、链路追踪和事件等信号理解系统内部状态的能力；核心信号可参考 [OpenTelemetry](https://opentelemetry.io/docs/concepts/signals/) 对指标、日志和追踪的划分。FDE 中可观测性是交付物的一部分，不是上线后的附加项。

### 服务等级目标

服务等级目标，简称 SLO，是对系统面向用户行为的可靠性承诺。SLO 通常由服务等级指标，简称 SLI，和目标阈值组成。FDE 中的 SLO 应从关键业务工作流倒推，而不是只看机器 CPU 或进程存活。

### SRE

SRE 是 Site Reliability Engineering 的缩写，即站点可靠性工程。它把软件工程方法用于运行系统，核心概念包括 SLI、SLO、错误预算、告警、事故响应和无责复盘。FDE 借鉴 SRE，不是把客户现场变成运维团队，而是让上线后的可靠性有可衡量承诺和反馈机制。

### Platform Engineering

Platform Engineering 指为开发和运维团队提供自助式平台能力的工程实践。它通常包括开发者门户、模板、环境编排、权限、流水线、可观测性和治理规则。FDE 中的平台工程价值在于把一次现场交付沉淀为可复用能力，而不是让每个客户项目重新搭底座。

### DORA

DORA 是 DevOps Research and Assessment 的缩写，常用于指 Google Cloud DORA 研究体系及其软件交付性能指标。当前 DORA 软件交付指标包括部署频率、变更前置时间、失败部署恢复时间、变更失败率和部署返工率。FDE 使用 DORA 指标时应结合客户业务 KPI 和 SLO，避免把交付速度当作唯一目标。

### SPACE

SPACE 是一个开发者生产力度量框架，覆盖 Satisfaction and well-being、Performance、Activity、Communication and collaboration、Efficiency and flow 五类维度。它提醒团队不要只用提交数、工时或部署次数衡量工程效率。

### SBOM

SBOM 是 Software Bill of Materials 的缩写，即软件物料清单。它记录软件组件、版本、供应商、依赖关系、许可证和标识信息。根据 [CISA SBOM](https://www.cisa.gov/sbom) 的定义，SBOM 有助于组织理解软件供应链风险和漏洞影响面。

### AIBOM

AIBOM 是 AI Bill of Materials 的缩写，用来描述 AI 系统中与模型、数据、权重、提示词、评测集、工具、依赖和运行环境相关的组成清单。AIBOM 尚不像 SBOM 那样完全标准化；在 FDE 项目中，它的价值是让 AI 资产来源、版本、限制和风险可审计。

### SLSA

SLSA 是 Supply-chain Levels for Software Artifacts 的缩写，是软件制品供应链完整性框架。FDE 项目使用 [SLSA](https://slsa.dev/spec/latest/) 的价值在于让构建来源、构建过程和发布制品可追溯、可验证，降低现场补丁和客户定制构建带来的供应链风险。

### Provenance / 来源证明

Provenance 指描述制品由哪个 builder、哪些输入、哪个构建过程生成的可验证信息；在 SLSA 中通常作为 attestation 分发和验证。FDE 项目不应只保存 provenance 文件，还应在部署门禁中校验 subject digest、builder 身份、source revision、build type、签名链和允许的构建参数。

### 特性开关（Feature Flag / Feature Toggle）

特性开关用于把代码部署和能力开放分离，使团队可以按用户、租户、区域、角色或运行状态控制功能路径。它能降低发布风险，但也会引入状态组合和长期维护成本；每个开关都应有 owner、默认安全值、监控指标、过期时间和删除条件。

### RAG

RAG 是 Retrieval-Augmented Generation 的缩写，即检索增强生成。它通过检索外部知识，再把证据提供给模型生成回答。FDE 中的 RAG 不应只理解为“向量数据库加提示词”，而应作为客户知识接入、证据链管理、权限控制和回答评测的系统工程。

### Agent

Agent 指能够根据目标、上下文和工具反馈进行多步推理与行动的 AI 系统。企业场景中的 Agent 通常需要工具调用、权限边界、状态管理、审计记录、人工接管和失败恢复机制。没有这些控制的 Agent 只能算实验性自动化。

### Tool Use

Tool Use 指模型或 Agent 调用外部函数、API、搜索、数据库、代码执行环境或业务系统的能力。FDE 项目应把工具调用视为生产接口：每个工具都要有 schema、权限、审计、错误处理和禁止动作。

### Context Window

Context Window 指模型一次请求可接收和处理的上下文容量。它不是“越大越好”的资源；过大的上下文会增加成本、延迟和提示注入风险。FDE 应把上下文预算、裁剪规则和证据优先级纳入测试。

### Token Budget

Token Budget 指一次任务、一个租户或一个工作流可消耗的 token 与费用上限。它既是成本控制，也是可靠性控制：超出预算时系统应降级、裁剪上下文、切换模型或转人工，而不是无限循环调用模型。

### Hallucination

Hallucination 指模型生成了缺乏证据、与事实冲突或超出授权范围的内容。FDE 项目不应只靠提示词减少幻觉，而应通过 RAG 引用、结构化输出、eval、人工复核、拒答策略和审计闭环降低业务影响。

### Model Card

Model Card 是对模型用途、训练数据范围、评测结果、限制、风险和适用场景的说明文档。FDE 使用第三方或本地模型时，应把模型卡作为上线证据的一部分；没有模型卡时，需要自行记录等价信息。

### System Card

System Card 是对完整 AI 系统的说明，覆盖模型之外的工具、数据、权限、人机协同、评测、监控和已知限制。它比模型卡更接近 FDE 交付边界，因为客户使用的是系统，而不是单个模型。

### LLMOps

LLMOps 指围绕大语言模型应用的开发、评测、部署、监控和治理实践。它与传统 MLOps 的差异在于需要管理提示词、上下文、检索语料、工具调用、模型版本、非确定性输出、成本、延迟和安全风险。

### MLOps

MLOps 指机器学习模型从实验、训练、部署到监控的工程实践，重点管理数据集、特征、训练管道、模型注册、在线服务和漂移。LLMOps 与 MLOps 有交集，但更强调提示词、上下文、RAG、工具调用和非确定性输出。

### 人机协同

人机协同指人类和 AI 系统在同一业务流程中分担任务、审批、纠错和决策。FDE 项目应明确哪些动作可自动执行，哪些动作必须人工确认，哪些场景需要人工接管，以及系统如何保留可审计证据。

### 平台化

平台化指把多次现场交付中重复出现的能力沉淀为标准接口、模板、工具、治理规则和自助服务。平台化不是把所有客户差异抽象掉，而是在保留必要差异的同时降低重复交付成本和运行风险。

### IDP

IDP 是 Internal Developer Platform 的缩写，即内部开发者平台。它通常把服务目录、模板、环境、流水线、权限、运行手册和可观测性入口整合成自助体验。IDP 的目标不是再造一个门户，而是降低团队交付和运维的认知负担。

### ADR

ADR 是 Architecture Decision Record 的缩写，即架构决策记录。它用简短文档记录某个重要技术决策的背景、选项、决定、后果和复审条件。FDE 使用 ADR 能避免现场决策只留在会议或聊天记录里。

### 客户自治

客户自治指客户团队具备独立运行、维护、扩展和治理系统的能力。FDE 项目的成熟退出条件通常不是工程师离场，而是客户能够理解系统边界、处理日常变更、排查常见故障，并知道何时升级求助。

### MCP

MCP 是 Model Context Protocol 的缩写，由 Anthropic 在 2024 年开源；本书固定引用 [Model Context Protocol 2025-11-25 规范](https://modelcontextprotocol.io/specification/2025-11-25)。它为 LLM 应用与外部数据源、工具之间定义了标准化接口，使工具可被支持 MCP 的客户端、host 或 agent 框架复用，而不必为每个模型 SDK 单独适配。截至 2026-05-19，Linux Foundation 公开信息显示 MCP 已进入 Agentic AI Foundation；协议治理中立化不等于生产安全默认成立，MCP server 仍需按供应链资产和工具权限治理。

### Ontology

Ontology 在本书语境中特指 Palantir Foundry 等平台中的语义对象层。Palantir Foundry 的 [Ontology 文档](https://www.palantir.com/docs/foundry/ontology/overview)将表、属性、关系、动作映射为业务术语对象，让数据管道、应用与 AI agent 围绕统一概念协作，而不是各自对接原始表。

### Evals

Evals 指对 LLM 与 agent 系统的可重复评测集与流程。它通常包含输入样本、期望行为、评分函数与回归报告，是 LLMOps 的核心交付物之一；离线 evals 用于上线门禁，在线 evals 用于漂移与质量监控。

### Prompt Injection

提示注入指攻击者通过用户输入、检索文档、网页或工具输出，把恶意指令嵌入模型上下文，诱导模型偏离原意；可用 [OWASP LLM01](https://owasp.org/www-project-top-10-for-large-language-model-applications/) 作为提示注入风险的检查入口。防御包括输入分层、可信内容标记、工具最小权限与输出审计。

### Guardrail

Guardrail 指部署在模型输入输出与工具调用边界上的策略层，用于拦截违规内容、敏感数据外泄、越权动作和异常调用模式。Guardrail 不是模型自身能力，而是独立的策略与监控组件。

### Service Mesh

Service Mesh 指在服务间通信链路上插入 sidecar 或代理层，统一处理身份、加密、重试、流量控制与可观测性，常见实现包括 [Istio](https://istio.io/) 和 Linkerd。FDE 在多团队、多租户环境中常用它把零信任策略落到服务调用层。

### Lakehouse

Lakehouse 是融合数据湖与数据仓库的架构，把结构化分析能力（事务、schema、SQL）建在对象存储与开放表格式（Delta、Iceberg、Hudi）之上。它让批处理、流处理与 BI/ML 共享同一份数据，减少多套副本带来的治理负担。

### 数据契约 / Data Contract

数据契约指数据生产方与消费方就字段、语义、SLA、变更流程达成的可执行约定。它通常以 schema、测试、版本与 owner 元数据形式存在于代码仓库，并由 CI 校验，目的是把数据当作产品而非副产物管理。ODCS 是 Open Data Contract Standard 的缩写，是一种厂商中立的数据契约规范。

### Semantic Layer

Semantic Layer 指集中定义实体、维度、度量、指标和可复用查询的语义层。它让 BI、Notebook、产品应用和 AI 助手通过同一套业务口径访问数据，避免各自复制 SQL 后产生口径漂移。

### Lineage

Lineage 指数据从源系统到下游报表、模型、应用和动作之间的血缘关系。技术血缘关注任务、表、列和运行记录，业务血缘关注指标、决策和流程影响。

### OpenLineage

OpenLineage 是用于表达数据血缘事件的开放标准，核心概念包括 run、job、dataset 和 facets。它适合把编排、转换、查询和质量结果中的运行时血缘标准化输出。

### OpenMetadata

OpenMetadata 是开源元数据与治理平台，覆盖数据发现、血缘、质量、数据契约、所有权和协作等能力。FDE 项目可用它或类似平台把数据产品的 owner、契约、质量结果和消费者关系集中到资产目录页。

### Bounded Context

Bounded Context 出自领域驱动设计，指一个明确语义边界内的领域模型；同一个名词（如“订单”）在不同上下文中可能有不同含义与生命周期。FDE 用它划清服务、数据集与 AI agent 的责任边界，避免跨上下文滥用通用模型。

### Zero Trust

按 [NIST SP 800-207](https://csrc.nist.gov/pubs/sp/800/207/final) 的描述，Zero Trust 是“永不信任、始终验证”的安全模型。它要求每次访问都基于身份、设备、上下文与策略动态判断，而不依赖网络边界。FDE 在现场交付时将其落到身份、权限、审批、审计与最小可执行权限。
