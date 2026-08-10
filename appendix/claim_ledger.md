# 第十四章声明账本

本账本为第十四章中可由外部来源核验的关键声明提供稳定编号。正文中的 `claim-id` 注释与下表一一对应，便于审校、更新和追踪来源失效。`verified_at` 只表示链接与所述材料在该日完成核验，不表示相关产品、项目或结果持续有效。

类型说明：`institutional-claim` 为公共机构或组织对其制度/项目的说明；`vendor-claim` 为供应商或客户案例中的自述；`research-result` 为研究论文结果；`regulatory-finding` 为监管或裁判文书认定；`reported-outcome` 为可访问公开材料记录的结果；`synthetic-pattern` 为本书明确标注的合成模式。

边界规则：vendor-claim 的结果数字不得转为本地验收目标。任何案例数字都只能描述其来源语境；本地项目必须根据本地基线、样本、风险、成本和责任边界重新设定指标。

| claim_id | 章节 | 类型 | 声明摘要 | 来源 | verified_at | 不可外推边界 |
| --- | --- | --- | --- | --- | --- | --- |
| FDE-14.1-001 | 14.1 | institutional-claim | GOV.UK Service Manual 要求政府数字服务采用敏捷方式持续构建、测试并根据反馈迭代。 | [GOV.UK agile government services](https://www.gov.uk/service-manual/agile-delivery/agile-government-services-introduction) | 2026-08-10 | 这是英国政府服务指导，不能替代其他司法辖区的法律、采购、可访问性与问责要求。 |
| FDE-14.1-002 | 14.1 | institutional-claim | GDS 公开案例记录了 Public Guardian 以敏捷方式改造 LPA 服务的背景和过程。 | [Public Guardian agile development](https://gds.blog.gov.uk/2014/09/26/the-public-guardian-on-agile-development/) | 2026-08-10 | 单一政府服务案例不能证明所有公共服务适用相同节奏或交付路径。 |
| FDE-14.1-003 | 14.1 | institutional-claim | GOV.UK 治理材料强调到现场查看、以证据核验，并记录其持续扩展敏捷实践的经验。 | [GOV.UK governance principles](https://www.gov.uk/service-manual/governance) 与 [GOV.UK scaling agile](https://gds.blog.gov.uk/2018/04/26/gov-uk-a-journey-in-scaling-agile/) | 2026-08-10 | 治理原则是工作方式证据，不是特定工具或项目收益承诺。 |
| FDE-14.2-001 | 14.2 | vendor-claim | Visa 介绍 VAAI Score 用于识别无卡交易枚举攻击并提供实时风险评分。 | [Visa VAAI Score announcement](https://usa.visa.com/about-visa/newsroom/press-releases.releaseId.20661.html) | 2026-08-10 | 供应商公开口径，仅作案例证据，不得转为本地目标；本地需重建欺诈、误报和延迟基线。 |
| FDE-14.2-002 | 14.2 | vendor-claim | Mastercard 介绍 Decision Intelligence Pro 使用生成式 AI 和实体关系辅助交易风险判断。 | [Mastercard Decision Intelligence Pro](https://www.mastercard.com/news/press/2024/february/mastercard-supercharges-consumer-protection-with-gen-ai/) | 2026-08-10 | 供应商公开口径，仅作案例证据，不得转为本地目标；初始建模结果不等于生产收益。 |
| FDE-14.3-001 | 14.3 | vendor-claim | Siemens 客户案例描述 ROJ 通过 Opcenter 与 Valor 建立电子制造数字化流程及公开结果。 | [Siemens ROJ case study](https://resources.sw.siemens.com/en-US/case-study-roj/) | 2026-08-10 | 供应商与客户联合口径，不得转为本地目标；工厂类型、设备、数据和实施条件均会改变结果。 |
| FDE-14.3-002 | 14.3 | vendor-claim | Siemens 将数字孪生描述为覆盖产品、机器、生产和工厂生命周期的仿真与运行数据能力。 | [Siemens comprehensive digital twin](https://www.siemens.com/en-us/company/digital-twin/comprehensive-digital-twin-for-industry/) | 2026-08-10 | 供应商能力说明不得转为本地目标；不能据此认定任一现场已经形成完整数字孪生。 |
| FDE-14.4-001 | 14.4 | institutional-claim | Mayo Clinic 公开介绍 Control Tower 基于统一数据平台支持住院患者照护工作流，并报告会诊时间与 60 天再入院结果。 | [Mayo Clinic Clinical Data Science](https://www.mayo.edu/research/centers-programs/robert-d-patricia-e-kern-center-science-health-care-delivery/research-activities/clinical-data-science) | 2026-08-10 | 单一机构项目不能证明其他医院、科室或人群获得相同临床结果。 |
| FDE-14.4-002 | 14.4 | research-result | 2021 年随机临床试验评估 AI-ECG 在初级护理中识别低射血分数的真实工作流效果。 | [Nature Medicine AI-ECG trial](https://www.nature.com/articles/s41591-021-01335-4) | 2026-08-10 | 研究设计、人群、终点和机构语境限定结论，不能替代本地临床验证与治理审批。 |
| FDE-14.4-003 | 14.4 | vendor-claim | Pfizer 介绍 AI 支持药物警戒报告摄取和处理中的重复任务，并保留专家责任。 | [Pfizer AI in Drug Safety](https://www.pfizer.com/news/articles/ai-drug-safety-building-elusive-%E2%80%98loch-ness-monster%E2%80%99-reporting-tools) | 2026-08-10 | 企业公开说明不得转为本地目标；不能推导普遍的安全报告效率或人员替代结论。 |
| FDE-14.4-004 | 14.4 | vendor-claim | Pfizer 与 CytoReason 的合作公告描述疾病模型用于支持药物研发决策。 | [Pfizer and CytoReason collaboration](https://www.pfizer.com/news/press-release/press-release-detail/cytoreason-announces-expanded-collaboration-deal-pfizer) | 2026-08-10 | 合作公告不得转为本地目标；不能推导研发成功率、上市速度或临床收益。 |
| FDE-14.5-001 | 14.5 | institutional-claim | 美国能源部项目页将认知数字孪生的目标描述为表示电力系统及其通信、控制和运行。 | [DOE smart-grid digital twin project](https://www.energy.gov/nepa/articles/cx-032183-cognitive-digital-twin-development-secure-and-resilient-smart-grid) | 2026-08-10 | 项目目标不是已实现的可靠性、安全性或经济收益。 |
| FDE-14.5-002 | 14.5 | vendor-claim | Ericsson 的 DNB 案例描述数据驱动到意图驱动网络运营的部署路径和供应商口径结果。 | [Ericsson DNB intent-based operations](https://www.ericsson.com/en/cases/2024/digital-nasional-berhad-intent-based-operations) | 2026-08-10 | 供应商公开口径，仅作案例证据，不得转为本地目标；自治范围需按本地网络和监管复验。 |
| FDE-14.6-001 | 14.6 | reported-outcome | JNCI 报道 MD Anderson 与 IBM Watson 项目支出、合同到期及未进入临床使用等情况。 | [M. D. Anderson Breaks With IBM Watson](https://academic.oup.com/jnci/article/109/5/djx113/3847623) | 2026-08-10 | 该项目结果不能推断医疗 AI 整体不可行。 |
| FDE-14.6-002 | 14.6 | reported-outcome | Zillow 的 SEC 文件记录关闭 Zillow Offers、约 25% 人员缩减和存货减值。 | [Zillow Form 8-K](https://www.sec.gov/Archives/edgar/data/1617640/000161764021000085/z-20211102.htm) | 2026-08-10 | 公开结果不能被简化为单一算法原因，也不能外推到所有自动估值或 iBuying 模式。 |
| FDE-14.6-003 | 14.6 | regulatory-finding | BC Civil Resolution Tribunal 在 Moffatt v. Air Canada 中处理了网站 chatbot 提供错误折扣信息引发的争议。 | [Moffatt v. Air Canada, 2024 BCCRT 149](https://decisions.civilresolutionbc.ca/crt/crtd/en/item/525448/index.do) | 2026-08-10 | 个案裁决不能推断所有客服机器人不可用；法律适用范围受司法辖区和事实约束。 |
| FDE-14.6-004 | 14.6 | regulatory-finding | SEC 文件记录 Knight Capital 2012 年部署与控制缺陷导致的交易事件。 | [SEC Administrative Proceeding 34-70694](https://www.sec.gov/litigation/admin/2013/34-70694.pdf) | 2026-08-10 | 监管个案不能推断所有自动交易必然失败；可迁移的是部署与止损控制要求。 |
| FDE-14.6-005 | 14.6 | synthetic-pattern | Demo-Driven Delivery 为本书合成反模式，用于演示 demo 边界与生产验收脱节的风险。 | [第十四章合成案例说明](https://github.com/yeasy/forward_deployed_engineering_guide) | 2026-08-10 | 合成案例不是对任何真实组织或项目的事实陈述，也不提供发生率或收益结论。 |

## 维护规则

新增或修改第十四章外部事实时，应先分配稳定 `claim_id`，再同步正文注释与账本；来源失效时保留原 ID，并以可访问的一手或权威替代来源更新记录。若只能获得供应商材料，应明确标为 `vendor-claim`，同时保留本地复验边界，不能悄然提升为独立研究结论。
