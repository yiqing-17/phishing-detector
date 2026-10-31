(function (root, factory) {
  const api = factory();
  if (typeof module === 'object' && module.exports) module.exports = api;
  if (root && root.document) api.start(root);
})(typeof globalThis !== 'undefined' ? globalThis : this, function () {
  'use strict';

  const text = {
    '偵測規則': 'Detection rules',
    '偵測規則一覽': 'Detection rules',
    '白名單': 'Allowlist',
    '白名單設定': 'Allowlist settings',
    '案件簿': 'Scan history',
    '貼信送檢': 'Analyze an email',
    '直接貼信送檢': 'Analyze an email',
    'Google 登入': 'Connect Gmail',
    '授權 Google 送檢': 'Analyze Gmail',
    '安全掃描 Gmail，快速找出可疑郵件': 'Inspect suspicious email, one clue at a time',
    '四層分析 / 案件檢視': 'Email forensics / case review',
    '授權 Google 後掃描最新 15 封郵件，結合規則引擎、機器學習、URL / HTML 解析與 AI 語意判讀，快速找出可疑信件。': 'Connect Gmail to inspect your 15 most recent inbox messages with four layers: rules, machine learning, URL and HTML checks, and AI-assisted review.',
    '不想連接 Gmail？直接貼信送檢': 'Prefer not to connect Gmail? Paste an email instead.',
    '看起來安全': 'Looks safe',
    '這是釣魚信': 'This is phishing',
    '四層分析，逐層交叉比對': 'Four layers examine the same message',
    '這封信，你會信嗎？': 'Would you trust this email?',
    '先憑直覺判斷，再看四層分析怎麼拆這封信。範例皆為虛構郵件；第 1 層的命中詞由實際規則詞庫即時比對，其餘三層為預先寫好的示意，並非即時模型輸出。': 'Make your call, then see how each layer examines the message. All examples are fictional. Rule matches use the live rules; the other three layers are demonstrations, not live model output.',
    'ML 模型測試結果': 'Machine-learning model results',
    '白名單機制已啟用': 'Allowlist hints are enabled',
    '白名單只提供網域比對提示；所有郵件仍會完成四層分析。': 'Allowlist matches are domain hints; every message still goes through all four analysis layers.',
    '加入白名單只會顯示網域比對提示，不會略過分析或保證郵件安全；寄件者欄位可能遭偽冒。': 'Allowlist entries are domain hints only. They do not skip analysis or prove sender identity; sender addresses can be spoofed.',
    '白名單命中只作為網域提示；每封郵件仍會進入四層分析。': 'An allowlist match is only a domain hint; every email still goes through all four analysis layers.',
    '白名單提示 · 仍完成分析': 'Allowlist hint · analysis completed',
    '網域比對提示': 'Domain match hint',
    '開啟郵件分析結果': 'Open email analysis',
    '者僅代表網域比對命中；所有郵件仍完成四層分析。': ' is only a domain match; every email still goes through all four analysis layers.',
    '白名單演示 ①：google.com 寄件網域命中（仍進行分析）': 'Allowlist demo 1: sender domain matches google.com (still analyzed)',
    '已知安全網域自動略過重複分析。': 'Allowlist matches are a domain hint; every message still goes through all four analysis layers.',
    '查看白名單': 'Review allowlist',
    '找出可疑郵件': 'Find suspicious email',
    '送檢中': 'Analysis in progress',
    '正在掃描你的 Gmail': 'Scanning your Gmail',
    '正在分析郵件': 'Analyzing email',
    '檢驗報告': 'Analysis report',
    '分析報告': 'Analysis report',
    '案件退回': 'Analysis could not be completed',
    '查無此案': 'Page not found',
    '內容過大': 'Message is too large',
    'Google Gmail 授權失敗': 'Gmail authorization failed',
    '找不到你要的頁面，可能已經移走，或網址打錯了。': 'We could not find that page. It may have moved, or the address may be incorrect.',
    '郵件內容太長，請縮短後再送檢。': 'This email is too long. Shorten it and try again.',
    '系統暫時發生錯誤，請稍後再試。': 'Something went wrong. Please try again later.',
    '請確認 Google OAuth 的重新導向 URI、Client ID / Secret 與 Gmail API 設定。': 'Check the Google OAuth redirect URI, client ID and secret, and Gmail API settings.',
    '偵測規則 R': 'Detection rules R',
    '白名單 W': 'Allowlist W',
    '案件簿 L': 'History L',
    '貼信送檢 P': 'Paste email P',
    'FILE 四層分析 / 案件檢視': 'FILE Email forensics / case review',
    '安全掃描 Gmail，快速找出': 'Inspect Gmail for',
    '可疑': 'Suspicious',
    '授權 Google 後掃描最新 15 封郵件': 'Inspect your 15 most recent inbox messages',
    '結合規則引擎、機器學習、URL / HTML 解析與 AI 語意判讀，快速找出可疑信件。': 'using rules, machine learning, URL and HTML checks, and AI-assisted review.',
    'FILE 02': 'FILE 02',
    'pipeline': 'four-layer review',
    '四層分析，': 'Four layers',
    '逐層': 'examine',
    '交叉比對': 'the message',
    '風險累積（示意）': 'Illustrative risk score',
    '待分析': 'Not analyzed',
    '往下捲動，逐層看這封信是怎麼被拆開的。數值為示意，非實際評分公式。': 'Scroll to see how each layer inspects the message. Scores are illustrative, not the live scoring formula.',
    '規則引擎': 'Rule engine',
    '已知釣魚樣式與關鍵字比對': 'Matches known phishing patterns and keywords',
    'ML 模型': 'Machine-learning model',
    '整體用詞接近釣魚樣本': 'Language resembles phishing examples',
    'URL / HTML 解析': 'URL / HTML inspection',
    '連結還原、追蹤像素、隱藏元素偵測': 'Checks link destinations, tracking pixels, and hidden elements',
    'AI 語意判讀': 'AI-assisted review',
    '交叉比對郵件意圖與敏感資訊索取': 'Reviews intent and requests for sensitive information',
    '這封信，': 'Would you trust',
    '你': 'this email?',
    '會信嗎？': '',
    'ML 模型': 'Machine-learning model',
    '測試結果': 'test results',
    '資料集　Phishing Email Dataset，清理後 82,077 筆（訓練 65,661 / 測試 16,416）': 'Dataset: Phishing Email Dataset; 82,077 cleaned messages (65,661 train / 16,416 test).',
    '以上僅為第 2 層 ML 模型在測試資料上的表現，不代表整體四層系統在真實信箱中的準確率。': 'These results describe only the second-layer model on its test set. They do not represent the four-layer system’s accuracy on real inboxes.',
    '白名單機制': 'Allowlist',
    '已啟用': 'hints enabled',
    '白名單提示': 'Allowlist hint',
    '寄件者': 'Sender',
    '主　旨': 'Subject',
    '原信批註': 'Email annotations',
    '四層檢驗': 'Four-layer findings',
    '四層各自獨立打分，再依固定權重融合成最終分數。': 'Each layer scores the message independently. The system combines those scores using fixed weights.',
    'AI 分析說明': 'Analysis summary',
    '為什麼會被判定為可疑？': 'Why was this flagged?',
    '各層偵測證據': 'Evidence by layer',
    '建議行動': 'Recommended next steps',
    '高風險': 'High risk',
    '中風險': 'Medium risk',
    '低風險': 'Low risk',
    '安全': 'Lower risk',
    '正在載入': 'Loading',
    '上一封': 'Previous email',
    '下一封': 'Next email',
    '案件總覽': 'Scan overview',
    '目前沒有案件紀錄': 'No scans yet',
    '尚無案件紀錄': 'No scan history yet',
    '搜尋案件': 'Search scans',
    '全部風險': 'All risk levels',
    '全部': 'All',
    '重新掃描': 'Scan again',
    '規則引擎原始分數': 'Raw rule-engine score',
    '輸入文字': 'Enter text',
    '命中標記': 'Matched rules',
    '搜尋關鍵字': 'Search keywords',
    '試試看': 'Try it',
    '關鍵字規則 R1–R6': 'Keyword rules R1–R6',
    'URL 結構 U1–U8': 'URL rules U1–U8',
    'HTML 結構 H1–H7': 'HTML rules H1–H7',
    '融合與分級': 'Score fusion and risk levels',
    '搜尋關鍵字，例如 密碼、verify…': 'Search keywords, e.g. password, verify…',
    '貼上一段文字，命中的關鍵字會被螢光筆標出，並依下方 R1–R5 的計分方式估算。僅為前端示意，不含 URL / HTML 結構規則、ML 與 AI 判讀，實際結果以後端為準。': 'Paste text to highlight rule matches. This front-end example estimates R1–R5 only; it does not run URL, HTML, machine-learning, or AI checks. The server scan is the actual result.',
    '輸入文字': 'Enter text',
    '偵測規則一覽': 'Detection rules',
    '貼上郵件，直接送檢': 'Paste an email to analyze it',
    '請貼上郵件內文再送出。': 'Paste the email body before submitting.',
    '若有郵件的 HTML 原始碼，可貼於此處以啟用多模態偵測...': 'Paste the email HTML source here to enable HTML checks…',
    '送檢': 'Analyze email',
    '送出後會進行完整的四層分析': 'The message will go through all four analysis layers.',
    '調閱範例': 'Load example',
    '調閱 .eml 檔': 'Open .eml file',
    '貼上郵件內文': 'Paste the email body',
    '寄件者信箱': 'Sender email',
    '郵件主旨': 'Email subject',
    '例如：example.com': 'e.g. example.com',
    '例如：no-reply@accounts.google.com': 'e.g. no-reply@accounts.google.com',
    '選填，用於白名單比對，例如 service@example.com': 'Optional; used for allowlist matching, e.g. service@example.com',
    '貼上郵件的純文字內容（必填）...': 'Paste the email text (required)…',
    '若有郵件的 HTML 原始碼，可貼於此處以啟用多模態偵測...': 'Optional: paste the email HTML source to enable HTML checks…',
    '選擇範例': 'Choose an example',
    '重播': 'Replay',
    '查看': 'View',
    '返回首頁': 'Back to home',
    '回首頁': 'Home',
    '重新開始': 'Start over',
    '新增': 'Add',
    '發放': 'Add domain',
    '發放通行': 'Add to allowlist',
    '重發預設通行': 'Restore defaults',
    '比對檢測': 'Test a sender',
    '目前白名單': 'Current allowlist',
    '檢測': 'Check sender',
    '撤銷': 'Remove',
    '預設網域': 'Default domain',
    '目前白名單網域': 'Allowlisted domains',
    '比對方式：完全相同／子網域': 'Exact domain or subdomain match',
    '請輸入網域': 'Enter a domain',
    '白名單數量已達上限（300）': 'The allowlist has reached its limit (300).',
    '網域格式不正確，請輸入例如 example.com': 'Invalid domain. Enter a domain such as example.com.',
    '網域格式不正確': 'Invalid domain format.',
    '這個網域已經在白名單中': 'This domain is already on the allowlist.',
    '系統暫時發生錯誤，請稍後再試。': 'Something went wrong. Please try again later.',
    '找不到 Google OAuth 設定。': 'Google OAuth is not configured.',
    '案件簿': 'Scan history',
    '白名單設定': 'Allowlist settings',
    '偵測規則': 'Detection rules',
    '清除篩選': 'Clear filters',
    '找不到符合條件的紀錄': 'No scans match these filters.',
    '共': 'Total',
    '封': 'messages',
    '安全掃描': 'Email scan',
    '寄件網域命中白名單者直接略過全部分析。': 'Whitelist matches are only a domain hint; every message still goes through all four analysis layers.',
    '目前沒有白名單網域': 'No allowlisted domains yet',
    '請輸入寄件者信箱，例如 name@example.com': 'Enter a sender address, e.g. name@example.com',
    '目前白名單（': 'Current allowlist (',
    ' 個）': ' domains)',
    '已放行 CLEARED': 'Allowlist hint',
    '安全掃描 Gmail': 'Scan Gmail',
    '分析完成': 'Analysis complete',
    '正在掃描': 'Scanning',
    '請稍候': 'Please wait',
    '郵件內容': 'Email body',
    '查看規則': 'View rules',
    '查看白名單': 'View allowlist',
    '找出可疑': 'Find suspicious',
    '郵件分析': 'Email analysis',
    '隱私說明': 'Privacy',
    'phishing-detector｜找出可疑郵件': 'phishing-detector | Find suspicious email',
    '郵件': 'Email',
    '主 旨': 'Subject',
    '您的帳戶已被暫停': 'Your account has been suspended',
    '親愛的客戶：': 'Dear customer,',
    '我們偵測到您的帳戶有異常登入行為。': 'We detected unusual sign-in activity on your account.',
    '請': 'Please ',
    '立即': 'immediately ',
    '點擊': 'click ',
    '驗證帳戶': 'verify your account',
    '，並': ', and ',
    '回覆您的帳號密碼與': 'reply with your account password and ',
    '信用卡號': 'credit card number',
    '，否則帳戶將於': ', or your account will be ',
    '24 小時內': 'within 24 hours',
    '永久停用。': 'permanently disabled.',
    '將游標移到「驗證帳戶」上，看它真正會連到哪裡。': 'Hover over “verify your account” to reveal the real destination.',
    '規則引擎：命中急迫語氣': 'Rule engine: urgent language',
    'ML 模型：整體用詞接近釣魚樣本': 'ML model: wording resembles phishing examples',
    'URL / HTML 解析：顯示文字與實際連結需還原比對': 'URL / HTML inspection: compares link text with its actual destination',
    'AI 語意判讀：索取敏感資訊': 'AI-assisted review: asks for sensitive information',
    '↙ 四個破綻，': '↙ Four clues. ',
    '滑過看看': 'Hover to explore',
    '示意郵件，非真實案例。滑過標記可對照批註，點擊印章可重播。': 'Fictional example. Hover over a marked clue to see its annotation; activate the stamp to replay.',
    '回覆您的帳號密碼與信用卡號': 'reply with your password and credit card number',
    '第 3 層會把連結還原：顯示文字與真正網址是否一致。': 'Layer 3 resolves links and checks whether their text matches the destination.',
    '例：': 'Example: ',
    '例：整體用詞特徵': 'Example: wording patterns',
    '顯示文字': 'Displayed text',
    '≠ 實際連結': '≠ actual destination',
    '索取密碼': 'Requests a password',
    '猜猜看': 'Test your instincts',
    '答對 0': 'Correct: 0',
    '資料集 Phishing Email Dataset，清理後 82,077 筆（訓練 65,661 / 測試 16,416）': 'Dataset: Phishing Email Dataset; 82,077 cleaned messages (65,661 train / 16,416 test).',
    '已放行': 'Domain hint',
    '送檢中｜phishing-detector': 'Analysis in progress | phishing-detector',
    '唯讀授權，只讀取收件匣最新 15 封信。每檢驗完一封，右邊就蓋上一枚印章。': 'Read-only access checks your 15 most recent inbox messages. Each completed scan adds a stamp to the case file.',
    '已等待 0 秒': 'Waiting: 0 seconds',
    '連線 Gmail，讀取最新信件': 'Connecting to Gmail and loading recent email',
    '逐封檢驗': 'Analyzing each message',
    '整理檢驗報告': 'Preparing the report',
    '注意': 'Caution',
    '白名單／略過': 'System messages skipped',
    '略過（系統通知）': 'System messages skipped',
    '案件牆': 'Case wall',
    '每一格是一封信。印章顏色是該封信的風險等級，進度來自後端實際完成的封數。': 'Each tile represents an email. Stamp colors show its risk level; progress reflects messages actually analyzed.',
    '退回': 'Could not complete',
    '改用貼信送檢': 'Paste an email instead',
    '貼信送檢｜phishing-detector': 'Analyze an email | phishing-detector',
    '不需要 Google 帳號授權，將郵件的寄件者、主旨與內文貼上即可，系統會以相同的三層式（規則引擎 + ML + HTML / URL + AI）架構進行分析。': 'No Google sign-in is needed. Paste the sender, subject, and body to use the same four-layer analysis: rules, machine learning, HTML and URL checks, and AI-assisted review.',
    '快速調閱測試信件': 'Load a sample email',
    '請選擇測試範例': 'Choose a sample',
    '帳戶停用釣魚信': 'Account suspension phishing',
    '中獎詐騙信': 'Prize scam',
    '假物流通知': 'Fake delivery notice',
    '正常商業信件': 'Legitimate business email',
    '白名單演示 ①：google.com 官方寄件者（會被略過）': 'Allowlist demo 1: sender using google.com (still analyzed)',
    '白名單演示 ②：偽冒網域 google.com.verify-login.xyz（不會被略過）': 'Allowlist demo 2: spoofed domain google.com.verify-login.xyz (analyzed)',
    '選擇範例後按「調閱範例」，系統會直接填入郵件欄位，不依賴 JavaScript。': 'Choose a sample and select “Load example” to fill in the email fields.',
    '待檢驗郵件': 'Email to analyze',
    '放開以調閱 .eml 檔': 'Drop an .eml file to load it',
    '附件：HTML 原始碼（選填，用於偵測像素追蹤／偽裝連結等）': 'Email HTML source (optional; used to inspect tracking pixels and deceptive links)',
    '在大部分信箱可透過「顯示原始郵件 / 檢視原始碼」取得 HTML 內容。': 'Most email clients provide HTML through “Show original” or “View source.”',
    '預檢標記（即時）': 'Live preview',
    '規則分數 0 → 正規化 0 / 100（僅 R1–R5）': 'Rule score 0 → normalized 0 / 100 (R1–R5 only)',
    '這只是規則引擎關鍵字與連結的前端預覽，送出後才會進行完整的四層分析。': 'This preview checks rule-engine keywords and links only. Full four-layer analysis starts when you submit.',
    '檢驗報告｜phishing-detector': 'Analysis report | phishing-detector',
    '掃描封數': 'Messages scanned',
    '略過': 'Skipped',
    '風險分布': 'Risk distribution',
    '已分析：ANALYZED_COUNT 封': 'Analyzed: ANALYZED_COUNT messages',
    '高風險優先顯示': 'High-risk messages first',
    '案件清單': 'Message list',
    '案件簿｜phishing-detector': 'Scan history | phishing-detector',
    '最近 20 次掃描的風險分布。每一列是一次掃描，色條依比例顯示各風險等級的郵件數量。': 'Risk distribution for the 20 most recent scans. Each row is one scan; bars show the share at each risk level.',
    '掃描次數': 'Scans',
    '郵件總數': 'Messages',
    '近期案件': 'Recent scans',
    '尚無案件': 'No scans yet',
    '案件簿還是空的，': 'Your scan history is empty. ',
    '送出第一批信件': 'Analyze your first email',
    '偵測規則｜phishing-detector': 'Detection rules | phishing-detector',
    '以下為系統實際使用中的規則（關鍵字清單直接讀取自偵測程式，與實際判斷同源）。規則引擎僅是四層分析中的第一層，其分數會再與 ML、HTML/URL、AI 判讀依固定權重融合。': 'These are the rules used by the system. The rule engine is the first of four layers; its score is combined with machine learning, HTML and URL checks, and AI-assisted review using fixed weights.',
    '關鍵字（4 類）': 'Keywords (4 groups)',
    'URL 結構規則': 'URL rules',
    'HTML 結構規則': 'HTML rules',
    '白名單網域': 'Allowlisted domains',
    '親愛的客戶，您的帳戶將於 24 小時內停用，請立即點擊 https://example.com/verify 驗證密碼。': 'Dear customer, your account will be suspended within 24 hours. Click https://example.com/verify now to verify your password.',
    '→ 正規化': '→ normalized',
    '第一層：規則引擎（郵件文字）': 'Layer 1: Rule engine (email text)',
    '命中即累加原始規則分數，並將觸發的規則與命中詞記錄於結果頁。關鍵字比對皆不分大小寫，同時涵蓋英文與繁體中文。': 'Matches add to the raw rule score. Triggered rules and terms appear in the report. Matching is case-insensitive and supports English and Traditional Chinese.',
    '+min(3 + 連結數, 8)': '+min(3 + link count, 8)',
    '含有連結': 'Contains a link',
    '郵件內文出現 http(s) 網址': 'An http(s) URL appears in the email body',
    '每個網址 +min(2×命中數, 8)': 'Each URL: +min(2 × matches, 8)',
    'URL 風險': 'URL risk',
    '對內文每個網址（最多 10 個）套用 U1–U8': 'Apply U1–U8 to each URL in the body (up to 10)',
    '規則分數會正規化為': 'The rule score is normalized to',
    'min(原始分數 × 5, 100)': 'min(raw score × 5, 100)',
    'URL 結構規則 U1–U8': 'URL structure rules U1–U8',
    '只解析網址字串，不連線、不開啟目標網站。': 'URLs are parsed as text; the target sites are never contacted or opened.',
    '第三層：HTML 結構規則 H1–H7': 'Layer 3: HTML structure rules H1–H7',
    '僅在郵件含 HTML 時執行。': 'Runs only when the email contains HTML.',
    'HTML 分數會正規化為': 'The HTML score is normalized to',
    '各層分數依固定權重融合；寄件網域命中': 'Layer scores are combined using fixed weights; an allowlist domain match',
    '有 AI 判讀': 'AI review enabled',
    '規則 35%': 'Rules: 35%',
    'rule_score ≥ 4、ML 機率 ≥ 0.30、html_score ≥ 4 任一成立才呼叫 AI。': 'AI runs when rule_score ≥ 4, ML probability ≥ 0.30, or html_score ≥ 4.',
    '無 AI 判讀': 'Without AI review',
    '規則 42.5%': 'Rules: 42.5%',
    'AI 未觸發或失敗時自動改用。': 'Used automatically when AI is not triggered or fails.',
    '風險等級': 'Risk level',
    '白名單｜phishing-detector': 'Allowlist | phishing-detector',
    '加入白名單後，來自該網域及其子網域的信件將直接標記為安全，不進行 AI 分析。請只加入確定可信任的網域。': 'Allowlist entries are domain hints only. They do not skip analysis or prove sender identity; sender addresses can be spoofed.',
    '輸入任一寄件者信箱，即時顯示是否命中白名單。寄件網域「完全相同」或為白名單網域的「子網域」才算命中；開頭相似、後面接其他網域的偽冒網域不會命中。': 'Enter a sender address to check for a match. A match requires the exact domain or one of its subdomains; lookalike domains do not match.',
    '範例①：官方網域（命中）': 'Example 1: official domain (match)',
    '範例②：子網域（命中）': 'Example 2: subdomain (match)',
    '範例③：偽冒網域（不命中）': 'Example 3: lookalike domain (no match)',
    '完整演示①：白名單信件': 'Walkthrough 1: email with an allowlist match',
    '完整演示②：偽冒信件': 'Walkthrough 2: spoofed email',
    '每個網域及其子網域都會被放行。': 'A domain match is only a hint; every email still goes through all four analysis layers.',
    '每一格是一封信。印章顏色是該封信的風險等級，進度來自後端實際完成的封數。': 'Each tile represents an email. Stamp colors show its risk level; progress reflects messages actually analyzed.',
    '郵件內文出現 http(s) 網址': 'An http(s) URL appears in the email body',
    '每個網址 +min(2×命中數, 8)': 'Each URL: +min(2 × matches, 8)',
    '對內文每個網址（最多 10 個）套用 U1–U8': 'Apply U1–U8 to each URL in the body (up to 10)',
    'min(HTML 分數 × 8, 100)': 'min(HTML score × 8, 100)',
    '後再進入融合。': ' before score fusion.',
  };

  const correctedChinese = new Map([
    ['已知安全網域自動略過重複分析。', '白名單只提供網域比對提示；所有郵件仍會完成四層分析。'],
    ['加入白名單後，來自該網域及其子網域的信件將直接標記為安全，不進行 AI 分析。請只加入確定可信任的網域。', '加入白名單只會顯示網域比對提示，不會略過分析或保證郵件安全；寄件者欄位可能遭偽冒。'],
    ['每個網域及其子網域都會被放行。', '白名單命中只作為網域提示；每封郵件仍會進入四層分析。'],
    ['白名單安全信件', '白名單命中提示'],
    ['白名單 · 略過分析', '白名單提示 · 仍完成分析'],
    ['已放行 CLEARED', '網域比對提示'],
  ]);

  function resolveLocale(query, saved) {
    if (query === 'en' || query === 'zh') return query;
    if (saved === 'en' || saved === 'zh') return saved;
    return 'zh';
  }

  function localizeText(value, locale) {
    let result = String(value == null ? '' : value);
    if (locale === 'zh') {
      for (const [oldText, safeText] of correctedChinese) {
        if (result === oldText) return safeText;
        if (result.includes(oldText)) result = result.replace(oldText, safeText);
      }
      result = result.replace(/者直接略過全部分析。/g, '者僅代表網域比對命中，郵件仍完成四層分析。');
      result = result.replace(/寄件網域命中白名單「([^」]+)」，系統將略過分析，直接判定為安全。/g,
        '寄件網域命中白名單「$1」；這只代表網域比對命中，郵件仍完成四層分析，且不代表寄件者身分已驗證。');
      return result;
    }
    if (Object.prototype.hasOwnProperty.call(text, result)) return text[result];
    result = result.replace(/^開啟郵件分析結果：/, 'Open email analysis: ');
    result = result.replace(/寄件網域命中白名單「([^」]+)」，系統將略過分析，直接判定為安全。/g,
      'The sender domain matched the allowlist (“$1”). This does not authenticate the sender; the email still goes through all four analysis layers.');
    result = result.replace(/寄件網域 ([^ ]+) 命中白名單「([^」]+)」（([^）]+)）。白名單只表示網域比對命中，不能驗證寄件者真實身分；此郵件仍完成四層分析。/g,
      'Sender domain $1 matched allowlisted domain "$2" ($3). This is only a domain match, does not verify the sender’s identity, and does not skip the four analysis layers.');
    result = result.replace(/資料集　(.+)，清理後 ([\d,]+) 筆（訓練 ([\d,]+) \/ 測試 ([\d,]+)）/g,
      'Dataset: $1; $2 cleaned rows ($3 train / $4 test).');
    result = result.replace(/目前白名單（\s*(\d+)\s*個）/g, 'Current allowlist ($1 domains)');
    result = result.replace(/者直接略過全部分析。/g,
      ' is only a domain hint; every message still goes through all four analysis layers.');
    return result;
  }

  function shouldTranslate(value, inUserContent) {
    return !inUserContent && typeof value === 'string' && value.length > 0;
  }

  function start(root) {
    const doc = root.document;
    let queryLanguage = '';
    try { queryLanguage = new URL(root.location.href).searchParams.get('lang') || ''; } catch (_) {}
    let savedLanguage = '';
    try { savedLanguage = root.localStorage.getItem('pd-language') || ''; } catch (_) {}
    let locale = resolveLocale(queryLanguage, savedLanguage || doc.documentElement.lang);
    const originalText = new WeakMap();
    const originalAttributes = new WeakMap();
    const originalTitle = doc.title;
    const descriptionMeta = doc.querySelector('meta[name="description"]');
    const originalDescription = descriptionMeta ? descriptionMeta.getAttribute('content') : '';
    let langButton = null;
    if (queryLanguage === 'en' || queryLanguage === 'zh') {
      try { root.localStorage.setItem('pd-language', queryLanguage); } catch (_) {}
    }

    function inUserContent(node) {
      const parent = node.parentElement;
      return !!(parent && parent.closest(
        'script,style,textarea,input,pre,code,[data-no-translate],.item-subj,.item-from,' +
        '.vd-subj,.vd-from,.mbody,.mdoc dd,.email-body,.raw-email'
      ));
    }

    function translateNode(node) {
      if (!node || !shouldTranslate(node.nodeValue, inUserContent(node))) return;
      if (!originalText.has(node)) originalText.set(node, node.nodeValue);
      const before = originalText.get(node);
      const trimmed = before.trim();
      const translated = localizeText(trimmed, locale);
      if (translated !== trimmed) {
        node.nodeValue = before.slice(0, before.indexOf(trimmed)) + translated + before.slice(before.indexOf(trimmed) + trimmed.length);
      }
    }

    function translateTree(target) {
      if (!target) return;
      const walker = doc.createTreeWalker(target, root.NodeFilter.SHOW_TEXT);
      let node;
      while ((node = walker.nextNode())) translateNode(node);
      if (target.nodeType === 1) {
        const elements = [target].concat(Array.from(target.querySelectorAll('*')));
        elements.forEach(function (element) {
          restoreMetric(element);
          const names = ['placeholder', 'aria-label', 'title', 'alt'];
          if (element.tagName === 'INPUT' && /^(submit|button|reset)$/i.test(element.type)) names.push('value');
          names.forEach(function (name) {
            const value = element.getAttribute(name);
            if (value) {
              let originals = originalAttributes.get(element);
              if (!originals) { originals = new Map(); originalAttributes.set(element, originals); }
              if (!originals.has(name)) originals.set(name, value);
              const original = originals.get(name);
              const translated = localizeText(original, locale);
              if (translated !== value) element.setAttribute(name, translated);
            }
          });
        });
        if (locale === 'en' && target.querySelectorAll &&
            ((target.matches && target.matches('h1,h2,h3')) || target.querySelector('h1,h2,h3'))) {
          fixHeadingSpacing();
        }
      }
    }

    function restoreMetric(element) {
      if (!element || !element.matches || !element.matches('.cu[data-to]')) return;
      const value = Number(element.getAttribute('data-to'));
      if (Number.isFinite(value) && element.textContent !== value.toFixed(2)) {
        element.textContent = value.toFixed(2);
      }
    }

    function edgeText(node, fromEnd) {
      if (node.nodeType === 3) return node;
      const children = node.childNodes || [];
      for (let i = fromEnd ? children.length - 1 : 0;
           fromEnd ? i >= 0 : i < children.length;
           i += fromEnd ? -1 : 1) {
        const found = edgeText(children[i], fromEnd);
        if (found && found.nodeValue) return found;
      }
      return null;
    }

    function fixHeadingSpacing() {
      if (locale !== 'en' || !doc.body) return;
      doc.body.querySelectorAll('h1,h2,h3').forEach(function (heading) {
        const children = heading.childNodes;
        for (let i = 0; i < children.length - 1; i++) {
          const left = edgeText(children[i], true);
          const right = edgeText(children[i + 1], false);
          if (!left || !right || !left.nodeValue || !right.nodeValue) continue;
          if (/[A-Za-z0-9]$/.test(left.nodeValue) && /^[A-Za-z0-9]/.test(right.nodeValue)) {
            left.nodeValue += ' ';
          }
        }
      });
    }

    const titleMap = {
      'phishing-detector｜找出可疑郵件': 'phishing-detector | Find suspicious email',
      '送檢中｜phishing-detector': 'Analysis in progress | phishing-detector',
      '貼信送檢｜phishing-detector': 'Analyze an email | phishing-detector',
      '檢驗報告｜phishing-detector': 'Analysis report | phishing-detector',
      '案件簿｜phishing-detector': 'Scan history | phishing-detector',
      '偵測規則｜phishing-detector': 'Detection rules | phishing-detector',
      '白名單｜phishing-detector': 'Allowlist | phishing-detector',
    };
    const nav = doc.querySelector('.hdr-nav');
    if (nav && !nav.querySelector('[data-lang-switch]')) {
      langButton = doc.createElement('button');
      langButton.type = 'button';
      langButton.className = 'pd-lang-toggle';
      langButton.setAttribute('data-lang-switch', '');
      langButton.addEventListener('click', function () {
        setLocale(locale === 'zh' ? 'en' : 'zh', true);
      });
      nav.appendChild(langButton);
    }

    function setLocale(next, updateUrl) {
      locale = next === 'en' ? 'en' : 'zh';
      doc.documentElement.lang = locale;
      if (doc.body) translateTree(doc.body);
      doc.title = locale === 'en' && titleMap[originalTitle] ? titleMap[originalTitle] : originalTitle;
      if (descriptionMeta) {
        descriptionMeta.setAttribute('content', locale === 'en'
          ? 'Inspect suspicious emails with four-layer analysis: rules, machine learning, URL and HTML checks, and AI-assisted review.'
          : originalDescription);
      }
      if (langButton) {
        langButton.setAttribute('aria-label', locale === 'zh' ? 'Switch language to English' : '切換為繁體中文');
        langButton.textContent = locale === 'zh' ? 'EN' : '繁中';
      }
      try { root.localStorage.setItem('pd-language', locale); } catch (_) {}
      if (updateUrl && root.history && root.history.replaceState) {
        const url = new URL(root.location.href);
        url.searchParams.set('lang', locale);
        root.history.replaceState(root.history.state, '', url.href);
      }
      if (doc.body) {
        doc.body.querySelectorAll('a[href],form[action]').forEach(function (element) {
          const attribute = element.tagName === 'FORM' ? 'action' : 'href';
          const value = element.getAttribute(attribute);
          if (!value || /^(mailto:|tel:|javascript:)/i.test(value)) return;
          try {
            const url = new URL(value, root.location.href);
            if (url.origin !== root.location.origin) return;
            url.searchParams.set('lang', locale);
            element.setAttribute(attribute, url.pathname + url.search + url.hash);
          } catch (_) {}
        });
      }
    }

    setLocale(locale, false);

    if (root.MutationObserver && doc.body) {
      const observer = new root.MutationObserver(function (records) {
        records.forEach(function (record) {
          if (record.type === 'characterData') {
            const metric = record.target.parentElement && record.target.parentElement.closest('.cu[data-to]');
            if (metric) restoreMetric(metric);
          }
          record.addedNodes.forEach(function (node) {
            if (node.nodeType === 3) translateNode(node);
            else if (node.nodeType === 1) translateTree(node);
          });
        });
      });
      observer.observe(doc.body, { childList: true, subtree: true, characterData: true });
    }
  }

  return { localizeText, resolveLocale, shouldTranslate, start };
});

