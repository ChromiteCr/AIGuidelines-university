"""School registry: the one place that decides each university's web address.

Every school gets a canonical page at /<slug>/ — e.g. ai.policy.nestudy.cn/MIT.
GitHub Pages paths are case-sensitive, so the site also ships a 404 page that
redirects any recognised variant (/mit, /Mit, /johns-hopkins, /麻省理工, /02)
to the canonical address. The variants are generated here from the slug, the
short and full English names, the Chinese name, and the extra aliases below.

To rename a school's address, change its slug here and rebuild. Nothing else
hard-codes it.
"""

import re

# id: (slug, official English name, Chinese name, extra aliases)
SCHOOLS = {
    "01-Stanford":        ("Stanford",     "Stanford University",                          "斯坦福大学",             ["斯坦福"]),
    "02-MIT":             ("MIT",          "Massachusetts Institute of Technology",        "麻省理工学院",           ["麻省理工"]),
    "03-Harvard":         ("Harvard",      "Harvard University",                           "哈佛大学",               ["哈佛"]),
    "04-Yale":            ("Yale",         "Yale University",                              "耶鲁大学",               ["耶鲁"]),
    "05-Cornell":         ("Cornell",      "Cornell University",                           "康奈尔大学",             ["康奈尔", "康乃尔"]),
    "06-Penn":            ("Penn",         "University of Pennsylvania",                   "宾夕法尼亚大学",         ["upenn", "宾大", "宾夕法尼亚"]),
    "07-Columbia":        ("Columbia",     "Columbia University",                          "哥伦比亚大学",           ["哥大", "哥伦比亚"]),
    "08-Duke":            ("Duke",         "Duke University",                              "杜克大学",               ["杜克"]),
    "09-Northwestern":    ("Northwestern", "Northwestern University",                      "西北大学",               ["nu", "西北"]),
    "10-UChicago":        ("UChicago",     "University of Chicago",                        "芝加哥大学",             ["chicago", "芝大", "芝加哥"]),
    "11-Princeton":       ("Princeton",    "Princeton University",                         "普林斯顿大学",           ["普林斯顿"]),
    "12-Caltech":         ("Caltech",      "California Institute of Technology",           "加州理工学院",           ["加州理工"]),
    "13-Johns-Hopkins":   ("JHU",          "Johns Hopkins University",                     "约翰斯·霍普金斯大学",    ["hopkins", "约翰霍普金斯", "霍普金斯"]),
    "14-Brown":           ("Brown",        "Brown University",                             "布朗大学",               ["布朗"]),
    "15-Vanderbilt":      ("Vanderbilt",   "Vanderbilt University",                        "范德堡大学",             ["范德堡", "范德比尔特"]),
    "16-UC-Berkeley":     ("Berkeley",     "University of California, Berkeley",           "加州大学伯克利分校",     ["ucb", "伯克利"]),
    "17-UCLA":            ("UCLA",         "University of California, Los Angeles",        "加州大学洛杉矶分校",     ["加州大学洛杉矶"]),
    "18-Rice":            ("Rice",         "Rice University",                              "莱斯大学",               ["莱斯"]),
    "19-Dartmouth":       ("Dartmouth",    "Dartmouth College",                            "达特茅斯学院",           ["达特茅斯"]),
    "20-Notre-Dame":      ("NotreDame",    "University of Notre Dame",                     "圣母大学",               ["nd", "圣母"]),
    "21-Carnegie-Mellon": ("CMU",          "Carnegie Mellon University",                   "卡内基梅隆大学",         ["卡耐基梅隆", "卡内基梅隆"]),
    "22-Michigan":        ("UMich",        "University of Michigan–Ann Arbor",             "密歇根大学",             ["密歇根", "密西根"]),
    "23-Georgetown":      ("Georgetown",   "Georgetown University",                        "乔治城大学",             ["乔治城"]),
    "24-Emory":           ("Emory",        "Emory University",                             "埃默里大学",             ["埃默里", "埃默瑞"]),
    "25-UNC-Chapel-Hill": ("UNC",          "University of North Carolina at Chapel Hill",  "北卡罗来纳大学教堂山分校", ["北卡", "北卡教堂山"]),
    "26-WashU":           ("WashU",        "Washington University in St. Louis",           "圣路易斯华盛顿大学",     ["wustl", "圣路易斯华盛顿"]),
    "27-UVA":             ("UVA",          "University of Virginia",                       "弗吉尼亚大学",           ["virginia", "弗吉尼亚"]),
    "28-USC":             ("USC",          "University of Southern California",            "南加州大学",             ["南加大", "南加州"]),
    "29-UC-San-Diego":    ("UCSD",         "University of California San Diego",           "加州大学圣地亚哥分校",   ["圣地亚哥"]),
    "30-NYU":             ("NYU",          "New York University",                          "纽约大学",               ["纽大"]),
    # Added from the College Fair list (2026-09-26).
    "31-UC-Irvine":       ("UCI",          "University of California, Irvine",             "加州大学欧文分校",       ["irvine", "欧文", "加州大学欧文"]),
    "32-Swarthmore":      ("Swarthmore",   "Swarthmore College",                           "斯沃斯莫尔学院",         []),
    "33-Williams":        ("Williams",     "Williams College",                             "威廉姆斯学院",           ["威廉斯学院", "威廉斯"]),
    "34-Pomona":          ("Pomona",       "Pomona College",                               "波莫纳学院",             []),
    "35-Boston-University": ("BU",         "Boston University",                            "波士顿大学",             ["bostonu"]),
    "36-Wellesley":       ("Wellesley",    "Wellesley College",                            "韦尔斯利学院",           ["卫斯理学院", "卫斯理"]),
    "37-Barnard":         ("Barnard",      "Barnard College",                              "巴纳德学院",             []),
    "38-Washington-Seattle": ("UW",        "University of Washington",                     "华盛顿大学（西雅图）",   ["uwseattle", "washingtonseattle", "华盛顿大学", "华大西雅图", "华盛顿大学西雅图"]),
    "39-LSE":             ("LSE",          "London School of Economics and Political Science", "伦敦政治经济学院",   ["londonschoolofeconomics", "伦敦政经"]),
    "40-Claremont-McKenna": ("CMC",        "Claremont McKenna College",                    "克莱蒙特·麦肯纳学院",    []),
    "41-Vassar":          ("Vassar",       "Vassar College",                               "瓦萨学院",               []),
    "42-Carleton":        ("Carleton",     "Carleton College",                             "卡尔顿学院",             []),
    "43-Georgia-Tech":    ("GeorgiaTech",  "Georgia Institute of Technology",              "佐治亚理工学院",         ["gatech", "gt", "佐治亚理工", "乔治亚理工"]),
    "44-NUS":             ("NUS",          "National University of Singapore",             "新加坡国立大学",         ["新加坡国立"]),
    "45-HKU":             ("HKU",          "The University of Hong Kong",                  "香港大学",               ["港大"]),
    "46-Oxford":          ("Oxford",       "University of Oxford",                         "牛津大学",               []),
    "47-Boston-College":  ("BC",           "Boston College",                               "波士顿学院",             []),
    "48-Cambridge":       ("Cambridge",    "University of Cambridge",                      "剑桥大学",               []),
    "49-Waseda":          ("Waseda",       "Waseda University",                            "早稻田大学",             ["早大"]),
    "50-HKUST":           ("HKUST",        "The Hong Kong University of Science and Technology", "香港科技大学",     ["ust", "港科大"]),
    "51-Imperial":        ("Imperial",     "Imperial College London",                      "帝国理工学院",           ["icl", "imperialcollege", "帝国理工", "帝国理工大学"]),
    "52-Toronto":         ("Toronto",      "University of Toronto",                        "多伦多大学",             ["uoft", "utoronto", "多大"]),
}

