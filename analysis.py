"""Email scoring, model loading, and incident report generation."""
import base64
import json
import os
import re
import uuid
from datetime import datetime
import joblib
from bs4 import BeautifulSoup
try:
    from groq import Groq
except ImportError:
    Groq = None
from config import GROQ_API_KEY
from agent import run_investigation

# ── ML 模型：Phishing Email Dataset ───────────────────────────
# V5 不再使用 SMS Spam/ham 資料。
# 模型由 train_phishing_model.py 預先訓練後，以 joblib 載入。
MODEL_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'models')
MODEL_PATH = os.path.join(MODEL_DIR, 'phishing_model.joblib')
VECTORIZER_PATH = os.path.join(MODEL_DIR, 'phishing_tfidf.joblib')
METRICS_PATH = os.path.join(MODEL_DIR, 'phishing_metrics.json')

model = None
vectorizer = None
model_metrics = {}

try:
    if os.path.exists(MODEL_PATH) and os.path.exists(VECTORIZER_PATH):
        model = joblib.load(MODEL_PATH)
        vectorizer = joblib.load(VECTORIZER_PATH)
        if os.path.exists(METRICS_PATH):
            with open(METRICS_PATH, 'r', encoding='utf-8') as f:
                model_metrics = json.load(f)
        print('OK - Phishing Email ML 模型已載入')
    else:
        print('WARNING - 尚未找到 Phishing Email ML 模型，ML 分析將暫停。請先執行 train_phishing_model.py')
except Exception as e:
    model = None
    vectorizer = None
    print(f'WARNING - ML 模型載入失敗：{e}')

groq_client = Groq(api_key=GROQ_API_KEY) if (GROQ_API_KEY and Groq is not None) else None
print('OK - 模型就緒' if GROQ_API_KEY else 'WARNING - Groq API Key 未設定，將跳過 LLM 深度分析')

# ── 分析函式 ─────────────────────────────────────────────────
def analyze_url(url):
    """分析 URL 結構，不連線、不開啟目標網站。"""
    from urllib.parse import urlparse
    import ipaddress

    findings = []
    try:
        parsed = urlparse(url.strip().rstrip('.,);]'))
        host = (parsed.hostname or '').lower()
        if not host:
            return findings

        try:
            ipaddress.ip_address(host)
            findings.append('URL 使用 IP 位址')
        except ValueError:
            pass

        if '@' in parsed.netloc:
            findings.append('URL 含有 @，可能隱藏真正目的地')

        if host.startswith('xn--') or '.xn--' in host:
            findings.append('網域含有 Punycode')

        suspicious_tlds = ('.xyz', '.top', '.click', '.zip', '.mov', '.work', '.biz')
        if any(host.endswith(tld) for tld in suspicious_tlds):
            findings.append('使用較高風險網域後綴')

        if len(url) > 100:
            findings.append('URL 過長')

        if host.count('.') >= 4:
            findings.append('子網域層級過深')

        shorteners = {
            'bit.ly', 'tinyurl.com', 't.co', 'is.gd', 'goo.gl',
            'ow.ly', 'buff.ly', 'rebrand.ly', 'cutt.ly'
        }
        if host in shorteners:
            findings.append('使用短網址服務')

        suspicious_words = [
            'login', 'verify', 'secure', 'update', 'account',
            'password', 'signin', 'confirm', 'wallet'
        ]
        if any(w in (host + parsed.path).lower() for w in suspicious_words):
            findings.append('URL 含有登入或驗證誘導字樣')

    except Exception:
        findings.append('URL 格式異常')

    return findings


URGENT_WORDS = [
    'urgent', 'immediately', 'expire', 'suspended', 'verify now', 'act now',
    '立即', '緊急', '即將停用', '馬上', '限時', '暫停', '停用',
    '逾期', '小時內', '今日內', '凍結', '鎖定', '否則',
]
BAIT_WORDS = [
    'free', 'winner', 'won', 'prize', 'claim', 'lucky', 'reward', 'gift',
    '中獎', '免費', '領取', '恭喜', '退款', '補助'
]
PERSONAL_WORDS = [
    'password', 'credit card', 'bank account', 'pin',
    '密碼', '帳號', '信用卡', '身分證', '帳戶',
    '驗證碼', 'otp', '卡號', '背面三碼', '存摺', '出生日期'
]
MONEY_WORDS = [
    '$', 'cash', 'money', 'transfer', 'wire', 'payment', 'invoice',
    '匯款', '轉帳', '付款', 'NT$', '退款'
]
# 中文（台灣）常見詐騙話術：單一詞就是強訊號，每命中 +3
ZH_SCAM_WORDS = [
    '補繳', '運費', '關稅', '滯納金', '手續費', '分期付款', '解除分期', 'ATM',
    '保證獲利', '零風險', '保證回本', '日領', '月入', '加入群組', 'Telegram',
    '監管帳戶', '檢察官', '勿告知', '不方便講電話', '新帳戶', '帳戶已變更',
    '點擊', '驗證身分', '重新驗證', '憑證', '異地登入', '盜刷', '洗錢',
    '傳票', '強制執行', '入金', '免擔保', '預審',
]
# 弱詞：在正常信件（帳單、收據、訂單）裡也很常見，單獨出現不計分；
# 必須同時有其他強訊號（連結、緊急語句、強詞）才計分，以降低誤報。
WEAK_WORDS = {
    '帳號', '帳戶', '信用卡', '付款', '退款', '$', 'nt$', 'payment', 'invoice',
    'cash', 'money', '免費', 'free', 'gift', 'reward', 'claim', '領取', '補助', '恭喜',
}
# 否定／免責句（「本行不會要求您提供密碼」「不需要任何額外操作」）不應被當成索取個資。
_NEG_RE = re.compile(r'(不會|不需要|不需|無需|不用|請勿將)[^。！？!?\n]*')


