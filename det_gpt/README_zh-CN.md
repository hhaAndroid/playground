# Det GPT

Det GPT: DetGPT: Detect What You Need via Reasoning
官方地址： https://detgpt.github.io/

**注意: 这不是一个官方的 Det GPT 也不是一个官方 Det GPT 复现，而是一个无需训练的仿真版本！** 

## 项目说明

<div align=center>
<img src="https://github.com/hhaAndroid/awesome-mm-chat/assets/17425982/928feaf4-d47c-4d81-89c3-257253347adc"/>
</div>

DetGPT 是通过输入文本来推理进行特定物体检测，而无需用户直接告诉模型我想要什么东西。

- 常规的目标检测是在特定类别上训练，然后给定图片将对应类别的所有物体都检测出来
- 开发词汇目标检测是给定特定类别的词汇表和一张图片，检测出包括特定类别词汇的所有物体
- Grounding 目标检测是给定特定类别词汇或者一句话，检测出包括特定类别词汇或者输入句子中蕴含的所有物体

而 DetGPT 做的是首先使用 LLM 生成句子中包括的物体，然后将类别词和图片输入到 Grounding 目标检测中。可以发现 DetGPT 做的主要是事情就是通过 LLM 生成符合用户要求的类别词。

以上图为例，用户输入： 我想喝冷饮，LLM 会自动进行推理解析输出 冰箱 这个单词，从而可以通过 Grounding 目标检测算法把冰箱检测出来。

一旦 DetGPT 的过程做的很鲁棒，将其嵌入到机器人中，机器人就能够直接理解用户质量，并且执行用户的命令例如前面说的他自己给你打开冰箱拿冷饮了。这样的机器人将会非常有趣。

<div align=center>
<img src="https://github.com/hhaAndroid/awesome-mm-chat/assets/17425982/12f22c88-75e7-4da8-b28d-3673bc078cb5"/>
</div>

以上是整体结构图，可以发现和 minigpt-4 类似，也是仅仅训练一个线性连接层，连接视觉特征和文本特征，其余模型参数全部估固定。

整个过程可以说是一个 PEFT 过程，核心在于跨模态文本-图片对的构建，然后基于这个数据集进行微调即可。

根据官方描述为：针对文本推理检测任务，模型要能够实现特定格式（task-specific）的输出，而尽可能不损害模型原本的能力。为指导语言模型遵循特定的模式，在理解图像和用户指令的前提下进行推理和生成符合目标检测格式的输出，作者利用 ChatGPT 生成跨模态 instruction data 来微调模型。具体而言，基于 5000 个 coco 图片，他们利用 ChatGPT 创建了 3w 个跨模态图像 - 文本微调数据集。为了提高训练的效率，他们固定住其他模型参数，只学习跨模态线性映射。

实验效果证明，即使只有线性层被微调，语言模型也能够理解细粒度的图像特征，并遵循特定的模式来执行基于推理的图像检测任务、表现出优异的性能。

作者在微调和推理时候会采用统一的 prompt，如下所示：

```text
system_message = "You must strictly answer the question step by step:\n" \
                 "Step-1. describe the given image in detail.\n" \
                 "Step-2. find all the objects related to user input, and concisely explain why these objects meet the requirement.\n" \
                 "Step-3. list out all related objects existing in the image strictly as follows: <Therefore the answer is: [object_names]>.\n" \
                 "If you did not complete all 3 steps as detailed as possible, you will be killed.\n" \
                 "You must finish the answer with complete sentences."
```

作者是通过微调的方式来促使模型能够输出符合特定格式的输出。那如果不微调呢？或者说如果不微调直接使用 MiniGPT-4 来实现这个功能效果如何？ 又或者将 LLM 模型换成 ChatGPT 呢？ 本项目就是做了这个比较简单的探索。

## MiniGPT-4 简单探索

