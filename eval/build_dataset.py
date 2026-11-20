"""產生 eval/dataset_zh.jsonl。樣本為人工撰寫的合成信件（非真實收集），
依類別與題型（含難例）手寫；以「同類別交錯」固定切成 dev / test：
規則調整只能看 dev，test 凍結後只跑一次。"""
import json, os

# (category, from, subject, body)
PHISH = [
("郵局","service@post-tw-notice.xyz","【中華郵政】包裹地址不全","您的包裹因地址不全無法投遞，請於24小時內至 http://post-tw-notice.xyz/pay 補繳運費 NT$25，逾期將退回寄件人。"),
("郵局","notice@chunghwa-post.top","郵件投遞失敗通知","您有一件國際郵件待領取，請點擊 https://chunghwa-post.top/track 確認收件資料並支付關稅。"),
("電信","bill@cht-telecom-bill.com","中華電信電信費逾期通知","您的電信帳單已逾期，服務將於今日停止。請立即登入 http://cht-telecom-bill.com/login 繳費，避免斷話。"),
("電信","care@fetnet-reward.click","遠傳會員點數即將到期","您有 8,800 點會員點數今日到期，請至 http://fetnet-reward.click/redeem 兌換現金禮券。"),
("銀行","security@ctbc-secure-verify.com","【中國信託】帳戶異常登入警示","偵測到您的網路銀行於異地登入，帳戶已暫時凍結。請於1小時內至 https://ctbc-secure-verify.com/unlock 驗證身分並輸入密碼與OTP。"),
("銀行","service@esun-bank-alert.top","玉山銀行信用卡盜刷通知","您的信用卡於海外消費 NT$48,000，如非本人操作請立即點擊 http://esun-bank-alert.top/dispute 填寫卡號與背面三碼。"),
("銀行","noreply@cathay-update.xyz","國泰世華 網銀憑證即將失效","您的網銀安控憑證將於今日失效，請更新憑證：http://cathay-update.xyz/cert ，未更新將無法轉帳。"),
("蝦皮","order@shopee-tw-help.com","蝦皮購物 訂單付款失敗","您的訂單付款失敗，帳號有安全風險。請重新驗證付款方式 https://shopee-tw-help.com/verify ，否則訂單將被取消。"),
("蝦皮","support@shopee-cs.work","蝦皮客服：誤設分期付款","因系統錯誤，您被誤設為12期分期付款，請聯絡客服或依指示操作ATM解除，否則每月自動扣款。"),
("momo","service@momo-shop-refund.top","momo 退款通知","您的訂單重複扣款，我們將退款 NT$3,690，請至 http://momo-shop-refund.top/refund 輸入銀行帳號與信用卡資料領取。"),
("政府","tax@etax-gov-refund.com","財政部國稅局 退稅通知","您符合退稅資格，退稅金額 NT$12,450。請於3日內至 https://etax-gov-refund.com/claim 填寫銀行帳號領取。"),
("政府","dmv@mvdis-fine.xyz","監理服務網 交通違規罰單未繳","您有一筆違規罰款 NT$900 逾期未繳，將加收滯納金。請立即至 http://mvdis-fine.xyz/pay 線上繳納。"),
("政府","health@nhi-card-update.top","健保卡換發通知","您的健保卡資料需更新，請於24小時內登入 http://nhi-card-update.top/id 驗證身分證字號與出生日期。"),
("中獎","promo@lucky-draw-tw.click","恭喜您獲選幸運得主","恭喜您抽中 iPhone 手機一支！請於今日內至 http://lucky-draw-tw.click/get 領取，需先支付運費 NT$99。"),
("中獎","vip@gift-center-rewards.com","超商禮券免費領取","您是本月幸運會員，可免費領取 1,000 元超商禮券，限時24小時：https://gift-center-rewards.com/claim"),
("投資","teacher@invest-wealth-club.net","內部飆股群組邀請","老師帶你月賺30%，保證獲利零風險。加入專屬群組領取明牌，名額有限，請回覆您的Line ID與手機號碼。"),
("投資","admin@crypto-profit-vip.xyz","虛擬貨幣高收益平台","本平台提供日收益 3%，新手註冊即送 100 USDT。請至 http://crypto-profit-vip.xyz/signup 開戶並匯款入金。"),
("求職","hr@job-offer-remote.top","遠端兼職 日領 3000","在家兼職點讚刷單，日領現金 NT$3,000，無需經驗。請加入 Telegram 並提供身分證與銀行帳戶以便匯款。"),
("客服","cs@amazon-tw-secure.work","亞馬遜帳戶已被暫停","您的 Amazon 帳戶因異常活動已被暫停，請立即至 https://amazon-tw-secure.work/signin 驗證密碼以恢復使用。"),
("ETC","etc@fetc-toll-pay.xyz","eTag 通行費未繳通知","您有未繳通行費 NT$32，逾期將處罰鍰。請至 http://fetc-toll-pay.xyz/pay 以信用卡繳納。"),
("Line","line@line-account-safe.top","LINE 帳號即將停用","您的 LINE 帳號涉及異常，將於今日停用。請至 https://line-account-safe.top/verify 驗證手機號碼與密碼。"),
("社交","friend@fb-photo-share.click","你有一則新的相片標註","有人在相片中標註了你，點擊查看：http://fb-photo-share.click/view 。請先登入您的 Facebook 帳號。"),
("商務詐騙","ceo.chen@company-exec-mail.net","急件：請協助處理","我現在開會不方便講電話，需要你今天幫我處理一筆緊急匯款給供應商，金額 NT$850,000，完成後請回覆，勿告知他人。"),
("商務詐騙","finance@vendor-newbank.org","供應商銀行帳戶變更通知","我司銀行帳戶已變更，之後貨款請匯入新帳戶：822-0123456789。舊帳戶已停用，請盡速更新付款資料。"),
("難例-無連結","info@secure-service-center.com","重要通知","親愛的用戶，您的帳戶需要確認。請回覆此信並附上您的身分證影本與銀行帳號，我們會在一小時內為您處理。"),
("難例-短文","a1982@mail-box.biz","您好","您好，我是檢察官助理，您涉及一起洗錢案件，請勿告知他人，並立即加入通訊軟體配合偵查，另需將存款轉至監管帳戶。"),
("郵局","post@taiwan-post-delivery.xyz","宅配包裹無法送達","親愛的客戶，您的宅配包裹無法送達。請立即點擊 http://taiwan-post-delivery.xyz/addr 更新地址並補繳運費。"),
("銀行","alert@fubon-card-notice.click","富邦信用卡額度異常","您的信用卡將被停用，請馬上登入 https://fubon-card-notice.click/login 輸入卡號及密碼以解除限制。"),
("政府","covid@gov-subsidy-tw.top","政府補助金申請通知","您符合紓困補助資格，可領取 NT$10,000。請於今日內至 http://gov-subsidy-tw.top/apply 填寫帳戶資料，逾期失效。"),
("客服","service@apple-id-locked.com","您的 Apple ID 已被鎖定","出於安全考量，您的 Apple ID 已被鎖定。請點擊 https://apple-id-locked.com/unlock 驗證密碼與信用卡資料。"),
("難例-純文字","promo@best-deal-offers.net","限時優惠","限時優惠！本週加入會員即可免費領取獎品，請回覆信件並提供您的手機與地址，我們將立即寄出。"),
("物流","dhl@dhl-express-parcel.top","DHL 快遞包裹待確認","您的 DHL 快遞包裹關稅未付，請點擊 http://dhl-express-parcel.top/pay 支付 NT$120 以便派送，否則將退回。"),
("遊戲","support@steam-trade-verify.xyz","Steam 帳號交易異常","您的 Steam 帳號有交易異常，請登入 https://steam-trade-verify.xyz/login 驗證密碼以避免帳號被封鎖。"),
("學校","admin@univ-mail-update.work","校園信箱容量已滿","您的學校信箱容量已滿，將於24小時內停用。請至 http://univ-mail-update.work/mail 登入密碼以擴充容量。"),
("房租","landlord@rent-tw-pay.click","房租繳費帳戶變更","房東通知：本月起租金請轉至新帳戶，並盡快匯款 NT$18,000，詳細資訊請點 http://rent-tw-pay.click/info 。"),
("保險","claim@life-insure-refund.com","保單溢繳款退還","您的保單有溢繳保費可退還 NT$7,500，請於3天內至 https://life-insure-refund.com/claim 填寫銀行帳號與身分證。"),
("電商","pay@pchome-order-fix.top","PChome 訂單異常需重新付款","您的訂單資訊異常，請立即重新付款，點擊 http://pchome-order-fix.top/pay 輸入信用卡資訊，逾期訂單作廢。"),
("電信","rewards@taiwanmobile-gift.xyz","台灣大哥大感謝回饋","感謝您多年支持，免費贈送您 5G 手機乙支，請至 http://taiwanmobile-gift.xyz/gift 領取並填寫收件資料及信用卡號支付運費。"),
("銀行","verify@taishin-bank-secure.net","台新銀行 簡訊驗證碼更新","為保障帳戶安全，請於今日內完成身分驗證：https://taishin-bank-secure.net/otp ，未驗證將暫停轉帳功能。"),
("難例-英中混合","security@paypa1-support.com","Account Alert 帳戶警示","Dear user, 您的 PayPal 帳戶有異常活動。Please verify your password at http://paypa1-support.com/login 立即確認，否則帳戶將被停用。"),
("社群","ig@instagram-copyright-appeal.top","Instagram 版權侵權警告","您的帳號被檢舉侵犯版權，將於24小時內刪除。請至 http://instagram-copyright-appeal.top/appeal 申訴並輸入密碼。"),
("外送","order@foodpanda-refund-tw.click","外送訂單退款處理","您的外送訂單因店家缺貨取消，款項退回需驗證，請至 https://foodpanda-refund-tw.click/r 輸入信用卡號。"),
("法院","court@judicial-notice-tw.xyz","法院傳票電子通知","您有一份法院傳票待查收，將於3日內強制執行。請點擊 http://judicial-notice-tw.xyz/doc 下載並填寫身分證與銀行帳戶。"),
("難例-正式語氣","notice@tw-customs-clearance.org","進口貨物清關通知","您的進口貨物已抵達海關，因申報資料不完整需補件，請依指示於本週內支付稅費 NT$2,300 至指定帳戶以完成清關。"),
("難例-短連結","dm@win-big.cc","你中獎了","點這裡 https://bit.ly/3xYz9aB 查看你的獎品，需要驗證手機號碼。"),
("OTP","noreply@secure-login-center.top","登入驗證碼異常","有人嘗試登入您的帳戶，請立即提供您收到的6位數驗證碼以取消登入，並更新密碼 http://secure-login-center.top/otp 。"),
("貸款","loan@fast-cash-approve.net","免擔保低利貸款核准","您已通過預審，可貸款 NT$500,000，免擔保低利率。請提供身分證與存摺帳號，並先匯款 NT$5,000 作為手續費。"),
("訂閱","billing@netflix-payment-hold.xyz","Netflix 付款失敗","您的 Netflix 訂閱付款失敗，帳戶將被暫停。請更新付款資料 https://netflix-payment-hold.xyz/billing ，需輸入信用卡號。"),
("包裹","track@seven-eleven-pickup.top","超商取貨通知","您的包裹已到店，但取貨資訊有誤，請點 http://seven-eleven-pickup.top/info 確認並支付手續費 NT$30。"),
("機票","airline@eva-air-refund.click","長榮航空 班機取消退款","您的班機已取消，可全額退款。請至 https://eva-air-refund.click/refund 填寫信用卡資料以便退款，限時處理。"),
("面試","recruit@hr-dept-interview.work","面試邀請與薪資確認","恭喜您通過履歷篩選！請填寫基本資料與銀行帳號以辦理薪資轉帳及入職保證金 NT$3,000。"),
("工作","admin@workfromhome-paid.net","日領高薪 免經驗","只需每天2小時，輕鬆月入十萬。請加入群組並匯款 NT$2,000 購買入職教材，保證回本。"),
]