def _kw_hit(word, text_lower):
    """關鍵字比對（text_lower 需已轉小寫）。
    - 純英文字母／空白的詞：前面不可緊接字母；4 字母以內的短詞（pin、won、free、wire…）前後都不可緊接字母，
      避免 pin 命中 shipping、wire 命中 wireless。
    - 其他詞（中文、$、NT$）：子字串比對；詞庫一律轉小寫後比較，修正 NT$ 永遠不命中。"""
    w = word.lower()
    if re.fullmatch(r'[a-z ]+', w):
        pat = r'(?<![a-z])' + re.escape(w) + (r'(?![a-z])' if len(w) <= 4 else '')
        return re.search(pat, text_lower) is not None
    return w in text_lower


def rule_based_score(text):
    score = 0
    triggered = []
    t = (text or '').lower()
    t_kw = _NEG_RE.sub(' ', t)     # 關鍵字比對用：先移除否定／免責句

    urgent = [w for w in URGENT_WORDS if _kw_hit(w, t_kw)]
    zh_scam = [w for w in ZH_SCAM_WORDS if _kw_hit(w, t_kw)]

    urls = re.findall(r'https?://[^\s<>"\']+', t)
    url_score, url_notes = 0, []
    if urls:
        url_score += min(3 + len(urls), 8)
        url_notes.append(f'含有連結: {urls[:2]}')
        for url in urls[:10]:
            url_findings = analyze_url(url)
            if url_findings:
                url_score += min(len(url_findings) * 2, 8)
                url_notes.append(f'URL 風險: {url_findings[:4]}')

    def split(words):
        hits = [w for w in words if _kw_hit(w, t_kw)]
        return [w for w in hits if w.lower() not in WEAK_WORDS], [w for w in hits if w.lower() in WEAK_WORDS]

    bait_s, bait_w = split(BAIT_WORDS)
    pers_s, pers_w = split(PERSONAL_WORDS)
    money_s, money_w = split(MONEY_WORDS)

    # 有其他強訊號時，弱詞才算數
    corroborated = bool(urls or urgent or zh_scam or bait_s or pers_s or money_s)

    if urgent:
        score += len(urgent) * 2
        triggered.append(f'緊急語句: {urgent}')
    if urls:
        score += url_score
        triggered.extend(url_notes)
    hits2 = bait_s + (bait_w if corroborated else [])
    if hits2:
        score += len(hits2) * 2
        triggered.append(f'誘騙話術: {hits2}')
    hits3 = pers_s + (pers_w if corroborated else [])
    if hits3:
        score += len(hits3) * 3
        triggered.append(f'索取個資: {hits3}')
    hits4 = money_s + (money_w if corroborated else [])
    if hits4:
        score += len(hits4) * 2
        triggered.append(f'金錢相關: {hits4}')
    if zh_scam:
        score += len(zh_scam) * 3
        triggered.append(f'詐騙話術: {zh_scam}')

    return score, triggered


# 規則展示頁使用的規則目錄（關鍵字直接引用上方常數，與實際偵測邏輯同源）
RULE_KEYWORD_GROUPS = [
    ('R1', '緊急語句', '製造時間壓力，逼迫收件者倉促行動', URGENT_WORDS, '每命中 1 個詞 +2'),
    ('R2', '誘騙話術', '以獎金、免費、退款等利益誘使點擊', BAIT_WORDS, '每命中 1 個詞 +2'),
    ('R3', '索取個資', '要求提供密碼、卡號、帳戶等敏感資料', PERSONAL_WORDS, '每命中 1 個詞 +3'),
    ('R4', '金錢相關', '涉及匯款、付款、轉帳等金流指示', MONEY_WORDS, '每命中 1 個詞 +2'),
    ('R5', '詐騙話術', '補繳運費、解除分期、監管帳戶等台灣常見詐騙用語', ZH_SCAM_WORDS, '每命中 1 個詞 +3'),
]
RULE_URL_ITEMS = [
    ('U1', 'URL 使用 IP 位址', '主機名稱為 IP 而非網域'),
    ('U2', 'URL 含有 @', '以 @ 隱藏真正目的地'),
    ('U3', '網域含 Punycode', '網域以 xn-- 開頭，可能為仿冒字元網域'),
    ('U4', '高風險網域後綴', '.xyz / .top / .click / .zip / .mov / .work / .biz'),
    ('U5', 'URL 過長', '網址長度超過 100 字元'),
    ('U6', '子網域層級過深', '主機名稱中的「.」達 4 個以上'),
    ('U7', '短網址服務', 'bit.ly、tinyurl.com、t.co 等 9 種短網址'),
    ('U8', '登入／驗證誘導字樣', 'login、verify、secure、update、account、password、signin、confirm、wallet'),
]
RULE_HTML_ITEMS = [
    ('H1', '網址結構風險', '連結 href 觸發 U1–U8 任一項', '每個連結 +3×命中數（上限 10）'),
    ('H2', '偽裝連結', '連結顯示文字的網域與實際 href 網域不同', '+6'),
    ('H3', '像素追蹤', '寬或高為 0 / 1 的圖片', '每個 +2（上限 8）'),
    ('H4', '隱藏元素', 'style 含 display:none 或 visibility:hidden', '+3'),
    ('H5', '表單元素', '含 <form>', '+3'),
    ('H6', '密碼輸入欄位', '含 type="password" 的 <input>', '+5'),
    ('H7', '品牌偵測', '內文出現 paypal / microsoft / apple / amazon / facebook / netflix / google', '+2'),
]


