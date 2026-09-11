# DocMind RAG

基于 **FastAPI + ChromaDB + SQLite** 构建的文档检索增强生成（RAG）后端服务。

项目支持 PDF / Markdown 文档上传、解析、切分、向量化与持久化，并提供语义检索、基于证据的问答、来源引用、无答案拒答、检索效果评测及 Docker 部署能力。

> 当前版本：`v1.0.0`

---

## 项目简介

DocMind RAG 面向本地知识库 / 文档问答场景，完整实现了一条可运行、可测试、可评估的 RAG 后端链路：

```text
文档上传
   ↓
PDF / Markdown 解析
   ↓
文本清洗与 Chunk 切分
   ↓
Embedding 向量化
   ↓
ChromaDB 向量索引
   ↓
语义检索
   ↓
证据充分性判断
   ↓
上下文构建
   ↓
LLM 生成回答
   ↓
Citation 校验与来源返回
```

系统同时使用：

- **SQLite**：保存文档元数据
- **ChromaDB**：保存 Chunk 向量与检索元数据
- **FastAPI**：提供文档管理、检索和问答 API
- **pytest**：覆盖核心业务与异常场景
- **Docker**：提供容器化运行方式

项目支持 `fake` 与 `real` 两种模型模式：`fake` 模式无需真实模型 API，可用于本地开发与测试；`real` 模式可接入 OpenAI-compatible 的 Embedding / LLM 服务。

---

## 核心功能

### 文档管理

- PDF 文档上传与解析
- Markdown 文档上传与标题层级解析
- 上传文件大小限制
- 文档 checksum 去重
- 文档列表查询
- 单文档查询
- 文档删除
- 删除文档时同步清理向量数据
- 入库失败时执行补偿清理，避免元数据与向量数据不一致

### RAG 检索与问答

- Query Embedding
- ChromaDB 余弦距离检索
- Top-K 检索
- 文档有效性过滤
- 检索距离阈值判断
- 无充分证据时拒答
- Context 长度控制
- LLM 生成
- Citation 校验
- 返回文档名、页码 / Markdown Section、Chunk Index 与引用片段
- 返回 Retrieve / LLM / Total 延迟信息

### 工程能力

- FastAPI App Factory
- 依赖容器管理
- 统一异常处理
- Request ID Middleware
- 结构化日志
- `/health/live` 存活检查
- `/health/ready` 就绪检查
- Fake / Real 模型模式
- pytest 自动化测试
- RAG 离线评测
- 检索阈值校准
- Docker Compose 部署
- 数据卷持久化

---

## 技术栈

| 分类 | 技术 |
| --- | --- |
| Web Framework | FastAPI |
| ASGI Server | Uvicorn |
| Validation / Config | Pydantic + pydantic-settings |
| Metadata Storage | SQLite + SQLAlchemy |
| Vector Database | ChromaDB |
| PDF Parsing | pypdf |
| HTTP Client | HTTPX |
| Model Interface | OpenAI-compatible API |
| Testing | pytest + pytest-cov |
| Containerization | Docker + Docker Compose |
| Python | Python 3.13 |

---

## 系统架构

```text
                         ┌────────────────────┐
                         │    FastAPI API     │
                         └─────────┬──────────┘
                                   │
              ┌────────────────────┴────────────────────┐
              │                                         │
     ┌────────▼────────┐                       ┌────────▼────────┐
     │ Document API    │                       │    RAG API      │
     └────────┬────────┘                       └────────┬────────┘
              │                                         │
     ┌────────▼────────┐                       ┌────────▼────────┐
     │ IngestionService│                       │  RAGPipeline    │
     └────────┬────────┘                       └────────┬────────┘
              │                                         │
      ┌───────┴────────┐                    ┌───────────┴───────────┐
      │                │                    │                       │
┌─────▼─────┐   ┌──────▼──────┐     ┌──────▼──────┐        ┌──────▼──────┐
│  SQLite   │   │  ChromaDB   │     │  Retriever  │        │ LLM Client  │
│ Metadata  │   │ Vector Store│     └──────┬──────┘        └─────────────┘
└───────────┘   └─────────────┘            │
                                      ┌─────▼─────┐
                                      │ ChromaDB  │
                                      └───────────┘
```

