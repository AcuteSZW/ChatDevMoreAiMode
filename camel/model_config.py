# -*- encoding: utf-8 -*-
MODELS = {
    "openai": {
        "base_url": "https://api.openai.com/v1",
        "api_types": ["openai"],
        "models": [{
            "name": "gpt-3.5-turbo",
            "num_tokens": 4096
        }, {
            "name": "gpt-4",
            "num_tokens": 8192
        }]
    },
    "qwen": {
        "base_url": "https://dashscope.aliyuncs.com/compatible-mode/v1",
        "api_types": ["openai", "self"],
        "models": [{
            "name": "qwen1.5-110-chat",
            "num_tokens": 8192
        }, {
            "name": "qwen-plus",
            "num_tokens": 8192
        }
        ]

    },
    "deepseek": {
        "base_url": "https://api.deepseek.com",
        "api_types": ["openai"],
        "models": [{
            "name": "deepseek-chat",
            "num_tokens": 8192
        }, {
            "name": "deepseek-reasoner",
            "num_tokens": 8192
        }]

    },
    "siliconflow": {
        "base_url": "https://api.siliconflow.cn/v1",
        "api_types": ["openai"],
        "models": [{
            "name": "deepseek-ai/DeepSeek-R1",
            "num_tokens": 8192
        }, {
            "name": "deepseek-ai/DeepSeek-V3",
            "num_tokens": 8192
        }]
    }
}