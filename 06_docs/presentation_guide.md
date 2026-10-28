# 灵巧手行走 · 汇报完全手册（中英对照）

## Dexterous Hand Locomotion — Complete Speaker's Guide (Bilingual)

> 这份文档是四页 PPT 的**全部讲解逻辑、逐字稿、公式、追问应答**。
> This document holds the **whole narrative logic, verbatim scripts, formulas and Q&A answers** for the four slides.
>
> 配套 deck / Companion deck: `06_docs/slide_deck.html`
> 讲稿结构 / Structure: `06_docs/slide_deck.md`

---

## 0. 怎么用这份文档 / How to Use This Document

| 你有多少时间 | 看哪几节 |
|---|---|
| **How much time you have** | **Which sections** |
| 上台前 3 分钟 / 3 min before speaking | §8 时间分配 + §13 数字速查 |
| 上台前 20 分钟 / 20 min before | §1 主线 + §3–6 逐字稿 |
| 想彻底搞懂 / Want full understanding | 全读，尤其 §10 与 §11 |
| 只有 3 分钟讲完 / Only 3 min total | §9 极简版 |

---

## 1. 一条主线 / The Throughline

### 中文

> **四页不是四个话题，是四个问题的连续回答。每一页收尾时，都故意留下一个“那怎么办”，下一页接住。**

```
S1  它难在哪？                  →  难到你不能当四足做
S2  那它凭什么能动？            →  因为脚不滑，关节一转就把身体反推出去
S3  原理都懂了，为什么做不出来？ →  物理余量把可行解压死，不是算法不聪明
S4  现在到哪一步？              →  走成了，但天花板在哪，下一步怎么接
```

一句话串起来：
**「这不是一只小四足，是一只侧向余量只有 5.3 厘米的手。它只能靠接触锚定推进，所以纯学习、纯开环都撞墙，最后靠确定性步态加两个标量反馈做成。」**

### English

> **These are not four topics. They are four questions answered in sequence. Every slide ends by deliberately leaving a "so what?" that the next slide picks up.**

```
S1  Why is it hard?               →  So hard you cannot treat it as a quadruped
S2  Then why can it move at all?  →  Because the feet do not slip, so joint motion pushes the body
S3  The principle is clear —     →  Physical margin kills the feasible set;
    why did it take so long?         it was never a matter of a smarter algorithm
S4  Where did we get to?          →  It walks, but where is the ceiling, and what comes next
```

In one sentence:
**"This is not a small quadruped. It is a hand with 5.3 cm of lateral margin. It can only propel itself by contact anchoring, which is why pure learning and pure open loop both hit a wall — and why a deterministic gait plus two scalar feedback terms is what finally worked."**

### 时间预算的不对称 / The timing is deliberately uneven

**S1 要慢**（立问题）、**S2 要快**（一条公式）、**S3 要重**（加分项）、**S4 要稳**（收尾）。
推荐 / Recommended: **3 : 2 : 2.5 : 2.5**

---

## 2. 四页问答链 / The Question–Answer Chain

| 页 Slide | 开场抛出的问题 / Question posed | 核心证据 / Core evidence | 收尾留下的钩子 / Hook left behind |
|---|---|---|---|
| **S1** | 一只 16 自由度的手，能靠指尖走路吗？<br>A 16-DoF hand — can it walk on its fingertips? | 5.29 cm 余量 / 25.3° 翻倒角<br>5.29 cm margin / 25.3° tipping angle | 那一碰就倒，它凭什么还能前进？<br>If it tips so easily, how does it move at all? |
| **S2** | 凭什么能前进？<br>Why can it move at all? | $J_c\dot q=0 \Rightarrow v_b=-J_b^{-1}J_j\dot q_j$ | 原理这么清楚，为什么一开始做不出来？<br>The principle is clear — why did it fail? |
| **S3** | 为什么做不出来？<br>Why did it fail? | RL 0.52 s 侧翻 / 四层根因<br>RL falls in 0.52 s / four root causes | 那最后到底走成什么样？<br>So what did we actually achieve? |
| **S4** | 走到哪一步？<br>Where did we get to? | 40 s / 1.10 m / 0 摔<br>40 s / 1.10 m / zero falls | 天花板在哪，下一步接什么？<br>Where is the ceiling, what next? |

---

# 3. Slide 1 — 平台与问题定义 / Platform & Problem Definition

## 3.1 这页真正的任务 / What this slide must achieve

**中文**：这页不是“展示我搭了环境”，而是**把“难”立住**。
如果讲完这页听众脑子里没有 **5.29 cm** 和 **25.3°**，后面三页都会显得小题大做。

**English**: This slide is not "look at the environment I built". Its job is to **establish that the problem is genuinely hard**.
If the audience does not walk away holding **5.29 cm** and **25.3°**, the next three slides will look like over-engineering.

---

## 3.2 五步展开 / Five moves

### 第 1 步 · 先抛矛盾，不要先讲工具（20 秒）
### Move 1 · Lead with the contradiction, never with the toolchain (20 s)

❌ 别这么开场 / Do NOT open like this:
> “我们基于 MuJoCo 搭建了仿真环境，导入了 URDF……”
> "We built a MuJoCo simulation and imported the URDF..."

✅ 这么开场 / Open like this:
> **中文**：
> “这只手有 16 个电机，看起来像个小四足。但它的侧向稳定余量只有 **5.3 厘米**。也就是说——**它往旁边漂 5 厘米就会倒。** 我今天讲的就是怎么让它走起来。”
>
> **English**:
> "This hand has 16 motors. It looks like a small quadruped. But its lateral stability margin is **5.3 centimetres** — which means **it falls over after drifting 5 centimetres sideways**. What I'm going to talk about is how we made it walk anyway."

一句话把“这是个有趣的难题”钉在听众脑子里，后面都会带着这个数字听。

One sentence that plants a number in their head, and they will carry that number through the entire talk.

### 第 2 步 · 它是什么（40 秒）
### Move 2 · What it is (40 s)

- 4 指 × 4 关节 = **16 驱动自由度**，装在 **6 自由度浮动基座**上
  *4 fingers × 4 joints = **16 actuated DoF**, carried on a **6-DoF floating base***
- 指尖是**面接触**（5 个球，宽 1.6 cm），不是点接触
  *The fingertips are **surface contacts** (5 spheres, 1.6 cm wide), not point contacts*
- 整机质量 **1.139 kg**（掌+指 0.635 kg）
  *Total mass **1.139 kg** (palm + fingers 0.635 kg)*

**不要说** URDF、碰撞网格、四元数这些实现细节。
**Do NOT mention** URDF, collision meshes or quaternions here.

> 这里有个取舍：16 个电机对 3 维指尖位置是冗余的（多出来的是 DIP）。
> **这页只讲“多”，不讲“为什么多”**——为什么多是 S2 的事。
>
> *A trade-off to note: 16 motors over-determine a 3-D position (the extra DoF is the DIP).*
> ***This slide only says "many"; it does not explain "why many"** — that is S2's job.*

### 第 3 步 · 它怎么站（30 秒）
### Move 3 · How it stands (30 s)

- 四指朝下，四个指尖着地
  *Four fingers point down, four fingertips on the floor*
- 支撑域 **13.64 × 15.59 cm**
  *Support polygon **13.64 × 15.59 cm***
- 用 `figs/fig1_layout.png` **只建立一个直觉**：四个小垫子撑一个手掌
  *Use `figs/fig1_layout.png` only to build an intuition: four small pads carrying a palm*

### 第 4 步 · ⭐ 转折：为什么不能当四足处理（90 秒，全篇最重要的 90 秒）
### Move 4 · ⭐ The turn: why it cannot be treated as a quadruped (90 s — the most important 90 seconds)

这是整页的脊柱，讲三个数，**一个都不要跳 / This is the spine of the page; three numbers, skip none**:

