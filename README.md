# 人生游戏 MUD — Python 版

> 提炼自 [LuaMUD](https://gitee.com/wadehan/luamud) 内核，以 Python asyncio 重写；面向《人生游戏沙盒》的 LifeOS 地基。

---

## 目录

1. [快速启动](#快速启动)
2. [项目结构](#项目结构)
3. [核心架构](#核心架构)
4. [地图世界](#地图世界)
5. [配置说明](#配置说明)
6. [玩家操作手册](#玩家操作手册)
7. [扩展开发](#扩展开发)

---

## 快速启动

**环境要求**：Python 3.11+。

### 方式一：使用 uv（推荐）

```bash
git clone https://github.com/vcalibrator/python_mud.git
cd python_mud
uv sync
cp .env.example .env   # 可选：按需修改配置
sh/check-env.sh
sh/start.sh
```

> 当前仓库按“应用项目”使用 uv，不作为可发布 wheel/package 安装；因此 `uv sync` 只同步依赖，不会执行 editable 安装。

### 方式二：使用 pip

```bash
git clone https://github.com/vcalibrator/python_mud.git
cd python_mud
python -m pip install -r requirements.txt
cp .env.example .env   # 可选：按需修改配置
sh/check-env.sh
sh/start.sh
```

启动后输出：

```
[INFO] MUD 服务器已启动，监听 0.0.0.0:7777
```

**连接方式**（任选其一）：

| 客户端 | 命令 / 设置 |
|---|---|
| **Mudlet（推荐）** | 新建 Profile → Host: `localhost`，Port: `7777`，编码设为 UTF-8 |
| Windows Telnet | `telnet localhost 7777` |
| PuTTY | Host: `localhost`，Port: `7777`，Connection: Raw 或 Telnet |
| MUSHclient | 新建连接 → localhost:7777，字符集 UTF-8 |
| Python 测试 | 见 `测试连接` 小节 |

> **编码说明**：服务器默认输出 UTF-8。  
> 如果你需要兼容老旧中文 Telnet/CP936 环境，可在 `.env` 中将 `CLIENT_ENCODING=utf-8` 改为 `gbk`。

---

## 项目结构

```
python_mud/
├── main.py                  # 入口：asyncio.run(main())
├── config.py                # 全局配置（端口、编码、LLM 设置）
├── sh/
│   ├── start.sh             # 启动脚本（优先 uv，回退 python）
│   └── check-env.sh         # 环境/端口/LLM 配置检查
│
├── engine/                  # 引擎层（对应 Lua 版 MudOS/）
│   ├── channel.py           # 频道广播（房间/全局）
│   ├── events.py            # 事件系统（pub/sub，带优先级）
│   ├── timer.py             # 心跳系统（HeartOfWorld，1 秒 tick）
│   ├── telnet.py            # Telnet 协议（IAC 剥离，ECHO/NAWS 协商）
│   ├── network.py           # asyncio TCP 服务器，每连接一个 Task
│   ├── llm.py               # Ollama / OpenAI 兼容异步客户端（urllib + executor）
│   ├── json_utils.py        # LLM JSON 宽松解析（json_repair + fallback）
│   └── llm_cmd.py           # 自然语言 → 结构化 JSON → 游戏指令解析器
│
├── world/                   # 世界层（对应 Lua 版 MudLib/）
│   ├── space.py             # SpaceObject：容器层级基类（put/leave/search）
│   ├── item.py              # Item + Weapon：堆叠、装备槽、克隆
│   ├── char.py              # Charactor：HP、装备、战斗列表、心跳
│   ├── combat.py            # 战斗函数：命中判定、伤害、广播
│   ├── npc.py               # Npc：关键词话题表
│   ├── llm_npc.py           # LlmNpc：Ollama 驱动，按玩家分组对话历史
│   ├── monster.py           # Monster：自动复活
│   ├── room.py              # Room：出口、频道、事件监听、地图加载
│   ├── player.py            # Player：reply()、enter()、save()/load()
│   └── login.py             # 登录状态机 + session_pool
│
├── cmds/                    # 指令层
│   ├── __init__.py          # command_list 注册表 + dispatch()（含 LLM 回退）
│   ├── common.py            # look / go / help / bye / who / inv
│   ├── say.py               # say
│   ├── kill.py              # kill
│   ├── hp.py                # hp / score
│   ├── get.py               # get / drop
│   └── use.py               # use / wear / remove
│
├── maps/                    # 地图定义
│   ├── station.py           # 车站世界（5 个房间 + AI 售票员 + 怪物）
│   └── dream_workshop.py    # 梦境工坊 Yesod（乌拉尼亚 AI Agent）
│
└── data/
    └── players/             # 玩家存档（每人一个 JSON 文件）
```

---

## 核心架构

### 对象层级

```
SpaceObject（容器基类）
├── Room（房间）
├── Charactor（角色基类）
│   ├── Player（玩家）
│   ├── Npc → LlmNpc（AI NPC）
│   └── Monster（怪物，自动复活）
└── Item → Weapon（物品/武器）
```

每个对象都有 `environment`（所在容器）和 `content[]`（内含物），形成树状空间层级。

### 主事件循环

```
asyncio.run(main())
  ├── asyncio.create_task(heart_of_world.run())   # 1秒心跳 tick
  ├── load_all_maps()                              # 导入 maps/*.py
  ├── reload_cmds()                                # 导入 cmds/*.py
  └── asyncio.start_server(handle_client, 7777)
        └── 每个连接 → Task
              ├── TelnetHandler.negotiate()        # Telnet 协商
              ├── 发送问候语
              └── async for line in telnet.lines(reader):
                    ├── LoginHandler.handle()      # 未登录
                    └── dispatch(player, line)     # 已登录
                          ├── dynamic_cmds         # 房间本地指令
                          ├── command_list         # 全局指令
                          └── llm_cmd（兜底）       # 自然语言解析
```

### LLM 集成

```
玩家输入未识别指令
  → llm_cmd.parse_natural_command(player, text)
      → Ollama /api/chat 或 OpenAI 兼容 /v1/chat/completions
      → 返回结构化 JSON（如 {"command":"go east"}）
      → json_repair / fallback 解析后 dispatch 再次执行

玩家 say <内容> 进入有 LlmNpc 的房间
  → LlmNpc.respond_to_say(player, message)
      → 带 system_prompt + 对话历史 → Ollama / OpenAI 兼容接口
      → 广播 NPC 回复到房间频道
```

---

## 地图世界

```
车站入口大厅（StationHall）★ 出生点
  └── east → 候车站台（Platform）
                └── north → 列车第一节车厢（Compartment1）
                              └── north → 列车第二节车厢（Compartment2）
                                            └── north → 列车第三节车厢·终端（Compartment3）
                                                          └── dream → 梦境工坊·Yesod（DreamWorkshop）
```

| 地点 | 特色 | NPC / 怪物 |
|---|---|---|
| 车站大厅 | 出生点，AI 售票员在此 | 售票员（LlmNpc）|
| 候车站台 | 有车票可拾取 | — |
| 第一车厢 | 地面有锈铁刀 | 车厢阴影（Monster）|
| 第二车厢 | 昏黄灯光 | 迷失的旅客（Monster）|
| 第三车厢 | 有 `read_wall` 指令，`dream` 出口 | — |
| **梦境工坊** | Yesod 层，有 `meditate`/`感应` 指令 | **乌拉尼亚**（LlmNpc）|

---

## 配置说明

推荐通过项目根目录的 `.env` 配置运行参数；程序启动时会自动读取该文件。

可先复制模板：

```bash
cp .env.example .env
```

关键配置项：

```env
# 服务监听
MUD_BIND_HOST=0.0.0.0
MUD_BIND_PORT=7777
CLIENT_ENCODING=utf-8

# LLM 开关与模型
LLM_ENABLED=true
LLM_MODEL=qwen2.5:3b
LLM_API_TYPE=ollama
LLM_API_URL=http://127.0.0.1:11434
LLM_API_KEY=
LLM_TIMEOUT=30
LLM_MAX_HISTORY=12
```

说明：
- `LLM_API_TYPE` 支持 `ollama` / `openai`
- `LLM_API_URL` 支持填写 base URL
  - Ollama 例：`http://127.0.0.1:11434`
  - OpenAI 兼容例：`http://127.0.0.1:1234/v1`、`http://your-host:11435/v1`
- OpenAI 兼容接口会自动补全到 `/v1/chat/completions`
- 若不使用 `.env`，也可直接通过系统环境变量覆盖
- 项目依赖 `json-repair` 来宽松解析 LLM 偶发返回的非标准 JSON

### LM Studio 示例

如果你本地开的是 LM Studio 的 OpenAI Compatible Server，可这样配置：

```env
LLM_ENABLED=true
LLM_API_TYPE=openai
LLM_API_URL=http://127.0.0.1:1234/v1
LLM_MODEL=你在 LM Studio 中加载的模型名
LLM_API_KEY=
```

如果你走的是局域网 / Tailscale 上的远端网关，也可以写成：

```env
LLM_ENABLED=true
LLM_API_TYPE=openai
LLM_API_URL=http://your-host:11435/v1
LLM_MODEL=your-remote-model-name
LLM_API_KEY=
```

---

## 玩家操作手册

### 登录 / 注册

连接后看到问候画面，直接按提示操作：

```
请输入用户名：<输入你的名字>
```

- **新用户**：输入名字 → 系统提示设置密码 → 再次确认 → 进入游戏
- **老用户**：输入名字 → 输入密码 → 进入游戏（自动回到上次所在房间，背包装备保留）

---

### 查看与移动

| 指令 | 缩写 | 说明 | 示例 |
|---|---|---|---|
| `look` | `l` | 查看当前房间（描述、出口、在场者）| `look` |
| `look <目标>` | `l <目标>` | 查看房间内的物体或人物 | `look 售票员` |
| `go <方向>` | — | 向指定出口移动 | `go east` |

**方向词**（中英文均可被 LLM 理解）：

| 方向 | 英文 | 可用位置 |
|---|---|---|
| 东 | `east` | 大厅 → 站台 |
| 西 | `west` | 站台 → 大厅 |
| 北 | `north` | 站台 → 车厢（逐节）|
| 南 | `south` | 车厢 → 前一节 |
| 梦境 | `dream` | 第三车厢 → 梦境工坊 |
| 回 | `back` | 梦境工坊 → 第三车厢 |

---

### 与人交流

| 指令 | 缩写 | 说明 |
|---|---|---|
| `say <内容>` | `' <内容>` | 向当前房间所有人/NPC 说话 |
| `who` | — | 查看当前在线的玩家列表 |

**与 AI NPC 对话**：

在有 AI NPC 的房间里使用 `say` 即可触发回复。NPC 会记住本次对话上下文。

```
> say 你好，我想了解这趟车去哪里
售票员 说：每个人上车的理由都不同，但终点只有一个——你自己知道在哪里。
```

```
> say 我不知道自己该往哪里走
乌拉尼亚 说：不知道方向，往往是因为还没问清楚：你想要的，
              是到达某个地方，还是成为某种人？
```

---

### 背包与物品

| 指令 | 缩写 | 说明 |
|---|---|---|
| `inv` | `i` | 查看背包内容 |
| `get <物品>` | `take` | 从房间拾取物品 |
| `drop <物品>` | — | 将物品放回当前房间 |
| `use <物品>` | — | 使用物品（触发物品效果）|
| `wear <装备>` | — | 穿戴装备（自动占用对应槽位）|
| `remove <装备>` | — | 卸下装备（回到背包）|

**拾取示例**：

```
> go north        ← 进入第一车厢
> look            ← 查看房间，看到"锈铁刀"
> get 锈铁刀
你拿起了 锈铁刀。
> wear 锈铁刀
你装备了 锈铁刀。
> hp
HP [██████████] 100/100
装备：right_hand: 锈铁刀
```

---

### 战斗

| 指令 | 缩写 | 说明 |
|---|---|---|
| `kill <目标>` | `k` | 对目标发起攻击 |
| `hp` / `score` | — | 查看当前 HP 和装备 |

**战斗机制**：

- 攻击开始后，**心跳驱动**（每 2 秒一轮），双方自动互打，无需持续输入指令。
- 基础命中率 50%；装备武器可提升伤害（锈铁刀：2~6 点）。
- 击杀怪物后，怪物会在一段时间后**自动复活**回原房间。
- 玩家死亡 → HP 恢复至一半 → 传送回出生点（大厅）。

```
> kill 车厢阴影
你向 车厢阴影 发起了攻击！
你 击中了 车厢阴影，造成 4 点伤害。
车厢阴影 击中了 你，造成 2 点伤害。
你 猛烈地打击 车厢阴影，造成 5 点重创！
车厢阴影 发出最后一声呻吟，缓缓倒下。
```

---

### 梦境工坊专属指令

进入梦境工坊（`go dream`）后可用以下本地指令：

| 指令 | 说明 |
|---|---|
| `meditate` / `冥想` | 触发 AI 引导的内心意象描绘 |
| `感应` | 感应神谕碎片，获得关于当前人生阶段的神谕 |

```
> meditate
你闭上眼睛……
你看见一片辽阔的海，浪并不大，但有一股力量从脚底涌上来，
提醒你：有些东西已经开始移动了，只是你还没有看见。

> 感应
【神谕】你正处于一次蜕变的中间——不是开始，也不是终点，
       而是那个最难熬的"之间"。坚持住，壳正在破开。
```

---

### 自然语言指令（LLM 回退）

当输入的指令不在标准列表内时，服务器会自动尝试用 AI 理解你的意图：

```
> 我想往东走
（正在理解你的意思……）
→ go east
[进入候车站台]

> 帮我看看背包里有什么
（正在理解你的意思……）
→ inv
背包：
  锈铁刀 — 一把锈迹斑斑的小刀

> 向售票员打个招呼
（正在理解你的意思……）
→ say 你好
你说：你好
售票员 说：嗯……你也来了。这里的旅客，都是带着问题上车的。
```

---

### 其他指令

| 指令 | 说明 |
|---|---|
| `help` / `h` | 显示全部指令列表 |
| `bye` / `quit` | 保存数据并退出游戏 |

> 断线时服务器会**自动保存**当前房间位置和背包内容。

---

## 扩展开发

### 添加新房间

在 `maps/` 目录下新建 `.py` 文件，服务器启动时自动加载：

```python
# maps/my_new_place.py
from world.room import Room, register_room

my_room = Room(
    room_id="MyPlace",
    title="我的新地方",
    desc="这是一个新房间。",
    exits={"south": "DreamWorkshop"},   # 连接到已有房间
)
register_room(my_room)
```

同时在被连接的房间出口中添加反向出口（如 `"north": "MyPlace"`）。

---

### 添加 AI NPC

```python
from world.llm_npc import LlmNpc

guide = LlmNpc(
    npc_id="guide",
    name="向导",
    desc="一位眼神深邃的向导。",
    system_prompt="你是一位智慧的向导，用简短的禅语回答旅行者的问题。",
    greeting="你来了。",
)
guide.put(my_room)   # 放入某个房间
```

---

### 添加新指令

在 `cmds/` 目录下新建文件或在已有文件末尾追加：

```python
from cmds import register

async def cmd_meditate(player, args):
    await player.reply("你静下心来……")

register("meditate", cmd_meditate, "进入冥想状态")
```

然后在 `cmds/__init__.py` 的 `reload_cmds()` 列表中加入模块名。

---

### 切换 LLM 模型

修改 `config.py`：

```python
LLM_MODEL = "qwen2.5:7b"   # 更大的模型，回复质量更高
LLM_MODEL = "llama3.1:8b"  # 英文能力更强
LLM_MODEL = "qwen3-coder"  # 适合代码相关场景
```

确保 Ollama 中已拉取对应模型（`ollama pull <model>`）。

---

### LifeOS 扩展路线

当前车站世界可直接映射为生命树结构：

| MUD 房间 | 生命树质点 | LifeOS 含义 |
|---|---|---|
| 梦境工坊 | Yesod（第9）| 潜意识、梦境、愿景 |
| （待建）英雄大厅 | Tiphereth（第6）| 英雄之路、使命 |
| （待建）神谕圣殿 | Kether（第1）| 最高目的、宇宙意志 |
| （待建）现实广场 | Malkuth（第10）| 落地执行、日常任务 |

每个房间配一个 `LlmNpc` Agent，即构成完整的 **AI Agent 社会网络**。
