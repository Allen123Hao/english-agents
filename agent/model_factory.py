from typing import Optional
import os
from langchain_openai import ChatOpenAI, AzureChatOpenAI
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

class ModelFactory:
    @staticmethod
    def create_model(model_type: str = "openrouter") -> ChatOpenAI:
        """
        根据配置创建不同的模型实例
        
        Args:
            model_type: 模型类型，可选 "openrouter"、"azure" 或 "openai"
            
        Returns:
            ChatOpenAI: 模型实例
        """
        if model_type == "openrouter":
            openrouter_api_key = os.getenv("OPENROUTER_API_KEY", "")
            if not openrouter_api_key:
                raise ValueError("未设置 OPENROUTER_API_KEY 环境变量")
            
            return ChatOpenAI(
                model="openai/gpt-4o-mini",
                base_url="https://openrouter.ai/api/v1",
                api_key=openrouter_api_key,
            )
        elif model_type == "azure":
            azure_endpoint = os.getenv("AZURE_OPENAI_ENDPOINT", "")
            azure_api_key = os.getenv("AZURE_OPENAI_API_KEY", "")
            
            if not azure_endpoint or not azure_api_key:
                raise ValueError("未设置 AZURE_OPENAI_ENDPOINT 或 AZURE_OPENAI_API_KEY 环境变量")
            
            return AzureChatOpenAI(
                model_name="gpt-4o",
                azure_endpoint=azure_endpoint,
                api_key=azure_api_key,
                api_version="2024-02-15-preview",
                deployment_name="gpt-4o"
            )
        elif model_type == "openai":
            openai_api_key = os.getenv("OPENAI_API_KEY", "")
            if not openai_api_key:
                raise ValueError("未设置 OPENAI_API_KEY 环境变量")
            
            return ChatOpenAI(
                model="gpt-4o",
                api_key=openai_api_key,
                temperature=0.7,
                max_tokens=2000
            )
        else:
            raise ValueError(f"不支持的模型类型: {model_type}") 