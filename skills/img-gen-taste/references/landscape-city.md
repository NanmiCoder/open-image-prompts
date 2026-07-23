# 风景与城市风格卡 / Landscape and City Style Cards

仅从 `oip-visual-v2` 已配对图片语料中蒸馏。参考图证明语料中存在该视觉语法，不代表模板已经通过生成盲测。

## 目录

- `landscape-golden-hour-wilderness`：荒野黄金时刻电影风景
- `city-retro-neon-rain`：雨夜复古霓虹城市
- `city-tilt-shift-miniature`：移轴微缩城市

## landscape-golden-hour-wilderness

- **中文名 / English name：** 荒野黄金时刻电影风景 / Golden-Hour Cinematic Wilderness
- **触发：** 用户需要山地、旷野、湖泊、乡间道路或自然旅行画面呈现安静、辽阔、可进入的电影感。
- **不适用：** 产品广告、城市地标海报、奇幻巨构、需要人物占据主要画面的任务。
- **视觉 DNA：** 地形和光共同讲故事；前景提供可触摸的自然纹理，中景形成路径，低角度暖光穿过薄雾，把视线带向远处，而不是依靠夸张天空制造震撼。
- **构图、光色与材质：** 宽画幅或竖幅远景；三分构图；前、中、远三层清楚；暖金光与略冷阴影；岩石、草地、水面和空气透视保留真实细节。
- **边界：** 可替换地貌、季节、天气和写实或轻绘画媒介；必须保持自然地形为主体、单一低角度光源、可读空间层次和克制色彩。若城市、产品或巨型角色成为最高对比主体，应改用其他卡。
- **反模式：** 全图橙黄、假 HDR 光晕、太阳正中、云层抢主体、所有景物同等锐利、随意加入人物或建筑、只有壁纸感而没有通向远方的视觉路径。
- **模板：**

```text
Cinematic wilderness landscape of {NATURAL LOCATION}, a tactile foreground of {ROCK / GRASS / WATER / WILDFLOWERS} leading through a readable midground path toward {DISTANT LANDFORM}, low golden-hour light entering from one side, restrained warm highlights and slightly cool shadows, thin atmospheric haze separating three depth layers, believable geology and vegetation, calm expansive mood, no hero product, no oversized figure, no text, no orange wash, no artificial HDR halo.
```

- **真实参考：**
  - `tweet_id: 2031792321885585825` — `images/2031792321885585825/1.jpg`
  - `tweet_id: 2075201271481430473` — `images/2075201271481430473/1.jpg`
  - `tweet_id: 2077271949474959754` — `images/2077271949474959754/1.jpg`
- **validation_status:** corpus-reviewed / generation-pending

## city-retro-neon-rain

- **中文名 / English name：** 雨夜复古霓虹城市 / Retro Neon Rain City
- **触发：** 用户需要雨夜街道、音乐视觉、电影环境或复古未来城市呈现潮湿、孤独、霓虹驱动的都市氛围。
- **不适用：** 人物肖像、明亮商业街纪实、白天城市规划图、要求准确复刻现实店招和建筑的任务。
- **视觉 DNA：** 城市环境而非人物是主角；一到两组霓虹色通过湿路、玻璃和薄雾反复出现，深色建筑和街道形成安静的负空间，少量车辆或行人只负责尺度和叙事。
- **构图、光色与材质：** 街面或小巷的宽景；青绿、洋红或钨丝暖色组成受控互补色；雨水在沥青上形成纵深反射；远处标牌逐渐虚化，黑位仍保留建筑层次。
- **边界：** 可替换年代、城市、车辆和行人；必须保持城市环境占主导、湿表面响应、有限霓虹色、深浅空间层次。若人物面部成为焦点，改用霓虹人像卡；若满画面飞车和义体成为核心，改用赛博科幻卡。
- **反模式：** 每块墙都塞满招牌、红蓝机械对半、所有颜色饱和到顶、路面像镜子、乱码文字占据主体、随意增加飞行汽车、黑位堵死、没有雨雾深度。
- **模板：**

```text
Wide cinematic night view of {RETRO URBAN STREET / NARROW ALLEY}, rain-darkened asphalt and shallow puddles carrying elongated reflections from only {COLOR 1} and {COLOR 2} neon sources, deep layered shopfronts and distant city structures, light rain and restrained steam revealing depth, one small {PARKED CAR / WALKING FIGURE} for scale, nostalgic retro-future atmosphere, readable shadow detail, environment remains the hero, no neon clutter, no random flying cars, no prominent text, no portrait framing.
```

- **真实参考：**
  - `tweet_id: 2034533564293767647` — `images/2034533564293767647/1.jpg`
  - `tweet_id: 2041089151886639180` — `images/2041089151886639180/1.jpg`
- **validation_status:** corpus-reviewed / generation-pending

## city-tilt-shift-miniature

- **中文名 / English name：** 移轴微缩城市 / Tilt-Shift Miniature City
- **触发：** 用户需要城市、地标或旅行视觉呈现真实摄影般的玩具尺度、模型感和俯瞰趣味。
- **不适用：** 正交信息图、等距 3D 城市、严肃建筑记录、需要整幅建筑都处于同一焦平面的画面。
- **视觉 DNA：** 真实城市几何被窄焦平面压缩成微缩模型；道路、桥梁和人流保持可信尺度，选择性清晰区域引导视线，其余区域自然过渡到光学虚化。
- **构图、光色与材质：** 高机位或航拍三分之四视角；窄而连续的对焦带；前后景渐进虚化；暖暮色或蓝调城市灯光；建筑、车辆和人物比例一致。
- **边界：** 可替换城市、地标、时间和旅行海报容器；必须保留摄影式透视、窄焦平面、可信城市比例和高机位。等距视图、正交投影或每栋建筑同样清晰属于 3D 微缩图解，不属于此卡。
- **反模式：** 径向后期假模糊、主体也失焦、人物和汽车比例混乱、道路断裂、建筑融化、正交等距视角、把整个城市做成塑料玩具、无意义的大字覆盖地标。
- **模板：**

```text
High-angle tilt-shift photograph of {CITY OR LANDMARK}, viewed from an elevated three-quarter position, one narrow continuous focus plane crossing {PRIMARY ROAD / BRIDGE / LANDMARK}, foreground and distant skyline falling into gradual optical blur, tiny pedestrians and vehicles at consistent believable scale, warm dusk or blue-hour practical lights, realistic architecture and road connections, playful miniature impression created by optics rather than toy materials, no isometric projection, no radial blur, no warped buildings, no oversized text.
```

- **真实参考：**
  - `tweet_id: 2035556384897647058` — `images/2035556384897647058/1.jpg`
  - `tweet_id: 2061856347940082026` — `images/2061856347940082026/1.jpg`
  - `tweet_id: 2065623612170911996` — `images/2065623612170911996/1.jpg`
- **validation_status:** corpus-reviewed / generation-pending
