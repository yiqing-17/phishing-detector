HOME_HTML = """<!DOCTYPE html>
<html lang="zh-TW">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>AI 釣魚信件偵測系統</title>
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=Noto+Sans+TC:wght@400;500;700&display=swap" rel="stylesheet">
    <style>
        * { box-sizing: border-box; margin: 0; padding: 0; }
        body {
            font-family: 'Inter', 'Noto Sans TC', -apple-system, BlinkMacSystemFont, sans-serif;
            background-color: #0b0f19;
            color: #e2e8f0;
            min-height: 100vh;
            line-height: 1.5;
        }
        .header {
            background: rgba(15, 23, 42, 0.85);
            backdrop-filter: blur(12px);
            border-bottom: 1px solid #1e293b;
            padding: 16px 32px;
            display: flex;
            align-items: center;
            justify-content: space-between;
            position: sticky;
            top: 0;
            z-index: 50;
        }
        .header h1 {
            font-size: 18px;
            font-weight: 700;
            color: #f8fafc;
            display: flex;
            align-items: center;
            gap: 10px;
        }
        .badge {
            background: rgba(56, 189, 248, 0.1);
            color: #38bdf8;
            font-size: 12px;
            font-weight: 600;
            padding: 4px 12px;
            border-radius: 9999px;
            border: 1px solid rgba(56, 189, 248, 0.25);
        }
        .container {
            max-width: 900px;
            margin: 0 auto;
            padding: 60px 24px;
            text-align: center;
        }
        h2 {
            font-size: 36px;
            font-weight: 700;
            color: #ffffff;
            margin-bottom: 16px;
            letter-spacing: -0.02em;
        }
        .sub {
            font-size: 16px;
            color: #94a3b8;
            max-width: 520px;
            margin: 0 auto 36px;
            line-height: 1.6;
        }
        .btn {
            display: inline-flex;
            align-items: center;
            gap: 12px;
            background: #ffffff;
            color: #0f172a;
            font-size: 15px;
            font-weight: 600;
            padding: 14px 28px;
            border-radius: 10px;
            text-decoration: none;
            transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
            box-shadow: 0 4px 12px rgba(0, 0, 0, 0.3);
        }
        .btn:hover {
            background: #f1f5f9;
            transform: translateY(-2px);
            box-shadow: 0 8px 24px rgba(255, 255, 255, 0.15);
        }
        .features {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(240px, 1fr));
            gap: 20px;
            margin-top: 56px;
            text-align: left;
        }
        .feat {
            background: #111827;
            border: 1px solid #1f2937;
            border-radius: 16px;
            padding: 28px 24px;
            text-align: center;
            transition: border-color 0.2s;
        }
        .feat:hover {
            border-color: #374151;
        }
        .feat .icon {
            font-size: 28px;
            margin-bottom: 12px;
        }
        .feat h3 {
            font-size: 15px;
            font-weight: 600;
            color: #f3f4f6;
            margin-bottom: 6px;
        }
        .feat p {
            font-size: 13px;
            color: #9ca3af;
            line-height: 1.6;
        }
        .whitelist-note {
            background: rgba(16, 185, 129, 0.08);
            border: 1px solid rgba(16, 185, 129, 0.25);
            border-radius: 12px;
            padding: 16px 20px;
            margin-top: 40px;
            font-size: 13px;
            color: #a7f3d0;
            text-align: left;
            line-height: 1.6;
        }
        .whitelist-note strong {
            color: #34d399;
        }
    </style>
</head>
<body>
    <div class="header">
        <h1>🛡️ AI 釣魚信件偵測系統</h1>
        <span class="badge">畢業專題</span>
    </div>
    <div class="container">
        <h2>一鍵掃描你的 Gmail</h2>
        <p class="sub">授權後系統自動掃描最新 15 封信件，用 AI 識別釣魚攻擊並產生詳細分析報告。</p>
        <a href="/login" class="btn">
            <svg width="20" height="20" viewBox="0 0 48 48">
                <path fill="#4285F4" d="M45.12 24.5c0-1.56-.14-3.06-.4-4.5H24v8.51h11.84c-.51 2.75-2.06 5.08-4.39 6.64l7.08 5.51C42.45 36.27 45.12 30.87 45.12 24.5z"/>
                <path fill="#FBBC05" d="M10.53 28.59c-.48-1.45-.76-2.99-.76-4.59s.27-3.14.76-4.59l-7.98-6.19C.92 16.46 0 20.12 0 24c0 3.88.92 7.54 2.56 10.78l7.97-6.19z"/>
                <path fill="#34A853" d="M24 48c6.48 0 11.93-2.13 15.89-5.81l-7.08-5.51c-2.13 1.45-4.84 2.3-8.81 2.3-6.72 0-12.43-4.54-14.47-10.64l-7.98 6.19C5.22 42.79 14.04 48 24 48z"/>
                <path fill="#EA4335" d="M24 4.8L6.4 19.2V43.2h10.4V28.8h14.4v14.4H41.6V19.2z"/>
            </svg>
            使用 Google 帳號授權
        </a>
        <div class="features">
            <div class="feat">
                <div class="icon">🔍</div>
                <h3>三層 AI 分析</h3>
                <p>規則引擎 + ML + LLaMA 3.3 深度分析</p>
            </div>
            <div class="feat">
                <div class="icon">🌐</div>
                <h3>HTML 多模態</h3>
                <p>偵測像素追蹤、偽裝連結、隱藏元素</p>
            </div>
            <div class="feat">
                <div class="icon">📄</div>
                <h3>IR 事件報告</h3>
                <p>高風險信件自動產生資安事件通報</p>
            </div>
        </div>
        <div class="whitelist-note">
            <strong>✅ 白名單已啟用：</strong>
            SKIMS、lululemon、Alo Yoga、玉山銀行、Google 等已知安全寄件者將直接標記為安全，不進行 AI 分析。
        </div>
    </div>
</body>
</html>"""

