import streamlit as st
import google.generativeai as genai
import os

# 1. إعدادات الصفحة والواجهة
st.set_page_config(
    page_title="مرشد القبول الأهلي 2026-2027",
    page_icon="🎓",
    layout="centered"
)

# تخصيص المظهر ودعم اللغة العربية (RTL)
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Tajawal:wght@400;700&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Tajawal', sans-serif;
        direction: rtl;
        text-align: right;
    }
    .stChatMessage {
        direction: rtl;
        text-align: right;
    }
    .stTextInput input {
        direction: rtl;
        text-align: right;
    }
    .header-box {
        background: linear-gradient(135deg, #1f4037, #99f2c8);
        padding: 20px;
        border-radius: 12px;
        color: white;
        text-align: center;
        margin-bottom: 25px;
    }
</style>
""", unsafe_allow_html=True)

# ترويسة الواجهة
st.markdown("""
<div class="header-box">
    <h2>🎓 المرشد الذكي لشؤون وضوابط القبول الجامعي الأهلي</h2>
    <p>مخصص لطلبة السادس الإعدادي | السنة الدراسية 2026 - 2027</p>
</div>
""", unsafe_allow_html=True)

# 2. إعداد مفتاح API الخاص بـ Gemini
# يتم جلبه من Secrets عند الرفع أو من متغيرات البيئة
api_key = st.secrets.get("GEMINI_API_KEY", os.getenv("GEMINI_API_KEY"))

if not api_key:
    st.error("يرجى ضبط مفتاح GEMINI_API_KEY في إعدادات Secrets.")
    st.stop()

genai.configure(api_key=api_key)

# 3. تحميل ومعالجة ملف الدليل مع التخزين المؤقت
@st.cache_resource(show_spinner="جاري تهيئة الدليل الإرشادي ومطابقة البيانات...")
def init_system():
    pdf_filename = "daleel_ahly_2026_2027.pdf"
    if not os.path.exists(pdf_filename):
        raise FileNotFoundError(f"الملف {pdf_filename} غير موجود في مسار التطبيق.")
    
    # رفع الملف مباشرة إلى واجهة Gemini File API
    uploaded_doc = genai.upload_file(pdf_filename)
    
    # توجيهات النظام الصارمة لحصر الإجابات بالدليل فقط ومنع الهلوسة
    system_instruction = (
        "أنت مرشد أكاديمي ذكي متخصص بالإجابة على استفسارات طلبة السادس الإعدادي في العراق "
        "للسنة الدراسية 2026-2027 حصراً استناداً إلى ملف 'الدليل الإرشادي للتقديم وضوابط القبول "
        "وشؤون الطلبة للجامعات والكليات الأهلية' المرفق معك.\n\n"
        "قواعد العمل الصارمة:\n"
        "1. اعتمد فقط وحصراً على المعلومات المذكورة داخل هذا الملف المرفق.\n"
        "2. إذا كان السؤال عن مسألة لم يتناولها هذا الدليل أو خارج نطاق التعليم الأهلي لعام 2026-2027، "
        "أجب بلباقة: 'عذراً، هذه المعلومة غير واردة في الدليل الإرشادي المعتمد للعام الدراسي 2026-2027'.\n"
        "3. قدم الإجابات بلغة عربية واضحة ودقيقة ومهذبة، واذكر الحدود الدنيا للأقسام، الشروط، "
        "خطوات منصة (قدّم)، الاستثناءات، وقنوات القبول بدقة تامة دون تخمين أو تأليف."
    )
    
    model = genai.GenerativeModel(
        model_name="gemini-1.5-flash",
        system_instruction=system_instruction
    )
    
    # بدء جلسة محادثة مع إرفاق المستند كجزء من السياق الأساسي
    chat = model.start_chat(history=[
        {
            "role": "user",
            "parts": [uploaded_doc, "اعتمد هذا الدليل المرفق كمرجع وحيد ودائم لكافة استفسارات المحادثة."]
        },
        {
            "role": "model",
            "parts": ["تم استيعاب الدليل الإرشادي بالكامل، وأنا جاهز لإرشاد الطلبة بدقة متناهية."]
        }
    ])
    return chat

try:
    chat_session = init_system()
except Exception as e:
    st.error(f"حدث خطأ أثناء تحميل الملف: {str(e)}")
    st.stop()

# 4. إدارة سجل المحادثة داخل الجلسة (Session State)
if "messages" not in st.session_state:
    st.session_state.messages = [
        {"role": "assistant", "content": "مرحباً بك! أنا مرشدك الذكي لشؤون التقديم والقبول في الكليات الأهلية لسنة 2026-2027. يمكنك سؤالي عن الحدود الدنيا، ضوابط قنوات القبول، المنحة المجانية، أو مراحل التقديم عبر تطبيق منصة (قدّم)."}
    ]

# عرض الرسائل السابقة
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.write(msg["content"])

# استقبال السؤال ومعالجته
if user_query := st.chat_input("اكتب استفسارك هنا (مثال: ما هو الحد الأدنى لهندسة الذكاء الاصطناعي؟)"):
    # إضافة سؤال المستخدم للواجهة والسجل
    st.session_state.messages.append({"role": "user", "content": user_query})
    with st.chat_message("user"):
        st.write(user_query)

    # توليد الإجابة
    with st.chat_message("assistant"):
        with st.spinner("جاري استخراج الإجابة من الدليل..."):
            try:
                response = chat_session.send_message(user_query)
                reply_text = response.text
                st.write(reply_text)
                st.session_state.messages.append({"role": "assistant", "content": reply_text})
            except Exception as err:
                err_msg = "تعذر الحصول على إجابة في الوقت الحالي، يرجى المحاولة ثانية."
                st.error(err_msg)
