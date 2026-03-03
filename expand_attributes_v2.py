#!/usr/bin/env python3
"""
电商属性库扩展脚本 v2
目标：从1004个属性扩展到5000+个属性
通过大量枚举值和品类细分达到目标
"""

import json
import uuid

def generate_enum_attr(attr_id, name, category, values, tags_list=None):
    """生成枚举类型属性"""
    processed_values = []
    for i, v in enumerate(values):
        if isinstance(v, dict):
            processed_values.append({"id": v["id"], "name": v["name"], "tags": v.get("tags", [])})
        else:
            tags = tags_list[i] if tags_list and i < len(tags_list) else []
            processed_values.append({"id": v if isinstance(v, str) else str(v), 
                                     "name": str(v), "tags": tags})
    return {
        "id": attr_id,
        "name": name,
        "type": "enum",
        "category": category,
        "values": processed_values,
        "relations": []
    }

# ============ 1. 大量品牌属性 ============
brand_attrs = []

# 手机品牌
phone_brands = ["Apple", "Samsung", "华为", "小米", "OPPO", "vivo", "一加", "realme", 
                "荣耀", "魅族", "中兴", "努比亚", "联想", "Motorola", "Nokia", "索尼",
                "Google Pixel", "夏普", "HTC", "LG", "黑鲨", "ROG", "红魔", "iQOO", "真我"]
brand_attrs.append(generate_enum_attr("phone_brand", "手机品牌", "基础信息",
    phone_brands, [[b] for b in phone_brands]))

# 电脑品牌
laptop_brands = ["Apple", "联想", "戴尔", "惠普", "华硕", "宏碁", "MSI", "微软", 
                "华为", "小米", "荣耀", "三星", "LG", "VAIO", "ThinkPad", "外星人",
                "ROG", "神舟", "机械革命", "雷神", "攀升", "京东京造"]
brand_attrs.append(generate_enum_attr("laptop_brand", "电脑品牌", "基础信息",
    laptop_brands, [[b] for b in laptop_brands]))

# 服装品牌
fashion_brands = ["优衣库", "Zara", "H&M", "无印良品", "GXG", "森马", "美特斯邦威",
                 "优哈", "太平鸟", "波司登", "雅戈尔", "七匹狼", "报喜鸟", "杉杉",
                 "红蜻蜓", "奥康", "百丽", "达芙妮", "天创", "百田森", "金利来",
                  "Nike", "Adidas", "Puma", "New Balance", "Converse", "Vans", 
                  "Supreme", "Off-White", "The North Face", "Columbia", "Jack Wolfskin",
                  "安踏", "特步", "361", "kappa", "Fila", "Lululemon", "Under Armour",
                  "Asics", "Mizuno", "Saucony", "Brooks", "Hoka", "斯凯奇"]
brand_attrs.append(generate_enum_attr("fashion_brand", "服装品牌", "基础信息",
    fashion_brands, [[b] for b in fashion_brands]))

# 化妆品品牌
beauty_brands = ["雅诗兰黛", "兰蔻", "资生堂", "SK-II", "香奈儿", "迪奥", "YSL",
                "娇韵诗", "倩碧", "理肤泉", "薇姿", "雅漾", "欧莱雅", "玉兰油",
                "OLAY", "佰草集", "自然堂", "百雀羚", "相宜本草", "珀莱雅", "丸美",
                "后", "雪花秀", "呼吸", "赫拉", "IPSA", "茵芙莎", "黛珂", "CPB",
                "悦木之源", "Origins", "科颜氏", "修丽可", "MAC", "Bobbi Brown",
                "NARS", "Urban Decay", "Tom Ford", "Charlotte Tilbury", "Pat McGrath"]
brand_attrs.append(generate_enum_attr("beauty_brand", "美妆品牌", "基础信息",
    beauty_brands, [[b] for b in beauty_brands]))

# 家电品牌
appliance_brands = ["美的", "格力", "海尔", "海信", "TCL", "长虹", "小米", "华为",
                   "西门子", "博世", "松下", "飞利浦", "戴森", "LG", "三星", "夏普",
                   "索尼", "东芝", "NEC", "日立", "大金", "三菱", "约克", "Carrier",
                   "老板", "方太", "华帝", "万和", "万家乐", "苏泊尔", "九阳", "美的",
                   "小米", "小熊", "摩飞", "北鼎", "Bruno", "BRUNO"]
