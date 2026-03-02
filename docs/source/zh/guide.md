# OpenStoryline 使用教程
---
## 0. 环境安装

参见[README](https://github.com/FireRedTeam/FireRed-OpenStoryline/blob/main/README_zh.md)部分

## 1. 基础使用教程

### 1.1. 开始
你可以用两种方式开始创作：

1. 有素材  
    - 点击对话框左侧文件上传按钮，选择你的图片/视频素材
    - 然后在输入框写下剪辑目标，例如：用我的素材剪一条新年全家欢 vlog，节奏轻快

2. 没素材  
    - 直接描述主题/氛围即可
    - 例如：帮我剪一个夏日海滩旅行 vlog，阳光、清爽、欢快

自动素材检索来自 [Pexels](https://www.pexels.com/zh-cn/)，请在网页侧边栏填写 Pexels API Key。  

免责声明：我们只提供工具，所有通过本工具下载和使用的素材（如 Pexels 图像）都由用户自行通过 API 获取，我们不对用户生成的视频内容、素材的合法性或因使用本工具导致的任何版权/肖像权纠纷承担责任。使用时请遵循 Pexels 的许可协议：[https://www.pexels.com/zh-cn/license](https://www.pexels.com/zh-cn/license)  
[https://www.pexels.com/terms-of-service](https://www.pexels.com/terms-of-service)

如果你只是想先了解它，也可以当作普通对话模型使用，例如：

- “介绍一下你自己”  
<img src="https://github.com/user-attachments/assets/a7c102a0-299d-4fcb-a890-0bcb165867d2" alt="demo" width="500">

### 1.2. 编辑

OpenStoryline 支持在任意阶段进行意图干预与局部重做：当某一步骤完成后，你可以直接用一句话提出修改要求，Agent会定位到需要重跑的步骤，而无需从流程起点重新开始。例如
- 帮我去掉那个拍摄天空的片段。
- 换一个欢快一点的背景音乐。
- 字幕换成更符合夕阳主题的颜色  
<img src="https://github.com/user-attachments/assets/18c1ac82-873d-4ced-beb3-443d0fc9192c" alt="demo" width="500">

### 1.3. 仿写
依靠仿写Skill复刻任意文风生成文案。例如：
- 用文言文为我进行古风混剪。
- 模仿鲁迅风格生成文案。
- 模仿我发朋友圈的语气。  
<img src="https://github.com/user-attachments/assets/67edcb95-a71d-447c-ac13-ae28d0bbd698" alt="demo" width="500">

### 1.4. 中断
在 Agent 执行的任意时刻，如果行为不符合预期，你可以随时：

- 点击输入框右侧的中止按钮：停止大模型回复与工具调用
- 或者直接按 Enter 发送新 prompt：系统会自动打断并执行你的新指令

中断不会清空当前进度，已生成的回复与已执行的工具结果都会保留，你可以基于现有结果继续提出指令。  

### 1.5. 切换语言

在网页右上角点击语言按钮可切换中/英文：
- 侧边栏与工具调用卡片的展示语言会同步切换
- 工具内部使用的 prompt 语言也会切换
- 已经发生的历史对话不会自动翻译  

### 1.6. 保存

当你打磨出一条满意的视频后，可以一键让 Agent 总结其中的剪辑逻辑（节奏、色调、转场习惯），并保存为你的专属 "Editing Skill"。  
下次剪辑类似内容时，只需告诉Agent调用这个 Skill，即可实现风格复刻。  
<img src="https://github.com/user-attachments/assets/d99faca2-233c-49d0-829e-336b2b76a46d" alt="demo" width="500">

### 1.7 移动端使用
**注意：下列命令会将你的服务暴露到局域网/公网，请仅在可信网络使用，不要在公用网络执行以下命令！！！**  
如果你的素材在手机上，不方便传输，可以使用下面的步骤，在手机上使用剪辑Agent。  
1. 在 config.toml 中填写LLM/VLM/Pexels/TTS 配置  
2. 将网页启动命令改为：
    ```bash
    # 再次提醒： --host 0.0.0.0 命令会将服务暴露到局域网/公网。请仅在可信网络使用。
    uvicorn agent_fastapi:app --host 0.0.0.0 --port 7860
    ```
3. 查看本机ip地址：
    - Windows: 在命令提示符（cmd）中输入 ipconfig，找到 IPv4 地址
    - Mac: 按住 option，点击 WI-FI 图标
    - Linux: 在终端中输入 ifconfig 命令  

4. 在手机浏览器中输入以下地址即可访问。
    ```
    {本机ip地址}:7860
    ```


## 2. 高级使用教程

受限于版权和分发协议，开源的资源不足以满足广大用户的剪辑需求，因此我们提供私有元素库的添加和构建方法。

### 2.1. 自定义音乐库


将私有音乐文件放到目录：`./resource/bgms`下，然后给音乐打标签写入`./resouce/bgms/meta.json`，重启mcp服务即可。

【标签维度】
- scene（场景）：Vlog, Travel, Relaxing, Emotion, Transition, Outdoor, Cafe, Evening, Scenery, Food, Date, Club
- genre（曲风）：Pop, BGM, Electronic, R&B/Soul, Hip Hop/Rap, Rock, Jazz, Folk, Classical, Chinese Style
- mood（情绪）：Dynamic, Chill, Happy, Sorrow, Romantic, Calm, Excited, Healing, Inspirational
- lang（语言）：bgm, en, zh, ko, ja

【打标方式】
- 手动打标：模仿meta.json中的其他item添加对应标签即可。注意：description字段是必须的；
- 自动打标：使用qwen3-omni-flash进行自动打标，需要依赖qwen大模型的API-KEY
qwen3-omni打标脚本：
```
export QWEN_API_KEY="you_api_key"
python -m scripts.omni_bgm_label
```
自动打标签不一定完全准确，如果需要强推荐的场景，建议人工再check一遍。

### 2.2. 自定义字体库

将私有字体文件放到目录：`./resource/fonts`下，然后给字体打标签写入`./resource/fonts/font_info.json`，重启mcp服务即可。

【标签维度】
- class（分类）：Creative, Handwriting, Calligraphy, Basic
- lang（语言）：zh, en

【打标方式】
目前仅支持手动打标，直接编辑`./resource/fonts/font_info.json`。


### 2.3. 自定义文案模板库

将私有文案模板放到目录：`./resource/script_templates`下，然后给字体打标签写入`./resource/fonts/meta.json`，重启mcp服务即可。
【标签维度】
- tags：Life, Food, Beauty, Entertainment, Travel, Tech, Business, Vehicle, Health, Family, Pets, Knowledge

【打标方式】
- 手动打标：模仿meta.json中的其他item添加对应标签即可。注意：description字段是必须的；
- 自动打标：使用deepseek进行自动打标，需要依赖qwen大模型的API-KEY
deepseek打标脚本：
```
export DEEPSEEK_API_KEY="you_api_key"
python -m scripts.llm_script_template_label
```
自动打标签不一定完全准确，如果需要强推荐的场景，建议人工再check一遍。


### 2.4. 自定义技能库

仓库自带两款Skills，一个用于文风仿写，另一个用于保存剪辑流程。如果用户有更多自定义的skill可以按照以下方法添加：

在`.storyline/skills`下创建一个新的文件夹，文件夹内新建`SKILL.md`文件；
SKILL内必须以：
```markdown
---
name: yous_skill_folder_name
description: your_skill_function_description
---
```
的形式开头，其中name和文件夹名字保持一致。
接着文件内写技能的具体内容，比如它的工作设定，需要调用哪些工具，输出格式等等。
完成后重启mcp服务即可