# 产品广告风格卡 / Product Advertising Style Cards

仅从 `oip-visual-v2` 已配对图片语料中蒸馏。参考图证明语料中存在该视觉语法，不代表模板已经通过生成盲测。

## 目录

- `product-elemental-dark-luxury`：暗黑元素奢侈品
- `product-white-gallery-high-key`：白色画廊高键产品
- `product-kinetic-splash`：动态液体爆破
- `product-as-world-surrealism`：产品即世界
- `product-exploded-identity`：爆炸结构与切面剧场
- `product-midnight-automotive`：午夜高性能汽车
- `product-precision-macro`：微距机械与贵金属

## product-elemental-dark-luxury

- **中文名 / English name：** 暗黑元素奢侈品 / Elemental Dark Luxury
- **触发：** 用户要求香氛、酒、护肤、饮料或精密产品呈现克制、深色、电影式的高级广告质感。
- **不适用：** 电商白底主图、童趣产品、需要完整说明书或多 SKU 对比的画面。
- **选择边界：** 若用户只要求“纯黑背景、瓶子清楚”，先给克制的黑色棚拍方案；湿石、水或烟雾属于需要用户明确选择的环境隐喻，不应自动添加。
- **视觉 DNA：** 单一英雄产品从水、湿石、烟雾或琥珀液体中浮现；环境只表达一种材质隐喻，产品身份始终清楚。
- **构图、光色与材质：** 4:5；产品占画面约 45–60%；低机位或轻微斜置；黑底配单一暖金或冷蓝边缘光；玻璃、湿石、磨砂金属保留物理反射和微瑕疵。
- **边界：** 可替换产品、元素介质和单一强调色；必须保持一个英雄产品、一种视觉隐喻、低键光和可读的产品轮廓。
- **反模式：** 堆满花果、廉价金光、标签变形、多个产品抢主体、黑位堵死、粒子覆盖产品。
- **模板：**

```text
4:5 premium product campaign for {PRODUCT}, one hero object emerging from {WET ROCK / DARK WATER / AMBER LIQUID}, low-key black environment, one controlled {WARM GOLD / COOL BLUE} rim light, physically accurate glass, metal and material reflections, sparse atmospheric haze, restrained luxury, product occupies 55% of frame, sharp label area, no extra products, no fake text, no logo unless supplied.
```

- **真实参考：**
  - `tweet_id: 2032732267815321748` — `images/2032732267815321748/2.jpg`
  - `tweet_id: 2066991919654424779` — `images/2066991919654424779/3.jpg`
  - `tweet_id: 2066749658769367143` — `images/2066749658769367143/1.jpg`
- **validation_status:** corpus-reviewed / generation-pending
- **pilot_note:** A clean-black perfume trial favored the simpler studio direction. Do not add the elemental environment unless the user selects that richer option; this card remains generation-pending.

## product-white-gallery-high-key

- **中文名 / English name：** 白色画廊高键产品 / White Gallery High-Key
- **触发：** 用户要求护肤、香水、珠宝等产品干净、可信、留白充分，接近画廊陈列或高端电商广告。
- **不适用：** 需要强情绪夜景、动态爆炸、复杂场景叙事的广告。
- **视觉 DNA：** 白色空间由石材、手部、柔影或珠宝切面建立层次，不靠装饰堆砌制造高级感。
- **构图、光色与材质：** 居中或三分构图；白、象牙、浅灰；大面积柔光和细窄接触阴影；透明玻璃、皮肤、石材和贵金属边缘清晰。
- **边界：** 可变更承托物与轻量辅助元素；必须保持高键、低噪声、真实接触关系和大面积负空间。
- **反模式：** 纯白过曝、产品漂浮无接触、廉价塑料感、花瓣或蝴蝶喧宾夺主、文字乱码。
- **模板：**

```text
Minimal high-key gallery product photograph of {PRODUCT}, clean white-to-ivory seamless space, placed on {PALE STONE / PRECISE HAND POSE / SIMPLE PLINTH}, soft large-source light from upper left, delicate contact shadow, accurate translucent and metallic edges, generous negative space, quiet premium mood, no decorative clutter, no text or branding unless provided.
```

