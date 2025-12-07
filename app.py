import streamlit as st
import pandas as pd
import yaml
import hashlib
import os

st.set_page_config(page_title="کانورتور فاکتور مالیاتی", layout="wide")
st.title("کانورتور هوشمند فاکتور به فرمت استاندارد سازمان امور مالیاتی")

# --- سیستم ورود ساده ---
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False

def login():
    st.sidebar.header("ورود به سیستم")
    username = st.sidebar.text_input("نام کاربری")
    password = st.sidebar.text_input("رمز عبور", type="password")
    if st.sidebar.button("ورود"):
        if username == "admin" and password == "123456":
            st.session_state.logged_in = True
            st.session_state.username = username
            st.sidebar.success("ورود موفق!")
        else:
            st.sidebar.error("نام کاربری یا رمز اشتباه است")

if not st.session_state.logged_in:
    login()
    st.stop()

if st.sidebar.button("خروج"):
    st.session_state.logged_in = False
    st.rerun()

# --- الگوهای استاندارد ---
templates = {
    "الگوی اول (فروش)": [
        "شماره منحصر به فرد مالیاتی", "تاریخ صدور", "نوع صورتحساب", "الگوی صورتحساب",
        "شماره اقتصادی فروشنده", "مجموع مبلغ قبل تخفیف", "مجموع تخفیفات", "مجموع پس از تخفیف",
        "مالیات ارزش افزوده", "مجموع صورتحساب", "شناسه کالا", "تعداد", "قیمت واحد", "مبلغ کل"
    ],
    "الگوی سوم (طلا و جواهر)": [
        "شماره منحصر به فرد مالیاتی", "تاریخ صدور", "وزن خالص", "عیار", "قیمت هر گرم",
        "اجرت ساخت", "سود فروشنده", "حق العمل", "جمع کل اجرت و سود", "مالیات", "مجموع صورتحساب"
    ]
}

# --- ذخیره تنظیمات ---
config_file = "user_config.yaml"
if os.path.exists(config_file):
    with open(config_file, "r", encoding="utf-8") as f:
        user_config = yaml.safe_load(f) or {}
else:
    user_config = {}

st.header("۱. انتخاب الگوی صورتحساب")
template = st.selectbox("الگوی مورد نظر را انتخاب کنید", list(templates.keys()))

if template:
    st.success(f"الگوی انتخاب شده: **{template}**")
    fields = templates[template]
    
    st.header("۲. مپ کردن ستون‌های فایل شما")
    mapping = user_config.get(template, {})
    
    new_mapping = {}
    for field in fields:
        default = mapping.get(field, "")
        col = st.text_input(f"ستون **{field}** در فایل شما کجاست؟ (مثل A یا H یا نام ستون)", value=default, key=field)
        if col.strip():
            new_mapping[field] = col.strip()

    col1, col2 = st.columns(2)
    with col1:
        if st.button("ذخیره تنظیمات (دفعه بعد لازم نیست دوباره وارد کنی)"):
            user_config[template] = new_mapping
            with open(config_file, "w", encoding="utf-8") as f:
                yaml.dump(user_config, f, allow_unicode=True)
            st.success("تنظیمات با موفقیت ذخیره شد!")

    st.header("۳. آپلود فایل اکسل و دریافت خروجی")
    uploaded_file = st.file_uploader("فایل اکسل خود را اینجا بکشید", type=["xlsx", "xls"])

    if uploaded_file and new_mapping:
        try:
            df = pd.read_excel(uploaded_file)
            headers = df.columns.tolist()
            
            output_df = pd.DataFrame()
            
            for field, user_col in new_mapping.items():
                if user_col.isdigit():
                    col_idx = int(user_col) - 1
                else:
                    col_idx = headers.index(user_col) if user_col in headers else None
                
                if col_idx is not None and col_idx < len(df.columns):
                    output_df[field] = df.iloc[:, col_idx]
                else:
                    output_df[field] = ""
                    st.warning(f"ستون {user_col} برای {field} پیدا نشد")

            st.success("تبدیل با موفقیت انجام شد!")
            st.dataframe(output_df.head(10))

            csv = output_df.to_csv(index=False, encoding='utf-8-sig').encode('utf-8-sig')
            st.download_button(
                label="دانلود فایل استاندارد (CSV)",
                data=csv,
                file_name=f"فاکتور_استاندارد_{template.replace(' ', '_')}.csv",
                mime="text/csv"
            )
            
            excel_bytes = output_df.to_excel(index=False, engine='openpyxl')
            st.download_button(
                label="دانلود فایل استاندارد (Excel)",
                data=excel_bytes,
                file_name=f"فاکتور_استاندارد_{template.replace(' ', '_')}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
            
        except Exception as e:
            st.error(f"خطا در خواندن فایل: {e}")

st.info("نکته: بعد از اولین بار تنظیم ستون‌ها، دفعه بعد فقط فایل آپلود کنید و خروجی بگیرید!")
