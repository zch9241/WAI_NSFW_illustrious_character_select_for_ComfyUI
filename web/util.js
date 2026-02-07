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
					draw: function (ctx, node, width, y) {
						if (!this.image || !this.image.complete) return;
						const x = (node.size[0] - this.image.naturalWidth) / 2;
						ctx.drawImage(this.image, x, y, this.image.naturalWidth, this.image.naturalHeight);
					},
					computeSize: function (width) {
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

				// -----------------------------------------------------------
				// Helper: Create and setup slider
				// -----------------------------------------------------------
				const createSlider = (name, label, dropdownWidget, items) => {
					// Add slider widget
					// NOTE: We use addWidget which appends to end, then we move it.
					const slider = this.addWidget("slider", name, 0, function (value, canvas, node, pos, event) {
						const index = Math.round(value);
						if (index >= 0 && index < items.length) {
							const itemName = items[index];
							if (dropdownWidget.value !== itemName) {
								dropdownWidget.value = itemName;
								if (dropdownWidget.callback) {
									dropdownWidget.callback(itemName, canvas, node, pos, event);
								}
							}
						}
					}, {
						min: 0,
						max: items.length - 1,
						step: 1,
						precision: 0
					});
					return slider;
				};

				// -----------------------------------------------------------
				// 1. Character Slider
				// -----------------------------------------------------------
				const characterNames = Object.keys(extension.characterData);

				if (characterNames.length > 0) {
					// Check if slider already exists (to avoid duplicate on reload if any?) 
					// Actually onNodeCreated runs once per node instance.
					const charSlider = createSlider("character_index", "Character Index", characterWidget, characterNames);

					// Update existing mainCallback to also sync the slider when dropdown changes
					const prevCharCallback = characterWidget.callback;
					characterWidget.callback = async function (value, canvas, node, pos, event) {
						if (prevCharCallback) await prevCharCallback(value, canvas, node, pos, event);
						const index = characterNames.indexOf(value);
						if (index !== -1 && charSlider) {
							charSlider.value = index;
						}
					};

					// Position after 'character' widget
					const charIdx = this.widgets.findIndex(w => w.name === "character");
					if (charIdx !== -1 && charSlider) {
						const sliderIdx = this.widgets.indexOf(charSlider);
						this.widgets.splice(sliderIdx, 1);
						this.widgets.splice(charIdx + 1, 0, charSlider);
					}
				}

				// -----------------------------------------------------------
				// 2. Action Slider
				// -----------------------------------------------------------
				if (actionWidget && actionWidget.options && actionWidget.options.values) {
					const actionNames = actionWidget.options.values;
					const actSlider = createSlider("action_index", "Action Index", actionWidget, actionNames);

					// Sync Slider when Dropdown changes
					const prevActCallback = actionWidget.callback;
					actionWidget.callback = function (value, canvas, node, pos, event) {
						if (prevActCallback) prevActCallback(value, canvas, node, pos, event);
						const index = actionNames.indexOf(value);
						if (index !== -1 && actSlider) {
							actSlider.value = index;
						}
					};

					// Position after 'action' widget
					// NOTE: We must find indices again because splicing changed them
					const actIdx = this.widgets.findIndex(w => w.name === "action");
					if (actIdx !== -1 && actSlider) {
						const sliderIdx = this.widgets.indexOf(actSlider);
						this.widgets.splice(sliderIdx, 1);
						this.widgets.splice(actIdx + 1, 0, actSlider);
					}
				}

				// -----------------------------------------------------------
				// 3. Serialization Fix (Exclude sliders)
				// -----------------------------------------------------------
				const onSerialize = this.onSerialize;
				this.onSerialize = function (o) {
					if (onSerialize) onSerialize.apply(this, arguments);

					// Helper to remove widget value by name from widgets_values array
					// We must map widget names to their CURRENT index in existing widgets array
					if (o.widgets_values) {
						// Identify indices of our sliders
						const indicesToRemove = [];
						const sliders = ["character_index", "action_index"];

						this.widgets.forEach((w, i) => {
							if (sliders.includes(w.name)) {
								indicesToRemove.push(i);
							}
						});

						// Sort descending to remove from end without affecting earlier indices
						indicesToRemove.sort((a, b) => b - a);

						indicesToRemove.forEach(idx => {
							if (o.widgets_values.length > idx) {
								o.widgets_values.splice(idx, 1);
							}
						});
					}
				};
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