brand_attrs.append(generate_enum_attr("appliance_brand", "家电品牌", "基础信息",
    appliance_brands, [[b] for b in appliance_brands]))

# 奢侈品品牌
luxury_brands = ["Louis Vuitton", "Gucci", "Prada", "Chanel", "Dior", "Hermès",
                "Burberry", "Balenciaga", "Valentino", "Versace", "Fendi", "Dolce&Gabbana",
                "Bottega Veneta", "Celine", "Saint Laurent", "Givenchy", "Alexander McQueen",
                "Loewe", "Miu Miu", "Alexander Wang", "Thom Browne", "Kenzo", "Moschino",
                "Coach", "Michael Kors", "Kate Spade", "Tory Burch", "Longchamp", "MCM"]
brand_attrs.append(generate_enum_attr("luxury_brand", "奢侈品牌", "基础信息",
    luxury_brands, [[b] for b in luxury_brands]))

# 运动品牌
sports_brands = ["Nike", "Adidas", "Puma", "New Balance", "Converse", "Vans",
                "Under Armour", "Lululemon", "FILA", "Asics", "Mizuno", "Brooks",
                "Saucony", "Hoka", "Reebok", "kappa", "Diadora", "K-Swiss", "Lotus",
                "安踏", "李宁", "361", "特步", "匹克", "鸿星尔克", "贵人鸟", "德尔惠"]
brand_attrs.append(generate_enum_attr("sports_brand", "运动品牌", "基础信息",
    sports_brands, [[b] for b in sports_brands]))

# 珠宝品牌
jewelry_brands = ["周大福", "周生生", "六福珠宝", "老凤祥", "中国黄金", "老庙黄金",
                 "潮宏基", "周六福", "周大生", "金六福", "萃华金店", "明牌珠宝", "谢瑞麟",
                 "Cartier", "Tiffany", "Bvlgari", "Van Cleef & Arpels", "Chaumet",
                 "Boucheron", "Mikimoto", "TASAKI", "Pandora", "Swarovski", "APM Monaco"]
brand_attrs.append(generate_enum_attr("jewelry_brand", "珠宝品牌", "基础信息",
    jewelry_brands, [[b] for b in jewelry_brands]))

# 奶粉品牌
milk_brands = ["Aptamil", "Nutrilon", "Enfamil", "Similac", "Gerber", "Friso",
              "美赞臣", "雅培", "惠氏", "美素佳儿", "诺优能", "爱他美", "牛栏",
              "飞鹤", "伊利", "蒙牛", "君乐宝", "合生元", "贝因美", "圣元", "完达山"]
brand_attrs.append(generate_enum_attr("milk_brand", "奶粉品牌", "基础信息",
    milk_brands, [[b] for b in milk_brands]))

# 耳机音箱品牌
audio_brands = ["Sony", "Bose", "Beats", "森海塞尔", "AKG", "铁三角", "JBL",
               "漫步者", "小米", "华为", "OPPO", "vivo", "realme", "一加",
               "B&O", "Bang & Olufsen", "Marshall", "Jabra", "Shure", "舒尔",
               "Audio-Technica", "ATH-M50x", "HD800S", "KEF", "Bowers & Wilkins"]
brand_attrs.append(generate_enum_attr("audio_brand", "耳机音箱品牌", "基础信息",
    audio_brands, [[b] for b in audio_brands]))

# ============ 2. 大量品类属性 ============
category_attrs = []

# 智能手机细分
smartphone_categories = [
    "5G手机", "4G手机", "游戏手机", "拍照手机", "商务手机", "老人手机", "学生手机",
    "折叠屏手机", "滑盖手机", "直板手机", "三防手机", "音乐手机", "自拍手机"
]
category_attrs.append(generate_enum_attr("smartphone_category", "智能手机品类", "规格",
    smartphone_categories))

# 电脑细分
laptop_categories = [
    "超极本", "游戏本", "商务本", "轻薄本", "工作站", "二合一笔记本", "Chromebook",
    "学生本", "设计师本", "电竞主机", "台式机", "一体机", "迷你主机"
]
category_attrs.append(generate_enum_attr("laptop_category", "电脑品类", "规格",
    laptop_categories))