| 说什么 / Point | 数字 / Value | 为什么非要这个数 / Why this number is essential |
|---|---|---|
| 余量不对称 / Asymmetric margin | 质心偏 0.78 cm，左 8.36 / 右 **5.29**<br>CoM off by 0.78 cm; left 8.36 / right **5.29** | 说明它**天生就往一边歪**<br>*It is born leaning to one side* |
| 余量太小 / Margin too small | **5.29 cm** | 后面所有“为什么救不回来”都靠它<br>*Every later "why it cannot recover" hangs on this* |
| 翻倒角太小 / Tipping angle too small | **25.3°**（前后 34.2°）<br>**25.3°** (fore–aft 34.2°) | 一个很小的扰动就能翻<br>*A tiny disturbance tips it* |
| 自救行程不够 / Stroke too short | **2.77 cm** < 5.29 cm | **杀手锏**：纠偏能力只有余量的 52%<br>***The killer fact**: corrective stroke is only 52 % of the margin* |

配 `figs/fig_p1_why_hard.png`（俯视 + 侧视 + 三数对比）。
*Pair with `figs/fig_p1_why_hard.png` (top view + side view + three-number comparison).*

**讲稿（可以原封不动念）/ Script (read it verbatim)**:

> **中文**：
> “很多人会问：不就是让手走两步吗？我给三个数。
> 它只有 5.3 厘米的侧向余量，质心还往一边偏了 0.8 厘米；
> 静态翻倒角只有 25 度；
> **它能用来救自己的行程总共 2.77 厘米。**
> 也就是说——它往侧面漂 5 厘米就会倒，而它能救自己的空间只有 2.8 厘米。
> 这不是一个算法问题，是一个**物理余量问题**。”
>
> **English**:
> "People ask: isn't this just making a hand take two steps? Let me give you three numbers.
> It has 5.3 cm of lateral margin, and the centre of mass is already 0.8 cm off to one side.
> Its static tipping angle is only 25 degrees.
> **And the total stroke it has available to save itself is 2.77 cm.**
> In other words — it falls after drifting 5 cm sideways, while it can only correct 2.8 cm.
> **This is not an algorithm problem. It is a physical-margin problem.**"

### 第 5 步 · 留钩子（10 秒）
### Move 5 · Leave the hook (10 s)

> “所以问题来了：一个一碰就倒的东西，**凭什么还能往前走？**”
> "So here is the question: something that tips this easily — **how does it move forward at all?**"

---

## 3.3 这页的坑 / Traps on this slide

| 坑 / Trap | 后果 / Consequence | 怎么避 / Fix |
|---|---|---|
| 花时间讲 URDF / MuJoCo / 碰撞球数量<br>*Spending time on URDF, MuJoCo or sphere counts* | 听众以为你要讲工程实现<br>*They think this is an implementation talk* | 全部删掉，或压到一句话<br>*Cut it, or compress to one clause* |
| High/Low 两张图放上去却不说图<br>*Showing the High/Low images without explaining them* | 听众只看红箭头<br>*They only see red dots* | 要么标上支撑域宽度，要么删掉<br>*Annotate the span, or drop them* |
| 说了“13.6 × 15.6”却不说余量<br>*Quoting the 13.6 × 15.6 span without the margin* | 数字听起来还行，难度立不住<br>*It sounds fine, the difficulty collapses* | **必须紧跟“但质心偏了 0.78，右边只剩 5.29”**<br>*Follow immediately with the 0.78 offset and 5.29 margin* |

## 3.4 这页必须说出口的数字 / The numbers you must say out loud

```
16          驱动自由度 / actuated DoF
13.64 × 15.59   支撑域 cm / support polygon
11.20       质心高度 cm / CoM height
-0.78       质心横向偏移 cm / lateral CoM offset
8.36 / 5.29 左右余量 cm / left & right margins
25.3°       侧向翻倒角 / lateral tipping angle
2.77 cm     横向纠偏行程 / lateral stroke
```

---

# 4. Slide 2 — 步态与推导 / Gait & Derivation

## 4.1 这页只讲一件事 / This slide says exactly one thing

**中文**：身体为什么会动。**只推一条公式**，不要推 DH 全表（那是 backup）。
**English**: Why the body moves at all. **Derive exactly one equation**; the full DH table belongs in backup.

---

## 4.2 四步展开 / Four moves

### 第 1 步 · 接住上一页的钩子（15 秒）
### Move 1 · Catch the hook from the previous slide (15 s)

> **中文**：“上一页说了它一碰就倒。但它确实能走。**秘密就一句话：脚不动，身体就被推着走。**”
> **English**: "Last slide I said it tips easily. Yet it does walk. **The secret is one sentence: the feet stay put, and the body gets pushed.**"

### 第 2 步 · 一条公式，推三步（60 秒）
### Move 2 · One equation, three steps (60 s)

$$
J_c(q)\,\dot q = 0 \;\Longrightarrow\; v_{body} = -J_b^{-1}J_j\,\dot q_j
$$

- ① 指尖速度是广义速度的线性函数 / *Fingertip velocity is linear in the generalised velocity*:
  $\dot p_c = J_c(q)\,\dot q$
- ② 脚不滑 ⇒ $\dot p_c = 0$ / *No slip ⇒ $\dot p_c = 0$*
- ③ 按机体/关节分块 $J_c=[J_b\mid J_j]$，解出机体速度 / *Split into base and joint blocks and solve for the base*

**一定要补一句让大家“听懂”的话 / Add the sentence that makes it land**:

> **中文**：“这就是轮腿机器人里那个**闭环约束**的等价物——只不过我们的闭环不是连杆，是**地面接触**。”
> **English**: "This is the exact analogue of the **closed-loop constraint** in a wheeled-legged robot — except our loop is not a linkage, it is **ground contact**."

配 `figs/fig_p2b_stance_side.png`：脚钉住（红叉），身体被推（蓝箭头）。
*Pair with `figs/fig_p2b_stance_side.png`: foot pinned (red cross), body pushed (blue arrow).*

**成立条件 / Validity condition**：$J_b$ 满秩 ⇔ 四个接触点**不共面**；退化时用阻尼最小二乘 $J_b^{\dagger}$。
*$J_b$ full rank ⇔ the four contacts are **not coplanar**; in the degenerate case use the damped least-squares inverse $J_b^{\dagger}$.*

### 第 3 步 · 一个反直觉的推论（40 秒）
### Move 3 · One counter-intuitive corollary (40 s)

这条公式推下去会得到一个**非常反直觉**的结论：

> **中文**：“**只有支撑相在推进，摆动相贡献是零。**”
> **English**: "**Only the stance phase propels. The swing phase contributes exactly zero.**"

为什么？因为摆动腿是抬起来的，它对地面不施加推力。所以：

$$
\Delta x_{cycle} = \sum_{stance} v_{body}\,\Delta t \;+\; \underbrace{0}_{swing}
$$

配 `figs/fig_p2c_swing_side.png`。

**这一句是全篇的“啊哈”点 / This is the "aha" of the whole talk**，因为它直接解释了后面所有失败：

> **中文**：“所以这台手能不能走，本质上取决于它**抬不抬得起脚**。”
> **English**: "So whether this hand can walk comes down to **whether it can lift its feet at all**."

### 第 4 步 · 那就选步态（60 秒）
### Move 4 · So the gait choice follows (60 s)

有了上面的结论，选步态不是“试试看”，而是**有依据的选择 / The gait is now a deduction, not a guess**:

| 步态 / Gait | 支撑 / Support | 抬脚需求 / Lift needed | 结果 / Result |
|---|---|---|---|
| 爬行 3&1 / Crawl 3&1 | 3 点最稳 / most stable | 低 / low | **实测后退 20.9 cm / measured −20.9 cm** |
| **对角 2&2 / Trot 2&2** | 2 点 / two points | 中 / medium | **3.11 cm/s 前进 / forward 3.11 cm/s** |

