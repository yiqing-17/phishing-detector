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
    '立即', '緊急', '即將停用', '馬上', '限時', '暫停', '停用'
]
BAIT_WORDS = [
    'free', 'winner', 'won', 'prize', 'claim', 'lucky', 'reward', 'gift',
    '中獎', '免費', '領取', '恭喜', '退款', '補助'
]
PERSONAL_WORDS = [
    'password', 'credit card', 'bank account', 'pin',
    '密碼', '帳號', '信用卡', '身分證', '帳戶'
]
MONEY_WORDS = [
    '$', 'cash', 'money', 'transfer', 'wire', 'payment', 'invoice',
    '匯款', '轉帳', '付款', 'NT$', '退款'
]


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

    hits = [w for w in URGENT_WORDS if _kw_hit(w, t)]
    if hits:
        score += len(hits) * 2
        triggered.append(f'緊急語句: {hits}')

    urls = re.findall(r'https?://[^\s<>"\']+', t)
    if urls:
        score += min(3 + len(urls), 8)
        triggered.append(f'含有連結: {urls[:2]}')

        for url in urls[:10]:
            url_findings = analyze_url(url)
            if url_findings:
                score += min(len(url_findings) * 2, 8)
                triggered.append(f'URL 風險: {url_findings[:4]}')

    hits2 = [w for w in BAIT_WORDS if _kw_hit(w, t)]
    if hits2:
        score += len(hits2) * 2
        triggered.append(f'誘騙話術: {hits2}')

    hits3 = [w for w in PERSONAL_WORDS if _kw_hit(w, t)]
    if hits3:
        score += len(hits3) * 3
        triggered.append(f'索取個資: {hits3}')

    hits4 = [w for w in MONEY_WORDS if _kw_hit(w, t)]
    if hits4:
        score += len(hits4) * 2
        triggered.append(f'金錢相關: {hits4}')

    return score, triggered


# 規則展示頁使用的規則目錄（關鍵字直接引用上方常數，與實際偵測邏輯同源）
RULE_KEYWORD_GROUPS = [
    ('R1', '緊急語句', '製造時間壓力，逼迫收件者倉促行動', URGENT_WORDS, '每命中 1 個詞 +2'),
    ('R2', '誘騙話術', '以獎金、免費、退款等利益誘使點擊', BAIT_WORDS, '每命中 1 個詞 +2'),
    ('R3', '索取個資', '要求提供密碼、卡號、帳戶等敏感資料', PERSONAL_WORDS, '每命中 1 個詞 +3'),
    ('R4', '金錢相關', '涉及匯款、付款、轉帳等金流指示', MONEY_WORDS, '每命中 1 個詞 +2'),
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


def build_explainable_findings(rules, html_findings, spam_prob, report):
    """把各分析層的原始證據整理成使用者看得懂的「為什麼可疑」。"""
    findings = []

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

    if spam_prob >= 0.70:
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
    ml_component = max(0, min(float(spam_prob) * 100, 100))

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
    ml_component = max(0, min(float(spam_prob) * 100, 100))
    html_component = min(max(float(html_score), 0) * 8, 100)

    if llm_score is not None:
        llm_component = max(0, min(float(llm_score), 100))
        rows = [
            ('規則引擎', rule_component, 35.0),
            ('ML 模型', ml_component, 35.0),
            ('HTML / URL', html_component, 15.0),
            ('AI 深度分析', llm_component, 15.0),
        ]
    else:
        llm_component = None
        rows = [
            ('規則引擎', rule_component, 42.5),
            ('ML 模型', ml_component, 42.5),
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

def full_pipeline(text, html=''):
    rule_score, rules = rule_based_score(text)

    # ML 模型使用 1 = phishing、0 = legitimate。
    if model is not None and vectorizer is not None:
        vec = vectorizer.transform([text])
        classes = list(model.classes_)
        phishing_index = classes.index(1) if 1 in classes else classes.index('1')
        spam_prob = float(model.predict_proba(vec)[0][phishing_index])
    else:
        spam_prob = 0.0

    html_score, html_findings = (0, [])
    if html:
        html_score, html_findings = analyze_html(html)

    # 有明顯證據才呼叫 LLM，降低不必要 API 成本。
    should_call_llm = (
        rule_score >= 4 or
        spam_prob >= 0.30 or
        html_score >= 4
    )

    if should_call_llm:
        report = ai_agent_analyze(text, rule_score, rules)
        llm_score = report.get('risk_score')
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
    ml_component = max(0, min(float(spam_prob) * 100, 100))
    html_component = min(html_score * 8, 100)
    llm_component = None if llm_score is None else max(0, min(float(llm_score), 100))

    # 最終風險分數由固定公式融合，不直接採用 LLM 自己的分數。
    final_score = calculate_risk_score(
        rule_score, spam_prob, html_score, llm_score
    )
    report = apply_risk_level(report, final_score)
    report['risk_breakdown'] = build_risk_breakdown(
        rule_score, spam_prob, html_score, llm_score
    )
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
        rules, html_findings, spam_prob, report
    )

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
            'weight': 42.5 if llm_score is None else 35,
            'status': '偵測到可疑規則' if rules else '未發現明顯規則異常',
            'findings': rules[:6]
        },
        'ml': {
            'name': 'ML 模型',
            'score': round(ml_component, 1),
            'probability': round(spam_prob * 100, 1),
            'weight': 42.5 if llm_score is None else 35,
            'status': '高度偏向釣魚信件' if spam_prob >= 0.7 else ('偏向釣魚信件' if spam_prob >= 0.3 else '偏向正常信件'),
            'findings': [
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
            'name': 'AI 深度分析',
            'score': round(llm_component, 1) if llm_component is not None else None,
            'weight': 15 if llm_score is not None else 0,
            'status': 'AI 分析完成' if llm_score is not None else '本次未呼叫或分析失敗',
            'findings': report.get('suspicious_points', [])[:6]
        }
    }

    report['fusion_formula'] = (
        '規則 35% + ML 35% + HTML 15% + AI 15%'
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