- **真实参考：**
  - `tweet_id: 2075686317984514102` — `images/2075686317984514102/1.jpg`
  - `tweet_id: 2039599784173195358` — `images/2039599784173195358/3.jpg`
  - `tweet_id: 2062144832471285937` — `images/2062144832471285937/1.jpg`
- **validation_status:** corpus-reviewed / generation-pending

## product-kinetic-splash

- **中文名 / English name：** 动态液体爆破 / Kinetic Splash
- **触发：** 用户要求饮料、果味食品或清洁产品具有新鲜、能量、速度和社交广告冲击力。
- **不适用：** 奢侈品静物、严肃医疗产品、需要安静可信感的电商主图。
- **视觉 DNA：** 冻结一个可读的动作瞬间；液体和原料沿统一轨迹围绕产品运动，而不是随机爆炸。
- **构图、光色与材质：** 产品稳定居中；液体形成 S 形、环形或冠状；高快门硬边配液滴背光；色彩来自口味，背景只用一到两种对比色。
- **边界：** 可替换液体、配料和轨迹；必须保留稳定英雄产品、单一运动方向、可读包装和可信黏度。
- **反模式：** 泥状液体、随机水果雨、包装被遮住、卡通泡沫、脏乱飞溅、所有元素同等清晰。
- **模板：**

```text
High-speed commercial shot of {BEVERAGE OR FOOD PRODUCT}, stable centered hero, one coherent {ARC / S-CURVE / CROWN} splash describing motion around, not over, the package, only {2-3 INGREDIENTS} in controlled trajectories, crisp backlit droplets, saturated flavor color against {CONTRAST BACKGROUND}, realistic viscosity and condensation, label unobstructed, no random debris, no fake typography.
```

- **真实参考：**
  - `tweet_id: 2033160192515264889` — `images/2033160192515264889/1.jpg`
  - `tweet_id: 2034560008923599196` — `images/2034560008923599196/1.jpg`
  - `tweet_id: 2073830761359372552` — `images/2073830761359372552/1.jpg`
- **validation_status:** corpus-reviewed / generation-pending

## product-as-world-surrealism

- **中文名 / English name：** 产品即世界 / Product-as-World Surrealism
- **触发：** 用户希望产品广告有一个清楚、能一句话说完的超现实视觉隐喻。
- **不适用：** 精确电商展示、结构说明、必须完全写实的合规广告。
- **视觉 DNA：** 产品尺度或结构变成一个微型世界；微型人物和环境只提供尺度，产品仍能被立即识别。
- **构图、光色与材质：** 中心视觉清晰；微型人物低权重；现实产品材质与超现实环境无缝连接；全画面只有一个统一光源。
- **边界：** 可替换产品和隐喻；必须只有一个核心概念，并保持产品轮廓、材质与品牌区域完整。
- **反模式：** 同时讲多个概念、玩具模型感、人物过多、产品身份消失、明显拼贴接缝。
- **模板：**

```text
Surreal premium campaign where {PRODUCT} literally becomes {ONE VISUAL METAPHOR}, product identity and silhouette remain instantly readable, tiny environmental details provide scale, seamless transition between real product materials and the imagined world, single light direction, cinematic depth, one clear idea only, no collage seams, no unrelated props, no explanatory text.
```

- **真实参考：**
  - `tweet_id: 2066476393047937147` — `images/2066476393047937147/1.jpg`
  - `tweet_id: 2077768467663527956` — `images/2077768467663527956/1.jpg`
- **validation_status:** corpus-reviewed / generation-pending

## product-exploded-identity

- **中文名 / English name：** 爆炸结构与切面剧场 / Exploded Identity
- **触发：** 用户需要解释产品内部结构、设计秩序或性能，把技术信息做成高级广告。
- **不适用：** 没有明确结构的软性产品、人物肖像、只要求氛围而不关心工程可信度的画面。
- **视觉 DNA：** 拆解解释功能和层级；零件沿明确工程轴排列，核心部件是最高视觉对比。
- **构图、光色与材质：** 正交或轻微三分之四视角；白底偏技术说明，黑底偏高级广告；零件间距均匀，材料区分准确。
- **边界：** 可在爆炸图和切面舞台之间选择；必须保持轴线、零件层级、原产品轮廓和结构可信性。
- **反模式：** 随机炸飞零件、机械结构错误、主体轮廓不可辨、部件间距混乱、注释乱码。
- **模板：**