- 爬行为什么失败？不是不稳，是**指尖只能抬 2 cm**，摆动腿离不了地，前后扫摆互相抵消 → 净位移为负
  *Why crawl fails: not instability — the fingertip can only lift 2 cm, so the swing leg never leaves the floor and the fore/aft sweep cancels out.*
- 对角两点凭什么成？**牺牲静态稳定，换切换速度**
  *Why trot works: it trades static stability for switching speed.*

### 第 5 步 · 留钩子（10 秒）
### Move 5 · Leave the hook (10 s)

> **中文**：“原理很清楚，步态也选对了。那为什么我们**做了很久才真的走成**？”
> **English**: "The principle is clear, the gait is right. So **why did it take so long to actually work?**"

---

## 4.3 这页的坑 / Traps

| 坑 / Trap | 后果 / Consequence | 怎么避 / Fix |
|---|---|---|
| 推 DH 表 / 前向运动学全展开<br>*Deriving the whole DH chain* | 3 分钟没了，听众睡着<br>*Three minutes gone, everyone asleep* | **只留一条锚定公式**，DH 放 backup<br>*Keep only the anchoring equation; DH to backup* |
| 说了 $J_c$ 却不解释它是什么<br>*Using $J_c$ without saying what it is* | 听众当作符号天书<br>*It is Greek to them* | 一句：“接触点速度对关节速度的灵敏度”<br>*Say: how fast contact points move per unit joint speed* |
| 直接给参数表，不说为什么<br>*Dumping the parameter table first* | 像在报菜单<br>*It reads like a menu* | 先给结论（只有支撑相推进），再给参数<br>*Conclusion first, parameters second* |

## 4.4 这页必须说出口的 / Must say

- **$J_c\dot q=0 \Rightarrow v_b=-J_b^{-1}J_j\dot q_j$**
- **“只有支撑相推进，摆动相为零”** / *"Only stance propels; swing is zero"*
- **“所以抬脚能力是命门”** / *"So the ability to lift the foot is the crux"*

---

# 5. Slide 3 — 失败案例与改进 / What Failed & What We Fixed

## 5.1 这页的性质 / The nature of this slide

**中文**：**这是加分页。** 大多数人会藏失败。你主动摆出来，并且每条失败对应一个可量化根因 + 一个具体修法——这是最有说服力的部分。
**English**: **This is the slide that earns marks.** Most people hide failures. You show them, and every failure gets a quantified root cause plus a concrete fix.

---

## 5.2 四步展开 / Four moves

### 第 1 步 · 先给全景（40 秒）
### Move 1 · The panorama first (40 s)

上汇总表，让人先看到“我们系统地试了 5 条路，4 条撞墙 / five routes tried, four hit a wall”:

| 尝试 / Attempt | 结果 / Result | 根因 / Root cause | 修法 / Fix |
|---|---|---|---|
| 开环爬行 / Open-loop crawl | −20.9 cm（后退 / backwards） | 抬脚只 2 cm / lift is 2 cm | 只当相位先验 / phase prior only |
| 残差 RL 60 万步 / Residual RL, 600k steps | 0.52 s 侧翻 / rolls over | 余量 vs 行程 / margin vs stroke | 换确定性控制 / go deterministic |
| 常数 bias / Constant bias | 0.8 s 摔 / falls | 开环无反馈 / no feedback | 加偏航反馈 / add yaw feedback |
| 横向增益 −4 / Lateral gain −4 | 摔 / falls | 过纠偏 / over-correction | −2 + 低通 / −2 + low-pass |
| **最终 / Final** | **走成 / walks** | — | **两个标量 / two scalars** |

**先给表的目的 / Why the table comes first**：让听众知道“后面要深挖的只是其中一条”。
*So the audience knows that only one row will be investigated in depth.*

### 第 2 步 · 深挖 RL（90 秒，最有说服力的一段）
### Move 2 · Dig into the RL run (90 s — the most persuasive stretch)

不要只说“RL 不行”，要给**时间线 / Do not just say "RL didn't work" — show the timeline**:

```
t = 0.00 s   X = +0.6 cm    up = 1.00
t = 0.17 s   X = +3.1 cm    up = 0.97   ← 开始倾斜 / starts to tilt
t = 0.34 s   X = +6.1 cm    up = 0.89   ← 越过支撑边界 / crosses the support edge
t = 0.52 s   X = +10.1 cm   up = 0.70   ← 判摔 / terminated, roll 45.9°
```

**三个必说的数字 / Three numbers you must give**:

| 数字 / Number | 含义 / Meaning |
|---|---|
| 横向 **18 cm/s** vs 前进 **4.6 cm/s** | 横向是前进的 4 倍 / lateral is 4× forward |
| 奖励 **+0.154 < +0.197** | 从未超过“什么都不做”基线 / never beat the do-nothing baseline |
| **每个 seed 完全一致** | 不是随机性问题，是必然 / not randomness, but necessity |

配 `figs/fig_p3_fall.png`（左漂移、右倾角，中间 0.18 s 死区）。
*Pair with `figs/fig_p3_fall.png` (drift left, tilt right, 0.18 s dead zone in between).*

### 第 3 步 · ⭐ 四层根因（60 秒，全篇最值钱的部分）
### Move 3 · ⭐ Four layers of root cause (60 s — the highest-value part of the talk)

「RL 不行」是结论不是解释。**四层才对 / "RL doesn't work" is a conclusion, not an explanation. Four layers are needed**:

| 层 / Layer | 根因 / Root cause | 一句话 / One line |
|---|---|---|
| **物理 / Physics** | 余量 5.29 < 行程 2.77 | **物理上不可恢复，不是策略菜**<br>*Physically unrecoverable — not a weak policy* |
| **接口 / Interface** | 16 个关节共用一个 0.25 rad 尺度<br>*16 joints share one 0.25 rad scale* | ABD 的敏感度远高于 FLX，随机探索等于往侧面推<br>*ABD is far more sensitive than FLX; random exploration pushes sideways* |
| **奖励 / Reward** | 不动就是最优解<br>*Standing still is optimal* | 摔倒惩罚只值 0.4 s 站立<br>*The fall penalty is worth only 0.4 s of standing* |
| **实现 / Implementation** | 超时被当成 `terminated`<br>*Time-out coded as `terminated`* | 价值函数在时间边界被系统性低估<br>*Values are systematically underestimated at the time boundary* |

> **中文**：“如果只有第一层，那是‘运气不好’。四层叠在一起，说明**这套框架在这台手上不适用**，不是调参能救的。”
> **English**: "If it were only the first layer, that would be bad luck. Four layers together mean **the framework does not fit this machine** — and no amount of tuning fixes that."

### 第 4 步 · 那什么管用了（40 秒）
### Move 4 · What did work (40 s)

- 放弃端到端 → **确定性开环 trot + 两个标量反馈**
  *Drop end-to-end → **deterministic open-loop trot + two scalar feedback terms***
- 偏航 P（快，内环）作用在步幅差分：**提速 85%**，横向 16.5% → 11%
  *Yaw P (fast, inner loop) acting on the stride differential: **+85 % speed**, lateral 16.5 % → 11 %*
- 横向 P（慢，外环）+ **τ = 4 s 低通**：横向 9% → 6%
  *Lateral P (slow, outer loop) + **τ = 4 s low-pass**: lateral 9 % → 6 %*

配 `figs/fig_ctrl_clean.png`（黑白框图）。
*Pair with `figs/fig_ctrl_clean.png` (the black-and-white block diagram).*

### 第 5 步 · 留钩子（10 秒）
### Move 5 · Leave the hook (10 s)

