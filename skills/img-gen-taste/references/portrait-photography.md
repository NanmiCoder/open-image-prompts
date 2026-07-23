# 人像、时尚与生活方式风格卡 / Portrait, Fashion and Lifestyle Style Cards

仅从 `oip-visual-v2` 已配对图片语料中蒸馏。参考图证明语料中存在该视觉语法，不代表模板已经通过生成盲测。

## 目录

- `portrait-quiet-luxury-studio`：安静奢华柔光棚拍
- `portrait-graphic-hard-shadow`：硬影几何时尚
- `portrait-skin-first-beauty`：皮肤优先美妆近景
- `portrait-neon-rain-cinematic`：雨夜霓虹电影人像
- `portrait-analog-golden-lifestyle`：Portra 金色日常
- `portrait-direct-flash-after-hours`：直闪夜生活快照
- `portrait-monochrome-sculptural`：黑白雕塑式编辑人像

## portrait-quiet-luxury-studio

- **中文名 / English name：** 安静奢华柔光棚拍 / Quiet Luxury Studio
- **触发：** 用户需要克制、可信、松弛的品牌人像、职场人像或时装编辑图。
- **不适用：** 霓虹夜景、强运动、夸张舞台妆、需要喧闹促销感的任务。
- **视觉 DNA：** 中性色衣物、自然姿态和少量道具；高级感来自人物松弛、衣料垂坠和背景细微色阶。
- **构图、光色与材质：** 眼平，中景或全身；米白、灰褐、炭灰；大窗式柔侧光；羊毛、棉麻、皮革和自然皮肤纹理清楚。
- **边界：** 可替换人物、衣装和单件座椅；必须保持低噪声、中性色、自然姿态和柔和方向光。
- **反模式：** 强行奢华布景、皮肤磨平、姿势僵硬、配饰堆砌、背景纯平无层次。
- **模板：**

```text
Quiet-luxury editorial portrait of {SUBJECT} wearing {SIMPLE TEXTURED OUTFIT}, relaxed asymmetrical pose on {STOOL / CHAIR / BARE STUDIO FLOOR}, seamless {WARM GRAY / IVORY / CHARCOAL} backdrop, broad soft window-like side light, natural skin texture, visible fabric drape, calm direct or off-camera gaze, restrained styling, no glamour props, no plastic skin.
```

- **真实参考：**
- **validation_status:** corpus-reviewed / generation-pending

## portrait-graphic-hard-shadow

- **中文名 / English name：** 硬影几何时尚 / Graphic Hard-Shadow Fashion
- **触发：** 用户要求时装图像具有杂志封面式的平面冲击、清晰轮廓和几何影子。
- **不适用：** 柔和生活方式、儿童人像、需要自然环境光连续性的纪实场景。
- **视觉 DNA：** 人物和硬影共同构成图形；姿势的外轮廓与投影关系比布景复杂度更重要。
- **构图、光色与材质：** 高位或正侧单点硬光；墙面或地面形成明确投影；服装控制在一到两色；可用俯拍强化图形。
- **边界：** 可调整视角、背景色和姿态；必须保留单一硬光、可读外轮廓、克制服装和明确影子。
- **反模式：** 多光源冲淡影子、服装花纹过多、手脚与影子粘连、背景杂乱、姿势没有清楚外轮廓。
- **模板：**

```text
Graphic fashion editorial of {SUBJECT} in {ONE-COLOR SILHOUETTE OUTFIT}, posed to create a clean readable body contour, one hard directional light casting a deliberate geometric shadow onto {WALL / FLOOR}, minimal {COLOR} studio, high contrast with preserved skin detail, composition designed as shape plus shadow, no fill-light clutter, no overlapping limbs.
```

- **真实参考：**
- **validation_status:** corpus-reviewed / generation-pending

## portrait-skin-first-beauty

- **中文名 / English name：** 皮肤优先美妆近景 / Skin-First Beauty
- **触发：** 用户需要护肤、美妆、首饰或人物面部的高级特写，强调真实皮肤和精确眼神。
- **不适用：** 全身时尚、复杂环境叙事、需要人物动作和场景关系的画面。
- **视觉 DNA：** 眼神、皮肤微纹理和一个局部妆容或色彩记忆点构成画面，不以配饰数量制造高级感。
- **构图、光色与材质：** 近景或极近景，85mm 感；前侧柔光包裹面部，眼睛必须锐利；肤色自然，妆面只突出一个色域。
- **边界：** 可替换妆面、珠宝或植物色素；必须保持眼睛主焦点、真实皮肤、干净背景和克制高光。
- **反模式：** 瓷娃娃皮肤、睫毛和发丝熔化、双眼焦点不一致、珠宝花卉过量、全脸都在发光。
- **模板：**

```text
Extreme beauty portrait of {SUBJECT}, eyes as the primary focal point, 85mm close framing, broad feathered key light with gentle falloff, real pores, peach fuzz and fine skin variation preserved, one restrained beauty accent {GLOSS / GOLD FLECK / BOTANICAL PIGMENT}, clean background, precise catchlights, no skin smoothing, no over-sharpening, no accessory clutter.
```

- **真实参考：**
- **validation_status:** corpus-reviewed / generation-pending

## portrait-neon-rain-cinematic

