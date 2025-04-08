from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Dict, Any, List
from dotenv import load_dotenv
import os
from agent.translator import create_translator_workflow, Language, TranslationRequest, JsonTranslationRequest, TranslationResponse, LanguageInfo

# 加载环境变量
load_dotenv()

app = FastAPI(
    title="Multi-Language Translator API",
    description="支持多语言互译的翻译服务，包括语言变体（如简体中文、繁体中文等）",
    version="1.0.0"
)

# 初始化翻译工作流
workflow = create_translator_workflow()

@app.get("/languages", response_model=List[LanguageInfo])
async def get_supported_languages() -> List[Dict[str, str]]:
    """获取支持的语言列表"""
    return [
        {"code": lang.value, "name": Language.get_display_name(lang.value)}
        for lang in Language
    ]

@app.post("/translate", response_model=TranslationResponse)
async def translate_text(request: TranslationRequest) -> Dict[str, Any]:
    """翻译文本"""
    try:
        if request.source_lang == request.target_lang:
            raise HTTPException(
                status_code=400,
                detail=f"源语言和目标语言不能相同：{Language.get_display_name(request.source_lang.value)}"
            )
            
        result = await workflow.ainvoke({
            "messages": [{"role": "user", "content": request.text}],
            "current_text": request.text,
            "translated_text": "",
            "source_lang": request.source_lang,
            "target_lang": request.target_lang,
            "json_data": None,
            "json_paths": None,
            "status": "pending",
            "error_message": None
        })
        
        if result["status"] == "error":
            raise HTTPException(status_code=500, detail=result["error_message"])
        
        return {
            "translated_text": result["translated_text"],
            "source_lang": request.source_lang,
            "target_lang": request.target_lang
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/translate/json", response_model=TranslationResponse)
async def translate_json(request: JsonTranslationRequest) -> Dict[str, Any]:
    """翻译 JSON 数据中的指定字段"""
    try:
        if request.source_lang == request.target_lang:
            raise HTTPException(
                status_code=400,
                detail=f"源语言和目标语言不能相同：{Language.get_display_name(request.source_lang.value)}"
            )
            
        if not request.json_paths:
            raise HTTPException(
                status_code=400,
                detail="必须指定至少一个要翻译的 JSON 路径"
            )
            
        result = await workflow.ainvoke({
            "messages": [{"role": "user", "content": str(request.json_data)}],
            "current_text": "",
            "translated_text": "",
            "source_lang": request.source_lang,
            "target_lang": request.target_lang,
            "json_data": request.json_data,
            "json_paths": request.json_paths,
            "status": "pending",
            "error_message": None
        })
        
        if result["status"] == "error":
            raise HTTPException(status_code=500, detail=result["error_message"])
        
        return {
            "translated_text": result["translated_text"],
            "source_lang": request.source_lang,
            "target_lang": request.target_lang
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 