> **中文**：“所以我们最后得到了什么？”
> **English**: "So what did we finally get?"

---

## 5.3 这页的坑 / Traps

| 坑 / Trap | 后果 / Consequence | 怎么避 / Fix |
|---|---|---|
| 只说“RL 不行”，不解释<br>*"RL didn't work" with no explanation* | 听众觉得你不会调参<br>*They think you cannot tune* | **必须给四层根因**<br>*Give the four layers* |
| 一次讲完所有失败<br>*Walking through every failure equally* | 变成流水账<br>*It becomes an inventory* | 汇总表快速过，**只深挖 RL 一条**<br>*Skim the table; dig into RL only* |
| 讲失败时不带数字<br>*Telling failures without numbers* | 可信度归零<br>*Credibility is zero* | 每条失败必须挂一个数<br>*Every failure needs a number* |

---

# 6. Slide 4 — 结果与展望 / Results & Future Work

## 6.1 这页的两个任务 / Two jobs

**中文**：给一个记得住的 headline + 诚实说一个缺陷，让 future work **直接接住 S3 的阻塞**。
**English**: Deliver a memorable headline, admit one defect honestly, and make every future-work item **land directly on a blocker from S3**.

---

## 6.2 五步展开 / Five moves

### 第 1 步 · Headline，大字（20 秒）
### Move 1 · The headline, large (20 s)

> **“40 秒 · 1.10 米 · 零摔倒。”**
> **"40 seconds. 1.10 metres. Zero falls."**

先说结论，再展开。别让听众等。
*Conclusion first, evidence second. Do not make them wait.*

### 第 2 步 · 数据（30 秒）
### Move 2 · The numbers (30 s)

| 指标 / Metric | 值 / Value |
|---|---|
| 前进速度 / Forward speed | **3.11 cm/s** |
| 横向占比 / Lateral share | 6–11 % |
| 40 s 偏航漂移 / Yaw drift over 40 s | ±7° |
| 峰值力矩 / Peak torque | 10.0 N·m（打满 / saturated） |
| RMS 力矩 / RMS torque | 1.19 N·m |

配 `figs/fig9_run.png`（轨迹 + 朝向）。
*Pair with `figs/fig9_run.png` (trajectory + heading).*

### 第 3 步 · ⭐ 主动暴露缺陷（40 秒）
### Move 3 · ⭐ Volunteer the defect (40 s)

**这一步不做，后面被问会很难看 / Skip this and the Q&A will hurt**:

> **中文**：“我必须诚实说一个问题：**四个 MCP-FLX 在支撑相是力矩打满的。**
> 静态重力只有 0.05 牛米，所以不是它撑不住，而是**抬腿那一瞬间的冲击太大**。”
>
> **English**: "I have to be honest about one thing: **all four MCP-FLX joints saturate during stance.**
> Static gravity load is only 0.05 N·m, so this is not a strength problem — **it is the impact at lift-off.**"

配 `figs/fig_t3_torque.png`。

**主动说的好处 / Why volunteering helps**：你不说，评审一定会问；你先说，就变成“你考虑过了”。
*If you don't say it, someone will ask; if you say it first, it reads as "you already thought about it".*

### 第 4 步 · Future work，每条接一个阻塞（60 秒）
### Move 4 · Future work, each item tied to a blocker (60 s)

**不能写成“提升鲁棒性、优化算法”这种空话。每条必须点名它解决 S3 的哪一条。**
***Never write "improve robustness" or "optimise the algorithm". Each item must name the S3 blocker it removes.***

| # | 改什么 / What | 接哪条 / Which blocker |
|---|---|---|
| 1 | 加宽支撑 5.29 → 7+ cm<br>*Widen the support 5.29 → 7+ cm* | 物理层，窗口 0.29 s → 0.5 s<br>*Physics: window 0.29 s → 0.5 s* |
| 2 | 关节分别缩放（ABD ≤ 0.08）<br>*Per-joint scaling (ABD ≤ 0.08)* | 接口层<br>*Interface* |
| 3 | 修正 `truncated` + bootstrap<br>*Fix `truncated` + bootstrap* | 实现层 bug<br>*Implementation bug* |
| 4 | 五次多项式摆动<br>*Quintic swing trajectory* | FLX 打满（端点速度 6.28 → 0）<br>*FLX saturation (endpoint speed 6.28 → 0)* |
| 5 | 加大 FLX 电机<br>*Upgrade the FLX motors* | 直接解决饱和<br>*Directly removes saturation* |

> **中文**：“每一条都不是‘提升鲁棒性’，而是**对着前面某个具体失败**。比如第五条——正弦在摆动结束还有 6.28 的速度，等于带着速度砸下去，这就是 FLX 打满的元凶。”
> **English**: "None of these is 'improve robustness'. Each one targets a specific failure from earlier. Take item five — a sinusoid still carries a speed of 6.28 at the end of swing, so the foot lands with velocity, and that is what saturates the FLX motors."

### 第 5 步 · 收尾金句（15 秒）
### Move 5 · The closing line (15 s)

> **中文**：“灵巧手不是小四足。它的稳定性余量以**厘米和个位数角度**计——
> 决定上限的是这个物理事实，**不是学习算法**。”
>
> **English**: "A dexterous hand is not a small quadruped. Its stability margin is measured in **centimetres and single-digit degrees**. What sets the ceiling is that physical fact — **not the learning algorithm**."

---

## 6.3 这页的坑 / Traps

| 坑 / Trap | 后果 / Consequence | 怎么避 / Fix |
|---|---|---|
| 只报喜不报忧<br>*Only good news* | 被问 FLX 打满时被动<br>*You get cornered on torque* | 主动暴露<br>*Volunteer it* |
| future work 写成空话<br>*Vague future work* | 显得没想清楚<br>*Looks unthought-through* | **每条挂一个具体失败**<br>*One concrete failure per item* |
| 收尾讲技术细节<br>*Ending on technical detail* | 没有记忆点<br>*No memorable line* | 用金句收，别再抛新信息<br>*Close on the line; add no new information* |

---

# 7. 三句过渡词 / Three Transition Lines

**这三句必须背下来，它们决定四页是散块还是链条。**
***Memorise these three. They decide whether the deck is a chain or a pile.***

| 位置 / Where | 一字不改地说 / Say it verbatim |
|---|---|
| S1 → S2 | “一碰就倒的东西，**凭什么还能往前走？**”<br>*"Something that tips this easily — **how does it move forward at all?**"* |
| S2 → S3 | “原理这么清楚，**为什么我们做了很久才走成？**”<br>*"The principle is clear — **why did it take so long to work?**"* |
| S3 → S4 | “那**最后到底走成什么样了？**”<br>*"So **what did we actually achieve?**"* |

---

# 8. 时间分配 / Timing (10 min)

| 页 / Slide | 时间 / Time | 累计 / Cumulative | 必须说出口 / Must say |
|---|---|---|---|
| S1 | 3:00 | 3:00 | **5.29 cm / 25.3° / 2.77 cm** |
| S2 | 2:00 | 5:00 | $v_b=-J_b^{-1}J_j\dot q_j$ + **“只有支撑相推进”** |
| S3 | 2:30 | 7:30 | **0.52 s** + **四层根因 / four layers** |
| S4 | 2:30 | 10:00 | **40 s / 1.10 m** + FLX 打满 |

**超时先砍 / Cut these first**：S1 的 High/Low 图、S2 的爬行细节、S4 的数据表（留 headline）。
*The High/Low images on S1, the crawl detail on S2, the data table on S4 (keep the headline).*

---

# 9. 3 分钟极简版 / The 3-Minute Version

