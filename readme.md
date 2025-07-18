# WAI NSFW illustrious character select for ComfyUI

这是一个为 **ComfyUI** 设计的自定义节点扩展包。它移植并扩展了 **Stable Diffusion WebUI** 扩展 [WAI-NSFW-illustrious-character-select](https://github.com/lanner0403/WAI-NSFW-illustrious-character-select) ，以 ComfyUI 原生的、基于节点的方式实现。

通过本扩展，你可以轻松地从预设的列表中选择角色和动作，自动应用风格化的增强提示词和 LoRA，并通过模块化的节点自由组合，构建出强大而灵活的生成工作流。

~~项目开发不易，请各位动动发财的小手点一个免费的star吧？~~

## 特色

1. 对所有角色和动作提供了完整的简体中文支持（个人渣翻

2. 对扩展中所有出现的LoRA都进行了整理，包括原作者未提及的。

3. 动态加载动作提示词中的LoRA，自动识别 `<lora:name:weight>` 格式并尝试加载。

4. 实时的节点内角色图像展示（除random和skip选项外均可实时展示），通过 javascript 实现。

5. 灵活而友好，可与上游的conditioning进行连接从而细化生成条件，同时仅需两个节点即可实现完整功能（详见示例工作流）。

## 安装方式

通过 `绘世启动器` 或 `ComfyUI Manager` 安装即可。

相关VAE和LoRA依赖位于[Lora Requirements.md](/Lora%20Requirements.md)中

## 节️点详解

在 ComfyUI 的节点菜单中，你可以在 `WAI Character Selector` 分类下找到以下节点：

### 1. (WAI)角色提示词生成器 (PromptAndLoraLoader)

这是本扩展的核心节点，它将 LoRA 加载、提示词构建和文本编码集成到了一个单元中。

**功能**: 提供角色和动作的选择下拉菜单，并自动构建正面和负面 conditioning。它还包含多个开关，用于动态加载可调节权重的增强型 LoRA。

**输入**:

*   `model`: 要应用 LoRA 的模型。
*   `clip`: 用于文本编码的 CLIP 模型。
*   `seed`: 用于随机选择角色和动作的种子（仅在`character`或`action`设置为`random`时有效）
*   `character`: 用于选择角色的下拉菜单。
*   `action`: 用于选择动作的下拉菜单。
*   `workflow_control`: 用于控制是否继续执行工作流（使用random角色/动作选项时，可以先预览一下随机结果，若满意则可在下次运行）
*   `add_nsfw` (布尔值): 切换是否添加 NSFW 提示词。
*   `add_details` (布尔值) & `add_details_lora_weight` (浮点数): 加载 `add-detail-xl.safetensors` LoRA。
*   `enhance_body` (布尔值) & `enhance_body_lora_weight` (浮点数): 加载 `ChihunHentai_20230709225610-000004.safetensors` LoRA。
*   `enhance_quality` (布尔值) & `enhance_quality_lora_weight` (浮点数): 加载 `spo_sdxl_10ep_4k-data_lora_webui.safetensors` LoRA。
*   `enhance_character` (布尔值) & `enhance_character_lora_weight` (浮点数): 加载 `ponyv4_noob1_2_adamW-000017.safetensors` LoRA。
*   `positive_conditioning_in` (可选): 用于连接上游节点的 conditioning。
*   `negative_conditioning_in` (可选): 用于连接上游节点的 conditioning。

**输出**:

*   `model`: 加载了所选 LoRA 的模型。
*   `clip`: 加载了所选 LoRA 的 CLIP 模型。
*   `positive_cond`: 最终的正面 conditioning，可直接连接到 KSampler。
*   `negative_cond`: 最终的负面 conditioning，可直接连接到 KSampler。

### 2. (WAI)工作流控制门 (ConditionalGate)

控制是否继续执行工作流的节点（主要搭配random选项）

若上游选择停止工作流，此节点会抛出异常以终止工作流（并非扩展出现错误）

### 3. 文本连接器 (TextConcatenate)

一个用于拼接两个字符串的简单实用节点。

**输入**:

*   `text_a` (字符串): 第一个文本输入。
*   `text_b` (字符串): 第二个文本输入。
*   `separator` (字符串, 可选): 用于分隔两个文本的字符串。默认为 ", "。

**输出**:

*   `STRING`: 最终合并的字符串。

## 注意事项

*   本扩展已经将角色名转成简体中文了，若需要原来的语言，请按如下方式修改：

```python
# custom_nodes/WAI_NSFW_illustrious_character_select_for_ComfyUI/__init__.py

# 加载配置文件
try:
    settings = utils.get_config('settings.json')
    actions = utils.get_config('action_zh_CN.json')    # 动作名-提示词   <==将action_zh_CN.json改成action.json即可
    characters = utils.get_config('zh_CN.json')   # 角色名-提示词   <==将zh_CN.json改成zh_TW.json即可
```

*   本扩展已经预设了 `WAI-NSFW-illustrious-SDXL v14.0` 模型作者推荐的默认正向和反向提示词，无需手动添加
*   本扩展暂时没有且暂时不计划实现原扩展中的 AI 补充提示词的功能。
*   **警告** :原作者及提示词中声明的部分 lora 与当前的 WAI 模型版本并不适配，若强行加载会在控制台输出错误信息，但并不影响工作流执行

## 推荐工作流

推荐工作流详见项目根目录下的 `examples` 文件夹。

## 致谢

本项目中的部分配置文件（角色、动作和提示词预设）来自 [@lanner0403](https://github.com/lanner0403/) 的项目 [WAI-NSFW-illustrious-character-select](https://github.com/lanner0403/WAI-NSFW-illustrious-character-select)。没有他（们）的工作，这个节点项目就不可能实现。
