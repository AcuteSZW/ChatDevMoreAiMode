import argparse
import logging
import os
import sys

from camel.typing import ModelType

root = os.path.dirname(__file__)
sys.path.append(root)

from chatdev.chat_chain import ChatChain

try:
    from openai.types.chat.chat_completion_message_tool_call import ChatCompletionMessageToolCall
    from openai.types.chat.chat_completion_message import FunctionCall

    openai_new_api = True  # 新的OpenAI API版本
except ImportError:
    openai_new_api = False  # 旧版 openai api 版本
    print(
        "警告: 您的 OpenAI 版本已过时。 \n "
        "请按照 requirement.txt 中的说明进行更新。 \n "
        "旧的 API 接口已被弃用，将不再受支持。")


def get_config(company):
    """
    返回 ChatChain 的配置 json 文件
    用户可以只自定义部分配置 json 文件，其他文件将使用默认配置
    参数:
        company: CompanyConfig/ 下的自定义配置名称

    返回:
        三个配置 json 的路径: [config_path, config_phase_path, config_role_path]
    """
    config_dir = os.path.join(root, "CompanyConfig", company)
    default_config_dir = os.path.join(root, "CompanyConfig", "Default")

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


parser = argparse.ArgumentParser(description='argparse')
parser.add_argument('--config', type=str, default="Default",
                    help="配置名称，用于在CompanyConfig下加载配置/")
parser.add_argument('--org', type=str, default="DefaultOrganization",
                    help="组织名称，您的软件将在WareHouse/name_org_timestamp中生成")
parser.add_argument('--task', type=str, default="开发一个基本的五子棋游戏。",
                    help="软件的提示")
parser.add_argument('--name', type=str, default="五子棋",
                    help="软件名称，您的软件将在WareHouse/name_org_timestamp中生成")
parser.add_argument('--model', type=str, default="GPT_4O_MINI",
                    help="GPT模型，从{'gpt_3_5_turbo'，'gpt_4'，'gpt_4_turbo'，'gpt_4o'，'gpt_4o_mini'}中选择")
parser.add_argument('--path', type=str, default="",
                    help="您的文件目录，ChatDev将以增量模式构建您的软件")
args = parser.parse_args()

# Start ChatDev

# ----------------------------------------
#          Init ChatChain
# ----------------------------------------
config_path, config_phase_path, config_role_path = get_config(args.config)
args2type = {'GPT_3_5_TURBO_NEW_1':ModelType.GPT_3_5_TURBO_NEW_1,
            'GPT_3_5_TURBO': ModelType.GPT_3_5_TURBO,
             'GPT_4': ModelType.GPT_4,
            #  'GPT_4_32K': ModelType.GPT_4_32k,
             'GPT_4_TURBO': ModelType.GPT_4_TURBO,
            #  'GPT_4_TURBO_V': ModelType.GPT_4_TURBO_V
            'GPT_4O': ModelType.GPT_4O,
            'GPT_4O_MINI': ModelType.GPT_4O_MINI,
             }
if openai_new_api:
    args2type['GPT_3_5_TURBO'] = ModelType.GPT_3_5_TURBO_NEW

print(args.model)
chat_chain = ChatChain(config_path=config_path,
                       config_phase_path=config_phase_path,
                       config_role_path=config_role_path,
                       task_prompt=args.task,
                       project_name=args.name,
                       org_name=args.org,
                       model_type=args2type[args.model],
                       code_path=args.path)

# ----------------------------------------
#          Init Log
# ----------------------------------------
logging.basicConfig(filename=chat_chain.log_filepath, level=logging.INFO,
                    format='[%(asctime)s %(levelname)s] %(message)s',
                    datefmt='%Y-%d-%m %H:%M:%S', encoding="utf-8")

# ----------------------------------------
#          Pre Processing
# ----------------------------------------

chat_chain.pre_processing()

# ----------------------------------------
#          Personnel Recruitment
# ----------------------------------------

chat_chain.make_recruitment()

# ----------------------------------------
#          Chat Chain
# ----------------------------------------

chat_chain.execute_chain()

# ----------------------------------------
#          Post Processing
# ----------------------------------------

chat_chain.post_processing()
