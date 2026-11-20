"""產生「困難樣本」集 eval/dataset_zh_hard.jsonl（split='hard'）。

目的：打破主資料集的兩個偏差——
  1. 主集的 49 封正常信全部沒有連結，釣魚信全部有連結 → 偵測器可能只是在認「有沒有連結」。
  2. 主集釣魚信的網域都是虛構的 → 任何網域查詢（DNS/RDAP）都不具代表性。
本集補：
  * 困難負例（label=0）：正常信但「有真實官方連結」「含密碼/驗證/付款/帳戶等敏感詞」「含短網址」
    「防詐宣導文（內文本身就在講詐騙話術）」。
  * 無連結釣魚（label=1）：只靠 LINE ID / 電話 / 回信索資料 / 匯款帳號變更。

紀律：本集「只評估、不調參」。規則與門檻不得因這份結果而修改，否則它就失去獨立性。
限制：仍是人工撰寫的合成信件，作者同為專題作者；它檢驗的是「偏差」，不是「真實分佈」。
"""
import json
import os

NEG = [  # (category, from, subject, body)
    ('帳號安全', 'no-reply@accounts.google.com', '安全性快訊：有新裝置登入你的帳戶', '我們偵測到你的 Google 帳戶在新裝置上登入。如果是你本人操作，無需處理。若不是你，請至 https://myaccount.google.com/security 檢查最近的安全性活動並變更密碼。'),
    ('帳號安全', 'security@facebookmail.com', '重設你的 Facebook 密碼', '你剛才要求重設密碼。請在 1 小時內使用此連結 https://www.facebook.com/recover/code 設定新密碼。如果不是你本人要求，可以忽略這封信。'),
    ('購物', 'service@momoshop.com.tw', '【momo購物網】訂單成立通知', '您好，您的訂單 20261103001 已成立，付款金額 NT$1,280，預計 11/22 配送。可至 https://www.momoshop.com.tw/order 查詢訂單明細。'),
    ('發票', 'einvoice@mail.etax.nat.gov.tw', '電子發票開立通知', '您於 2026/11/10 的消費已開立電子發票，發票金額 350 元。您可於 https://www.einvoice.nat.gov.tw 查詢發票明細與中獎資訊。'),
    ('銀行', 'ebill@cathaybk.com.tw', '國泰世華信用卡電子帳單', '您的 11 月電子帳單已產生，請登入網路銀行 https://www.cathaybk.com.tw 查看。本行不會以電話或 Email 要求您提供密碼或信用卡資料，謹防詐騙。'),
    ('開發', 'notifications@github.com', '[repo] Pull request #42 merged', 'Your pull request has been merged into main. View it here: https://github.com/example/repo/pull/42. You are receiving this because you authored the thread.'),
    ('公司', 'pm@corp.com.tw', '週五專案會議邀請', '各位同仁好，週五 14:00 進行專案進度會議，會議連結 https://meet.google.com/abc-defg-hij，請事先閱讀附件的進度表。'),
    ('學校', 'registrar@ntu.edu.tw', '選課系統開放通知', '各位同學，下學期選課將於 12/1 上午 9 點開放，請使用學號登入選課系統 https://course.ntu.edu.tw 進行加退選。'),
    ('物流', 'notice@t-cat.com.tw', '黑貓宅急便配送通知', '您的包裹已由司機配送中，貨號 123456789012，可至 https://www.t-cat.com.tw/inquire/trace.aspx 查詢配送進度。'),
    ('航空', 'booking@evaair.com', '電子機票確認', '感謝您訂購長榮航空機票，付款已確認，訂位代號 AB12CD。您可至 https://www.evaair.com 管理訂位與線上報到。'),
    ('電子報', 'edm@pxmart.com.tw', '全聯週末免費領好禮', '本週末憑福利中心 App 即可免費領取限量好禮，限時優惠至週日。詳情請見 https://www.pxmart.com.tw/campaign，數量有限，送完為止。'),
    ('會議', 'no-reply@zoom.us', 'Zoom 會議提醒', '您預約的會議「期末報告彩排」將於明天上午 10:00 開始。加入會議：https://zoom.us/j/12345678901，密碼已附於行事曆邀請。'),
    ('保險', 'service@cathaylife.com.tw', '保險費繳費通知', '您好，您的保單本期保費 NT$3,200 將於 11/25 自動扣款，請確認帳戶餘額充足。保單明細可至 https://www.cathaylife.com.tw 查詢。'),
    ('訂閱', 'info@mailer.netflix.com', 'Netflix 付款收據', '感謝您的付款，本月訂閱費用 NT$390 已從您的信用卡扣款。管理會員資格請至 https://www.netflix.com/account。'),
    ('稅務', 'service@dgbas.gov.tw', '綜合所得稅申報提醒', '115 年度綜合所得稅申報期間為 5 月 1 日至 5 月 31 日，可使用自然人憑證或健保卡於 https://www.tax.nat.gov.tw 辦理申報。'),
    ('同事', 'amy@corp.com.tw', '簡報連結', '嗨，上次講的簡報我放在雲端了，連結 https://bit.ly/3xyzABC，看完再跟我說意見，謝謝！'),
    ('驗證碼', 'noreply@shopee.tw', '蝦皮購物登入驗證碼', '您的驗證碼是 482913，10 分鐘內有效。請勿將驗證碼告訴任何人，包含客服人員。如果不是您本人操作，請忽略此信。'),
    ('租屋', 'landlord@gmail.com', '十二月房租', '你好，十二月房租 NT$15,000 請於 5 號前匯到上次給你的帳戶就好，收到後我會回信確認，謝謝。'),
    ('防詐宣導', 'service@165.gov.tw', '【165 反詐騙】防範假冒客服詐騙', '近期有詐騙集團假冒電商客服，以「訂單錯誤、解除分期付款」為由要求操作 ATM 或提供密碼。請勿點擊不明連結、勿提供帳號密碼，如有疑問請撥打 165 或至 https://165.npa.gov.tw 查證。'),
    ('銀行', 'notice@esunbank.com.tw', '玉山銀行轉帳成功通知', '您已於 11/18 14:32 完成一筆轉帳，轉出金額 NT$5,000。如非本人操作，請立即撥打客服電話 (02)2182-1313 或至 https://www.esunbank.com.tw 查詢。'),
]

