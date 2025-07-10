# Author: zch9241[zch2426936965@gmail.com]
# 

import json
import os
import base64
import io
from PIL import Image
import numpy as np
import torch

import folder_paths
from nodes import LoraLoader

# 获取扩展的基础目录
BASEDIR = os.path.dirname(os.path.abspath(__file__))

def get_config(path, open_mode='r'):
    """从指定路径加载配置文件。
    
    Args:
    path (str): 配置文件的相对路径。
    open_mode (str): 打开文件的模式，默认为 'r'（只读模式）。

    Returns:
    dict: 配置文件的内容，如果加载失败则返回空字典。
    """
    file = os.path.join(BASEDIR, path)
    try:
        with open(file, open_mode, encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"Error loading {file}: {e}")
        return {}

def base64_to_pil(base64_str):
    """将 Base64 编码的字符串转换为 PIL Image 对象。

    Args:
    base64_str (str): Base64 编码的字符串，可以包含前缀 "data:image/png;base64,"。
    """
    if "base64," in base64_str:
        base64_str = base64_str.split("base64,")[1]
    image_data = base64.b64decode(base64_str)
    return Image.open(io.BytesIO(image_data))

def pil_to_tensor(image: Image.Image) -> torch.Tensor:
    """将 PIL Image 转换为 ComfyUI 需要的 Tensor 格式"""
    # (H, W, C) -> (1, H, W, C) with float32 values in [0, 1]
    image_np = np.array(image).astype(np.float32) / 255.0
    return torch.from_numpy(image_np).unsqueeze(0)