---

## 项目结构

```text
docmind-rag/
├── app/
│   ├── clients/                 # Embedding / LLM Client
│   │   ├── base.py
│   │   ├── embeddings.py
│   │   ├── fake.py
│   │   ├── factory.py
│   │   ├── http_common.py
│   │   └── llm.py
│   │
│   ├── core/                    # 配置、日志、中间件、异常处理
│   ├── ingestion/               # 文档上传、解析、清洗、切分与入库
│   │   ├── cleaner.py
│   │   ├── loader.py
│   │   ├── service.py
│   │   ├── splitter.py
│   │   ├── types.py
│   │   └── upload.py
│   │
│   ├── rag/                     # RAG 核心流程
│   │   ├── citation.py
│   │   ├── context.py
│   │   ├── gate.py
│   │   ├── pipeline.py
│   │   ├── prompt.py
│   │   ├── retriever.py
│   │   └── types.py
│   │
│   ├── routers/                 # FastAPI Router
│   ├── schemas/                 # 请求 / 响应 Schema
│   ├── storage/                 # SQLite / ChromaDB
│   │   ├── database.py
│   │   ├── document_repo.py
│   │   ├── document_service.py
│   │   ├── models.py
│   │   └── vector_store.py
│   │
│   ├── container.py             # 应用依赖容器
│   ├── deps.py
│   └── main.py
│
├── data/
│   └── sample/                  # 公开评测样本文档
│
├── eval/
│   ├── results/                 # 评测结果
│   ├── calibrate_threshold.py   # Distance 阈值校准
│   ├── collect_distances.py
│   ├── metrics.py
│   ├── questions.jsonl
│   └── run_eval.py
│
├── tests/                       # 自动化测试
├── .env.example
├── .env.docker.example
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
└── README.md
```

---

## API 概览

### Health

| Method | Endpoint | Description |
| --- | --- | --- |
| GET | `/health/live` | 服务存活检查 |
| GET | `/health/ready` | SQLite、Chroma、数据目录及模型配置就绪检查 |

### Documents

| Method | Endpoint | Description |
| --- | --- | --- |
| POST | `/documents` | 上传并索引 PDF / Markdown |
| GET | `/documents` | 获取文档列表 |
| GET | `/documents/{document_id}` | 获取单个文档 |
| DELETE | `/documents/{document_id}` | 删除文档及关联向量 |

### RAG

| Method | Endpoint | Description |
| --- | --- | --- |
| POST | `/retrieve` | 执行语义检索 |
| POST | `/ask` | 基于知识库检索结果生成回答 |

启动服务后可通过 Swagger 查看完整接口：

```text
http://127.0.0.1:8001/docs
```

---

## 快速开始

### 1. 克隆项目

```bash
git clone https://github.com/yibanban0923/docmind-rag.git
cd docmind-rag
```

### 2. 创建虚拟环境

```bash
python3.13 -m venv .venv
source .venv/bin/activate
```

### 3. 安装依赖

```bash
python -m pip install --upgrade pip
pip install -r requirements.txt
```

### 4. 创建环境配置

```bash
cp .env.example .env
```

项目默认：

```env
MODEL_MODE=fake
```

因此无需真实模型 API，即可启动服务、运行接口和自动化测试。

### 5. 启动服务

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8001 --reload
```

访问：

```text
Swagger:       http://127.0.0.1:8001/docs
Live Check:    http://127.0.0.1:8001/health/live
Ready Check:   http://127.0.0.1:8001/health/ready
```

---

## Fake / Real 模型模式

### Fake 模式

`.env`：

```env
MODEL_MODE=fake
```

Fake 模式提供确定性的本地 Embedding 与固定 LLM 响应，主要用于：

- 本地开发
- API 联调
- pytest
- CI
- 无模型 API Key 场景

> Fake 模式用于功能验证，不用于真实 RAG 效果评估。

### Real 模式

将：

```env
MODEL_MODE=real
```

并配置：

```env
LLM_API_KEY=your_key
LLM_ENDPOINT=https://your-provider-endpoint
LLM_MODEL=your-model

