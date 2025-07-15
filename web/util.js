import { app } from "../../../scripts/app.js";

const fetch_data = async (url) => {
	try {
		const response = await fetch(url);
		if (!response.ok) {
			throw new Error(`API call failed: ${response.statusText}`);
		}
		const data = await response.json();
		return data;
	} catch (error) {
		console.error("Failed to load json:", error);
	}
}
app.registerExtension({
	name: "Comfy.WAICharSelect.Util",
	async setup(app) {
		// 加载配置文件
		this.characterImages = await fetch_data(`/wai-char-select/get-char-image`);    // Array
		this.characterData = await fetch_data(`/wai-char-select/get-char-data`);    // Object
	},

	async beforeRegisterNodeDef(nodeType, nodeData, app) {
		const extension = this;
		if (nodeData.name === "PromptAndLoraLoader") {
			const onNodeCreated = nodeType.prototype.onNodeCreated;
			nodeType.prototype.onNodeCreated = function () {
				onNodeCreated?.apply(this, arguments);

				const imageWidget = this.addCustomWidget({
					name: "image_display",
					type: "custom_image",
					y: 0,
					image: null,
					draw: function(ctx, node, width, y) {
						if (!this.image || !this.image.complete) return;
						const x = (node.size[0] - this.image.naturalWidth) / 2;
						ctx.drawImage(this.image, x, y, this.image.naturalWidth, this.image.naturalHeight);
					},
					computeSize: function(width) {
						if (this.image && this.image.naturalHeight > 0) {
							return [width, this.image.naturalHeight + 10];
						}
						return [width, 0];
					}
				})
				this.imageWidget = imageWidget;

				const characterWidget = this.widgets.find(w => w.name === "character");
				const actionWidget = this.widgets.find(w => w.name === "action");

				// 回调函数
				// 如果不是随机模式，把seed相关控件设置为不可见
				const handleModeChange = (value, canvas, node, pos, event) => {
					const seedWidget = this.widgets.find(w => w.name === "seed");
					const controlWidget = this.widgets.find(w => w.name === "control_after_generate");

					if (!seedWidget || !controlWidget) return;
					if (characterWidget.value !== "random" && actionWidget.value !== "random") {
						seedWidget.hidden = true;
						controlWidget.hidden = true;
					} else {
						seedWidget.hidden = false;
						controlWidget.hidden = false;
					}

					canvas?.draw(true, true);
				}
				const handleCharacterChange = async (value, canvas, node, pos, event) => {
					const imageWidget = this.imageWidget;

					// 如果选择 skip 或 random，则清除图像并恢复节点尺寸
					if (value === "skip" || value === "random") {
						if (imageWidget.image) {
							imageWidget.image = null;
							this.setDirtyCanvas(true, true);
						}
						return;
					}
					// 正常选人的情况（非random或skip）
					const characterEng = extension.characterData[value];
					if (!characterEng) {
						console.log(`No data found for character: ${value}. Skipping.`);
						return;
					}

					const characterImageObj = extension.characterImages.find(imgObj => imgObj.hasOwnProperty(characterEng));
					if (!characterImageObj) {
						console.log(`No image found for character: ${value} (${characterEng}). Skipping.`);
						return;
					}
					const base64Data = characterImageObj[characterEng];

					const img = new Image();
					
					img.onload = () => {
						imageWidget.image = img;
						node.setDirtyCanvas(true, true);
					};
					img.src = base64Data;
				}

				const mainCallback = async (value, canvas, node, pos, event) => {
					handleModeChange(value, canvas, node, pos, event);
					await handleCharacterChange(value, canvas, node, pos, event);
				}

				characterWidget.callback = mainCallback;
				actionWidget.callback = handleModeChange;

				extension.mainCallback = mainCallback;

				// 初始化
				handleModeChange("random", app.canvas, this);
			}

			const onExecuted = nodeType.prototype.onExecuted;
			nodeType.prototype.onExecuted = function (message) {
				onExecuted?.apply(this, arguments);

				// 记忆存在random选项时的cha/act数据，修改相应控件，以便重新运行工作流时使用
				if (message.selected_character && message.selected_action) {
					const characterWidget = this.widgets.find(w => w.name === "character");
					const actionWidget = this.widgets.find(w => w.name === "action");

					if (characterWidget && characterWidget.value === "random") {
						characterWidget.value = message.selected_character[0];
						extension.mainCallback(characterWidget.value, app.canvas, this);
					}
					if (actionWidget && actionWidget.value === "random") {
						actionWidget.value = message.selected_action[0];
					}
				}
			}
		}
	},
});