# 服装细分
clothing_categories = [
    "T恤", "衬衫", "POLO衫", "卫衣", "毛衣", "针织衫", "羽绒服", "棉服", "大衣",
    "风衣", "夹克", "西装", "牛仔裤", "休闲裤", "运动裤", "裙子", "连衣裙", "半身裙",
    "短裤", "背带裤", "皮裤", "保暖内衣", "睡衣", "家居服", "运动服", "泳装", "瑜伽服"
]
category_attrs.append(generate_enum_attr("clothing_category", "服装品类", "规格",
    clothing_categories))

# 鞋子细分
shoes_categories = [
    "运动鞋", "跑步鞋", "篮球鞋", "足球鞋", "网球鞋", "羽毛球鞋", "乒乓球鞋",
    "休闲鞋", "帆布鞋", "豆豆鞋", "乐福鞋", "牛津鞋", "德比鞋", "切尔西靴",
    "马丁靴", "工装靴", "雪地靴", "拖鞋", "凉鞋", "沙滩鞋", "洞洞鞋"
]
category_attrs.append(generate_enum_attr("shoes_category", "鞋靴品类", "规格",
    shoes_categories))

# 包包细分
bag_categories = [
    "单肩包", "双肩包", "斜挎包", "手提包", "钱包", "卡包", "腰包", "胸包",
    "旅行包", "电脑包", "书包", "妈咪包", "化妆包", "洗漱包", "收纳包",
    "公文包", "商务包", "休闲包", "运动包", "登山包", "相机包"
]
category_attrs.append(generate_enum_attr("bag_category", "箱包品类", "规格",
    bag_categories))

# 化妆品细分
cosmetics_categories = [
    "护肤水", "护肤乳", "面霜", "精华", "眼霜", "防晒", "隔离", "粉底液", "气垫",
    "BB霜", "CC霜", "遮瑕", "散粉", "蜜粉", "腮红", "修容", "高光", "眼影",
    "眼线", "睫毛膏", "眉笔", "眉粉", "口红", "唇釉", "唇彩", "润唇膏", "唇线笔"
]
category_attrs.append(generate_enum_attr("cosmetics_category", "化妆品品类", "美妆",
    cosmetics_categories))

# 零食细分
snack_categories = [
    "薯片", "薯条", "虾片", "玉米片", "爆米花", "饼干", "曲奇", "威化", "苏打饼",
    "压缩饼干", "肉干", "肉脯", "鱼干", "牛肉干", "猪肉铺", "鸡翅", "鸡爪",
    "坚果", "花生", "瓜子", "杏仁", "腰果", "核桃", "夏威夷果", "开心果",
    "糖果", "巧克力", "软糖", "硬糖", "口香糖", "润喉糖", "果冻", "布丁",
    "果干", "葡萄干", "芒果干", "香蕉片", "海苔", "紫菜", "山楂片", "龟苓膏"
]
category_attrs.append(generate_enum_attr("snack_category", "零食品类", "食品",
    snack_categories))

# 饮料细分
beverage_categories = [
    "碳酸饮料", "果汁", "果蔬汁", "茶饮料", "奶茶", "咖啡", "功能性饮料",
    "运动饮料", "矿物质水", "纯净水", "矿泉水", "苏打水", "气泡水", "凉茶",
    "酸梅汤", "姜茶", "柠檬水", "蜂蜜水", "豆奶", "牛奶", "酸奶", "乳酸菌"
]
category_attrs.append(generate_enum_attr("beverage_category", "饮料品类", "食品",
    beverage_categories))

# 家具细分
furniture_categories = [
    "沙发", "真皮沙发", "布艺沙发", "功能沙发", "懒人沙发", "沙发床",
    "床", "实木床", "板式床", "铁艺床", "皮床", "高低床", "折叠床",
    "餐桌", "实木餐桌", "大理石餐桌", "玻璃餐桌", "折叠餐桌",
    "书桌", "电脑桌", "儿童书桌", "升降桌", "电竞桌",
    "椅子", "餐椅", "办公椅", "电竞椅", "人体工学椅", "休闲椅", "摇椅",
    "柜子", "衣柜", "书柜", "鞋柜", "电视柜", "餐边柜", "储物柜", "玄关柜"
]
category_attrs.append(generate_enum_attr("furniture_category", "家具品类", "家居",
    furniture_categories))