在本地部署好 MiniGPT-4 13b 模型后就可以直接验证了。安装过程可以参考 [这里](https://github.com/hhaAndroid/awesome-mm-chat/blob/main/minigpt4.md)。 下面是两个简单例子

输入图片如下：

<div align=center>
<img src="https://github.com/OptimalScale/DetGPT/assets/17425982/27cc403b-5135-4474-9c55-1cae9186df16"/>
</div>

输入的中文 prompt:

```text
你必须严格按步骤回答问题：

第1步详细描述给定的图像。
第2步，在给定的图像中找到所有与用户输入有关的物体，并简明地解释为什么这些物体符合要求。
第3步，严格按照以下步骤列出图像中存在的所有相关物体并用中文回复： <因此，答案是：[object_names]>。

如果你没有尽可能详细地完成所有3个步骤，你将被杀死。你必须用完整的句子完成答案。

现在用户输入是： 找到高蛋白的食物
```

<div align=center>
<img src="https://github.com/OptimalScale/DetGPT/assets/17425982/b2d9de5f-9d4b-4bcb-b5d8-4e0bbef03817"/>
</div>

输入英文 prompt：

```text
You must strictly answer the question step by step:

Step-1. describe the given image in detail.
Step-2. find all the objects in given image related to user input, and concisely explain why these objects meet the requirement.
Step-3. list out all related objects existing in the image strictly as follows: <Therefore the answer is: [object_names]>.

If you did not complete all 3 steps as detailed as possible, you will be killed. You must finish the answer with complete sentences.

user input: find the foods high in protein
```

<div align=center>
<img src="https://github.com/hhaAndroid/awesome-mm-chat/assets/17425982/05410f26-94b7-46e4-bdbf-b1b0bb578a1b"/>
</div>

显示格式有点小问题。可以看到 MiniGPT-4 其实已经有很强的指令跟随功能了，每次都能正确的按照我要求的格式输出，但是效果好像是差一点。DetGPT 设置的 beam search 参数是 5，而由于机器显存有限，MiniGPT-4 中我只能设置为 1，否则会 OOM,因此这个参数也有点影响。

总的来说通过特定的数据集微调效果确实还是比 MiniGPT-4 好一些，但是 MiniGPT-4 也还行，如果能构建更好的 prompt 估计会更好。下面探索采用强大的 ChatGPT3 效果如何。

## 环境安装

注意： 目前你需要有 OpenAI Key 否则你跑不起来。但是如果你想换成其他模型例如 MiniGPT-4 则可以实现本地部署而无需  OpenAI Key。 

OpenAI Key 是通过环境变量方式导入的，因此再运行前你需要设置环境变量

```shell
export OPENAI_API_KEY=YOUR_API_KEY
```

(1) 安装基础环境

```shell
conda create -n mmdet-sam python=3.8 -y
conda activate mmdet-sam
pip install torch==1.9.1+cu111 torchvision==0.10.1+cu111 -f https://download.pytorch.org/whl/torch_stable.html
pip install mmengine

git clone https://github.com/open-mmlab/playground.git
cd playground
```

(2) 安装其他依赖

```shell
pip install openai transformers
```

(3) 安装 GroundingDINO

```shell
cd playground
pip install git+https://github.com/IDEA-Research/GroundingDINO.git # 需要编译 CUDA OP，请确保你的 PyTorch 版本、GCC 版本和 NVCC 编译版本兼容
```

(4) 安装 GLIP [可选]

如果你想使用 GLIP 而不是 GroundingDINO 来作为 grounding 目标检测器，那么可以安装 GLIP

```shell
cd playground

pip install git+https://github.com/facebookresearch/segment-anything.git
pip install einops shapely timm yacs tensorboardX ftfy prettytable pymongo transformers nltk inflect scipy pycocotools opencv-python matplotlib

git clone https://github.com/microsoft/GLIP.git
cd GLIP; python setup.py build develop --user  # 需要编译 CUDA OP，请确保你的 PyTorch 版本、GCC 版本和 NVCC 编译版本兼容，暂时不支持 PyTorch 1.11+ 版本
```

## 功能演示

(1) 使用 GroundingDINO

```shell
cd det_gpt
python simulate_det_gpt.py ../images/big_kitchen.jpg \
        configs/GroundingDINO_SwinT_OGC.py \
        ../models/groundingdino_swint_ogc.pth \
        'I want to have a cold beverage' # 我想要个冷饮
```

<div align=center>
<img src="https://github.com/hhaAndroid/awesome-mm-chat/assets/17425982/b64f0fdf-8e6c-4386-8a6a-980d63b20413" width="50%" />
</div>

如果你想看到完整运行过程，可以启动训练时候传入 `--verbose` 参数

```shell
python simulate_det_gpt.py ../images/cat_remote.jpg \
        configs/GroundingDINO_SwinT_OGC.py \
        ../models/groundingdino_swint_ogc.pth \
        'I want to watch TV' # 我想看电视
```

<div align=center>
<img src="https://github.com/hhaAndroid/awesome-mm-chat/assets/17425982/43e583e4-aafc-4403-be62-e4593495bc82"/>
</div>

```shell
python simulate_det_gpt.py ../images/000000101762.jpg \
        configs/GroundingDINO_SwinT_OGC.py \
        ../models/groundingdino_swint_ogc.pth \
        'I want to take my favorite animal on a trip to a very faraway place' # 我想带上我最喜欢的动物去很远的地方旅行
```

<div align=center>
<img src="https://github.com/hhaAndroid/awesome-mm-chat/assets/17425982/bf6afe11-f294-412c-9dad-6ea59877423b"/>
</div>

(2) GLIP

```shell
python simulate_det_gpt.py ../images/big_kitchen.jpg \
        configs/glip_A_Swin_T_O365.yaml \
        ../models/glip_a_tiny_o365.pth \
        'I want to have a cold beverage' # 我想要一个冷饮
```

效果和上述类似，故不在此展示。 