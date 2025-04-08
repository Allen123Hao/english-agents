from typing import Dict, Any, TypedDict, List, Union, Literal, Optional
from langgraph.graph import StateGraph, END
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
import os
from enum import Enum
import json
import jsonpath_ng
from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.responses import StreamingResponse
from sse_starlette.sse import EventSourceResponse
from pydantic import BaseModel
from .model_factory import ModelFactory

# 加载环境变量
load_dotenv()

class Language(str, Enum):
    # 中文变体
    SIMPLIFIED_CHINESE = "zh_CN"  # 简体中文
    TRADITIONAL_CHINESE_TW = "zh_TW"  # 繁体中文(台湾)
    TRADITIONAL_CHINESE_HK = "zh_HK"  # 繁体中文(香港)
    
    # 英语变体
    ENGLISH_US = "en_US"  # 美式英语
    ENGLISH_UK = "en_GB"  # 英式英语
    
    # 其他语言
    JAPANESE = "ja_JP"  # 日语
    KOREAN = "ko_KR"  # 韩语
    FRENCH = "fr_FR"  # 法语
    GERMAN = "de_DE"  # 德语
    SPANISH_ES = "es_ES"  # 西班牙语(西班牙)
    RUSSIAN = "ru_RU"  # 俄语
    
    @classmethod
    def get_display_name(cls, lang_code: str) -> str:
        """获取语言的显示名称"""
        display_names = {
            "zh_CN": "简体中文",
            "zh_TW": "繁体中文(台湾)",
            "zh_HK": "繁体中文(香港)",
            "en_US": "美式英语",
            "en_GB": "英式英语",
            "ja_JP": "日语",
            "ko_KR": "韩语",
            "fr_FR": "法语",
            "de_DE": "德语",
            "es_ES": "西班牙语(西班牙)",
            "ru_RU": "俄语"
        }
        return display_names.get(lang_code, lang_code)

# API 模型定义
class TranslationRequest(BaseModel):
    text: str
    source_lang: Language
    target_lang: Language

class JsonTranslationRequest(BaseModel):
    json_data: Dict[str, Any]
    json_paths: List[str]
    source_lang: Language
    target_lang: Language

class TranslationResponse(BaseModel):
    translated_text: str
    source_lang: Language
    target_lang: Language

class LanguageInfo(BaseModel):
    code: str
    name: str

# 定义状态类型
class TranslatorState(TypedDict):
    messages: List[Dict[str, Any]]           # 保存完整对话历史
    current_text: str                        # 当前要翻译的文本
    translated_text: str                     # 翻译结果
    source_lang: Language                    # 源语言
    target_lang: Language                    # 目标语言
    json_data: Optional[Dict[str, Any]]      # JSON 数据
    json_paths: Optional[List[str]]          # JSON 路径
    status: Literal["pending", "success", "error"]  # 状态标记
    error_message: Optional[str]             # 错误信息

