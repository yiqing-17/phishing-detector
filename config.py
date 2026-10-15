Warning: fs was declared with const; use let for reassignable variables.
"""Environment-backed application settings."""
import os

GROQ_API_KEY = os.environ.get('GROQ_API_KEY', '')
MY_EMAIL = os.environ.get('MY_EMAIL', '')
BASE_URL = os.environ.get('BASE_URL', 'http://localhost:5000')
SCOPES = ['https://www.googleapis.com/auth/gmail.readonly']
GOOGLE_CLIENT_ID = os.environ.get('GOOGLE_CLIENT_ID', '')
GOOGLE_CLIENT_SECRET = os.environ.get('GOOGLE_CLIENT_SECRET', '')
GOOGLE_PROJECT_ID = os.environ.get('GOOGLE_PROJECT_ID', 'phishing-detector')
FLASK_SECRET_KEY = os.environ.get('FLASK_SECRET_KEY')
COOKIE_SECURE = os.environ.get('COOKIE_SECURE', '1' if BASE_URL.startswith('https://') else '0') == '1'

if BASE_URL.startswith('http://'):
    os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'

DEFAULT_WHITELIST = [
    'skims.com', 'emails.skims.com', 'links.skims.com',
    'lululemon.com', 'email.lululemon.com', 'e.lululemon.com',
    'aloyoga.com', 'email.aloyoga.com',
    'esunbank.com.tw', 'esun.com.tw', 'esunsec.com.tw',
    'google.com', 'accounts.google.com', 'googlemail.com',
]
SKIP_SUBJECTS = ['[警告]', '[正常]', 'AI 釣魚偵測報告', 'AI 釣魚信件偵測報告']

if not (GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET):
    print('WARNING: GOOGLE_CLIENT_ID / GOOGLE_CLIENT_SECRET 尚未設定，Gmail OAuth 將無法使用。')
