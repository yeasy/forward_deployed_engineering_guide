## 工具索引

工具索引按 FDE 工作流能力分组。选择工具时，应先回答四个问题：客户环境是否允许引入该工具；团队是否具备维护能力；工具是否降低长期风险；工具是否能留下可审计证据。

### 开发者门户与服务目录

[Backstage](https://backstage.io/docs/) 适合建立服务目录、技术文档、模板化创建服务和平台入口。FDE 团队可用它把客户现场系统、负责人、运行环境、依赖关系、运行手册和部署入口整理为统一视图。

[Humanitec](https://humanitec.com/) 提供 Platform Orchestrator 与 Score 工作负载规范，适合多环境、多云下动态生成应用配置与基础设施清单，常作为 Backstage 之外的编排底座。

[Port](https://www.port.io/) 是 SaaS 化的开发者门户，强调可配置目录、自助操作与 scorecards，适合希望快速落地门户而无意自托管 Backstage 的客户。

[Cortex](https://www.cortex.io/) 在服务目录之外提供工程健康度 Scorecard 与自助流程，适合用可量化指标驱动工程成熟度治理。

### 容器与云原生平台

[Kubernetes](https://kubernetes.io/docs/) 是云原生交付的事实标准之一，适合承载容器化应用、声明式部署、弹性伸缩和自愈能力。[Istio](https://istio.io/latest/docs/) 等服务网格可用于东西向流量治理、双向 TLS、流量切分和策略控制，但应在复杂度收益明确时引入。

### GitOps 与交付控制

[Argo CD](https://argo-cd.readthedocs.io/) 和 [Flux](https://fluxcd.io/flux/) 适合把 Kubernetes 应用状态从 Git、Helm 或 OCI 制品拉取到集群内持续调和。它们的价值不是“自动部署”本身，而是让客户环境的期望状态、变更历史、回滚路径和审批证据统一。

### 基础设施即代码

[Terraform](https://developer.hashicorp.com/terraform/intro)、[OpenTofu](https://opentofu.org/docs/)、[Pulumi](https://www.pulumi.com/docs/iac/) 和 [Crossplane](https://docs.crossplane.io/) 可用于管理云资源与平台抽象。Terraform/OpenTofu 更适合声明式资源生命周期，Pulumi 更适合用通用编程语言封装基础设施能力，Crossplane 则适合把外部云资源抽象为 Kubernetes API。

### 可复现流水线

[Dagger](https://docs.dagger.io/) 将构建、测试、发布和运行任务表达为可编程流水线，适合需要跨本地、CI 和客户环境复现交付动作的团队。FDE 场景中，它可以减少“只在某个工程师机器上能跑”的交付风险。

### 可靠工作流

[Temporal](https://docs.temporal.io/) 适合长事务、跨系统流程、审批、重试、补偿和失败恢复。客户现场常见的 ERP、CRM、票据、仓储、支付、人工审批和第三方 API 集成，通常比单次 HTTP 请求复杂，可靠工作流引擎能显著降低异常处理成本。

### 数据编排

[Dagster](https://docs.dagster.io/) 强调数据资产，适合以数据产品、血缘和质量为中心组织管道。[Apache Airflow](https://airflow.apache.org/docs/apache-airflow/stable/) 强调工作流调度，适合大量已有 DAG、批处理任务和企业调度生态。FDE 项目应根据客户存量和治理目标选型。

### 数据治理与质量

[OpenLineage](https://openlineage.io/) 可用于标准化血缘事件。[OpenMetadata](https://docs.open-metadata.org/) 提供元数据、血缘、质量、所有权和治理能力。[Great Expectations](https://docs.greatexpectations.io/) 可用于表达和验证数据质量规则。它们共同服务于一个目标：让数据产品可解释、可追责、可变更。

### AI 应用编排

[LangGraph](https://docs.langchain.com/oss/python/langgraph/overview) 适合构建带状态、工具调用、人机协同和可恢复执行的 Agent 工作流。[LlamaIndex](https://developers.llamaindex.ai/python/framework/) 更偏向企业知识接入、索引、检索和 RAG 应用。FDE 项目应把它们放在权限、评测、观测和审计框架内使用。

### 向量检索与知识索引

[Milvus](https://milvus.io/docs)、[Weaviate](https://weaviate.io/developers/weaviate)、[Qdrant](https://qdrant.tech/documentation/) 和 [pgvector](https://github.com/pgvector/pgvector) 可用于构建企业 RAG 的向量检索层。选型时不要只看 benchmark：还要看 ACL 过滤、元数据 schema、备份恢复、混合检索、重排、租户隔离和运维团队已有数据库能力。

### 评测与回归

[OpenAI Evals](https://platform.openai.com/docs/guides/evals)、[Ragas](https://docs.ragas.io/)、[promptfoo](https://www.promptfoo.dev/docs/intro/)、[Langfuse](https://langfuse.com/docs)、[Arize Phoenix](https://docs.arize.com/phoenix) 和 [Braintrust](https://www.braintrust.dev/docs) 可用于构建 LLM/RAG/Agent 的离线评测、trace 分析和回归门禁。FDE 项目应优先定义任务样本、评分函数和失败处置，再选择工具。

### Guardrails 与运行时保护

[NVIDIA NeMo Guardrails](https://docs.nvidia.com/nemo/guardrails/)、[Llama Guard](https://www.llama.com/docs/model-cards-and-prompt-formats/llama-guard-3/)、[Amazon Bedrock Guardrails](https://docs.aws.amazon.com/bedrock/latest/userguide/guardrails.html) 和 [Azure AI Content Safety](https://learn.microsoft.com/azure/ai-services/content-safety/) 可用于内容安全、拒答、策略约束和高风险输出拦截。它们不能替代身份、权限和审计，只能作为模型输入输出与工具执行边界上的一层控制。

### AI Gateway 与模型路由

[LiteLLM](https://docs.litellm.ai/)、[Portkey](https://portkey.ai/docs) 和云厂商模型网关能力可用于统一模型调用、限流、重试、成本标签、缓存、审计和供应商切换。FDE 在客户现场引入 AI gateway 时，应明确它是否处理敏感数据、是否记录 prompt、如何与现有身份系统和日志平台对接。

### AI 平台与模型 API

[Claude / Anthropic API](https://docs.anthropic.com/) 提供 Claude 系列模型、工具调用、长上下文与企业 DPA/BAA，可作为对内 agent、客户面应用与离线评测的统一入口。

[Azure AI Foundry](https://learn.microsoft.com/azure/ai-foundry/) 在 Azure 上集成模型目录、agent、评测与责任 AI 工具，适合已在 Microsoft 生态、需要私网与合规审计的客户。

[Amazon Bedrock](https://docs.aws.amazon.com/bedrock/) 在 AWS 区域内提供多家模型托管、Guardrails、Knowledge Bases 与 Agents，对在 AWS 落地数据与权限的项目集成成本较低。

[Google Vertex AI](https://cloud.google.com/vertex-ai/docs) 在 GCP 上整合 Gemini 系列、模型花园、Pipelines 与 Model Registry，适合需要 TPU、BigQuery 数据或与 Google Workspace 工作流深度集成的场景。

### 模型与实验治理

[MLflow](https://mlflow.org/docs/latest/) 可用于实验追踪、模型注册、评测和生命周期管理。[Ray](https://docs.ray.io/) 可用于扩展 Python、机器学习和推理工作负载。它们适合需要从单机原型走向集群化、可重复、可追踪 AI 工作负载的场景。

### 供应链安全

[SLSA](https://slsa.dev/spec/latest/)、[Sigstore](https://docs.sigstore.dev/)、[CycloneDX](https://cyclonedx.org/specification/overview)、[SPDX](https://spdx.dev/about/overview/) 和 [in-toto](https://in-toto.io/docs/getting-started/) 构成软件供应链安全的重要生态。FDE 团队应至少理解制品来源证明、签名验证、软件物料清单和部署前校验。