def ai_agent_analyze(text, rule_score, triggered_rules):
    rules_str = ', '.join(triggered_rules) if triggered_rules else 'none'
    prompt = (
        "You are a cybersecurity analyst. Analyze this email and reply ONLY with JSON.\\n"
        f"Message: {text}\\n"
        f"Deterministic rule score: {rule_score}, Triggered evidence: {rules_str}\\n"
        "Do not invent URLs, sender facts, or technical evidence.\\n"
        'JSON: {"risk_level":"high/medium/low","risk_score":0-100,'
        '"category":"釣魚信件/詐騙簡訊/正常信件/商業詐騙",'
        '"suspicious_points":["點1","點2"],'
        '"explanation":"繁體中文2-3句說明",'
        '"recommended_action":"繁體中文建議"}'
    )
    try:
        if not GROQ_API_KEY:
            raise RuntimeError('GROQ_API_KEY 未設定')
        resp = groq_client.chat.completions.create(
            model='openai/gpt-oss-120b',
            messages=[{'role': 'user', 'content': prompt}],
            temperature=0.2
        )
        raw = resp.choices[0].message.content.strip()
        raw = raw.replace('```json', '').replace('```', '').strip()
        result = json.loads(raw)

        result['risk_score'] = float(result.get('risk_score', 0))
        result['suspicious_points'] = result.get('suspicious_points', []) or []
        return result
    except Exception as e:
        return {
            'risk_level': 'unknown',
            'risk_score': None,
            'category': '分析失敗',
            'suspicious_points': [],
            'explanation': f'AI 深度分析暫時失敗：{e}',
            'recommended_action': '請依規則與 ML 結果人工檢查，不要直接點擊信件中的連結。'
        }