```text
Precision exploded-view campaign of {PRODUCT}, outer shell and functional components separated along one clear engineering axis, exact alignment and believable part hierarchy, hero core highlighted, {WHITE TECHNICAL STUDIO / BLACK PREMIUM STAGE}, orthographic three-quarter view, controlled spacing, material-accurate metal, plastic and glass, no random fragments, no illegible annotations.
```

- **真实参考：**
  - `tweet_id: 2071674030998933562` — `images/2071674030998933562/1.jpg`
  - `tweet_id: 2039274904843960366` — `images/2039274904843960366/1.jpg`
  - `tweet_id: 2073026525243310084` — `images/2073026525243310084/4.jpg`
- **validation_status:** corpus-reviewed / generation-pending

## product-midnight-automotive

- **中文名 / English name：** 午夜高性能汽车 / Midnight Performance Automotive
- **触发：** 用户要求跑车、摩托或交通工具呈现性能、阶层感和电影式夜景广告。
- **不适用：** 二手车记录照、家庭生活方式汽车图、需要展示全套内饰功能的目录页。
- **视觉 DNA：** 车身轮廓、地面接触、连续曲面反射与环境尺度共同表达性能，不依赖过量霓虹。
- **构图、光色与材质：** 低机位三分之四前视；车占 55–70%；冷蓝夜景配少量暖光，或纯白设计实验室；轮胎必须接地。
- **边界：** 可替换夜港、湿路、实验室；必须保留真实车辆几何、连续车漆高光、地面接触和单一英雄车辆。
- **反模式：** 车辆漂浮、轮毂变形、雨夜霓虹过量、环境抢主体、海报文字压住车身。
- **模板：**

```text
Premium automotive campaign for {VEHICLE}, low three-quarter hero angle, body fills 65% of frame, grounded tires and physically continuous reflections across painted metal, {MIDNIGHT HARBOR / WET MOUNTAIN ROAD / WHITE DESIGN LAB}, restrained cool palette with one warm accent, believable scale and road contact, no motion-streak clutter, no fake badge or typography.
```

- **真实参考：**
  - `tweet_id: 2053355587170181319` — `images/2053355587170181319/4.jpg`
  - `tweet_id: 2059599866527887656` — `images/2059599866527887656/4.jpg`
  - `tweet_id: 2077763527826379111` — `images/2077763527826379111/1.jpg`
- **validation_status:** corpus-reviewed / generation-pending

## product-precision-macro

- **中文名 / English name：** 微距机械与贵金属 / Precision Macro Horology
- **触发：** 用户希望手表、珠宝、相机或精密器件通过结构精度和真实材料表现高级感。
- **不适用：** 需要完整产品全貌、多人生活方式、低成本促销海报的任务。
- **视觉 DNA：** 高级感来自机械精度、表面纹理与受控反射，焦点只落在一个最重要的结构或连接处。
- **构图、光色与材质：** 微距或极近景；浅而可信的焦平面；侧光揭示拉丝、抛光、宝石切面、皮革颗粒和微小使用痕迹。
- **边界：** 可替换精密对象和重点结构；必须保持精确几何、物理景深、克制配色和可读材质差异。
- **反模式：** 全画面锐利、宝石塑料感、机械齿轮不咬合、镜面爆白、后期假糊、装饰性假齿轮。
- **模板：**

```text
Extreme macro product portrait of {WATCH / JEWELRY / PRECISION OBJECT}, focus locked on {KEY MECHANISM / GEM FACET / MATERIAL JOIN}, shallow but physically plausible depth of field, narrow side light revealing brushed metal, polished edges and microscopic imperfections, restrained charcoal-and-{ACCENT} palette, exact geometry, no decorative fantasy gears, no blown highlights.
```

- **真实参考：**
  - `tweet_id: 2033001740891730149` — `images/2033001740891730149/1.jpg`
  - `tweet_id: 2038078836198510651` — `images/2038078836198510651/1.jpg`
  - `tweet_id: 2066129525784694882` — `images/2066129525784694882/1.jpg`
- **validation_status:** corpus-reviewed / generation-pending