# Display names for the universities added after the first thirty; build_data.py
# takes the first thirty's from its own table.
SHORT = {
    "31-UC-Irvine": "UC Irvine", "32-Swarthmore": "Swarthmore", "33-Williams": "Williams",
    "34-Pomona": "Pomona", "35-Boston-University": "Boston University", "36-Wellesley": "Wellesley",
    "37-Barnard": "Barnard", "38-Washington-Seattle": "UW Seattle", "39-LSE": "LSE",
    "40-Claremont-McKenna": "Claremont McKenna", "41-Vassar": "Vassar", "42-Carleton": "Carleton",
    "43-Georgia-Tech": "Georgia Tech", "44-NUS": "NUS", "45-HKU": "HKU", "46-Oxford": "Oxford",
    "47-Boston-College": "Boston College", "48-Cambridge": "Cambridge", "49-Waseda": "Waseda",
    "50-HKUST": "HKUST", "51-Imperial": "Imperial", "52-Toronto": "Toronto",
}

# Universities outside the United States: (Chinese, English), shown beside the name.
COUNTRY = {
    "39-LSE": ("英国", "UK"), "46-Oxford": ("英国", "UK"), "48-Cambridge": ("英国", "UK"),
    "51-Imperial": ("英国", "UK"), "44-NUS": ("新加坡", "Singapore"),
    "45-HKU": ("中国香港", "Hong Kong"), "50-HKUST": ("中国香港", "Hong Kong"),
    "49-Waseda": ("日本", "Japan"), "52-Toronto": ("加拿大", "Canada"),
}

# Derived short forms that would name two schools at once — /boston could be
# Boston University or Boston College — are left to the 404 page's list.
AMBIGUOUS = {"boston", "波士顿", "washington", "香港"}

# Top-level names already taken by the site; no school alias may shadow them.
RESERVED = {"index", "atlas", "guidelines", "admissions", "versions", "404", "cname", "home", "docs", "nojekyll"}

_STRIP = re.compile(r"[\s\-_.,'’()·–—/]")


def normalize(s):
    """The key a typed path is reduced to before lookup. Must match the 404 page's JS."""
    s = s.strip().lower()
    if s.endswith(".html"):
        s = s[:-5]
    return _STRIP.sub("", s)


def slug(school_id):
    return SCHOOLS[school_id][0]


def aliases(school_id, short_name=""):
    """Every normalised key that should reach this school."""
    sl, en, zh, extra = SCHOOLS[school_id]
    num = school_id.split("-")[0]
    keys = {sl, en, zh, school_id, num, str(int(num)), short_name, *extra}
    # "University of Chicago" → also "Chicago"; "斯坦福大学" → also "斯坦福"
    keys.add(re.sub(r"^(University of |The )", "", en))
    keys.add(re.sub(r" (University|College)$", "", en))
    keys.add(re.sub(r"(大学|学院)$", "", zh))
    return {normalize(k) for k in keys if k and normalize(k)} - {normalize(a) for a in AMBIGUOUS}


def alias_table(short_names):
    """{normalised alias: slug}, with collisions and reserved-name clashes raised as errors."""
    table, owner = {}, {}
    for sid in SCHOOLS:
        for key in aliases(sid, short_names.get(sid, "")):
            if key in RESERVED:
                raise ValueError(f"{sid}: 别名 {key!r} 与站点已有页面重名")
            if key in owner and owner[key] != sid:
                raise ValueError(f"别名冲突：{key!r} 同时指向 {owner[key]} 和 {sid}")
            owner[key] = sid
            table[key] = slug(sid)
    return table