| 页 / Slide | 只讲这一句 / Say only this | 用哪张图 / Figure |
|---|---|---|
| S1 | “侧向余量 5.3 cm，翻倒角 25°，自救行程只有 2.8 cm。”<br>*"5.3 cm of lateral margin, a 25° tipping angle, and only 2.8 cm of stroke to save itself."* | `fig_p1_why_hard` |
| S2 | “脚不滑，所以关节一转身体就被推出去；只有支撑相推进。”<br>*"Feet don't slip, so joint motion pushes the body; only stance propels."* | `fig_p2b_stance_side` |
| S3 | “RL 0.52 秒就侧翻，三个 seed 一模一样，因为物理上救不回来。”<br>*"RL rolls over in 0.52 s, identically on every seed, because it is physically unrecoverable."* | `fig_p3_fall` |
| S4 | “40 秒 1.1 米没摔；FLX 打满指向下一步。”<br>*"40 s, 1.1 m, no falls; saturated FLX points to what's next."* | `fig9_run` |

---

# 10. 开场句逐字拆解 / Anatomy of the Opening Line

> “这只手有 16 个电机，看起来像个小四足。但它的侧向稳定余量只有 5.3 厘米。也就是说——它往旁边漂 5 厘米就会倒。我今天讲的就是怎么让它走起来。”
>
> *"This hand has 16 motors. It looks like a small quadruped. But its lateral stability margin is only 5.3 centimetres — which means it falls after drifting 5 centimetres sideways. What I'm going to talk about is how we made it walk anyway."*

## 10.1 四句话，四个功能 / Four clauses, four functions

| 原句 / Clause | 功能 / Function | 删掉会怎样 / Remove it and… |
|---|---|---|
| “16 个电机”<br>*"16 motors"* | **建立错误预期**<br>*Build a wrong expectation* | 听众不知道复杂度，后面“难”立不住<br>*The difficulty has nothing to contrast against* |
| “看起来像个小四足”<br>*"looks like a small quadruped"* | **点破这个错误预期**<br>*Name the expectation* | 少了反差，整句话失去张力<br>*The contrast, and the tension, vanish* |
| “但侧向稳定余量只有 5.3 厘米”<br>*"but the margin is only 5.3 cm"* | **用具体数字反驳**<br>*Refute it with a number* | 变成“它有点难”这种废话<br>*It becomes "it's a bit hard"* |
| “漂 5 厘米就会倒”<br>*"falls after 5 cm of drift"* | **把数字翻译成人话**<br>*Translate the number* | 非本行听众听不懂 margin<br>*Non-specialists lose the thread* |
| “我今天讲的就是怎么让它走起来”<br>*"how we made it walk"* | **给出承诺**<br>*Make the promise* | 听众不知道你要讲什么<br>*They don't know what they're listening for* |

**真正在做的事**：建立预期 → 打破预期 → 承诺解答。
*What it actually does: build an expectation → break it → promise the answer.*

## 10.2 “侧向稳定余量”到底是什么 / What the lateral margin actually is

把四个指尖的着地点连成一个多边形（**支撑多边形**），质心垂直投影到地面得一个点。**这个点到多边形边缘的最近距离**就是稳定余量。

*Join the four contact points into a polygon (the **support polygon**), project the centre of mass vertically onto the floor, and take **the distance from that point to the nearest polygon edge**.*

$$
\text{margin} = \operatorname{dist}\big(\pi_{xy}(p_{com}),\ \partial\mathcal{P}\big)
$$

- 余量 $>0$ → 投影在多边形内，**重力矩被地面反力平衡，站得住**
  *margin $>0$ → the projection is inside; gravity is balanced by the ground reaction*
- 余量 $<0$ → 投影跑到外面，**重力矩变成倾覆力矩，开始加速倒**
  *margin $<0$ → it is outside; gravity becomes a tipping torque and the fall accelerates*

### 我们的实际数字 / Our actual numbers

```
        X = -9.14                          X = +4.51
            │                                  │
   左边缘 ──┼──────────────────────────────────┼── 右边缘
            │                                  │
            │        ● 质心投影 (-0.78, +0.16) │
            │        ←──── 5.29 ──────────────→│
            │←────────── 8.36 ─────────────────│
```

- 支撑面 X 范围 / support X range: **−9.14 → +4.51 cm**（宽 13.64 cm）
- 质心投影 / CoM projection: **(−0.78, +0.16) cm**
- 到右边缘 / to right edge: $4.51-(-0.78)=\mathbf{5.29}$ cm
- 到左边缘 / to left edge: $-0.78-(-9.14)=\mathbf{8.36}$ cm

**两个关键观察 / Two key observations**:

1. **质心不在中心**：支撑面几何中心在 $-2.32$ cm，质心在 $-0.78$ cm，**偏右 1.5 cm**。
   所以左边富余 8.36，右边只剩 5.29。**它天生就歪向一边。**
   *The CoM sits 1.5 cm right of the geometric centre, so the right margin is the small one. **It is born leaning.***

2. **5.29 cm 是最薄弱方向**：四个方向里最近的那条边。用它代表难度是合理的最坏情况。
   *5.29 cm is the thin direction — the nearest edge of four. Using it is a fair worst case.*

## 10.3 “漂 5 厘米就会倒”严谨吗 / Is the claim rigorous?

**不严谨，但方向正确。** 严格说法需要三个前提 / *Not rigorous, but pointing the right way. Three conditions:*

### 前提 1 · 漂的是**质心投影**，不是手
### Condition 1 · It is the **CoM projection** that drifts, not the hand

$$
\text{倒的条件：}\ \pi_{xy}(p_{com}) \text{ 越过边界}
$$

不是“手移动 5 厘米”，而是“质心投影相对支撑面移动 5 厘米”。
如果整只手脚同时挪 5 厘米，支撑面跟着挪，余量根本不变。

*It is not "the hand moves 5 cm" but "the CoM projection moves 5 cm relative to the support polygon". If the whole robot including the feet translates, the polygon translates too and the margin is unchanged.*

### 前提 2 · 准静态、不主动调整
### Condition 2 · Quasi-static, with no active correction

如果手在漂的过程中主动屈曲关节把质心拉回来，5.29 cm 就不是硬上限。
**但实际上拉不回来**——关节能提供的横向行程只有 **2.77 cm**：

$$
\underbrace{2.77}_{\text{能纠偏 / can correct}} \;<\; \underbrace{5.29}_{\text{需要纠偏 / must correct}}
$$

**这才是真正的杀手锏**：需要 5.29，只有 2.77，缺口 48%。
*This is the real killer: it needs 5.29 and has 2.77 — a 48 % shortfall.*

### 前提 3 · 这是一个位姿下的值
### Condition 3 · It is a single-pose value

5.29 cm 是**沉降后静止站姿**测出来的。行走中质心高度和横向位置都在变，余量浮动（实测 4.9–6.1 cm）。
*5.29 cm is the settled static stance. During walking it varies between 4.9 and 6.1 cm.*

**被问“一直 5.3 吗”怎么答 / If asked "is it always 5.3?"**:
> “这是静止站姿的实测值，行走中在 4.9–6.1 之间浮动。我用它代表难度，因为它是**最好的情况**——行走时只会更差。”
> *"That's the settled stance. In walking it varies 4.9–6.1 cm. I quote it because it is the **best case** — walking only makes it worse."*

## 10.4 为什么说“侧向”不说“稳定性” / Why "lateral", not just "stability"

不同方向余量差很多，必须指名 / *The directions differ substantially, so name one*:

| 方向 / Direction | 余量 / Margin | 翻倒角 / Tipping angle |
|---|---|---|
| **侧向（X，左右）/ Lateral** | **5.29 cm** | **25.3°** |
| 前后（Y，前进）/ Fore–aft | 7.60 / 7.99 cm | 34.2° |

侧向比前后危险得多，而且实测摔倒**全部是侧翻**（roll 45.9°）。
*Lateral is far more dangerous, and every measured fall was a roll (45.9°).*

