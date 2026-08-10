# 附录 G 快变事实核验表

> `verified_at`: 2026-08-10 · `expires_at`: 2026-09-24 · `ttl_days`: 45
>
> 本表是全书**唯一**权威的外部事实核验日期。超过 `expires_at` 后 `check_project_rules.py` 会失败，
> 强制有人重新打开下面的权威入口逐类复核。正文与本表冲突时，先按官方来源更新本表，再同步正文。
>
> 本表按**类别**维护漂移节奏，不逐条复制事实；第 14 章的逐条声明溯源见[声明账本](claim_ledger.md)，
> 两张表分工不同：声明账本记录「某条证据在某日核验过、以及它不能被外推到哪里」，是历史记录，不过期；
> 本表记录「哪一类外部事实会变、多久该回头看一次」，是时钟，会过期。

<!-- volatile-status: id=fde-volatile status=current -->

| 类别 | 当前维护口径 | 权威入口 | 复核节奏 | 编辑要求 |
| --- | --- | --- | --- | --- |
| 角色定义与岗位来源 | 岗位页是全书漂移最快的来源，且无法靠引用规范来补救：招聘 req 按数字 ID 归档，撤下后 URL 即失效。**Anthropic 公开招聘板上已无以 Forward Deployed / FDE 命名的岗位**（本表 `verified_at` 当日经 Greenhouse 板 API 全量核对，391 条岗位零命中——网页端分 8 页，只看首页会漏），对应职责由 Applied AI Architect 系列承担。 | [Anthropic 招聘板](https://job-boards.greenhouse.io/anthropic)、[OpenAI 招聘搜索](https://openai.com/careers/search/)、[Scale AI 招聘](https://scale.com/careers)、[Palantir FDE 文档](https://www.palantir.com/docs/foundry/architecture-center/overview)、[京发改〔2026〕1185号](https://www.beijing.gov.cn/) | 每轮 | 任何 `.../jobs/<数字 ID>` 或 `.../careers/<slug>/` 深链**不得作为某条主张的唯一支撑**，必须配一段即使链接失效也仍成立的转述。**注意失效岗位会 307/302 跳到通用招聘板并返回 200**，链接检查器永远抓不到，只能靠人复核；`openai.com/careers/<slug>/` 已实测出现过这种静默失效（旧 slug 跳到通用搜索页，岗位本身仍在但换了 slug）。按职责而非岗位名称对照。 |
| 模型、API 与厂商平台口径 | 只写**形态**不写具体型号价格：输入/缓存/输出/批量的计费结构、ZDR 与 BAA 的资格边界、留存与清除窗口的量词。16.6 刻意不写单模型价格，这个纪律正是这一行可维护的原因。 | [OpenAI 弃用公告](https://developers.openai.com/api/docs/deprecations)、[OpenAI 数据使用](https://developers.openai.com/api/docs/guides/your-data)、[OpenAI 定价](https://openai.com/api/pricing/)、[Anthropic 文档](https://platform.claude.com/docs/en/about-claude/models/overview) | 每轮 | 留存/资格类主张必须照抄厂商自己的量词，且正文各处口径必须彼此一致。已知待办：Assistants API 于 **2026-08-26** 完全下线，届时 9.2 的时态需从「将下线」改为历史陈述。`platform.openai.com/docs/*` 已整体迁到 `developers.openai.com`，现有链接靠 301 存活。 |
| Kubernetes 与云原生特性阶段 | 耐久写法是「在 vX.YY GA」，不是「已进入 stable」——后者对旧集群读者会直接变成假话，也没有可 diff 的锚点。GPU 栈版本钉（GPU Operator、驱动最低版本、DRA driver）按季度滚动，是本类中最快的子面。 | [Kubernetes 特性门控](https://kubernetes.io/docs/reference/command-line-tools-reference/feature-gates/)、[DRA 概念](https://kubernetes.io/docs/concepts/scheduling-eviction/dynamic-resource-allocation/)、[NVIDIA GPU Operator](https://docs.nvidia.com/datacenter/cloud-native/gpu-operator/latest/)、[MIG 支持矩阵](https://docs.nvidia.com/datacenter/tesla/mig-user-guide/) | 每轮 | 特性阶段主张必须点名 GA 版本；alpha/beta 子特性要与已 GA 的核心分开写。**绝不钉 NVIDIA 带版本号的文档路径**——`/gpu-operator/25.10.0/...` 已 404，只能引 `/latest/` 并把版本写在正文里以便编辑。 |
| 协议与规范版本 | 本类的典型失效是**静默过期而非链接失效**。钉版本的 URL（`slsa.dev/spec/v1.2/`、`modelcontextprotocol.io/specification/2025-11-25`）在不再是当前版之后仍永远返回 200；滚动 URL（`iceberg.apache.org/docs/latest/`）则会在链接文字仍写着旧版本时悄悄换成另一份文档。 | [MCP 版本策略](https://modelcontextprotocol.io/specification/versioning)、[SLSA 规范](https://slsa.dev/spec/)、[SPDX 规范](https://spdx.dev/use/specifications/)、[OTel GenAI 语义约定](https://github.com/open-telemetry/semantic-conventions)、[Gateway API](https://gateway-api.sigs.k8s.io/) | 季度 | 钉版本时正文必须写明版本**并说明这是刻意为之**（16.4 与术语表已是正确范例）；用滚动 URL 时链接文字不得断言该 URL 无法保证的版次。**MCP `2026-07-28` 修订已取代 `2025-11-25` 成为当前修订**：握手改为无状态，`initialize` 握手与 Streamable HTTP 的 `Mcp-Session-Id` 会话头被移除，Roots、Sampling、Logging 转入至少十二个月的弃用期而非移除。本书钉版已于 2026-07-28 统一升级到该修订（术语表、references 两条书目、16.4 共四处同步改毕）；全书对 MCP 的描述停在协议定位层，无 initialize 握手、`Mcp-Session-Id`、`resources/subscribe` 或 roots/sampling 回调等表述，故升级钉版不需要章节改写。注意「MCP 版本策略」页自身仍把 `2025-11-25` 写作当前版本，该句已过期，复核以 `/specification/latest` 的跳转目标为准。 |
| 安全、合规与监管基线 | 内容变化最慢，但有离散的**翻转事件**（草案转正式、生效日到达、版次重编号），一步就能让一句话失效。 | [OWASP GenAI](https://genai.owasp.org/)、[NIST AI RMF](https://www.nist.gov/itl/ai-risk-management-framework)、[NIST 隐私框架](https://www.nist.gov/privacy-framework)、[CISA SBOM](https://www.cisa.gov/)、[EU AI Act 时间线](https://digital-strategy.ec.europa.eu/en/policies/regulatory-framework-ai)、[国家网信办](https://www.cac.gov.cn/) | 季度 | 每条草案/待定主张必须带日期化的对冲，并点明什么事件会证伪它（6.5 与 8.2 已是正确范例，**不要「清理」这些对冲**）。OWASP 条目按 ID 引用（LLM01:2025、ASI01–ASI10），不要只用译名。已知待翻转：CISA SBOM 最小要素（评论期 2025-10-03 已截止仍为草案）、NIST 隐私框架 1.1。 |
| 平台与工具生态定位 | 证据最弱的一类，**要刻意写粗**。厂商定位表是营销文案的转述，而营销文案的重写速度远快于产品能力的变化。 | 只用厂商文档根目录：[Dagger](https://docs.dagger.io/)、[Humanitec](https://developer.humanitec.com/)、[Envoy AI Gateway](https://aigateway.envoyproxy.io/)、[Kong AI Gateway](https://developer.konghq.com/ai-gateway/)、[Phoenix](https://arize.com/docs/phoenix/)、[OPA](https://www.openpolicyagent.org/docs/kubernetes) | 半年 | 表格只描述**能力类别**，绝不写成逐产品特性矩阵；属于本书编辑判断而非厂商陈述的，必须显式标注（11.3 的「本书建议」是正确范例）。引用要指向真正承载证据的那一页。 |
| 案例与结果数字 | 本行只负责把第 14 章挂到同一个时钟上，**不复制任何案例数字**。 | [声明账本](claim_ledger.md) | 每轮 | 刷新本表 `verified_at` 时，同步重跑声明账本的来源核验并更新其逐行 `verified_at`；`不可外推边界`一列始终以声明账本为准，不得复制到本表。 |

## 本轮无法核验的项（需人工用浏览器确认）

以下条目的 HTTP 状态码**不携带任何信号**，自动核验一律失败，必须人工打开：

- **`openai.com` 全站对自动抓取一律 403**。已做对照实验：一个刻意编造的不存在 slug 同样返回 403，因此状态码无法区分存活与失效。涉及 `01_role/1.2_field.md`、`16_future/16.6_cost.md`、`11_production/11.3_scale.md`、`09_ai_native/9.2_llm.md` 以及第 15 章四处的 careers 链接。
- **`iso.org`、`cisa.gov`、`developer.meta.com`、`ai.google.dev/gemma/terms`、`developer.humanitec.com` 深层页**：均对非浏览器请求返回 403 或需 JS 渲染。
- **`mayo.edu`（第 14.4 节 Mayo 案例，逐条溯源见[声明账本](claim_ledger.md)）**：Mayo 自家 2026-05-19 新闻稿把结果表述为「timely palliative care referrals 提升 44%」，与书中「时间缩短超过 40%」看似矛盾；实际书中转述忠实于所引的 Kern Center 页面原文（"decreased the time ... by more than 40%"）。**复核时要确认该页面没有被改写成新闻稿口径**——若已改写，书中句子会在仍然为真的同时失去来源。