BENIGN = [
("同事","manager@corp.com.tw","明天專案會議","各位同仁，明天下午三點在三樓會議室討論專案進度，請準時出席並帶上本週報告。"),
("同事","amy.lin@corp.com.tw","週五聚餐","這週五晚上要不要一起去吃火鍋？我訂了六點的位子，想參加的人回覆我一下。"),
("同事","hr@corp.com.tw","年度健康檢查通知","公司將於下月 15 日舉辦年度健康檢查，請至公司內網報名，檢查前一晚請禁食。"),
("朋友","wei@gmail.com","週末爬山","週六早上七點在捷運站集合，一起去象山，記得帶水和防曬。"),
("朋友","mom@gmail.com","這週回家吃飯嗎","你這週有空回家吃飯嗎？我想煮你愛吃的滷肉飯，你爸也很想你。"),
("學校","teacher@ntu.edu.tw","期中報告繳交提醒","同學們，期中報告請於下週三前上傳至課程網站，遲交將扣分，有問題歡迎來信詢問。"),
("學校","office@school.edu.tw","家長會通知","本學期家長會訂於 11 月 25 日晚上七點舉行，歡迎各位家長蒞臨，會中將說明下學期課程安排。"),
("硬例-帳單","ebill@cathaybk.com.tw","【國泰世華】11月電子帳單","親愛的客戶您好，您 11 月份信用卡電子帳單已產生，應繳金額 NT$3,280，繳款截止日為 12 月 5 日。請登入官方 App 查詢，本行不會以電子郵件要求您提供密碼。"),
("硬例-帳單","bill@cht.com.tw","中華電信 電子帳單通知","您好，您的 10 月份電信費帳單已寄出，付款方式為信用卡自動扣繳，如有疑問請洽客服 123。"),
("硬例-訂單","order@shopee.tw","您的訂單已出貨","您的蝦皮訂單 #2311208892 已出貨，預計 2 天內到店。付款方式：貨到付款。感謝您的購買。"),
("硬例-訂單","service@momoshop.com.tw","momo 訂單成立通知","您的訂單已成立，付款已完成 NT$1,290，預計三日內配送。如需取消請至會員中心訂單查詢。"),
("硬例-物流","noreply@post.gov.tw","郵件已投遞通知","您的掛號郵件已於今日送達，簽收人：本人。如需查詢請至中華郵政官網輸入掛號號碼。"),
("硬例-電子報","news@news.cw.com.tw","天下雜誌 本週精選","本週精選：台灣半導體產業展望、年末理財規劃指南。免費訂閱電子報，隨時可取消訂閱。"),
("硬例-促銷","promo@pxmart.com.tw","全聯福利中心 週年慶","全聯週年慶開跑，會員享免費領取購物袋活動，憑 App 會員碼至門市兌換，數量有限送完為止。"),
("硬例-付款","accounting@vendor.com.tw","發票與付款確認","附件為 11 月份請款發票，付款期限為 30 天，匯款帳號與去年相同，如有變更我們會電話與您確認。"),
("硬例-銀行","info@esunbank.com.tw","玉山銀行 重要權益調整公告","為保障您的權益，本行信用卡約定條款將於 12 月 1 日更新，詳細內容請至官網公告查閱。本行不會要求您提供密碼或 OTP。"),
("硬例-安全","no-reply@accounts.google.com","安全性快訊","有新裝置登入您的 Google 帳戶。如果是您本人操作，不需要採取任何動作。"),
("工作","boss@startup.tw","本週工作安排","這週請優先完成客戶簡報與預算表，週四前交給我，有困難隨時告訴我，我們一起討論。"),
("工作","recruiter@104.com.tw","面試時間確認","您好，感謝您應徵，面試訂於 11 月 28 日上午 10 點，地點為公司總部 12 樓，請攜帶作品集。"),
("活動","event@meetup.tw","技術分享會報名成功","您已成功報名 12 月 3 日的技術分享會，現場提供午餐，活動前一日會再寄送提醒。"),
("房租","landlord@gmail.com","房租與水電","本月房租和水電費明細如附件，匯款到原本的帳戶就可以，有問題再跟我說，謝謝。"),
("醫療","clinic@hospital.org.tw","門診預約提醒","提醒您明天上午 9:30 有牙科門診預約，請提前 10 分鐘報到並攜帶健保卡。"),
("旅遊","booking@hotel.com.tw","訂房確認","您的住宿訂房已確認，入住日期 12 月 20 日，總金額 NT$6,800，將於入住時付款。"),
("家人","sister@yahoo.com.tw","爸爸生日","下週六是爸爸生日，我訂了餐廳，大家一起慶祝，你記得準備禮物喔。"),
("社團","club@school.edu.tw","社團迎新活動","社團迎新將於下週二晚上舉行，有桌遊和小點心，歡迎新舊社員一起來玩。"),
("工作","it@corp.com.tw","系統維護公告","公司內部系統將於本週六凌晨 2 點至 4 點進行例行維護，期間無法使用，造成不便敬請見諒。"),
("硬例-密碼","it-helpdesk@corp.com.tw","密碼到期提醒","您好，您的內部系統密碼將於 7 天後到期，請至公司 IT 入口網站依標準流程自行變更。IT 不會向您索取密碼。"),
("硬例-投資","service@sinotrade.com.tw","證券月對帳單","您好，您 11 月份的證券月對帳單已產生，請登入官方網站查閱。投資一定有風險，基金投資有賺有賠。"),
("硬例-退款","service@pchome.com.tw","退貨退款完成通知","您的退貨申請已完成，退款 NT$590 將於 5 個工作天內退回您原付款的信用卡，不需要任何額外操作。"),
("朋友","leo@gmail.com","借你的書","上次你借我的那本書我看完了，這週找時間還你，順便請你喝杯咖啡。"),
("硬例-政府","tax@mail.etax.nat.gov.tw","綜合所得稅申報提醒","115 年度綜合所得稅申報期間為 5 月 1 日至 5 月 31 日，可使用自然人憑證線上申報。本部不會以電子郵件要求提供帳戶或密碼。"),
("工作","pm@corp.com.tw","需求文件 v2","需求文件第二版已更新至共用雲端，請大家在週三前確認自己負責的部分，有意見直接留言。"),
("社群","notification@facebookmail.com","你有 3 則新通知","你的朋友在貼文中提到了你。登入 Facebook 查看通知。"),
("硬例-健康","care@nhi.gov.tw","健保卡到期換發提醒","您的健保卡有效期限將屆，請攜帶身分證至各健保署服務櫃檯或郵局辦理換發。本署不會電話或簡訊要求匯款。"),
("朋友","cathy@gmail.com","演唱會門票","我搶到兩張演唱會門票，你要一起去嗎？票價 NT$2,800 我先墊，到時候再轉給我就好。"),
("硬例-緊急","ops@corp.com.tw","緊急：伺服器負載過高","目前正式環境伺服器負載偏高，請值班同仁立即確認，我已先重啟服務，預計十分鐘內恢復。"),
("硬例-中獎","promo@familymart.com.tw","全家 會員抽獎活動","恭喜！您於本次會員抽獎活動獲得咖啡兌換券一張，請至 App 的「我的票夾」查看，不需提供任何個人資料。"),
("學校","library@ntu.edu.tw","圖書館借閱到期提醒","您借閱的 2 本書將於 12 月 1 日到期，請至圖書館官網辦理續借，逾期每日罰款 5 元。"),
("工作","legal@corp.com.tw","合約用印流程","供應商合約請依用印流程送簽，需要主管核章後再交給法務，已更新的版本在共用資料夾。"),
("硬例-外送","noreply@ubereats.com","您的訂單已送達","您的訂單已送達，總付款金額 NT$385。感謝使用，歡迎為這次的餐點評分。"),
("硬例-訂閱","billing@spotify.com","Spotify 付款收據","感謝您的訂閱，本月 NT$149 已從您的信用卡扣款。如需變更方案請至帳戶頁面。"),
("朋友","jack@gmail.com","租屋推薦","我朋友的房子明年一月釋出，兩房一廳，租金 25,000，你有興趣的話我幫你牽線。"),
("硬例-快遞","notice@sf-express.com","順豐速運 派件通知","您的快件正在派送，預計今日 18:00 前送達，請保持電話暢通。"),
("工作","finance@corp.com.tw","差旅費報銷","本月差旅費請於 25 日前提交報銷單，附上發票正本，財務會於下月初統一匯款至薪資帳戶。"),
("家人","dad@gmail.com","新年旅遊","農曆年想去花蓮玩三天，我先看了民宿，你把想去的景點傳給我。"),
("硬例-驗證","noreply@github.com","GitHub 登入驗證碼","你的驗證碼是 482913。請勿將此驗證碼分享給任何人。如果不是你本人，請立即更改密碼。"),
("學校","admin@school.edu.tw","獎學金申請公告","本學期獎學金開始受理申請，請於 12 月 10 日前繳交申請表與成績單至教務處，審核結果將另行公告。"),
("朋友","ann@gmail.com","謝謝你昨天","昨天真的很謝謝你陪我，心情好多了。改天換我請你吃飯。"),
("硬例-銀行","ebill@ctbcbank.com","中國信託 e 化帳單","您好，您的 10 月份帳戶月結單已產生。為保護您的資安，本行不會以電子郵件索取帳號密碼，請提防詐騙。"),
]

def split(rows, label):
    out, per = [], {}
    for i, (cat, frm, subj, body) in enumerate(rows):
        n = per.get(cat, 0); per[cat] = n + 1
        out.append({
            'id': f"{'P' if label else 'B'}{i+1:02d}", 'label': label, 'category': cat,
            'split': 'dev' if i % 2 == 0 else 'test',
            'from': frm, 'subject': subj, 'body': body,
            'text': f"From: {frm}\nSubject: {subj}\nBody: {body}",
        })
    return out

if __name__ == '__main__':
    rows = split(PHISH, 1) + split(BENIGN, 0)
    path = os.path.join(os.path.dirname(__file__), 'dataset_zh.jsonl')
    with open(path, 'w', encoding='utf-8') as f:
        for r in rows: f.write(json.dumps(r, ensure_ascii=False) + '\n')
    from collections import Counter
    print(len(rows), Counter((r['split'], r['label']) for r in rows))