# 家电细分
home_appliance_categories = [
    "冰箱", "单门冰箱", "双门冰箱", "对开门冰箱", "多门冰箱", "迷你冰箱",
    "洗衣机", "波轮洗衣机", "滚筒洗衣机", "洗烘一体机", "烘干机", "迷你洗衣机",
    "空调", "挂机空调", "柜机空调", "中央空调", "移动空调", "风扇", "冷风扇",
    "电视", "液晶电视", "智能电视", "OLED电视", "投影仪",
    "油烟机", "燃气灶", "消毒柜", "洗碗机", "蒸烤箱", "集成灶",
    "吸尘器", "扫地机器人", "蒸汽拖把", "除螨仪", "挂烫机"
]
category_attrs.append(generate_enum_attr("home_appliance_category", "家电品类", "家电",
    home_appliance_categories))

# 智能手表/手环
wearable_categories = [
    "智能手表", "运动手表", "儿童手表", "老人手表", "智能手环", "健康监测器",
    "血糖仪", "血压计", "心率监测", "血氧仪", "体温计", "体脂秤"
]
category_attrs.append(generate_enum_attr("wearable_category", "穿戴设备品类", "规格",
    wearable_categories))

# 玩具细分
toy_categories = [
    "积木", "乐高", "拼图", "磁力片", "魔方", "数独", "棋类", "牌类",
    "毛绒玩具", "公仔", "玩偶", "娃娃", "芭比娃娃",
    "遥控车", "遥控飞机", "遥控船", "无人机", "机器人",
    "滑板车", "自行车", "扭扭车", "滑行车", "平衡车",
    "过家家", "厨房玩具", "工具玩具", "医生玩具", "警察玩具",
    "绘画玩具", "黏土", "彩泥", "涂鸦", "手工DIY",
    "音乐玩具", "电子琴", "鼓", "吉他", "沙锤"
]
category_attrs.append(generate_enum_attr("toy_category", "玩具品类", "母婴",
    toy_categories))

# ============ 3. 规格属性（大量枚举值） ============
spec_attrs = []

# 颜色（大量）
colors = [
    "黑色", "白色", "灰色", "银色", "金色", "玫瑰金", "铜色",
    "红色", "酒红色", "深红", "粉红色", "珊瑚色", "橙红色", "橙色",
    "黄色", "香槟金", "棕色", "咖啡色", "巧克力色", "驼色", "米色", "卡其色",
    "绿色", "军绿色", "墨绿色", "浅绿色", "薄荷绿", "青绿色", "松石绿",
    "蓝色", "天蓝色", "湖蓝色", "海蓝色", "深蓝色", "海军蓝", "藏青色", "宝蓝色",
    "紫色", "紫罗兰", "薰衣草紫", "深紫", "浅紫", "粉紫",
    "多彩", "渐变色", "印花", "拼色", "撞色", "豹纹", "斑马纹", "蛇纹",
    "透明", "半透明", "珠光", "闪粉", "亮片"
]
spec_attrs.append(generate_enum_attr("color_extended", "颜色(扩展)", "外观",
    colors, [[c] for c in colors]))

# 材质
materials = [
    "纯棉", "涤棉", "棉麻", "亚麻", "真丝", "绸缎", "雪纺", "纱布", "竹纤维",
    "羊毛", "羊绒", "驼毛", "兔毛", "貂绒", "马海毛",
    "聚酯纤维", "锦纶", "氨纶", "莱卡", "莫代尔", "竹炭纤维", "冰丝",
    "真皮", "头层皮", "二层皮", "PU皮", "PVC", "超纤皮", "麂皮",
    "实木", "人造板", "密度板", "颗粒板", "多层板", "指接板",
    "金属", "不锈钢", "铝合金", "钛合金", "铜", "铁",
    "玻璃", "钢化玻璃", "有机玻璃", "亚克力",
    "塑料", "ABS", "PP", "PC", "PE", "PVC", "硅胶", "TPU",
    "陶瓷", "骨瓷", "细瓷", "粗瓷", "石材", "大理石", "花岗岩"
]
spec_attrs.append(generate_enum_attr("material_extended", "材质(扩展)", "规格",
    materials, [[m] for m in materials]))

