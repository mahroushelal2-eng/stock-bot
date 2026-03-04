import yfinance as yf
import asyncio
import logging
import nest_asyncio
import pandas as pd
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

# --- إعدادات محروس الخاصة ---
TOKEN = '8134571916:AAFXfnTmpMTpt7loclaymCN2og4w3T06sVQ'
USER_CHAT_ID = 5074413

logging.basicConfig(level=logging.INFO)
nest_asyncio.apply()

# دالة لحساب المؤشرات الفنية (دخول/خروج)
def get_signals(df):
    # حساب RSI (مؤشر القوة النسبية)
    delta = df['Close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
    rs = gain / loss
    df['RSI'] = 100 - (100 / (1 + rs))
    
    # حساب المتوسطات المتحركة
    df['SMA20'] = df['Close'].rolling(window=20).mean()
    
    current_rsi = df['RSI'].iloc[-1]
    current_price = df['Close'].iloc[-1]
    sma20 = df['SMA20'].iloc[-1]
    
    signal = "⚖️ محايد"
    if current_rsi < 30:
        signal = "📥 دخول (تشبع بيعي)"
    elif current_rsi > 70:
        signal = "📤 خروج (تشبع شرائي)"
    elif current_price > sma20:
        signal = "📈 إيجابي (فوق المتوسط)"
    
    return signal, current_rsi

# 1. وظيفة البحث اليدوي التفصيلية
async def check_stock(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("❓ اكتب الرمز بعد الأمر، مثال: `/check TSLA`", parse_mode='Markdown')
        return

    symbol = context.args[0].upper()
    try:
        ticker = yf.Ticker(symbol)
        # جلب بيانات شهر لضمان دقة المؤشرات
        df = ticker.history(period='1mo')
        
        if df.empty:
            await update.message.reply_text(f"❌ لم أجد بيانات لرمز {symbol}")
            return

        price = df['Close'].iloc[-1]
        volume = df['Volume'].iloc[-1]
        avg_volume = df['Volume'].mean()
        vol_ratio = volume / avg_volume
        
        # جلب إشارات الدخول والخروج
        signal, rsi_val = get_signals(df)

        msg = (
            f"🔍 *تحليل محروس لـ {symbol}*\n"
            f"--------------------------\n"
            f"💰 *السعر الحالي:* `${price:.2f}`\n"
            f"📊 *قوة السيولة:* `{vol_ratio:.2f}x`\n"
            f"📉 *مؤشر RSI:* `{rsi_val:.1f}`\n"
            f"--------------------------\n"
            f"📢 *الإشارة:* **{signal}**\n\n"
            f"{'🚀 اختراق سيولة ضخم!' if vol_ratio > 2 else ''}"
        )
        await update.message.reply_text(msg, parse_mode='Markdown')
    except Exception as e:
        await update.message.reply_text(f"⚠️ حدث خطأ أثناء التحليل.")

# 2. المحرك الأساسي
async def main():
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("check", check_stock))
    
    print("🚀 رادار محروس قيد التشغيل...")
    await app.initialize()
    await app.start_polling(drop_pending_updates=True)
    while True: await asyncio.sleep(1)

if __name__ == "__main__":
    asyncio.run(main())