POS = [  # 無連結釣魚
    ('假冒檢警', 'agent@gmail.com', '地檢署通知：您涉及洗錢案件', '經調查您的帳戶涉及洗錢案件，請於今日內加入 LINE ID：moj-case-0000 與承辦檢察官聯繫，並配合辦理監管帳戶，勿告知他人，否則將依法拘提。'),
    ('假冒客服', 'service@mail-help.net', '訂單設定錯誤，將重複扣款', '因系統錯誤，您的訂單被設定為每月扣款 12 期，請立即撥打 0900-000-000 由專員協助解除分期，逾時將自動扣款。'),
    ('BEC', 'ceo.office@gmail.com', '急件：請協助處理', '我現在在開會不方便講電話，有一筆款項需要你今天幫我處理，請直接回覆這封信，我再給你匯款資料，這件事先不要跟其他人提。'),
    ('投資', 'vip@invest-club.org', '內線飆股名單免費領', '我們老師團隊本週精選三檔飆股，保證獲利翻倍，請加入 LINE 群組 ID：stock-vip-0000 領取名單，名額只剩 5 位。'),
    ('中獎', 'prize@lucky-center.com', '恭喜您中獎 NT$500,000', '您被抽中本月幸運大獎 NT$500,000，請回覆您的姓名、身分證字號與銀行帳號，我們將於 24 小時內匯款至您的帳戶。'),
    ('求職', 'hr@job-offer-tw.com', '錄取通知：在家兼職月入十萬', '恭喜您通過履歷審核，請回信提供身分證字號、銀行帳號與提款卡照片以辦理薪轉，完成後即可開始工作。'),
    ('帳號', 'support@account-center.org', '您的帳戶將於今日停用', '系統偵測到您的帳戶異常，請直接回覆此信，附上您的帳號、密碼與信用卡末四碼以恢復使用，否則帳戶將永久停用。'),
    ('假冒親友', 'ming.chen88@gmail.com', '借我一點錢', '我手機壞了用朋友的信箱寫信給你，我現在急需周轉 NT$30,000，請匯到這個帳戶：國泰 012-345678901234，晚點再還你，先不要打電話。'),
    ('勒索', 'unknown@proton-mail.org', 'I recorded you', '我已入侵你的電腦並錄下你的私人影片。48 小時內轉 0.05 BTC 到錢包地址 bc1q-example-0000，否則我會把影片寄給你所有的聯絡人。'),
    ('退稅', 'refund@tax-service.org', '您有一筆退稅款待領取', '財政部通知您有 NT$8,640 退稅款尚未領取，請直接回信提供您的銀行帳號與身分證字號，我們將於三個工作天內匯入。'),
    ('供應商', 'accounting@vendor-corp.biz', '銀行帳戶變更通知', '本公司已更換往來銀行，自本月起所有貨款請匯至新帳戶：永豐銀行 807-00112233445566，戶名同前。舊帳戶即日停用，請勿再匯款，如有疑問請回信聯絡。'),
    ('假冒政府', 'notice@gov-assist.org', '健保卡異常，請盡速處理', '您的健保卡因資料異常將於 24 小時內停用，請立即回信提供身分證字號與出生年月日，或撥打 0800-000-000 辦理。'),
]


def mk(i, label, cat, frm, subj, body):
    return {'id': i, 'label': label, 'category': cat, 'split': 'hard', 'from': frm,
            'subject': subj, 'body': body, 'text': f'From: {frm}\nSubject: {subj}\nBody: {body}'}


if __name__ == '__main__':
    rows = [mk(f'HN{i:02d}', 0, *r) for i, r in enumerate(NEG, 1)]
    rows += [mk(f'HP{i:02d}', 1, *r) for i, r in enumerate(POS, 1)]
    out = os.path.join(os.path.dirname(__file__), 'dataset_zh_hard.jsonl')
    with open(out, 'w', encoding='utf-8') as f:
        for r in rows:
            f.write(json.dumps(r, ensure_ascii=False) + '\n')
    print(f'{len(rows)} 封（正常 {len(NEG)}、釣魚 {len(POS)}）→ {out}')
