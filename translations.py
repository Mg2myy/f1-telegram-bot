"""F1 车手和车队中文名称映射。"""

DRIVER_NAMES: dict[str, str] = {
    # 2026 赛季车手
    "Max VERSTAPPEN": "维斯塔潘",
    "Lando NORRIS": "诺里斯",
    "Charles LECLERC": "勒克莱尔",
    "Oscar PIASTRI": "皮亚斯特里",
    "Carlos SAINZ": "塞恩斯",
    "Lewis HAMILTON": "汉密尔顿",
    "George RUSSELL": "拉塞尔",
    "Kimi ANTONELLI": "安东内利",
    "Fernando ALONSO": "阿隆索",
    "Lance STROLL": "斯特罗尔",
    "Pierre GASLY": "加斯利",
    "Esteban OCON": "奥康",
    "Alexander ALBON": "阿尔本",
    "Franco COLAPINTO": "科拉皮托",
    "Yuki TSUNODA": "角田裕毅",
    "Liam LAWSON": "劳森",
    "Nico HULKENBERG": "霍肯伯格",
    "Gabriel BORTOLETO": "博尔托莱托",
    "Oliver BEARMAN": "比尔曼",
    "Isack HADJAR": "哈贾尔",
    "Jack DOOHAN": "杜汉",
    "Andrea Kimi ANTONELLI": "安东内利",
    "ZHOU Guanyu": "周冠宇",
    "Guanyu ZHOU": "周冠宇",
    "Daniel RICCIARDO": "里卡多",
    "Kevin MAGNUSSEN": "马格努森",
    "Valtteri BOTTAS": "博塔斯",
    "Logan SARGEANT": "萨金特",
    "Nyck DE VRIES": "德弗里斯",
}

TEAM_NAMES: dict[str, str] = {
    "Red Bull Racing": "红牛",
    "McLaren": "迈凯伦",
    "Ferrari": "法拉利",
    "Mercedes": "梅赛德斯",
    "Aston Martin": "阿斯顿·马丁",
    "Alpine": "阿尔派",
    "Williams": "威廉姆斯",
    "Racing Bulls": "红牛二队",
    "Kick Sauber": "索伯",
    "Haas F1 Team": "哈斯",
    "Sauber": "索伯",
    "AlphaTauri": "红牛二队",
    "Alfa Romeo": "阿尔法·罗密欧",
}

COUNTRY_NAMES: dict[str, str] = {
    "Australia": "澳大利亚",
    "China": "中国",
    "Japan": "日本",
    "Bahrain": "巴林",
    "Saudi Arabia": "沙特阿拉伯",
    "United States": "美国",
    "Canada": "加拿大",
    "Monaco": "摩纳哥",
    "Spain": "西班牙",
    "Austria": "奥地利",
    "United Kingdom": "英国",
    "Hungary": "匈牙利",
    "Belgium": "比利时",
    "Netherlands": "荷兰",
    "Italy": "意大利",
    "Azerbaijan": "阿塞拜疆",
    "Singapore": "新加坡",
    "Mexico": "墨西哥",
    "Brazil": "巴西",
    "Qatar": "卡塔尔",
    "United Arab Emirates": "阿联酋",
    "Abu Dhabi": "阿布扎比",
    "Las Vegas": "拉斯维加斯",
}

GP_NAMES: dict[str, str] = {
    "Australian Grand Prix": "澳大利亚大奖赛",
    "Chinese Grand Prix": "中国大奖赛",
    "Japanese Grand Prix": "日本大奖赛",
    "Bahrain Grand Prix": "巴林大奖赛",
    "Saudi Arabian Grand Prix": "沙特阿拉伯大奖赛",
    "Miami Grand Prix": "迈阿密大奖赛",
    "Canadian Grand Prix": "加拿大大奖赛",
    "Monaco Grand Prix": "摩纳哥大奖赛",
    "Spanish Grand Prix": "西班牙大奖赛",
    "Austrian Grand Prix": "奥地利大奖赛",
    "British Grand Prix": "英国大奖赛",
    "Hungarian Grand Prix": "匈牙利大奖赛",
    "Belgian Grand Prix": "比利时大奖赛",
    "Dutch Grand Prix": "荷兰大奖赛",
    "Italian Grand Prix": "意大利大奖赛",
    "Azerbaijan Grand Prix": "阿塞拜疆大奖赛",
    "Singapore Grand Prix": "新加坡大奖赛",
    "Mexican Grand Prix": "墨西哥大奖赛",
    "São Paulo Grand Prix": "圣保罗大奖赛",
    "Las Vegas Grand Prix": "拉斯维加斯大奖赛",
    "Qatar Grand Prix": "卡塔尔大奖赛",
    "Abu Dhabi Grand Prix": "阿布扎比大奖赛",
    "Emilia Romagna Grand Prix": "艾米利亚-罗马涅大奖赛",
}

WEATHER_TERMS: dict[str, str] = {
    "Dry": "晴",
    "Rain": "雨",
    "Humidity": "湿度",
    "Wind": "风速",
}


CIRCUIT_NAMES: dict[str, str] = {
    "Melbourne": "墨尔本",
    "Shanghai": "上海",
    "Suzuka": "铃鹿",
    "Sakhir": "萨基尔",
    "Jeddah": "吉达",
    "Miami": "迈阿密",
    "Montreal": "蒙特利尔",
    "Monaco": "摩纳哥",
    "Barcelona": "巴塞罗那",
    "Spielberg": "施皮尔贝格",
    "Silverstone": "银石",
    "Budapest": "布达佩斯",
    "Spa-Francorchamps": "斯帕",
    "Zandvoort": "赞德沃特",
    "Monza": "蒙扎",
    "Baku": "巴库",
    "Singapore": "新加坡",
    "Mexico City": "墨西哥城",
    "São Paulo": "圣保罗",
    "Las Vegas": "拉斯维加斯",
    "Lusail": "卢赛尔",
    "Yas Island": "亚斯岛",
    "Imola": "伊莫拉",
    "Albert Park": "阿尔伯特公园",
    "Marina Bay": "滨海湾",
    "Interlagos": "英特拉格斯",
    "Hungaroring": "匈格罗宁",
    "Red Bull Ring": "红牛环",
    "Circuit de Monaco": "摩纳哥赛道",
}


def t_circuit(name: str) -> str:
    """翻译赛道/城市名称。"""
    return CIRCUIT_NAMES.get(name, name)


def t_driver(name: str) -> str:
    """翻译车手名称。"""
    return DRIVER_NAMES.get(name, name)


def t_team(name: str) -> str:
    """翻译车队名称。"""
    return TEAM_NAMES.get(name, name)


def t_country(name: str) -> str:
    """翻译国家名称。"""
    return COUNTRY_NAMES.get(name, name)


def t_gp(name: str) -> str:
    """翻译大奖赛名称。"""
    return GP_NAMES.get(name, name)