- **中文名 / English name：** 雨夜霓虹电影人像 / Neon Rain Cinematic
- **触发：** 用户要求都市夜景、音乐视觉、科幻时尚或电影角色人像具有湿润、情绪化的霓虹氛围。
- **不适用：** 真实企业头像、白底证件照、日光生活方式和不允许强色光的肤色广告。
- **视觉 DNA：** 冷暖双色由环境光源驱动；湿润皮肤、衣料、城市反射和克制情绪共同构成电影感。
- **构图、光色与材质：** 近景或中近景；青蓝环境光加窄洋红边光；背景霓虹化成柔焦色块；脸部暗区保留细节。
- **边界：** 可替换城市、工坊和服装；必须保持物理光源逻辑、湿表面响应、深黑层次和单一情绪。
- **反模式：** 面部机械红蓝对半、所有霓虹都清晰、随意增加义体、饱和度顶满、皮肤塑料感。
- **模板：**

```text
Cinematic night portrait of {SUBJECT} on a rain-darkened {CITY STREET / WORKSHOP}, close to medium framing, cool cyan ambient light and a narrow magenta rim from physically motivated signs, wet skin, hair or leather catching selective highlights, soft neon bokeh behind, emotionally restrained gaze, deep blacks with facial detail, no symmetrical red-blue split, no generic cyber implants.
```

- **真实参考：**
- **validation_status:** corpus-reviewed / generation-pending
- **pilot_note:** A directional rainy-neon portrait trial favored this card over a generic rewrite, but restraint varied and the card remains generation-pending.

## portrait-analog-golden-lifestyle

- **中文名 / English name：** Portra 金色日常 / Analog Golden Lifestyle
- **触发：** 用户需要咖啡馆、花园、街道、旅行或日常人物呈现自然、亲近、像朋友抓拍的胶片气质。
- **不适用：** 严格棚拍、冷色科技广告、需要极高快门和锐利动作冻结的画面。
- **视觉 DNA：** 轻微不完美构图、暖肤色、环境空气感和人物正在做的小动作，形成被观察而不是被安排的瞬间。
- **构图、光色与材质：** 35mm 或中画幅模拟；三分构图或轻微倾斜；逆光金边、阴影略青；细颗粒，避免橙色滤镜。
- **边界：** 可替换地点、动作和服装；必须保留环境可读性、非居中自然构图、胶片色彩和真实日光方向。
- **反模式：** 每张都正中摆拍、夕阳过曝、全图橙黄、虚假漏光、背景被压成摄影棚。
- **模板：**

```text
Candid analog lifestyle photograph of {SUBJECT DOING SIMPLE ACTION} at {CAFE / GARDEN / STREET}, late-afternoon backlight, organic off-center framing as if observed rather than posed, Contax and Kodak Portra color response, warm skin with slightly cool shadows, fine natural grain, subtle lens softness at edges, environment still readable, no fake light leaks, no orange wash.
```

- **真实参考：**
- **validation_status:** corpus-reviewed / generation-pending

## portrait-direct-flash-after-hours

- **中文名 / English name：** 直闪夜生活快照 / Direct-Flash After Hours
- **触发：** 用户需要便利店、街边餐馆、酒吧或派对时尚图具有生猛、偶然但仍可控的即时感。
- **不适用：** 正式企业肖像、柔和婚礼人像、要求皮肤极度温润的美妆广告。
- **视觉 DNA：** 机顶硬闪把人物从夜间环境中切出；偶然构图与设计好的姿势、色彩和环境曝光同时存在。
- **构图、光色与材质：** 28–35mm；眼平或虫眼；硬闪近影，环境招牌和实用灯仍可见；皮肤、金属和亮片保留局部高光。
- **边界：** 可替换地点、服装和相机角度；必须保留直接闪光、环境曝光、真实皮肤和轻微不完美裁切。
- **反模式：** 把随手拍做成低清图、闪光过曝脸、背景全黑、广角脸严重变形、夜景只剩噪点。
- **模板：**

```text
After-hours direct-flash fashion snapshot of {SUBJECT} in {CONVENIENCE STORE / STREET CAFE / BAR}, 28-35mm handheld framing, decisive on-camera flash with crisp near shadow, ambient signage and practical lights still visible, slightly imperfect crop and candid posture, real skin and fabric texture, controlled highlight rolloff, no blown face, no empty black background, no artificial motion blur.
```

- **真实参考：**
- **validation_status:** corpus-reviewed / generation-pending

## portrait-monochrome-sculptural

- **中文名 / English name：** 黑白雕塑式编辑人像 / Monochrome Sculptural Editorial
- **触发：** 用户需要时装、艺术家肖像或封面图通过轮廓、留白和灰阶呈现冷静、雕塑般的形体感。
- **不适用：** 依赖彩色产品、节庆氛围、自然日常纪实或需要明确地点色彩的任务。
- **视觉 DNA：** 黑白用于组织人物、衣物、动物或建筑之间的形体关系，而不是简单去色。
- **构图、光色与材质：** 黑白或极低饱和；一个软主光加窄边光；大面积负空间；黑衣和黑发保留内部褶皱与分离层次。
- **边界：** 可替换人物、服装和极简场景；必须保持完整灰阶、清楚轮廓、负空间和材质细节。
- **反模式：** 死黑无细节、简单去色、背景与头发粘连、肤色像灰泥、姿势像证件照。
- **模板：**

```text
Monochrome sculptural editorial portrait of {SUBJECT}, minimal architectural or seamless setting, body and garment arranged as one strong silhouette, large negative space, soft directional key plus a narrow separation edge, full tonal range from textured blacks to clean highlights, restrained expression, no crushed fabric detail, no flat grayscale conversion, no unnecessary props.
```

- **真实参考：**
- **validation_status:** corpus-reviewed / generation-pending