def build_explainable_findings(rules, html_findings, spam_prob, report, agent_trace=None):
    """把各分析層的原始證據整理成使用者看得懂的「為什麼可疑」。"""
    findings = []

    # Agent 實際查證到的事實放最前面，並標明來自第幾步，事件回應報告可直接引用。
    from agent import SIGNAL_LABELS
    for step in agent_trace or []:
        for sig in step.get('signals', []):
            findings.append({
                'severity': 'high',
                'source': 'AI Agent 查證',
                'title': SIGNAL_LABELS.get(sig, sig),
                'detail': f"步驟 {step['step']}・{step['tool']}"
            })

    for item in rules or []:
        s = str(item)
        if s.startswith('緊急語句'):
            findings.append({
                'severity': 'high',
                'source': '規則引擎',
                'title': '偵測到緊急／施壓語句',
                'detail': s
            })
        elif s.startswith('索取個資'):
            findings.append({
                'severity': 'high',
                'source': '規則引擎',
                'title': '出現帳號或敏感資訊要求',
                'detail': s
            })
        elif s.startswith('URL 風險'):
            findings.append({
                'severity': 'high',
                'source': 'URL 分析',
                'title': '連結具有可疑結構',
                'detail': s
            })
        elif s.startswith('含有連結'):
            findings.append({
                'severity': 'medium',
                'source': '規則引擎',
                'title': '郵件包含外部連結',
                'detail': s
            })
        elif s.startswith('誘騙話術'):
            findings.append({
                'severity': 'medium',
                'source': '規則引擎',
                'title': '偵測到誘因／獎勵型話術',
                'detail': s
            })
        elif s.startswith('金錢相關'):
            findings.append({
                'severity': 'high',
                'source': '規則引擎',
                'title': '出現金錢或付款相關內容',
                'detail': s
            })
        else:
            findings.append({
                'severity': 'medium',
                'source': '規則引擎',
                'title': '偵測到可疑文字特徵',
                'detail': s
            })

    for category, items in html_findings or []:
        for item in items[:3]:
            title = {
                'URL 結構風險': 'URL 結構存在風險',
                '偽裝連結': '顯示網址與實際連結不一致',
                '像素追蹤': '發現可能的追蹤像素',
                '隱藏元素': 'HTML 含有隱藏元素',
                '表單元素': '郵件內含表單',
                '密碼輸入欄位': '郵件內含密碼輸入欄位'
            }.get(category, f'HTML 偵測到{category}')
            findings.append({
                'severity': 'high' if category in ('偽裝連結', '密碼輸入欄位') else 'medium',
                'source': 'HTML / URL',
                'title': title,
                'detail': f'{category}：{item}'
            })

    if spam_prob is None:
        findings.append({
            'severity': 'low',
            'source': 'ML 模型',
            'title': 'ML 模型不適用於此信件',
            'detail': '模型以英文語料訓練，此信件超出其可判斷範圍，已排除在分數之外，改由規則、HTML / URL 與 AI Agent 查證判斷。'
        })
    elif spam_prob >= 0.70:
        findings.append({
            'severity': 'high',
            'source': 'ML 模型',
            'title': '模型高度偏向釣魚信件',
            'detail': f'釣魚信件機率為 {spam_prob:.1%}。此結果代表模型在目前輸入文字上的分類傾向，並非單獨作為最終判定。'
        })
    elif spam_prob >= 0.30:
        findings.append({
            'severity': 'medium',
            'source': 'ML 模型',
            'title': '模型偏向釣魚信件',
            'detail': f'釣魚信件機率為 {spam_prob:.1%}，需要搭配其他分析層判斷。'
        })
    else:
        findings.append({
            'severity': 'low',
            'source': 'ML 模型',
            'title': '模型未明顯偏向釣魚信件',
            'detail': f'釣魚信件機率為 {spam_prob:.1%}，仍會搭配規則與 HTML / URL 分析。'
        })

    # LLM 的理由保留為「AI 輔助說明」，避免把 LLM 生成內容誤標成確定技術證據。
    llm_points = report.get('suspicious_points', []) or []
    for point in llm_points[:5]:
        point = str(point)
        if point.startswith('[HTML]'):
            continue
        findings.append({
            'severity': 'medium',
            'source': 'AI 深度分析',
            'title': 'AI 輔助判讀',
            'detail': point
        })

    # 去除完全重複項目，最多保留 10 個，讓畫面不會過長。
    unique = []
    seen = set()
    for item in findings:
        key = (item['source'], item['title'], item['detail'])
        if key not in seen:
            seen.add(key)
            unique.append(item)

    return unique[:10]


def analyze_html(html_content):
    findings = []
    score = 0
    soup = BeautifulSoup(html_content, 'html.parser')

    links = soup.find_all('a', href=True)
    for link in links:
        href = link.get('href', '')
        text_label = link.get_text(' ', strip=True)

        url_findings = analyze_url(href)
        if url_findings:
            score += min(len(url_findings) * 3, 10)
            findings.append(('URL 結構風險', url_findings[:4]))

        # 顯示文字與實際連結網域不同時提高風險。
        visible_urls = re.findall(r'https?://[^\s<>"\']+', text_label.lower())
        if visible_urls:
            from urllib.parse import urlparse
            try:
                visible_host = urlparse(visible_urls[0]).hostname or ''
                actual_host = urlparse(href).hostname or ''
                if visible_host and actual_host and visible_host.lower() != actual_host.lower():
                    score += 6
                    findings.append(('偽裝連結', [f'{visible_host} → {actual_host}']))
            except Exception:
                pass

    trackers = [
        img.get('src', '')[:80]
        for img in soup.find_all('img')
        if str(img.get('width', '')).lower() in ['1', '0']
        or str(img.get('height', '')).lower() in ['1', '0']
    ]
    if trackers:
        findings.append(('像素追蹤', trackers[:2]))
        score += min(len(trackers) * 2, 8)

    hidden = soup.find_all(style=re.compile(r'display\\s*:\\s*none|visibility\\s*:\\s*hidden', re.I))
    if hidden:
        findings.append(('隱藏元素', [f'{len(hidden)} 個']))
        score += 3

    forms = soup.find_all('form')
    password_inputs = soup.find_all('input', attrs={'type': re.compile(r'password', re.I)})
    if forms:
        findings.append(('表單元素', [f'{len(forms)} 個']))
        score += 3
    if password_inputs:
        findings.append(('密碼輸入欄位', [f'{len(password_inputs)} 個']))
        score += 5

    found_brands = [
        b for b in ['paypal', 'microsoft', 'apple', 'amazon', 'facebook', 'netflix', 'google']
        if b in soup.get_text(' ').lower()
    ]
    if found_brands:
        findings.append(('品牌偵測', [', '.join(found_brands)]))
        score += 2

    return score, findings