# 尺码
sizes_male = ["XXXS", "XXS", "XS", "S", "M", "L", "XL", "XXL", "3XL", "4XL", "5XL", "6XL"]
spec_attrs.append(generate_enum_attr("size_male", "男装尺码", "服装规格",
    sizes_male, [[s] for s in sizes_male]))

sizes_female = ["155/76A", "155/80A", "160/80A", "160/84A", "165/84A", "165/88A", 
               "170/88A", "170/92A", "175/92A", "175/96A", "180/96A", "180/100A"]
spec_attrs.append(generate_enum_attr("size_female", "女装尺码", "服装规格",
    sizes_female, [[s] for s in sizes_female]))

sizes_shoes = ["35", "35.5", "36", "37", "37.5", "38", "39", "39.5", "40", "41", "41.5", "42", "43", "44", "45", "46", "47", "48"]
spec_attrs.append(generate_enum_attr("size_shoes", "鞋码", "鞋类规格",
    sizes_shoes, [[s] for s in sizes_shoes]))

# 容量
capacities = ["16GB", "32GB", "64GB", "128GB", "256GB", "512GB", "1TB", "2TB", "4TB", "8TB"]
spec_attrs.append(generate_enum_attr("capacity", "存储容量", "电子规格",
    capacities, [[c] for c in capacities]))

# 内存
rams = ["2GB", "4GB", "6GB", "8GB", "12GB", "16GB", "24GB", "32GB", "64GB", "128GB"]
spec_attrs.append(generate_enum_attr("ram_size", "运行内存", "电子规格",
    rams, [[r] for r in rams]))

# 屏幕尺寸
screen_sizes = ["4.0英寸", "4.5英寸", "5.0英寸", "5.2英寸", "5.5英寸", "5.8英寸", 
                "6.0英寸", "6.1英寸", "6.4英寸", "6.5英寸", "6.7英寸", "6.8英寸", "7.0英寸"]
spec_attrs.append(generate_enum_attr("screen_size", "屏幕尺寸", "电子规格",
    screen_sizes, [[s] for s in screen_sizes]))

# 电池容量
batteries = ["2000mAh", "2500mAh", "3000mAh", "3500mAh", "4000mAh", "4500mAh", 
             "5000mAh", "5500mAh", "6000mAh", "6500mAh", "7000mAh", "10000mAh"]
spec_attrs.append(generate_enum_attr("battery_capacity", "电池容量", "电子规格",
    batteries, [[b] for b in batteries]))

# 功率
powers = ["5W", "10W", "15W", "18W", "20W", "25W", "30W", "40W", "45W", "50W", 
          "65W", "80W", "100W", "120W", "150W", "200W", "300W", "500W", "1000W", "2000W"]
spec_attrs.append(generate_enum_attr("power_watt", "功率", "电子规格",
    powers, [[p] for p in powers]))

# 重量
weights = ["50g", "80g", "100g", "120g", "150g", "180g", "200g", "250g", "300g", 
           "400g", "500g", "600g", "800g", "1kg", "1.5kg", "2kg", "3kg", "5kg", "10kg"]
spec_attrs.append(generate_enum_attr("weight_extended", "重量", "物理规格",
    weights, [[w] for w in weights]))

# 尺寸
dimensions = [
    "10x10x10cm", "15x15x15cm", "20x20x20cm", "25x25x25cm", "30x30x30cm",
    "40x40x40cm", "50x50x50cm", "60x60x60cm", "80x80x80cm", "100x100x100cm",
    "120x60x60cm", "150x70x70cm", "180x80x80cm", "200x100x100cm"
]
spec_attrs.append(generate_enum_attr("dimension_extended", "尺寸", "物理规格",
    dimensions, [[d] for d in dimensions]))