余量和翻倒角是同一个东西的两种表达 / *Margin and tipping angle are the same fact twice*:

$$
\tan\theta=\frac{\text{margin}}{h}=\frac{5.29}{11.20}=0.472 \;\Rightarrow\; \theta=25.3^\circ
$$

## 10.5 为什么这个开场有效 / Why the opening works

1. **具体数字 > 形容词**：听众记不住“很难”，但记得住 **5.3**。
   *Concrete beats adjectival: nobody remembers "hard", everybody remembers 5.3.*
2. **对比制造张力**：“16 个电机”（多）vs “5.3 厘米”（少），落差就是戏剧性来源。
   *16 motors vs 5.3 cm — the gap is the drama.*
3. **最后一句给了“为什么听”**：这是一个难题被解决的故事，不是说明书。
   *The last clause tells them this is a problem solved, not a manual.*

## 10.6 外行版 / For a non-specialist audience

> **中文**：“这只手有 16 个电机，比很多四足机器狗还多。但它走路的时候，**往旁边歪 5 厘米就会翻**。5 厘米大概就是**三根手指并起来的宽度**。我今天讲的就是：怎么让一个只能歪 5 厘米的东西，稳稳地走 40 秒、1.1 米。”
>
> **English**: "This hand has 16 motors — more than many quadruped robots. Yet when it walks, **it tips over after leaning 5 cm sideways**. Five centimetres is roughly **the width of three fingers side by side**. What I'll show is how we made something with only 5 cm to play with walk steadily for 40 seconds and 1.1 metres."

## 10.7 进阶版（更狠）/ Advanced version (bolder)

> **中文**：“先说结果：这只手走了 40 秒、1.1 米，一次没摔。但我想先告诉你它有多难——**侧向余量只有 5.3 厘米，纠偏能力只有 2.8 厘米。** 也就是说，**它一开始就注定救不回来。**”
>
> **English**: "Let me lead with the result: 40 seconds, 1.1 metres, no falls. But first, how hard this is — **5.3 cm of lateral margin and only 2.8 cm of authority to correct with.** In other words, **it was unrecoverable from the start.**"

---

# 11. 理论附录 / Theory Appendix

## 11.1 广义坐标与运动学 / Coordinates & Kinematics

$$
q=\begin{bmatrix}q_b\\ q_j\end{bmatrix}\in\mathbb{R}^{23},\qquad
\dot q\in\mathbb{R}^{22},\qquad
p_c=f(q),\qquad \dot p_c=J_c(q)\,\dot q
$$

- $q_b\in SE(3)$：浮动基座（位置 + **四元数**，欧拉角会万向节死锁）
  *$q_b\in SE(3)$: floating base, position + **quaternion** — Euler angles gimbal-lock*
- $q_j\in\mathbb{R}^{16}$：每个指尖 4 个关节 / *4 joints per fingertip*
- $J_c\in\mathbb{R}^{3\times 22}$：接触点速度雅可比（单指 3×4）
  *contact-point velocity Jacobian (3×4 per finger)*

**实测 / Measured**：单指速度椭圆奇异值 $\sigma=(13.9,\;5.6,\;1.8)$ cm/rad，$\kappa=\sigma_1/\sigma_2=2.5$；
工作空间内 $\kappa$ 从 **2 到 343**（中位 5.4）——**边缘位形有方向完全推不动**。
*Single-finger velocity-ellipse singular values $(13.9, 5.6, 1.8)$ cm/rad, $\kappa=2.5$; across the workspace $\kappa$ spans **2 to 343** (median 5.4) — at the edge some direction cannot be pushed at all.*

> 注意两个不同的数 / *Note two different numbers*:
> - **$\kappa=2.5$**：单指速度椭圆的轴比 / *axis ratio of one finger's velocity ellipse*
> - **13 : 1**：$\kappa_{\text{MCP-FLX},Y} : \kappa_{\text{MCP-ABD},X}\approx 6.0 : 0.45$，关节权限比 / *per-joint authority ratio*

## 11.2 接触锚定 / The Anchoring Constraint

$$
J_c=\big[\,J_b\mid J_j\,\big],\qquad
\underbrace{J_b}_{6\times6}\,v_b+\underbrace{J_j}_{6\times16}\,\dot q_j=0
\;\Longrightarrow\;
\boxed{\,v_b=-J_b^{-1}J_j\,\dot q_j\,}
$$

**推导三步 / Three steps**：
① $\dot p_c=J_c\dot q$；② 不滑 ⇒ $\dot p_c=0$ / *no slip ⇒ zero contact velocity*；③ 分块解出 $v_b$ / *split and solve*。

**成立条件 / Validity**：$J_b$ 满秩 ⇔ 四个接触点**不共面**；退化时（只剩对角两点共线）改用阻尼最小二乘 $J_b^{\dagger}$。
*$J_b$ full rank ⇔ the four contacts are **not coplanar**; in the degenerate case use the damped least-squares inverse.*

> 这是轮腿机器人“闭环约束 $p_B=p_C$”的等价物——**我们的闭环是地面接触**。
> *The exact analogue of the wheeled-legged closed-loop constraint — **our loop is ground contact**.*

## 11.3 接触力与摩擦锥 / Contact Force Feasibility

$$
\lambda_s=\begin{bmatrix}f_t\\ f_n\end{bmatrix},\qquad
f_n\ge 0,\qquad \|f_t\|\le \mu f_n
$$

- 模型：`condim=4`（法向 + 2 切向 + 扭转）/ *normal + 2 tangential + torsional*
- **$\mu=5.0$** 远大于实际切向/法向比 ⇒ **不滑假设成立**
  *$\mu=5.0$, far above the actual tangential-to-normal ratio ⇒ **the no-slip assumption holds***

## 11.4 浮动基拉格朗日动力学 / Floating-base Dynamics

$$
M(q)\,\ddot q+C(q,\dot q)\,\dot q+G(q)
=\underbrace{B_u\tau}_{\text{16 个电机}}+\underbrace{\sum_{s}J_{c,s}^{\top}\lambda_s}_{\text{地面反力}}+Q_{ext}
$$

| 符号 / Symbol | 含义 / Meaning | 我们的值 / Ours |
|---|---|---|
| $q/\dot q$ | 广义坐标/速度 / coordinates & rates | 23 / 22 |
| $M$ | 质量矩阵 / mass matrix | 22×22 |
| $C\dot q+G$ | 偏置力 `qfrc_bias` / bias forces | 实测 0 ~ 0.05 N·m |
| $B_u$ | 驱动选择矩阵 / actuation selector | 22×16 |
| $\tau$ | 关节力矩 / joint torque | **限幅 ±10 N·m** |
| $\lambda_s$ | 接触力 / contact force | 每点 3 维 / 3 per point |

## 11.5 伺服环 / Servo Loop

$$
\tau=K_p\,(q^{*}-q)+K_d\,(\dot q^{*}-\dot q),\qquad |\tau_i|\le 10\ \mathrm{N\cdot m}
$$

**实测 / Measured**：峰值 $|\tau|=10.0$ N·m（**打满 / saturated**），RMS 1.19 N·m，打满的全是 4 个 MCP-FLX。
静态重力只有 0.05 N·m ⇒ **饱和来自冲击 × 高增益，不是自重**。
*Static gravity is only 0.05 N·m ⇒ **the saturation comes from impact times high gain, not from weight**.*

## 11.6 步态代数 / Gait Algebra

$$
\Delta x_{\text{cycle}}=\sum_{\text{stance}} v_b\,\Delta t+\underbrace{\sum_{\text{swing}}0}_{\text{无推力 / no thrust}}
\quad\Longrightarrow\quad
v=f\,\Delta x_{\text{cycle}}
$$

**实测 / Measured**：$f=1/1.6$ Hz，$\Delta x_{\text{cycle}}\approx 5$ cm ⇒ $v\approx 3.1$ cm/s ✔