LOADING_HTML = """<!DOCTYPE html>
<html lang="zh-TW">
<head>
    <meta charset="UTF-8">
    <meta http-equiv="refresh" content="3;url=/result">
    <title>掃描中...</title>
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;600&family=Noto+Sans+TC:wght@400;600&display=swap" rel="stylesheet">
    <style>
        * { box-sizing: border-box; margin: 0; padding: 0; }
        body {
            font-family: 'Inter', 'Noto Sans TC', -apple-system, sans-serif;
            background-color: #0b0f19;
            color: #e2e8f0;
            min-height: 100vh;
            display: flex;
            align-items: center;
            justify-content: center;
            flex-direction: column;
            gap: 20px;
        }
        .spinner {
            width: 56px;
            height: 56px;
            border: 4px solid #1e293b;
            border-top: 4px solid #38bdf8;
            border-radius: 50%;
            animation: spin 1s cubic-bezier(0.55, 0.15, 0.45, 0.85) infinite;
        }
        @keyframes spin {
            to { transform: rotate(360deg); }
        }
        h2 {
            font-size: 22px;
            font-weight: 600;
            color: #f8fafc;
        }
        p {
            font-size: 14px;
            color: #94a3b8;
        }
    </style>
</head>
<body>
    <div class="spinner"></div>
    <h2>正在掃描你的 Gmail...</h2>
    <p>三層 AI 分析引擎運作中，請稍候</p>
</body>
</html>"""