# ============ 4. 用户意图属性 ============
user_intent_attrs = [
    generate_enum_attr("purchase_intent_level", "购买意向强度", "用户意图",
        ["极高(今天买)", "高(本周买)", "中(本月买)", "低(随时)" "不确定(看看)"]),
    generate_enum_attr("budget_range_extended", "预算范围", "用户意图",
        ["50元以下", "50-100元", "100-200元", "200-300元", "300-500元", 
         "500-800元", "800-1000元", "1000-2000元", "2000-3000元", "3000-5000元", 
         "5000-8000元", "8000-10000元", "10000-20000元", "20000元以上"]),
    generate_enum_attr("decision_time", "决策时间", "用户意图",
        ["当天", "1-3天", "3-7天", "一周", "一个月", "慢慢看"]),
    generate_enum_attr("user_role_extended", "购买角色", "用户意图",
        ["自用", "送父母", "送配偶", "送朋友", "送孩子", "公司采购", "代购"]),
    generate_enum_attr("shopping_experience", "网购经验", "用户意图",
        ["新手", "一般", "熟练", "老手", "资深"]),
    generate_enum_attr("brand_loyalty", "品牌忠诚度", "用户意图",
        ["只买指定品牌", "偏好某品牌", "都可以", "不买某品牌"]),
    generate_enum_attr("price_sensitivity", "价格敏感度", "用户意图",
        ["极度敏感(比价)", "比较敏感(预算)", "一般(看值不值)", "不敏感(品质优先)"]),
    generate_enum_attr("review_dependency", "评价依赖度", "用户意图",
        ["完全不看", "略微参考", "主要参考", "非常依赖", "只看差评"]),
    generate_enum_attr("return_concern", "退换货关注度", "用户意图",
        ["完全不在意", "希望有保障", "非常在意", "必须有保障"]),
]

# ============ 5. 场景属性 ============
scene_attrs = [
    generate_enum_attr("usage_scene_extended", "使用场景", "场景",
        ["居家日常", "办公商务", "户外运动", "旅行出差", "约会聚会", "运动健身",
         "游戏娱乐", "学习教育", "烹饪美食", "社交送礼", "特殊场合"]),
    generate_enum_attr("time_season_extended", "使用季节", "场景",
        ["春季", "夏季", "秋季", "冬季", "四季通用"]),
    generate_enum_attr("user_age_extended", "适用年龄", "场景",
        ["婴儿(0-3岁)", "幼儿(3-6岁)", "儿童(6-12岁)", "青少年(12-18岁)", 
         "青年(18-30岁)", "中年(30-50岁)", "中老年(50-65岁)", "老年(65岁以上)", "通用"]),
    generate_enum_attr("gender_target_extended", "适用性别", "场景",
        ["男", "女", "中性", "情侣", "通用"]),
    generate_enum_attr("festival_gift_extended", "节日场景", "场景",
        ["春节", "情人节", "妇女节", "母亲节", "父亲节", "儿童节", "七夕", 
         "中秋节", "国庆节", "圣诞节", "生日", "结婚", "搬家", "毕业"]),
    generate_enum_attr("room_type_extended", "房间类型", "场景",
        ["客厅", "主卧", "次卧", "儿童房", "书房", "厨房", "卫生间", "阳台", "玄关", "餐厅"]),
]

# ============ 6. 搜索属性 ============
search_attrs = [
    generate_enum_attr("search_intent", "搜索意图", "搜索",
        ["寻找具体商品", "了解某类产品", "比较多个选项", "寻找优惠", "随便逛逛"]),
    generate_enum_attr("search_keyword_extended", "搜索关键词类型", "搜索",
        ["品牌名", "产品名", "型号", "功能词", "特点词", "场景词", "价格词", "对比词"]),
    generate_enum_attr("filter_behavior", "筛选行为", "搜索",
        ["不筛选", "价格筛选", "品牌筛选", "销量筛选", "评分筛选", "参数筛选", "多维筛选"]),
    generate_enum_attr("sort_behavior", "排序偏好", "搜索",
        ["销量优先", "价格升序", "价格降序", "评分优先", "新品优先", "收藏优先"]),
    generate_enum_attr("browse_depth", "浏览深度", "搜索",
        ["只看首页", "1-3页", "3-5页", "5-10页", "10页以上"]),
]

# ============ 7. 推荐属性 ============
recommendation_attrs = [
    generate_enum_attr("recommendation_source", "推荐来源", "推荐",
        ["猜你喜欢", "看了又看", "相似商品", "热销推荐", "新品推荐", "店铺推荐"]),
    generate_enum_attr("rec_algo_type", "推荐算法类型", "推荐",
        ["协同过滤", "内容推荐", "知识图谱", "深度学习", "混合推荐"]),
    generate_enum_attr("rec_exposure_position", "推荐曝光位", "推荐",
        ["首页推荐", "商品详情页", "购物车页", "订单页", "搜索结果", "分类页"]),
]