EMBEDDING_API_KEY=your_key
EMBEDDING_ENDPOINT=https://your-provider-endpoint
EMBEDDING_MODEL=your-embedding-model
```

Client 使用 OpenAI-compatible 接口，因此可以根据实际模型服务填写对应 Endpoint、Model 与 API Key。

---

## 环境变量

核心参数：

```env
APP_NAME=DocMind RAG
APP_ENV=development
APP_HOST=0.0.0.0
APP_PORT=8001

MODEL_MODE=fake

DATA_DIR=./data

CHUNK_SIZE=700
CHUNK_OVERLAP=100

TOP_K=3
MAX_DISTANCE=0.5

CONTEXT_MAX_CHARS=7000
MAX_UPLOAD_MB=10
EMBED_BATCH_SIZE=32

CHROMA_COLLECTION=docmind_chunks
```

参数说明：

| 参数 | 说明 |
| --- | --- |
| `CHUNK_SIZE` | Chunk 最大字符数 |
| `CHUNK_OVERLAP` | 相邻 Chunk 重叠字符数 |
| `TOP_K` | 默认返回的检索结果数量 |
| `MAX_DISTANCE` | 证据充分性判断的最大距离阈值 |
| `CONTEXT_MAX_CHARS` | 送入 LLM 的上下文最大字符数 |
| `MAX_UPLOAD_MB` | 单文档最大上传大小 |
| `EMBED_BATCH_SIZE` | 文档向量化批次大小 |

`CHUNK_OVERLAP` 必须小于 `CHUNK_SIZE`。

---

## 文档上传

目前支持：

- `.pdf`
- `.md`

### cURL 示例

```bash
curl -X POST \
  http://127.0.0.1:8001/documents \
  -F "file=@data/sample/example.pdf"
```

成功后会完成：

```text
上传
→ 临时文件
→ 文档解析
→ 文本清洗
→ Chunk 切分
→ Embedding
→ ChromaDB 写入
→ SQLite 元数据写入
```

PDF Chunk 会保留页码信息；Markdown 会保留 Section 路径，可用于回答来源定位。

---

## 检索示例

```bash
curl -X POST \
  http://127.0.0.1:8001/retrieve \
  -H "Content-Type: application/json" \
  -d '{
    "question": "文档中主要介绍了什么？",
    "top_k": 3
  }'
```

响应包含：

- Rank
- Distance
- Chunk 文本
- Document ID
- Filename
- File Type
- Page / Section
- Chunk Index
- Retrieval Latency

---

## RAG 问答示例

```bash
curl -X POST \
  http://127.0.0.1:8001/ask \
  -H "Content-Type: application/json" \
  -d '{
    "question": "文档中主要介绍了什么？"
  }'
