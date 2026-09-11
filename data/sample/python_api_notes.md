# Python API 工程笔记

这份笔记用于 DocMind RAG 的 Markdown 摄取、section metadata 与检索测试。

## 1. 类型提示与边界对象

Python 类型提示的主要价值不是让运行时变成静态语言，而是让接口边界更清晰。对 API 项目而言，请求模型、响应模型、Repository 返回值和 Client 协议都应该尽量有明确类型。

对外部数据，优先通过 Pydantic 做运行时校验；对内部简单数据结构，可以使用 dataclass 或 TypedDict。不要为了类型提示把所有函数都写成复杂泛型，类型应服务于可读性和维护性。

## 2. pathlib 与数据目录

文件路径建议使用 `pathlib.Path`，不要在业务代码里大量手工拼接字符串。项目可以从 `DATA_DIR` 派生 `sqlite_path`、`chroma_path` 和临时上传目录，并在启动时确保必要目录存在。

相对路径应明确以项目工作目录为基准。进入 Docker 后，持久化目录可以统一放在 `/app/data`，再通过 volume 挂载。

## 3. request_id 与结构化日志

每个 HTTP 请求都可以生成一个 request_id，并通过响应头和日志携带。这样一次 `/ask` 涉及 retrieve、LLM 和 storage 多个阶段时，可以使用同一个 request_id 串联排查。

日志建议记录事件名称、阶段、耗时、document_id、top_k、best_distance 和异常类型；不要记录 API Key、Authorization、完整文档或完整 Prompt。

## 4. 异常边界与外部 Client

Embedding 和 LLM 属于外部依赖。Client 层负责超时、有限重试以及把供应商异常转换为项目内部异常；业务层不要到处直接捕获特定供应商 SDK 的异常类型。

一个清晰的边界是：Client 处理“供应商怎么调用”，pipeline 处理“调用失败后本业务怎么响应”。这样测试时可以用 FakeEmbeddingClient / FakeLLMClient 替换真实实现。