def calculate_risk_score(rule_score, spam_prob, html_score, llm_score=None):
    """固定融合規則、ML、HTML 與 LLM，避免單一模型直接決定最終分數。"""
    rule_component = min(rule_score * 5, 100)
    html_component = min(html_score * 8, 100)
    # spam_prob 為 None 表示 ML 不適用（見 ml_reliability），其權重改給規則引擎。
    ml_component = None if spam_prob is None else max(0, min(float(spam_prob) * 100, 100))

    if ml_component is None:
        components = [(0.70, rule_component), (0.15, html_component)]
        if llm_score is not None:
            components.append((0.15, max(0, min(float(llm_score), 100))))
        else:
            components = [(0.85, rule_component), (0.15, html_component)]
        return int(round(sum(weight * value for weight, value in components)))

    components = [
        (0.35, rule_component),
        (0.35, ml_component),
        (0.15, html_component)
    ]

    if llm_score is not None:
        components.append((0.15, max(0, min(float(llm_score), 100))))
    else:
        # LLM 未啟用時，把其權重平均分配給規則與 ML。
        components = [
            (0.425, rule_component),
            (0.425, ml_component),
            (0.15, html_component)
        ]

    return int(round(sum(weight * value for weight, value in components)))



def build_risk_breakdown(rule_score, spam_prob, html_score, llm_score=None):
    rule_component = min(max(float(rule_score), 0) * 5, 100)
    ml_na = spam_prob is None
    ml_component = 0.0 if ml_na else max(0, min(float(spam_prob) * 100, 100))
    html_component = min(max(float(html_score), 0) * 8, 100)

    if llm_score is not None:
        llm_component = max(0, min(float(llm_score), 100))
        rows = [
            ('規則引擎', rule_component, 70.0 if ml_na else 35.0),
            ('ML 模型', ml_component, 0.0 if ml_na else 35.0),
            ('HTML / URL', html_component, 15.0),
            ('AI 深度分析', llm_component, 15.0),
        ]
    else:
        llm_component = None
        rows = [
            ('規則引擎', rule_component, 85.0 if ml_na else 42.5),
            ('ML 模型', ml_component, 0.0 if ml_na else 42.5),
            ('HTML / URL', html_component, 15.0),
        ]

    total = sum(score * weight / 100 for _, score, weight in rows)
    return {
        'components': [
            {
                'name': name,
                'score': round(score, 2),
                'weight': weight,
                'contribution': round(score * weight / 100, 2)
            }
            for name, score, weight in rows
        ],
        'raw_total': round(total, 2),
        'rounded_final': int(round(total)),
        'llm_used': llm_component is not None,
        'ml_used': not ml_na,
        'thresholds': {'low': '< 40', 'medium': '40 - 69', 'high': '>= 70'}
    }


def run_risk_score_self_test():
    cases = [
        ('zero', calculate_risk_score(0, 0, 0, None), 0),
        ('maximum_without_llm', calculate_risk_score(20, 1, 13, None), 100),
        ('maximum_with_llm', calculate_risk_score(20, 1, 13, 100), 100),
        ('ml_50pct_without_llm', calculate_risk_score(0, 0.5, 0, None), 21),
        ('llm_100pct', calculate_risk_score(0, 0, 0, 100), 15),
    ]
    results = []
    for name, actual, expected in cases:
        results.append({'name': name, 'actual': actual, 'expected': expected, 'passed': actual == expected})

    level_cases = [(39, 'low'), (40, 'medium'), (69, 'medium'), (70, 'high'), (100, 'high')]
    for score, expected in level_cases:
        report = apply_risk_level({}, score)
        results.append({'name': f'level_{score}', 'actual': report['risk_level'], 'expected': expected, 'passed': report['risk_level'] == expected})

    return results


def apply_risk_level(report, final_score):
    final_score = max(0, min(int(final_score), 100))
    report['risk_score'] = final_score

    if final_score >= 70:
        report['risk_level'] = 'high'
    elif final_score >= 40:
        report['risk_level'] = 'medium'
    else:
        report['risk_level'] = 'low'

    return report



def build_safety_actions(risk_level, rules=None, html_findings=None, category=''):
    """依風險等級與偵測特徵產生可直接執行的安全處置建議。"""
    rules = rules or []
    html_findings = html_findings or []
    high_signal = any(
        str(x).startswith(('緊急語句', '索取個資', 'URL 風險', '金錢相關'))
        for x in rules
    )
    has_phishing_link = any(cat in ('URL 結構風險', '偽裝連結', '密碼輸入欄位')
                            for cat, _ in html_findings)

    if risk_level == 'high':
        actions = [
            '不要點擊郵件中的連結、附件，也不要回覆或提供帳號密碼。',
            '將郵件標記為垃圾郵件／釣魚郵件，並依組織規範進行通報或隔離。',
            '若需要確認通知內容，請自行開啟官方網站或使用既有官方聯絡方式，不要使用郵件提供的連結。'
        ]
        if high_signal or has_phishing_link:
            actions.append('若已輸入密碼或敏感資訊，請立即從官方網站變更密碼並檢查帳號安全設定。')
        return actions

    if risk_level == 'medium':
        actions = [
            '先不要點擊連結或開啟附件，確認寄件者與郵件內容是否合理。',
            '若涉及帳號、付款或驗證，請透過官方網站或其他可信管道獨立確認。',
            '不確定時可將郵件標記為垃圾郵件／釣魚郵件，並請管理者或資安人員協助判斷。'
        ]
        return actions

    return [
        '目前未發現明顯高風險訊號，但仍不建議點擊未知來源的連結或附件。',
        '若郵件要求提供密碼、付款或敏感資訊，請改用官方管道再次確認。'
    ]