class TranslatorAgents:
    def __init__(self, model_type: str = "openrouter"):
        # 使用模型工厂初始化模型
        self.model = ModelFactory.create_model(model_type)
        
        # 初始化提示模板
        self.prompts = self._init_prompts()
        
        # 初始化输出解析器
        self.output_parser = StrOutputParser()
    
    def _init_prompts(self) -> Dict[str, ChatPromptTemplate]:
        """初始化所有提示模板"""
        return {
            "translate": ChatPromptTemplate.from_messages([
                ("system", "你是一个专业的翻译。请将用户输入的{source_lang}准确翻译成{target_lang}。切记，不要翻译英文部分，保持专业、准确和自然的翻译风格。"),
                ("user", "请将以下{source_lang}翻译成{target_lang}：\n{text}")
            ]),
            "translate_json": ChatPromptTemplate.from_messages([
                ("system", """你是一个专业的 JSON 翻译器。
请将指定字段从{source_lang}翻译成{target_lang}。
只翻译指定的字段，注意：英文部分不要翻译，保持完整 JSON 结构不变。
请确保翻译准确、专业和自然。
返回 JSON 格式，不要包含"```"，不要做其他解释"""),
                ("user", """请翻译以下 JSON 数据中指定字段的值，从{source_lang}到{target_lang}：

需要翻译的字段：
{fields_text}

原始 JSON 数据：
{json_data}""")
            ])
        }
    
    async def translate_text(self, state: TranslatorState) -> TranslatorState:
        """翻译普通文本"""
        try:
            source_lang_name = Language.get_display_name(state['source_lang'].value)
            target_lang_name = Language.get_display_name(state['target_lang'].value)
            
            # 使用 LangChain 链式调用
            chain = self.prompts["translate"] | self.model | self.output_parser
            
            translated_text = await chain.ainvoke({
                "source_lang": source_lang_name,
                "target_lang": target_lang_name,
                "text": state['current_text']
            })
            
            # 更新消息历史
            state["messages"].append({
                "role": "assistant",
                "content": translated_text
            })
            
            return {
                **state,
                "translated_text": translated_text,
                "status": "success"
            }
        except Exception as e:
            return {
                **state,
                "status": "error",
                "error_message": str(e)
            }
    
    async def translate_json(self, state: TranslatorState) -> TranslatorState:
        """翻译 JSON 数据中的指定字段"""
        if not state['json_data'] or not state['json_paths']:
            return {
                **state,
                "status": "error",
                "error_message": "Missing JSON data or paths"
            }
        
        try:
            source_lang_name = Language.get_display_name(state['source_lang'].value)
            target_lang_name = Language.get_display_name(state['target_lang'].value)
            
            # 构建需要翻译的字段文本
            fields_text = "\n".join([f"- {path}" for path in state['json_paths']])
            
            # 使用 LangChain 链式调用
            chain = self.prompts["translate_json"] | self.model | self.output_parser
            
            translations_text = await chain.ainvoke({
                "source_lang": source_lang_name,
                "target_lang": target_lang_name,
                "fields_text": fields_text,
                "json_data": json.dumps(state['json_data'], ensure_ascii=False, indent=2)
            })
            
            try:
                translations = json.loads(translations_text)
                result_data = state['json_data'].copy()
                
                # 应用翻译结果
                for path, translated_value in translations.items():
                    jsonpath_expr = jsonpath_ng.parse(path)
                    jsonpath_expr.update(result_data, translated_value)
                
                # 更新消息历史
                state["messages"].append({
                    "role": "assistant",
                    "content": json.dumps(result_data, ensure_ascii=False)
                })
                
                return {
                    **state,
                    "translated_text": json.dumps(result_data, ensure_ascii=False),
                    "status": "success"
                }
            except json.JSONDecodeError:
                return {
                    **state,
                    "status": "error",
                    "error_message": "Invalid JSON response from translation"
                }
        except Exception as e:
            return {
                **state,
                "status": "error",
                "error_message": str(e)
            }

def router(state: TranslatorState) -> Dict[str, Any]:
    """路由决策函数"""
    next_step = "translate_json" if state.get("json_data") and state.get("json_paths") else "translate_text"
    return {**state, "next": next_step}

def create_translator_workflow() -> StateGraph:
    """创建翻译工作流"""
    # 创建代理实例
    agents = TranslatorAgents()
    
    # 创建工作流
    workflow = StateGraph(TranslatorState)
    
    # 添加节点
    workflow.add_node("route", router)
    workflow.add_node("translate_text", agents.translate_text)
    workflow.add_node("translate_json", agents.translate_json)
    
    # 添加条件路由
    workflow.add_conditional_edges(
        "route",
        lambda x: x["next"],
        {
            "translate_text": "translate_text",
            "translate_json": "translate_json"
        }
    )

    # 设置入口点
    workflow.set_entry_point("route")

    # 设置终止节点
    workflow.add_edge("translate_text", END)
    workflow.add_edge("translate_json", END)
    
    return workflow.compile()

# 创建 FastAPI 应用
app = FastAPI()

# 编译工作流
workflow = create_translator_workflow()

@app.post("/translate")
async def translate(request: TranslationRequest):
    """翻译端点"""
    async def event_generator():
        # 初始化状态
        state = TranslatorState(
            messages=[{"role": "user", "content": request.text}],
            current_text=request.text,
            translated_text="",
            source_lang=request.source_lang,
            target_lang=request.target_lang,
            json_data=request.json_data,
            json_paths=request.json_paths,
            status="pending",
            error_message=None
        )
        
        try:
            # 执行工作流
            result = await workflow.ainvoke(state)
            
            if result["status"] == "success":
                yield json.dumps({
                    "event": "translation",
                    "data": {
                        "translated_text": result["translated_text"],
                        "status": "success"
                    }
                })
            else:
                yield json.dumps({
                    "event": "error",
                    "data": {
                        "message": result["error_message"],
                        "status": "error"
                    }
                })
        except Exception as e:
            yield json.dumps({
                "event": "error",
                "data": {
                    "message": str(e),
                    "status": "error"
                }
            })
    
    return EventSourceResponse(event_generator())

@app.get("/languages")
def get_languages():
    """获取支持的语言列表"""
    return [
        {"code": lang.value, "name": Language.get_display_name(lang.value)}
        for lang in Language
    ]