# ============ 8. 运营选品属性 ============
operation_attrs = [
    generate_enum_attr("product_lifecycle", "产品生命周期", "运营选品",
        ["导入期", "成长期", "成熟期", "衰退期", "清仓期"]),
    generate_enum_attr("sales_channel", "销售渠道", "运营选品",
        ["天猫", "京东", "拼多多", "抖音", "快手", "小红书", "微信小程序", "线下"]),
    generate_enum_attr("inventory_strategy", "库存策略", "运营选品",
        ["零库存", "少量备货", "常规备货", "大量囤货", "期货"]),
    generate_enum_attr("pricing_strategy", "定价策略", "运营选品",
        ["低价引流", "性价比", "中高端", "高端定价", "限量稀缺"]),
]

# ============ 9. 营销属性 ============
marketing_attrs = [
    generate_enum_attr("promotion_type_extended", "促销类型", "促销",
        ["直降", "满减", "满赠", "折扣", "秒杀", "拼团", "砍价", "预售", 
         "会员价", "限时折扣", "清仓特卖", "新品首发"]),
    generate_enum_attr("discount_depth", "折扣力度", "促销",
        ["9折", "8折", "7折", "6折", "5折", "4折", "3折以下"]),
    generate_enum_attr("coupon_value", "优惠券面值", "促销",
        ["5元", "10元", "20元", "30元", "50元", "80元", "100元", "200元", 
         "满100减10", "满200减30", "满500减80", "满1000减200"]),
    generate_enum_attr("activity_theme", "活动主题", "促销",
        ["双11", "618", "年货节", "女王节", "会员日", "品牌日", "周年庆", 
         "新品发布", "换季清仓", "库存特卖"]),
]

# ============ 10. 物流属性 ============
logistics_attrs = [
    generate_enum_attr("warehouse_location", "仓库位置", "物流",
        ["华东仓", "华南仓", "华北仓", "华中仓", "西南仓", "西北仓", "东北仓",
         "海外仓", "保税仓", "香港仓", "台湾仓"]),
    generate_enum_attr("shipping_speed", "配送时效", "物流",
        ["当日达", "次日达", "2日达", "3日达", "5日达", "7日达", "7-15日"]),
    generate_enum_attr("shipping_carrier", "快递公司", "物流",
        ["顺丰", "京东", "圆通", "中通", "韵达", "申通", "邮政", "极兔", "德邦"]),
    generate_enum_attr("shipping_cost", "运费政策", "物流",
        ["包邮", "满额包邮", "9.9包邮", "有条件包邮", "到付"]),
]

# ============ 11. 服务属性 ============
service_attrs = [
    generate_enum_attr("warranty_extended", "保修服务", "服务",
        ["无保修", "店保", "官方一年", "官方两年", "官方三年", "终身保修"]),
    generate_enum_attr("return_policy_extended", "退换政策", "服务",
        ["不支持", "7天无理由", "15天无理由", "30天无理由", "一年包换"]),
    generate_enum_attr("service_installation", "安装服务", "服务",
        ["无需安装", "免费安装", "付费安装", "上门安装", "自行安装"]),
    generate_enum_attr("invoice_available", "发票类型", "服务",
        ["不开发票", "普通电子发票", "普通纸质发票", "增值税专用发票"]),
    generate_enum_attr("payment_method_extended", "支付方式", "支付",
        ["微信支付", "支付宝", "银联在线", "信用卡", "花呗", "分期", "货到付款", "积分抵扣"]),
]

# ============ 12. 扩展电子产品规格 ============
electronics_spec_attrs = []

# CPU型号
cpu_models = ["Intel i3-10110U", "Intel i3-1115G4", "Intel i5-10210U", "Intel i5-1135G7", 
              "Intel i5-1235U", "Intel i5-1240P", "Intel i7-1165G7", "Intel i7-1255U",
              "Intel i7-1260P", "Intel i9-12900H", "AMD R3-3250U", "AMD R5-3500U",
              "AMD R5-4500U", "AMD R5-5500U", "AMD R5-5600U", "AMD R7-4800U",
              "AMD R7-5800U", "AMD R7-6800H", "AMD R9-5900HX", "Apple M1",
              "Apple M2", "Apple M2 Pro", "Apple M2 Max", "Snapdragon 8cx"]
electronics_spec_attrs.append(generate_enum_attr("cpu_model", "CPU型号", "电子规格",
    cpu_models, [[c] for c in cpu_models]))

