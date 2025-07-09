from . import utils
from PIL import Image



# 加载配置文件
try:
    settings = utils.get_config('settings.json')
    actions = utils.get_config('action.json')    # 动作名-提示词
    characters = utils.get_config('zh_TW.json')   # 角色名-提示词
    
    # 动作名
    action_names = list(actions.keys())
    
    # 角色预览图像(角色提示词-图片数据)
    character_images = []
    for i in range(11):
        img_data = utils.get_config(f'output_{i + 1}.json')
        if img_data:
            character_images.extend(img_data)
    
    # 角色名
    character_names = list(characters.keys())


except Exception as e:
    print(f"[CharacterSelector] Error loading data: {e}")
    character_names =["Error loading data"]
    action_names = ["Error loading data"]


# 定义节点类
class CharacterPromptBuilder:
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "character": (character_names, ),
                "action": (action_names, ),
                "add_nsfw": ("BOOLEAN", {"default": True}),
                "add_details": ("BOOLEAN", {"default": True}),
                "enhance_body": ("BOOLEAN", {"default": True}),
                "enhance_quality": ("BOOLEAN", {"default": True}),
                "enhance_character": ("BOOLEAN", {"default": True}),
            }
        }

    RETURN_TYPES = ("STRING", "STRING", "STRING")
    RETURN_NAMES = ("positive_prompt", "negative_prompt", "character_name")
    FUNCTION = "build_prompt"
    CATEGORY = "Character Selector"
    
    def build_prompt(self, character, action, add_nsfw, add_details, enhance_body, enhance_quality, enhance_character):
        """根据选择的角色和动作构建正向和负向提示词。"""
        
        prompt_parts = []
        
        prompt_parts.append(settings["pos_prompt"])  # 添加默认的正向提示词

        # 添加角色和动作提示词
        if character in character_names:
            prompt_parts.append(characters[character])
        
        if action in action_names:
            prompt_parts.append(actions[action])
            
        # 根据复选框添加增强提示词
        if add_nsfw:
            prompt_parts.append(settings["nsfw"])
        if add_details:
            prompt_parts.append(settings["more_detail"])
        if enhance_body:
            prompt_parts.append(settings["chihunhentai"])
        if enhance_quality:
            prompt_parts.append(settings["quality"])
        if enhance_character:
            prompt_parts.append(settings["character_enhance"])

        # 使用 .strip(',') 清理可能多余的逗号
        final_pos_prompt = ", ".join(p.strip().strip(',') for p in prompt_parts if p)

        neg_prompt = settings["neg_prompt"]

        return (final_pos_prompt, neg_prompt, character)


class CharacterImagePreviewer:
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "character": ("STRING",)
            }
        }
    RETURN_TYPES = ("IMAGE",)
    RETURN_NAMES = ("character_image",)
    FUNCTION = "get_character_image"
    CATEGORY = "Character Selector"
    
    def get_character_image(self, character):
        """根据角色名称获取对应的预览图像。"""
        if character in character_names:
            character_prompt = characters[character]
            for character_image in character_images:
                if list(character_image.keys()) == [character_prompt]:
                    character_image_data = character_image[character_prompt]
                    break
            pil_image = utils.base64_to_pil(character_image_data)
            tensor_image = utils.pil_to_tensor(pil_image)
            return (tensor_image, )
        else:
            # 如果找不到图像，返回一个黑色的空图像，避免工作流中断
            print(f"[CharacterImagePreviewer] No image found for character: {character}. Returning a black image.")
            black_image = Image.new('RGB', (64, 64), 'black')
            return (utils.pil_to_tensor(black_image),)


class TextConcatenate:
    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                "text_a": ("STRING", {"multiline": True, "default": ""}),
                "text_b": ("STRING", {"multiline": True, "default": ""}),
            },
            "optional": {
                # 增加一个分隔符选项，更灵活
                "separator": ("STRING", {"default": ", "})
            }
        }

    RETURN_TYPES = ("STRING",)
    FUNCTION = "concatenate"
    CATEGORY = "Character Selector"

    def concatenate(self, text_a, text_b, separator=", "):
        # 过滤掉空的输入，避免产生多余的分隔符
        parts = [text for text in [text_a, text_b] if text and text.strip()]
        result = separator.join(parts)
        return (result,)


class EncodeAndCombineConditioning:
    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                "clip": ("CLIP", ),
                # 接收来自 CharacterPromptBuilder 或其他文本生成节点的字符串
                "text": ("STRING", {"multiline": True}),
                # 权重滑块，用于控制这个新编码文本的强度
                "weight": ("FLOAT", {"default": 1.0, "min": -10.0, "max": 10.0, "step": 0.01}),
            },
            "optional": {
                # 接收上游的 conditioning
                "conditioning_in": ("CONDITIONING",)
            }
        }

    RETURN_TYPES = ("CONDITIONING",)
    FUNCTION = "encode_and_combine"
    CATEGORY = "Character Selector"

    def encode_and_combine(self, clip, text, weight, conditioning_in=None):
        # 处理输入文本
        # 如果输入的文本是空的，我们不应该生成新的 conditioning
        if not text or not text.strip():
            # 如果有上游 conditioning，直接返回它
            if conditioning_in is not None:
                return (conditioning_in,)
            # 如果没有上游，也没有文本，返回一个空的 conditioning
            else:
                # 这种情况下，我们需要创建一个“空”的 conditioning 以避免工作流中断
                empty_tokens = clip.tokenize("")
                cond, pooled = clip.encode_from_tokens(empty_tokens, return_pooled=True)
                return ([[cond, {"pooled_output": pooled}]], )

        # 使用 CLIP 对文本进行编码，并应用权重
        tokens = clip.tokenize(text)

        # 应用权重
        if weight != 1.0:
            # 遍历 token 结构并乘以权重
            # (token_id, weight) -> (token_id, weight * user_weight)
            for i in range(len(tokens)):
                for j in range(len(tokens[i])):
                    if tokens[i][j][0] != 0: # 避免修改特殊 token
                        tokens[i][j] = (tokens[i][j][0], tokens[i][j][1] * weight)

        cond, pooled = clip.encode_from_tokens(tokens, return_pooled=True)
        new_conditioning = [[cond, {"pooled_output": pooled}]]

        # 合并 Conditioning
        if conditioning_in is not None:
            # 将上游的 conditioning 和新创建的 conditioning 合并
            final_conditioning = conditioning_in + new_conditioning
            return (final_conditioning, )
        else:
            # 如果没有上游输入，则直接返回新创建的
            return (new_conditioning, )


# 注册节点
NODE_CLASS_MAPPINGS = {
    "CharacterPromptBuilder": CharacterPromptBuilder,
    "CharacterImagePreviewer": CharacterImagePreviewer,
    "TextConcatenate": TextConcatenate,
    "EncodeAndCombineConditioning": EncodeAndCombineConditioning,
}
NODE_DISPLAY_NAME_MAPPINGS = {
    "CharacterPromptBuilder": "(WAI)角色提示词生成器",
    "CharacterImagePreviewer": "(WAI)角色图片预览",
    "TextConcatenate": "文本连接器",
    "EncodeAndCombineConditioning": "(WAI)编码并合并条件",
}

print("[WAI_NSFW_illustrious_character_select_for_ComfyUI] Node loaded successfully.")