```

响应示例：

```json
{
  "answer": "根据提供的资料，可以确认相关信息。[S1]",
  "sources": [
    {
      "source_id": "S1",
      "document_id": "...",
      "filename": "example.pdf",
      "page": 1,
      "section": null,
      "chunk_index": 0,
      "excerpt": "..."
    }
  ],
  "latency_ms": {
    "retrieve": 10.2,
    "llm": 220.5,
    "total": 231.4
  },
  "request_id": "..."
}
```

系统会对检索结果执行证据阈值判断。当最佳检索结果不足以支撑回答时，会直接拒答，而不是强行调用 LLM 生成答案。

---

## 数据存储

运行时数据默认保存到：

```text
data/
├── docmind.db
├── chroma/
└── tmp/
```

其中：

```text
SQLite     → 文档元数据
ChromaDB   → Chunk 文本、Embedding 与检索元数据
tmp        → 上传过程临时文件
```

上传结束后临时文件会被清理。

---

## 自动化测试

运行：

```bash
pytest -q
```

项目测试覆盖包括：

- Health / Document API
- RAG API
- 文档删除
- Markdown Loader
- Cleaner / Splitter
- SQLite Repository
- Chroma Vector Store
- RAG Gate
- Context / Citation
- Ingestion Compensation

如需覆盖率：

```bash
pytest --cov=app --cov-report=term-missing
```

---

## RAG 评测

项目内置评测脚本，用于比较不同 Chunk / Top-K 配置，并统计：

- Recall@K
- No-answer Accuracy
- False Refusal Rate
- Retrieval Average / P95 Latency
- LLM Average / P95 Latency
- Total Average / P95 Latency

### 运行评测

评测使用真实模型，因此先确保：

```env
MODEL_MODE=real
```

并完成 LLM / Embedding 配置。

然后：

```bash
python -m eval.run_eval --config all
```

当前内置三组配置：

```text
baseline_a  → chunk_size=700,  overlap=100, top_k=3
chunk_b     → chunk_size=1000, overlap=150, top_k=3
topk_c      → chunk_size=700,  overlap=100, top_k=5
```

评测结果输出到：

```text
eval/results/
```

### 检索阈值校准

收集检索距离：

```bash
python -m eval.collect_distances
```

计算候选阈值：

```bash
python -m eval.calibrate_threshold
```

可根据真实评测结果调整：

```env
MAX_DISTANCE=<calibrated-value>
```

---

## Docker 部署

### 1. 创建 Docker 配置

当前 `docker-compose.yml` 从项目根目录的 `.env` 读取环境变量。

可以从 Docker 模板生成：

```bash
cp .env.docker.example .env
```

然后填写真实模型配置。

特别注意：

```env
MAX_DISTANCE=0.5
```

必须填写为数值；生产环境建议使用评测校准后的阈值。

### 2. 构建并启动

```bash
docker compose up --build -d
```

### 3. 查看状态

```bash
docker compose ps
```

### 4. 查看日志

```bash
docker compose logs -f api
```

### 5. 健康检查

```bash
curl http://127.0.0.1:8001/health/live
curl http://127.0.0.1:8001/health/ready
```

Docker 使用数据卷持久化运行时数据，即使容器重建，SQLite 与 ChromaDB 数据仍可保留。

### 6. 停止服务

```bash
docker compose down
```

如执行：

```bash
docker compose down -v
```

会同时删除持久化数据卷，请谨慎使用。

---

## 设计要点

### 1. 文档去重

上传文档会计算 checksum；相同内容重复上传时拒绝重复入库。

### 2. 双存储一致性

ChromaDB 保存向量，SQLite 保存文档元数据。

如果向量写入后元数据保存失败，系统会执行补偿删除，降低两个存储之间的数据不一致风险。

### 3. 检索有效性过滤

向量检索后会根据 SQLite 中仍然存在的 Document ID 过滤结果，避免已经删除的文档继续进入 RAG 上下文。

### 4. Evidence Gate

RAG Pipeline 不会对所有问题都直接调用 LLM。

当检索结果为空或距离超过设定阈值时，系统直接返回拒答结果，减少无依据生成。

### 5. Citation Validation

模型回答完成后，会校验回答中实际使用的 Citation，仅向调用方返回有效引用来源。

### 6. 可观测性

接口返回 Request ID，并记录：

- Parse Latency
- Embedding Latency
- Index Latency
- Retrieval Latency
- LLM Latency
- Total Latency

便于定位问题与进行性能评测。

---

## 后续计划

- 增加更多文档格式支持
- 增加用户与知识库隔离
- 增加 Hybrid Search / Reranker
- 增加流式回答
- 增加模型调用缓存
- 增加 GitHub Actions CI
- 引入更完整的线上观测指标
- 扩充 RAG Benchmark 数据集

---

## Repository

https://github.com/yibanban0923/docmind-rag

---

## Author

**yibanban0923**

DocMind RAG 是一个用于学习、实践和展示 RAG 系统工程化实现的后端项目。
