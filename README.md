# Multi-Language Translator Agent

基于 LangGraph 和 FastAPI 实现的高性能多语言翻译服务，支持语言变体和 JSON 数据翻译。支持多种 AI 模型后端，包括 OpenAI、Azure OpenAI 和 OpenRouter。

## 项目特点

- 🚀 **高性能架构**：基于 FastAPI 的异步处理，支持高并发请求
- 🔄 **智能翻译**：支持多种 AI 模型后端，提供高质量的翻译结果
- 🌐 **多语言支持**：支持多种语言及其变体之间的互译
- 📦 **JSON 支持**：支持翻译 JSON 数据中的指定字段
- 🔒 **类型安全**：使用 Pydantic 进行数据验证和类型检查
- 📚 **完整文档**：提供详细的 API 文档和示例

## 技术栈

- **后端框架**：FastAPI
- **AI 模型**：
  - OpenAI GPT-4
  - Azure OpenAI GPT-4
  - OpenRouter GPT-4
- **工作流引擎**：LangGraph
- **数据验证**：Pydantic
- **环境管理**：python-dotenv
- **API 文档**：Swagger UI / ReDoc

## 支持的语言

### 中文变体

- 简体中文 (zh_CN)
- 繁体中文(台湾) (zh_TW)
- 繁体中文(香港) (zh_HK)

### 英语变体

- 美式英语 (en_US)
- 英式英语 (en_GB)

### 其他语言

- 日语 (ja_JP)
- 韩语 (ko_KR)
- 法语 (fr_FR)
- 德语 (de_DE)
- 西班牙语(西班牙) (es_ES)
- 西班牙语(墨西哥) (es_MX)
- 俄语 (ru_RU)

## 快速开始

### 环境要求

- Python 3.10+
- 选择以下任一 AI 模型服务：
  - OpenAI API Key
  - Azure OpenAI 服务
  - OpenRouter API Key

### 安装步骤

1. 克隆仓库：

```bash
git clone <repository-url>
cd english-agents
```

2. 安装依赖：

```bash
pip install -r requirements.txt
```

3. 配置环境变量：
   创建 `.env` 文件并添加以下内容（根据您选择的模型服务）：

```bash
# OpenAI 配置
OPENAI_API_KEY=your_openai_api_key_here

# 或 Azure OpenAI 配置
AZURE_OPENAI_ENDPOINT=your_azure_endpoint_here
AZURE_OPENAI_API_KEY=your_azure_api_key_here

# 或 OpenRouter 配置
OPENROUTER_API_KEY=your_openrouter_api_key_here
```

要获取 OpenRouter API Key：

1. 访问 https://openrouter.ai/
2. 注册并登录
3. 在控制台中创建 API Key

### 运行服务

```bash
# 开发环境运行
python main.py

# 生产环境运行（使用 nohup）
./nohup-run.sh
```

服务将在 http://localhost:8000 启动

## 模型配置

### OpenAI 配置
```python
from agent.model_factory import ModelFactory

# 使用 OpenAI 模型
model = ModelFactory.create_model(model_type="openai")
```

### Azure OpenAI 配置
```python
from agent.model_factory import ModelFactory

# 使用 Azure OpenAI 模型
model = ModelFactory.create_model(model_type="azure")
```

### OpenRouter 配置
```python
from agent.model_factory import ModelFactory

# 使用 OpenRouter 模型（默认）
model = ModelFactory.create_model(model_type="openrouter")
```

## API 文档

### 基础翻译接口

**POST /translate**

请求示例：

```json
{
  "text": "Hello, how are you?",
  "source_lang": "en_US",
  "target_lang": "zh_CN"
}
```

响应示例：

```json
{
  "translated_text": "你好，你好吗？",
  "source_lang": "en_US",
  "target_lang": "zh_CN"
}
```

### JSON 数据翻译

**POST /translate/json**

请求示例：

```json
{
  "json_data": {
    "title": "Hello World",
    "description": "This is a test"
  },
  "json_paths": ["title", "description"],
  "source_lang": "en_US",
  "target_lang": "zh_CN"
}
```

### 获取支持的语言列表

**GET /languages**

响应示例：

```json
[
  {
    "code": "zh_CN",
    "name": "简体中文"
  },
  {
    "code": "en_US",
    "name": "美式英语"
  }
]
```

## 部署

项目提供了部署脚本 `deploy.sh`，支持一键部署到生产环境。

```bash
./deploy.sh
```

## 开发指南

### 添加新语言

1. 在 `Language` 枚举中添加新的语言代码
2. 在 `Language.get_display_name()` 方法中添加对应的显示名称
3. 更新 API 文档中的语言列表

### 错误处理

服务实现了完整的错误处理机制：
- 400：请求参数错误
- 500：服务器内部错误
- 详细的错误信息会通过响应返回

## 贡献指南

欢迎提交 Issue 和 Pull Request 来帮助改进项目。

## 许可证

[MIT License](LICENSE)
