# RAG 评估方法笔记

这份笔记用于 DocMind RAG 的 Markdown 摄取和 Day 5 固定评测。

## 1. Recall@K：正确证据有没有被召回

Recall@K 用来回答“正确来源是否进入 Top-K”。对于每个可回答问题，评测程序检查检索结果的 metadata 是否命中 `expected_document + expected_locator`。如果命中，则该 case 记为成功。

这个指标关注检索，不直接判断 LLM 最终答案质量。若正确证据根本没有进入候选，上层生成再强也无法稳定补救。

## 2. No-answer Accuracy：无资料问题是否被拒答

固定评测集中应包含一部分明确无答案问题。它们应该在 Evidence Gate 阶段被拒答，而且拒答分支不调用 LLM。

评估时除了统计无答案问题的拒答准确率，也要观察可回答问题被错误拒答的数量。阈值过严会提高拒答率，却可能损害正常问题的可用性。

## 3. Latency：耗时发生在哪里

延迟至少拆成 retrieve、LLM 和 total。需要时还可以记录 embed。报告中可以保存平均值，并在样本量允许时计算 P95，以避免只看平均值掩盖长尾请求。

优化时应先看瓶颈属于本地检索、Embedding provider、LLM provider 还是过大的 Context，而不是盲目优化所有模块。

## 4. 对照实验与失败分析

实验应固定同一批文档和问题，一次主要改变一个变量。基线可以使用 `chunk_size=700, overlap=100, top_k=3`；然后单独改变 chunk 参数或 Top-K。

每次实验都要保存完整配置、指标和失败 case，不应只保留最好的一组结果。失败案例能够帮助区分：是证据没有召回、Evidence Gate 阈值不合适，还是 LLM 没有正确使用已经提供的证据。
