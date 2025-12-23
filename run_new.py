import argparse
import logging
import os
import sys

from camel.typing import ModelType
from camel.typing import ModelTypeNew
from chatdev.chat_chain import ChatChain
from camel.utils import get_model_info
from dotenv import load_dotenv

class ChatDevRunner:
    def __init__(self):
        # 设置根目录并将其添加到系统路径中
        self.root = os.path.dirname(__file__)
        sys.path.append(self.root)
        # 检查 OpenAI API 版本
        self.openai_new_api = self.check_openai_api()

    def check_openai_api(self):
        try:
            # 尝试导入新的 OpenAI API 模块
            from openai.types.chat.chat_completion_message_tool_call import ChatCompletionMessageToolCall
            from openai.types.chat.chat_completion_message import FunctionCall
            return True
        except ImportError:
            # 如果导入失败，提示用户更新 OpenAI 版本
            print(
                "警告: 您的 OpenAI 版本已过时。 \n "
                "请按照 requirement.txt 中的说明进行更新。 \n "
                "旧的 API 接口已被弃用，将不再受支持。")
            return False

    def get_config(self, company):
        # 获取配置文件路径
        config_dir = os.path.join(self.root, "CompanyConfig", company)
        default_config_dir = os.path.join(self.root, "CompanyConfig", "Default")

        config_files = [
            "ChatChainConfig.json",
            "PhaseConfig.json",
            "RoleConfig.json"
        ]

        config_paths = []

        for config_file in config_files:
            company_config_path = os.path.join(config_dir, config_file)
            default_config_path = os.path.join(default_config_dir, config_file)

            if os.path.exists(company_config_path):
                config_paths.append(company_config_path)
            else:
                config_paths.append(default_config_path)

        return tuple(config_paths)

    def parse_args(self):
        # 解析命令行参数
        parser = argparse.ArgumentParser(description='argparse')
        parser.add_argument('--config', type=str, default="Default", help="配置名称，用于在CompanyConfig下加载配置/")
        parser.add_argument('--org', type=str, default="个人开发", help="组织名称，您的软件将在WareHouse/name_org_timestamp中生成")
        parser.add_argument('--task', type=str, default="开发一个基本的五子棋游戏。", help="软件的提示")
        parser.add_argument('--name', type=str, default="五子棋", help="软件名称，您的软件将在WareHouse/name_org_timestamp中生成")
        parser.add_argument('--model', type=str, default="deepseek-ai/DeepSeek-V3", help="GPT模型，从{'gpt_3_5_turbo'，'gpt_4'，'gpt_4_turbo'，'gpt_4o'，'gpt_4o_mini'}中选择")
        parser.add_argument('--platform', type=str, default="siliconflow", help="模型平台，可供选择 {'hunyuan','qianfan'}")
        parser.add_argument('--api_type', type=str, default="openai", help="模型平台，可供选择 {'openai','self'}")
        parser.add_argument('--path', type=str, default="", help="您的文件目录，ChatDev将以增量模式构建您的软件")
        return parser.parse_args()

    def init_logging(self, log_filepath):
        # 初始化日志记录
        logging.basicConfig(
            filename=log_filepath, 
            level=logging.INFO,
            format='[%(asctime)s %(levelname)s] %(message)s',
            datefmt='%Y-%d-%m %H:%M:%S', 
            encoding="utf-8"
        )

    def run(self):
        # 运行 ChatDev
        args = self.parse_args()
        # 获取配置文件全路径
        config_path, config_phase_path, config_role_path = self.get_config(args.config)
        # args2type = self.get_model_type_mapping()

        base_url, num_tokens, api_type = get_model_info(args.platform, args.model, args.api_type)
        model_type = ModelTypeNew(args.platform, name=args.model, base_url=base_url, num_tokens=num_tokens, api_type=api_type)
        # 初始化 ChatChain 实例
        chat_chain = ChatChain(
            config_path=config_path,
            config_phase_path=config_phase_path,
            config_role_path=config_role_path,
            task_prompt=args.task,
            project_name=args.name,
            org_name=args.org,
            model_type=model_type,
            code_path=args.path
        )

        # # 初始化日志记录
        self.init_logging(chat_chain.log_filepath)

        # # 执行 ChatChain 的各个阶段
        chat_chain.pre_processing()
        chat_chain.make_recruitment()
        chat_chain.execute_chain()
        chat_chain.post_processing()
      
# 加载环境变量  
load_dotenv()

if __name__ == "__main__":
    # 创建并运行 ChatDevRunner 实例
    # 1. 设置环境变量
    # set OPENAI_API_KEY=xxxxxx
    # echo %OPENAI_API_KEY%
    # 启动命令
    # python run.py --config Default --org DefaultOrganization --task "开发一个基本的五子棋游戏。" --name "五子棋" --model gpt-3.5-turbo --platform hunyuan --api_type openai --path ""
    # python run_new.py --config "Human" --task "贪吃蛇游戏" --name "贪吃蛇" --model "deepseek-ai/DeepSeek-V3" --platform "siliconflow"
    # python run_new.py --config "Human" --task "贪吃蛇游戏" --name "贪吃蛇" --model "deepseek-chat" --platform "deepseek"
    runner = ChatDevRunner()
    runner.run()