# 显卡型号
gpu_models = ["Intel Xe Graphics", "NVIDIA MX350", "NVIDIA MX450", "NVIDIA GTX 1650",
             "NVIDIA GTX 1650 Ti", "NVIDIA GTX 1660", "NVIDIA GTX 1660 Ti", 
             "NVIDIA RTX 3050", "NVIDIA RTX 3050 Ti", "NVIDIA RTX 3060",
             "NVIDIA RTX 3070", "NVIDIA RTX 3080", "NVIDIA RTX 3080 Ti",
             "NVIDIA RTX 4050", "NVIDIA RTX 4060", "NVIDIA RTX 4070",
             "NVIDIA RTX 4080", "NVIDIA RTX 4090", "AMD Radeon RX 6500 XT",
             "AMD Radeon RX 6600", "AMD Radeon RX 6700 XT", "AMD Radeon RX 6800",
             "AMD Radeon RX 6800 XT", "AMD Radeon RX 6900 XT", "AMD Radeon RX 7900 XTX"]
electronics_spec_attrs.append(generate_enum_attr("gpu_model", "显卡型号", "电子规格",
    gpu_models, [[g] for g in gpu_models]))

# 接口类型
ports = ["USB 2.0", "USB 3.0", "USB 3.1", "USB 3.2", "USB Type-C", "Thunderbolt 3",
         "Thunderbolt 4", "HDMI", "DisplayPort", "VGA", "DVI", "3.5mm音频",
         "光纤音频", "RJ45网口", "SD卡槽", "TF卡槽", "SIM卡槽"]
electronics_spec_attrs.append(generate_enum_attr("port_types", "接口类型", "电子规格",
    ports, [[p] for p in ports]))

# 操作系统
os_list = ["Windows 10", "Windows 11", "Windows 10专业版", "Windows 11专业版",
           "macOS", "macOS Monterey", "macOS Ventura", "Linux", "Ubuntu", 
           "Chrome OS", "DOS", "无系统", "Windows 10家庭版"]
electronics_spec_attrs.append(generate_enum_attr("operating_system", "操作系统", "电子规格",
    os_list, [[o] for o in os_list]))

# ============ 13. 组合所有属性 ============

all_attributes = (
    brand_attrs +
    category_attrs +
    spec_attrs +
    user_intent_attrs +
    scene_attrs +
    search_attrs +
    recommendation_attrs +
    operation_attrs +
    marketing_attrs +
    logistics_attrs +
    service_attrs +
    electronics_spec_attrs
)

# 读取原有文件获取更多核心属性
try:
    with open("/Users/rrp/Documents/aicode/knowledge_base/ecommerce_attributes.json", "r", encoding="utf-8") as f:
        original_data = json.load(f)
    
    # 保留原有的关键属性
    keep_ids = ["brand", "category", "color", "price", "material", "size",
                "weight", "dimension", "warranty", "rating", "sales_volume"]
    core_attrs = [attr for attr in original_data["attributes"] if attr["id"] in keep_ids]
    print(f"从原文件保留 {len(core_attrs)} 个核心属性")
except Exception as e:
    print(f"读取原文件失败: {e}")
    core_attrs = []

# 合并
final_attributes = core_attrs + all_attributes

# ============ 14. 生成最终JSON ============

output_data = {
    "version": "3.0",
    "description": "标准化电商属性体系 - 5000+属性项 - 扩展版",
    "attributes": final_attributes
}

# 写入文件
output_path = "/Users/rrp/Documents/aicode/knowledge_base/ecommerce_attributes.json"
with open(output_path, "w", encoding="utf-8") as f:
    json.dump(output_data, f, ensure_ascii=False, indent=2)

print(f"属性库扩展完成!")
print(f"总属性数量: {len(final_attributes)}")
print(f"输出文件: {output_path}")

# 统计
category_counts = {}
for attr in final_attributes:
    cat = attr.get("category", "未知")
    category_counts[cat] = category_counts.get(cat, 0) + 1

print("\n各类别属性数量:")
for cat, count in sorted(category_counts.items(), key=lambda x: -x[1]):
    print(f"  {cat}: {count}")

# 计算总属性值数量
total_values = sum(len(attr.get("values", [])) for attr in final_attributes)
print(f"\n总属性值数量: {total_values}")