AGENT_TRIGGER_SCORE = 40  # 規則 + ML + HTML 的預估分數達「中等風險」才啟動調查 Agent


def _extract_urls(text, html=''):
    urls = [u.rstrip('.,);]') for u in re.findall(r'https?://[^\s<>"\']+', text or '')]
    if html:
        urls += [a['href'].strip() for a in BeautifulSoup(html, 'html.parser').find_all('a', href=True)
                 if a['href'].strip().lower().startswith(('http://', 'https://'))]
    seen, out = set(), []
    for u in urls:
        if u not in seen:
            seen.add(u)
            out.append(u)
    return out[:8]


# ── ML 可靠度檢查 ─────────────────────────────────────────────
# 模型以英文語料訓練。中文信的 TF-IDF 向量幾乎全零，模型只剩截距項，
# 會對任何中文信輸出約 80–98% 的「釣魚機率」。這種輸出不是證據，所以
# 超出訓練分布時把 ML 視為「未知」，不納入融合，權重重分配給其他層。
ML_MAX_CJK_RATIO = 0.20     # 去除網址後，CJK 字元佔比超過此值 → 不可靠
ML_MIN_KNOWN_TOKENS = 5     # 落在模型詞彙內的詞數低於此值 → 證據不足
_URL_RE = re.compile(r'https?://\S+|www\.\S+', re.I)
_LABEL_RE = re.compile(r'^(from|subject|body)\s*:', re.I | re.M)
_CJK_RE = re.compile(r'[\u3040-\u30ff\u3400-\u4dbf\u4e00-\u9fff\uac00-\ud7af]')
_LATIN_RE = re.compile(r'[A-Za-z]')


def ml_reliability(text):
    """回傳 (是否可靠, 原因, 統計)。只檢查輸入是否在模型訓練分布內。"""
    cleaned = _LABEL_RE.sub(' ', _URL_RE.sub(' ', text or ''))
    cjk = len(_CJK_RE.findall(cleaned))
    latin = len(_LATIN_RE.findall(cleaned))
    ratio = cjk / (cjk + latin) if (cjk + latin) else 0.0
    known = 0
    if vectorizer is not None:
        vocab = vectorizer.vocabulary_
        tok = vectorizer.build_tokenizer()
        known = sum(1 for w in tok(cleaned) if w.lower() in vocab)
    stats = {'cjk_ratio': round(ratio, 3), 'known_tokens': known}
    if ratio > ML_MAX_CJK_RATIO:
        return False, '信件以中文（非英文）為主，超出模型訓練語料範圍', stats
    if known < ML_MIN_KNOWN_TOKENS:
        return False, '信件中落在模型詞彙內的詞太少，證據不足', stats
    return True, '', stats