## 11.7 支撑多边形与静态裕度 / Support Polygon & Margin

$$
\mathcal{P}=\operatorname{conv}\{p_{c,i}\},\qquad
m=\operatorname{dist}\!\big(\pi_{xy}(p_{com}),\,\partial\mathcal{P}\big)
=\begin{cases}m>0 & \text{安全 / safe}\\ m<0 & \text{已出界 / out, falling}\end{cases}
$$

**实测 / Measured**：$\mathcal{P}=13.64\times15.59$ cm，$m_{\min}=5.29$ cm（左 8.36 / 右 5.29，**不对称 / asymmetric**）。

**几何事实 / Geometric fact**：2&2 步态在对角切换瞬间只剩 2 个接触点，$\mathcal{P}$ **退化成线段**——
「保持 CoM 在支撑面内」这个判据**在 2&2 里根本没有定义**，必须用动态判据。
*At the diagonal switch the polygon **degenerates to a line segment**, so a static criterion is simply undefined for trot.*

## 11.8 零矩点 / Zero Moment Point

$$
p_{zmp}=\frac{\sum_i\left(p_i f_{i,z}-z_i f_{i,xy}\right)}{\sum_i f_{i,z}}
\quad\Longleftrightarrow\quad
p_{zmp}=p_{com}-\frac{h}{g}\,\ddot p_{com}
$$

动力学可行 ⇔ $p_{zmp}\in\mathcal{P}$。
**实测 / Measured**：$|p_{zmp}-p_{com}|$ 中位 **1.16 cm**（trot）/ 0.72 cm（crawl），远小于 5.29 cm 余量。

## 11.9 捕获点与时间常数 / DCM & Time Constant

$$
\xi=p_{com}+\frac{\dot p_{com}}{\omega},\qquad
\omega=\sqrt{\frac{g}{h}},\qquad \frac{1}{\omega}=\text{恢复时间常数 / recovery time constant}
$$

**实测 / Measured**：$h=11.20$ cm ⇒ $\omega=9.4$ rad/s，$\mathbf{1/\omega=0.107}$ **s**。
DCM 前移量 $v/\omega=\mathbf{0.33}$ cm，比余量小 16 倍。
*DCM lead is 0.33 cm — sixteen times smaller than the margin.*

## 11.10 倾覆是不可稳定平衡 / Tipping is an Unstable Equilibrium

$$
I\ddot\theta=mg\,h\sin\theta
\;\xrightarrow{\;\theta\ll1\;}\;
\ddot\theta=\omega^2\theta
\;\Longrightarrow\;
\boxed{\theta(t)=\theta_0\cosh(\omega t)}
$$

配 `figs/fig_f4_cosh.png`。

**实测 / Measured**：$1/\omega=0.107$ s 是唯一逃生窗口；出界后 0.10 s 还几乎没歪，**0.20 s 就失控**——与 $\cosh$ 完全吻合。
*The only escape window; almost upright at 0.10 s, out of control by 0.20 s — exactly what cosh predicts.*

## 11.11 无量纲数 / Froude Number

$$
\mathrm{Fr}=\frac{v^2}{g\,h}=\frac{(0.0311)^2}{9.81\times0.112}\approx \mathbf{0.0009}\;\;(\ll 1)
$$

$\mathrm{Fr}\ll1$ ⇒ 惯性项远小于重力项 ⇒ **准静态**。这也是为什么“确定性开环 + 两个标量反馈”就够，而**不需要全身 MPC**。
*Inertia is negligible against gravity, which is why deterministic open loop plus two scalars suffices — no whole-body MPC needed.*

## 11.12 摔倒判据 / The Real Fall Criterion

单看 $m<0$ 会误报——实测正常行走有 **6 %** 的时间 $m<0$，却从不摔。真正的判据是：

$$
\text{fall}\iff m<0 \;\text{持续} > \tau_{\text{crit}}\approx \frac{1}{\omega}=0.107\ \mathrm{s}
$$

| 情形 / Case | 出界占比 / Out-of-polygon share | 结果 / Result |
|---|---|---|
| 正常 trot / Normal trot | 6 % | 不摔 / no fall |
| bias = −0.40 | **62 %** | 0.8 s 摔 / falls at 0.8 s |

> **中文**：“出界本身不是摔倒的原因，**出界之后回不回来才是**。我们的手只有 0.1 秒的窗口。”
> **English**: "Being outside is not what makes it fall — **whether it comes back is**. This hand has a 0.1-second window."

## 11.13 摆动轨迹：为什么必须五次 / Why the Quintic

五次多项式是**唯一同时满足端点位置、速度、加速度全部为零**的最低阶多项式：

$$
s(\sigma)=10\sigma^3-15\sigma^4+6\sigma^5,\quad \sigma\in[0,1]
$$
$$
s(0)=0,\; s(1)=1,\qquad \dot s(0)=\dot s(1)=0,\qquad \ddot s(0)=\ddot s(1)=0
$$

| 量 / Quantity | 正弦（现在）/ Sine (current) | 五次多项式 / Quintic |
|---|---|---|
| 端点速度 / endpoint speed | **6.28（不为 0）** | **0.00** |
| 峰值加速度 / peak acceleration | 39.5 | **5.77（降 7 倍 / 7× lower）** |

## 11.14 电机可行性 / Actuator Feasibility

$$
|\tau_i(t)|\le \tau_{\max}=10\ \mathrm{N\cdot m}\;\;\forall t,\;\forall i
\quad\Longleftrightarrow\quad
\text{执行器可行 / feasible}
$$

实测 $\max|\tau|=10.0$ N·m —— **等号成立就是不合格**。
*Equality means infeasible.*

---

# 12. 追问应答手册 / Q&A Playbook

| 问题 / Question | 答案 / Answer |
|---|---|
| **5.3 怎么算的？**<br>*How is 5.3 computed?* | 质心投影 (−0.78, +0.16)，支撑面 X 到 +4.51，$4.51-(-0.78)=5.29$ cm<br>*CoM projection at −0.78 cm, support edge at +4.51 cm* |
| **为什么质心是偏的？**<br>*Why is the CoM off-centre?* | 掌和四指质量分布不对称（C 指只在单侧），模型实测<br>*Asymmetric mass distribution — the C finger sits on one side; measured, not chosen* |
| **5.3 厘米听起来不算小？**<br>*5.3 cm doesn't sound small* | 关键不是它小，而是**纠偏行程只有 2.77 cm**——需要 5.3，只有 2.8<br>*The point is the 2.77 cm of stroke, not the 5.29 itself* |
| **走路时也是 5.3 吗？**<br>*Is it 5.3 in walking too?* | 不是，行走中 4.9–6.1 浮动；用静止值因为那是最好情况<br>*No — 4.9–6.1 cm; the static value is the best case* |
| **条件数 2.5 说明什么？**<br>*What does κ = 2.5 mean?* | 单指速度椭圆轴比 $\sigma_1/\sigma_2=13.9/5.56$；工作空间边缘能到 343<br>*Axis ratio of one finger's velocity ellipse; up to 343 at the workspace edge* |
| **为什么不用 MPC？**<br>*Why no MPC?* | $\mathrm{Fr}\approx0.0009\ll1$，深度准静态；$|p_{zmp}-p_{com}|$ 中位 1.16 cm，两个标量已经够<br>*Deeply quasi-static; two scalars suffice* |
| **为什么 2&2 而不是 3&1？**<br>*Why trot over crawl?* | 爬行实测后退 20.9 cm（抬脚只 2 cm，摆动腿离不了地）<br>*Crawl measured −20.9 cm because the foot cannot leave the floor* |
| **RL 为什么不用更好的奖励？**<br>*Why not a better reward?* | 至少 7 个因子在 180k 步窗口内不可辨识，20 次试跑全部 $|\rho|<0.18$<br>*Seven-plus factors are unidentifiable in that window; all 20 runs gave \|ρ\| < 0.18* |
| **FLX 打满会不会烧电机？**<br>*Will saturating FLX burn the motors?* | 仿真里是限幅不是过热；真机上这是必须解决的<br>*In sim it is a clamp, not heat; on hardware it must be fixed* |
| **为什么不定量比较 RL 与经典？**<br>*Why no head-to-head number?* | 两者差一个量级，且目标函数不可比，硬比反而误导<br>*They differ by an order of magnitude and the objectives are not comparable* |
| **横向增益为什么不能更大？**<br>*Why not a larger lateral gain?* | −4 直接摔；−2 配 τ=4 s 低通才稳<br>*−4 falls outright; −2 with a 4 s low-pass is stable* |
| **偏航增益上限在哪？**<br>*What limits the yaw gain?* | 0.5 提速 85 %，0.6 已经摔<br>*0.5 gives +85 % speed; 0.6 already falls* |