RESULT_HTML = """<!DOCTYPE html>
<html lang="zh-TW">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>掃描結果 — AI 釣魚信件偵測系統</title>
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500&family=Noto+Sans+TC:wght@400;500;700&display=swap" rel="stylesheet">
    <style>
        * { box-sizing: border-box; margin: 0; padding: 0; }
        body {
            font-family: 'Inter', 'Noto Sans TC', -apple-system, BlinkMacSystemFont, sans-serif;
            background-color: #0b0f19;
            color: #e2e8f0;
            min-height: 100vh;
            line-height: 1.5;
        }
        .header {
            background: rgba(15, 23, 42, 0.85);
            backdrop-filter: blur(12px);
            border-bottom: 1px solid #1e293b;
            padding: 16px 32px;
            display: flex;
            align-items: center;
            justify-content: space-between;
            position: sticky;
            top: 0;
            z-index: 50;
        }
        .header h1 {
            font-size: 18px;
            font-weight: 700;
            color: #f8fafc;
        }
        .header-right {
            display: flex;
            align-items: center;
            gap: 12px;
        }
        .scan-time {
            font-size: 12px;
            color: #94a3b8;
            font-family: 'JetBrains Mono', monospace;
        }
        .container {
            max-width: 900px;
            margin: 0 auto;
            padding: 32px 20px 60px;
        }
        .back {
            display: inline-flex;
            align-items: center;
            gap: 8px;
            background: #1e293b;
            color: #38bdf8;
            font-size: 13px;
            font-weight: 500;
            padding: 8px 16px;
            border-radius: 8px;
            text-decoration: none;
            border: 1px solid #334155;
            margin-bottom: 24px;
            transition: all 0.2s;
        }
        .back:hover {
            background: #334155;
            color: #7dd3fc;
        }
        .summary {
            background: #111827;
            border: 1px solid #1f2937;
            border-radius: 16px;
            padding: 24px 32px;
            margin-bottom: 32px;
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(110px, 1fr));
            gap: 16px;
            align-items: center;
        }
        .stat {
            text-align: center;
        }
        .stat .num {
            font-size: 32px;
            font-weight: 700;
            line-height: 1.2;
        }
        .stat .lbl {
            font-size: 12px;
            color: #9ca3af;
            margin-top: 4px;
            font-weight: 500;
        }
        .high .num { color: #f87171; }
        .med .num { color: #fbbf24; }
        .low .num { color: #34d399; }
        .total .num { color: #38bdf8; }
        .skip .num { color: #64748b; }

        .sec-title {
            font-size: 16px;
            font-weight: 600;
            color: #f3f4f6;
            margin: 32px 0 16px;
            display: flex;
            align-items: center;
            gap: 8px;
        }
        .card {
            background: #111827;
            border: 1px solid #1f2937;
            border-radius: 12px;
            padding: 20px 24px;
            margin-bottom: 14px;
            position: relative;
            transition: border-color 0.2s;
        }
        .card:hover {
            border-color: #374151;
        }
        .card.h { border-left: 4px solid #ef4444; }
        .card.m { border-left: 4px solid #f59e0b; }
        .card.l { border-left: 4px solid #10b981; }
        .card.w { border-left: 4px solid #64748b; opacity: 0.75; }

        .top {
            display: flex;
            justify-content: space-between;
            align-items: flex-start;
            gap: 16px;
            margin-bottom: 10px;
        }
        .subj {
            font-size: 15px;
            font-weight: 600;
            color: #f9fafb;
            line-height: 1.4;
        }
        .from {
            font-size: 13px;
            color: #9ca3af;
            margin-top: 4px;
        }
        .rb {
            font-size: 11px;
            font-weight: 700;
            padding: 4px 10px;
            border-radius: 6px;
            white-space: nowrap;
            letter-spacing: 0.05em;
        }
        .bh { background: rgba(239, 68, 68, 0.15); color: #f87171; border: 1px solid rgba(239, 68, 68, 0.3); }
        .bm { background: rgba(245, 158, 11, 0.15); color: #fbbf24; border: 1px solid rgba(245, 158, 11, 0.3); }
        .bl { background: rgba(16, 185, 129, 0.15); color: #34d399; border: 1px solid rgba(16, 185, 129, 0.3); }
        .bw { background: rgba(100, 116, 139, 0.15); color: #94a3b8; border: 1px solid rgba(100, 116, 139, 0.3); }

        .exp {
            font-size: 13px;
            color: #cbd5e1;
            margin-top: 10px;
            line-height: 1.6;
        }
        .act {
            font-size: 13px;
            color: #38bdf8;
            margin-top: 10px;
            font-weight: 500;
            display: flex;
            align-items: center;
            gap: 6px;
        }
        .tags {
            margin-top: 12px;
            display: flex;
            flex-wrap: wrap;
            gap: 6px;
        }
        .tag {
            font-size: 11px;
            color: #f59e0b;
            background: rgba(245, 158, 11, 0.1);
            padding: 3px 8px;
            border-radius: 4px;
            border: 1px solid rgba(245, 158, 11, 0.2);
        }
        .sc {
            font-size: 11px;
            color: #64748b;
            margin-top: 12px;
            font-family: 'JetBrains Mono', monospace;
        }
        .ir {
            background: rgba(16, 185, 129, 0.05);
            border: 1px solid rgba(16, 185, 129, 0.2);
            border-radius: 8px;
            padding: 14px 16px;
            margin-top: 14px;
        }
        .ir-t {
            font-size: 12px;
            font-weight: 600;
            color: #34d399;
            margin-bottom: 4px;
        }
        .ir-id {
            font-size: 11px;
            color: #94a3b8;
            font-family: 'JetBrains Mono', monospace;
        }
        .ir-b {
            font-size: 12px;
            color: #a7f3d0;
            margin-top: 6px;
            line-height: 1.5;
        }
        .ir-actions {
            margin-top: 8px;
        }
        .ir-action {
            font-size: 12px;
            color: #6ee7b7;
            margin-top: 4px;
        }
    </style>
</head>
<body>
    <div class="header">
        <h1>🛡️ AI 釣魚信件偵測系統</h1>
        <div class="header-right">
            <span class="scan-time">掃描時間：{{scan_time}}</span>
        </div>
    </div>
    <div class="container">
        <a href="/" class="back">← 重新掃描</a>

        <div class="summary">
            <div class="stat total"><div class="num">{{total}}</div><div class="lbl">掃描封數</div></div>
            <div class="stat high"><div class="num">{{high}}</div><div class="lbl">🚨 高風險</div></div>
            <div class="stat med"><div class="num">{{med}}</div><div class="lbl">⚠️ 中風險</div></div>
            <div class="stat low"><div class="num">{{low}}</div><div class="lbl">✅ 安全</div></div>
            <div class="stat skip"><div class="num">{{whitelist_count}}</div><div class="lbl">🔒 白名單</div></div>
            <div class="stat skip"><div class="num">{{skipped}}</div><div class="lbl">⏭️ 略過</div></div>
        </div>

        {% if high_emails %}
        <div class="sec-title">🚨 高風險信件（請立即處理）</div>
        {% for e in high_emails %}
        <div class="card h">
            <div class="top">
                <div>
                    <div class="subj">{{e.subject}}</div>
                    <div class="from">{{e.sender}}</div>
                </div>
                <span class="rb bh">HIGH {{e.risk_score}}/100</span>
            </div>
            <div class="exp">{{e.explanation}}</div>
            <div class="act">📋 {{e.recommended_action}}</div>
            {% if e.html_findings %}
            <div class="tags">
                {% for f in e.html_findings %}
                <span class="tag">{{f}}</span>
                {% endfor %}
            </div>
            {% endif %}
            <div class="sc">規則: {{e.rule_score}}分 | ML: {{e.ml_prob}} | HTML: +{{e.html_score}}分</div>
            {% if e.ir_id %}
            <div class="ir">
                <div class="ir-t">📄 IR 事件通報報告已自動產生</div>
                <div class="ir-id">{{e.ir_id}} | 嚴重等級: {{e.ir_severity}}</div>
                <div class="ir-b">{{e.ir_summary}}</div>
                {% if e.ir_actions %}
                <div class="ir-actions">
                    {% for a in e.ir_actions %}
                    <div class="ir-action">• {{a}}</div>
                    {% endfor %}
                </div>
                {% endif %}
            </div>
            {% endif %}
        </div>
        {% endfor %}
        {% endif %}

        {% if med_emails %}
        <div class="sec-title">⚠️ 中風險信件</div>
        {% for e in med_emails %}
        <div class="card m">
            <div class="top">
                <div>
                    <div class="subj">{{e.subject}}</div>
                    <div class="from">{{e.sender}}</div>
                </div>
                <span class="rb bm">MED {{e.risk_score}}/100</span>
            </div>
            <div class="exp">{{e.explanation}}</div>
            <div class="act">📋 {{e.recommended_action}}</div>
            {% if e.html_findings %}
            <div class="tags">
                {% for f in e.html_findings %}
                <span class="tag">{{f}}</span>
                {% endfor %}
            </div>
            {% endif %}
            <div class="sc">規則: {{e.rule_score}}分 | ML: {{e.ml_prob}} | HTML: +{{e.html_score}}分</div>
        </div>
        {% endfor %}
        {% endif %}

        {% if low_emails %}
        <div class="sec-title">✅ 安全信件</div>
        {% for e in low_emails %}
        <div class="card l">
            <div class="top">
                <div>
                    <div class="subj">{{e.subject}}</div>
                    <div class="from">{{e.sender}}</div>
                </div>
                <span class="rb bl">LOW {{e.risk_score}}/100</span>
            </div>
            <div class="exp">{{e.explanation}}</div>
        </div>
        {% endfor %}
        {% endif %}

        {% if whitelist_emails %}
        <div class="sec-title">🔒 白名單信件（已知安全，略過分析）</div>
        {% for e in whitelist_emails %}
        <div class="card w">
            <div class="top">
                <div>
                    <div class="subj">{{e.subject}}</div>
                    <div class="from">{{e.sender}}</div>
                </div>
                <span class="rb bw">白名單</span>
            </div>
        </div>
        {% endfor %}
        {% endif %}

    </div>
</body>
</html>"""