def full_pipeline(text, html='', headers=None, sender='', wl_note=None):
    """wl_note：白名單驗證結果 {'verdict','domain','hit','floor'}；spoof_suspect 時最終分數至少為 floor。"""
    rule_score, rules = rule_based_score(text)

    # ML 模型使用 1 = phishing、0 = legitimate。
    if model is not None and vectorizer is not None:
        vec = vectorizer.transform([text])
        classes = list(model.classes_)
        phishing_index = classes.index(1) if 1 in classes else classes.index('1')
        spam_prob = float(model.predict_proba(vec)[0][phishing_index])
    else:
        spam_prob = 0.0
    ml_ok, ml_reason, ml_stats = ml_reliability(text)
    ml_raw_prob = spam_prob
    if not ml_ok:
        spam_prob = None   # 未知：不納入融合，也不顯示成「正常」

    html_score, html_findings = (0, [])
    if html:
        html_score, html_findings = analyze_html(html)

    # 先用規則 + ML + HTML 算出預估分數；達到中等風險才啟動調查 Agent，控制 API 成本與延遲。
    pre_score = calculate_risk_score(rule_score, spam_prob, html_score, None)
    wl_floor = (wl_note or {}).get('floor', 0) if (wl_note or {}).get('verdict') == 'spoof_suspect' else 0
    pre_score = max(pre_score, wl_floor)   # 冒用白名單網域：至少達到啟動 Agent 的門檻
    agent_result = None
    should_call_llm = pre_score >= AGENT_TRIGGER_SCORE and groq_client is not None

    if should_call_llm:
        agent_result = run_investigation(
            groq_client, text, _extract_urls(text, html), sender=sender, headers=headers)
        final_info = agent_result.get('final') or {}
        report = {
            'risk_level': 'unknown',
            'category': final_info.get('category', '調查未完成'),
            'explanation': final_info.get('explanation') or '調查 Agent 未能產生結論，請依規則與 ML 結果人工檢查。',
            'recommended_action': final_info.get('recommended_action') or '不要點擊信件中的連結。',
            'suspicious_points': list(final_info.get('suspicious_points') or []),
        }
        # 分數只來自工具回傳的證據（agent.SIGNAL_POINTS），不採用 LLM 自己給的分數。
        llm_score = agent_result['agent_score'] if agent_result['status'] != 'error' else None
    else:
        report = {
            'risk_level': 'low',
            'risk_score': None,
            'category': '正常信件',
            'explanation': '目前規則與 ML 模型未發現明顯異常訊號。',
            'recommended_action': '可正常閱讀，但仍不建議點擊未知連結。',
            'suspicious_points': []
        }
        llm_score = None

    # 保存各層的「原始證據」與「融合用分數」。
    rule_component = min(rule_score * 5, 100)
    ml_component = 0 if spam_prob is None else max(0, min(float(spam_prob) * 100, 100))
    html_component = min(html_score * 8, 100)
    llm_component = None if llm_score is None else max(0, min(float(llm_score), 100))

    # 最終風險分數由固定公式融合，不直接採用 LLM 自己的分數。
    final_score = calculate_risk_score(
        rule_score, spam_prob, html_score, llm_score
    )
    # Agent 只能加分、不能扣分：「查不到問題」不等於「安全」（驗證通過只代表寄件者身分，
    # 查無資料也只是未知），所以最終分數不會低於三層融合的預估分數。
    agent_floor_applied = llm_score is not None and pre_score > final_score
    if agent_floor_applied:
        final_score = pre_score
    wl_floor_applied = wl_floor > final_score
    if wl_floor_applied:
        final_score = wl_floor
    report = apply_risk_level(report, final_score)
    report['risk_breakdown'] = build_risk_breakdown(
        rule_score, spam_prob, html_score, llm_score
    )
    if wl_floor_applied:
        report['risk_breakdown']['floor_applied'] = True
        report['risk_breakdown']['rounded_final'] = final_score
    if agent_floor_applied:
        report['risk_breakdown']['floor_applied'] = True
        report['risk_breakdown']['rounded_final'] = final_score
    report['score_validation'] = {
        'formula_total': report['risk_breakdown']['raw_total'],
        'final_score': final_score,
        'consistent': report['risk_breakdown']['rounded_final'] == final_score,
        'threshold_rule': '高風險 >= 70；中風險 40-69；低風險 < 40'
    }

    # 將 HTML 證據加入可疑特徵。
    for cat, items in html_findings:
        for item in items:
            report.setdefault('suspicious_points', []).append(
                f'[HTML] {cat}: {item}'
            )

    # 給前端的「為什麼可疑」證據清單。
    report['explainable_findings'] = build_explainable_findings(
        rules, html_findings, spam_prob, report, (agent_result or {}).get('trace')
    )

    if wl_note and wl_note.get('verdict') in ('spoof_suspect', 'unverified'):
        spoof = wl_note['verdict'] == 'spoof_suspect'
        report['explainable_findings'].insert(0, {
            'severity': 'high' if spoof else 'low',
            'source': '白名單驗證',
            'title': '疑似冒用白名單網域' if spoof else '白名單寄件者無法驗證身分',
            'detail': (f"寄件網域 {wl_note.get('domain','')} 在白名單內，但 Gmail 的 DMARC / SPF / DKIM 驗證失敗，"
                       '可能是偽造寄件者，因此不採信白名單、完整分析，且風險至少為中等。') if spoof else
                      (f"寄件網域 {wl_note.get('domain','')} 在白名單內，但沒有可信的驗證結果（例如貼信模式），"
                       'From 可以被偽造，因此不略過分析。'),
        })

    # 依最終風險產生可執行的安全處置建議。
    report['safety_actions'] = build_safety_actions(
        report['risk_level'], rules, html_findings, report.get('category', '')
    )

    # 給前端的多層分析資料。
    report['analysis_layers'] = {
        'rule': {
            'name': '規則引擎',
            'score': round(rule_component, 1),
            'raw_score': rule_score,
            'weight': (85 if llm_score is None else 70) if spam_prob is None else (42.5 if llm_score is None else 35),
            'status': '偵測到可疑規則' if rules else '未發現明顯規則異常',
            'findings': rules[:6]
        },
        'ml': {
            'name': 'ML 模型',
            'score': None if spam_prob is None else round(ml_component, 1),
            'probability': None if spam_prob is None else round(spam_prob * 100, 1),
            'weight': 0 if spam_prob is None else (42.5 if llm_score is None else 35),
            'status': ('不適用：' + ml_reason) if spam_prob is None else (
                '高度偏向釣魚信件' if spam_prob >= 0.7 else ('偏向釣魚信件' if spam_prob >= 0.3 else '偏向正常信件')),
            'reliable': spam_prob is not None,
            'coverage': ml_stats,
            'findings': [
                '未納入融合（原始輸出 %.1f%% 不可作為證據）' % (ml_raw_prob * 100)
            ] if spam_prob is None else [
                f'釣魚信件機率：{spam_prob:.1%}'
            ]
        },
        'html': {
            'name': 'HTML / URL',
            'score': round(html_component, 1),
            'raw_score': html_score,
            'weight': 15,
            'status': '偵測到 HTML / URL 風險' if html_findings else '未發現明顯 HTML / URL 異常',
            'findings': [
                f'{cat}：{item}'
                for cat, items in html_findings[:6]
                for item in items[:2]
            ]
        },
        'llm': {
            'name': 'AI Agent 調查',
            'score': round(llm_component, 1) if llm_component is not None else None,
            'weight': 15 if llm_score is not None else 0,
            'status': 'AI Agent 調查完成' if llm_score is not None else '本次未啟動（風險未達中等）或調查失敗',
            'findings': (agent_result['signal_labels'] if agent_result else [])[:6]
        }
    }

    # 調查過程（時間軸）：每一步用了什麼工具、查到什麼、對應哪些風險訊號。
    report['agent_trace'] = (agent_result or {}).get('trace', [])
    report['agent_meta'] = {
        'triggered': agent_result is not None,
        'pre_score': pre_score,
        'trigger_score': AGENT_TRIGGER_SCORE,
        'status': (agent_result or {}).get('status', 'skipped'),
        'error': (agent_result or {}).get('error', ''),
        'elapsed_s': (agent_result or {}).get('elapsed_s'),
        'signals': (agent_result or {}).get('signals', []),
    }

    if spam_prob is None:
        report['fusion_formula'] = (
            '規則 70% + HTML 15% + AI Agent 15%（ML 不適用，權重移給規則；Agent 只加分、不低於預估分數）'
            if llm_score is not None
            else '規則 85% + HTML 15%（ML 不適用，權重移給規則）'
        )
    else:
        report['fusion_formula'] = (
            '規則 35% + ML 35% + HTML 15% + AI Agent 15%（Agent 只加分、不低於三層融合分數）'
            if llm_score is not None
            else '規則 42.5% + ML 42.5% + HTML 15%'
        )

    return report, html_score, html_findings, rule_score, spam_prob