---

# 13. 数字速查表 / Number Card

## 13.1 几何与静力学 / Geometry & Statics

| 量 / Quantity | 值 / Value |
|---|---|
| 驱动自由度 / Actuated DoF | **16**（4 指 × 4 关节） |
| 浮动基座 / Floating base | 6 DoF |
| 整机质量 / Total mass | **1.139 kg**（掌+指 0.635 kg） |
| 质心高度 / CoM height | **11.20 cm**（行走 9.4–12.2） |
| 质心横向偏移 / Lateral CoM offset | **−0.78 cm** |
| 支撑域 / Support polygon | **13.64 × 15.59 cm** |
| 左右余量 / L–R margins | **8.36 / 5.29 cm** |
| 前后余量 / Fore–aft margins | 7.60 / 7.99 cm |
| 侧向翻倒角 / Lateral tipping angle | **25.3°** |
| 前后翻倒角 / Fore–aft tipping angle | 34.2° |
| 横向纠偏行程 / Lateral stroke | **2.77 cm** |

## 13.2 时间尺度与无量纲数 / Time Scales & Dimensionless Numbers

| 量 / Quantity | 值 / Value |
|---|---|
| $\omega=\sqrt{g/h}$ | **9.4 rad/s** |
| 恢复时间常数 $1/\omega$ | **0.107 s** |
| Froude 数 / Froude number | **≈ 0.0009** |
| DCM 前移量 $v/\omega$ | **0.33 cm** |
| 步态周期 / Gait period | 1.6 s |
| 出界时长判据 $\tau_{crit}$ | 0.107 s |

## 13.3 结果 / Results

| 量 / Quantity | 值 / Value |
|---|---|
| 连续行走 / Continuous walking | **40 s** |
| 前进距离 / Distance | **1.10 m** |
| 前进速度 / Forward speed | **3.11 cm/s** |
| 横向占比 / Lateral share | **6–11 %** |
| 40 s 偏航漂移 / Yaw drift | **± 7°** |
| 峰值力矩 / Peak torque | **10.0 N·m（打满）** |
| RMS 力矩 / RMS torque | **1.19 N·m** |

## 13.4 失败数据 / Failure Data

| 量 / Quantity | 值 / Value |
|---|---|
| RL 摔倒时间 / RL time to fall | **0.52 s** |
| 横向漂移 / Lateral drift | **18 cm/s** |
| 前进漂移 / Forward drift | 4.6 cm/s |
| RL 奖励 / RL reward | **+0.154**（基线 baseline +0.197） |
| 判摔倾角 / Termination angle | **45.9°**（up_z 0.70） |
| 物理翻倒角 / Physical tipping | **25.3°**（up_z 0.90） |
| 死区 / Dead zone | **0.18 s** |
| 爬行结果 / Crawl result | **−20.9 cm** |
| bias −0.40 结果 | 0.8 s 摔 / falls |

## 13.5 雅可比 / Jacobian

| 量 / Quantity | 值 / Value |
|---|---|
| 单指奇异值 / Finger singular values | **13.9 / 5.6 / 1.8** cm/rad |
| 单指条件数 $\kappa=\sigma_1/\sigma_2$ | **2.5** |
| 工作空间 $\kappa$ 范围 / Workspace range | **2 – 343**（中位 median 5.4） |
| 关节权限比 / Joint authority ratio | **13 : 1**（FLX 6.0 : ABD 0.45） |

---

# 14. 五分钟自检 / Five-Minute Self-Check

上台前对着这张清单过一遍 / *Run this list before you go on*:

- [ ] 开场第一句是 **“16 个电机”** 起手，不是“我们搭了环境”
      *First sentence starts with 16 motors, not with the toolchain*
- [ ] 说过 **5.29 / 25.3° / 2.77** 三个数
      *Said 5.29 / 25.3° / 2.77*
- [ ] 说过 **“只有支撑相推进，摆动相为零”**
      *Said "only stance propels, swing is zero"*
- [ ] 说过 **“0.52 秒，三个 seed 一模一样”**
      *Said "0.52 s, identical on every seed"*
- [ ] 说过 **“FLX 打满 10 N·m”**（主动暴露）
      *Volunteered the 10 N·m FLX saturation*
- [ ] 三句过渡词都用了 / *Used all three transition lines*
- [ ] 收尾用金句，没有抛新信息
      *Closed on the line, added no new information*
- [ ] 计时：S1 ≤ 3:30，总时长 ≤ 10:00
      *Timing: S1 ≤ 3:30, total ≤ 10:00*

---

# 15. 四处需要你最终拍板的数字 / Four numbers to settle

| 项 / Item | 文档 A / Doc A | 文档 B / Doc B | 建议 / Recommendation |
|---|---|---|---|
| CoM 高度 / CoM height | 10.5 cm（行走中 / walking） | **11.20 cm**（沉降 / settled） | 说“9.4–12.2 cm，取 11.2”<br>*Say "9.4–12.2 cm, take 11.2"* |
| Froude 数 / Froude number | 0.0055（`stability_analysis.md`） | **0.0009** | 老文档这个算错了：$(0.0274)^2/(9.81\times0.105)=7.3\times10^{-4}$<br>*The old doc is wrong; recompute* |
| 质量 / Mass | 0.635 kg（掌+指） | **1.139 kg**（整机） | 讲“整机 1.139 / 掌指 0.635”<br>*Say both, specify which* |
| yaw 增益 / yaw gain | 0.3（旧图 / old figure） | **0.5**（deck 与实测 / deck & measurements） | 用 0.5；旧图需重画<br>*Use 0.5; the old figure needs redrawing* |

---

## 附：图件清单 / Figure index

| 文件 / File | 用在哪 / Used on | 说明 / Note |
|---|---|---|
| `figs/fig1_layout.png` | S1 | 四指落点俯视 / contact layout |
| `figs/fig_p1_why_hard.png` | S1 | 俯视+侧视+三数对比 / margin, triangle, comparison |
| `figs/fig_p2b_stance_side.png` | S2 | 支撑项侧视 / stance side view |
| `figs/fig_p2c_swing_side.png` | S2 | 摆动项侧视 / swing side view |
| `figs/fig_p2_anchor.png` | S2 backup | 锚定合并版 / combined anchoring |
| `figs/fig_p3_fall.png` | S3 | RL 摔倒时间线 / RL fall timeline |
| `figs/fig_ctrl_clean.png` / `.svg` | S3 | 黑白三环控制框图 / control cascade |
| `figs/fig9_run.png` | S4 | 40 s 轨迹 / 40 s trajectory |
| `figs/fig_t3_torque.png` | S4 | 力矩曲线 / torque trace |
| `figs/fig_f4_cosh.png` | S2·S | cosh 倾覆曲线 / tipping curve |

---

*文档结束 / End of document*