def gen_ir(email_data, report):
    incident_id = f"IR-{datetime.now().strftime('%Y%m%d')}-{str(uuid.uuid4())[:6].upper()}"
    risk = int(report.get('risk_score', 0))
    if risk >= 85:
        default_severity = 'Critical'
    elif risk >= 70:
        default_severity = 'High'
    else:
        default_severity = 'Medium'

    findings = report.get('explainable_findings', [])[:8]
    finding_text = '\n'.join(
        f"- {x.get('title','可疑特徵')}：{x.get('detail','')}" for x in findings
    ) or '- 未提供額外可疑特徵'

    prompt = (
        "You are a cybersecurity incident response analyst. Reply ONLY with valid JSON.\n"
        "Do not invent facts. Base the assessment only on the supplied email and detection evidence.\n"
        f"Email from: {email_data.get('sender','未知')}\n"
        f"Subject: {email_data.get('subject','未知')}\n"
        f"Risk score: {risk}/100\n"
        f"Detection evidence:\n{finding_text}\n"
        'JSON: {"severity":"Critical/High/Medium","impact_assessment":"繁體中文",'
        '"immediate_actions":["行動1","行動2","行動3"],'
        '"containment":"繁體中文", "verification":"繁體中文", "recovery":"繁體中文"}'
    )
    try:
        if not groq_client:
            raise RuntimeError('AI client unavailable')
        resp = groq_client.chat.completions.create(
            model='openai/gpt-oss-120b',
            messages=[{'role':'user','content':prompt}], temperature=0.2)
        raw = resp.choices[0].message.content.strip().replace('```json','').replace('```','').strip()
        ir = json.loads(raw)
    except Exception:
        ir = {
            'severity': default_severity,
            'impact_assessment': '依目前偵測結果，可能存在帳號遭竊、個資外洩或財務損失風險；實際影響仍需人工確認。',
            'immediate_actions': ['不要點擊連結或附件', '不要回覆或提供帳號密碼與個資', '依組織流程標記、隔離並通報可疑郵件'],
            'containment': '先停止與郵件中連結、附件及要求的外部服務互動；若已點擊或輸入資料，應立即通知資安人員。',
            'verification': '透過官方網站、已知電話或其他可信管道獨立確認寄件者與事件真實性。',
            'recovery': '若確認已受影響，依組織流程進行密碼重設、工作階段撤銷及必要的帳號與端點檢查。'
        }

    ir['incident_id'] = incident_id
    ir['created_at'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    ir['risk_score'] = risk
    ir['email_sender'] = email_data.get('sender', '')
    ir['email_subject'] = email_data.get('subject', '')
    ir['status'] = 'Open'
    ir.setdefault('severity', default_severity)
    ir.setdefault('immediate_actions', [])
    ir.setdefault('containment', '依組織資安事件處理流程進行隔離與通報。')
    ir.setdefault('verification', '使用可信管道確認事件。')
    ir.setdefault('recovery', '確認影響範圍後依流程復原。')
    return incident_id, ir


def ir_download_fields(ir_detail, sender, subject):
    """供前端「下載 IR 報告」使用的完整欄位（畫面上的摘要有截斷，下載檔不截斷）。"""
    return {
        'impact_full': ir_detail.get('impact_assessment', ''),
        'actions_full': ir_detail.get('immediate_actions', []),
        'email_sender': sender,
        'email_subject': subject,
    }


