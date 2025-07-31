import streamlit as st
import hashlib
import sqlite3

st.set_page_config(
    page_title='로그인 테스트',
    page_icon='🚩',
    layout='wide',
    initial_sidebar_state='expanded'
)

st.markdown("""
<style>
    .block-container {
        padding-top: 2rem !important;
        padding-bottom: 0 !important;
        max-width: 100% !important;
    }
    
    .main > div {
        max-width: 100% !important;
        padding-left: 1.5rem !important;
        padding-right: 1.5rem !important;
    }
    
    .element-container {
        margin-bottom: 10px !important;
    }
    
    # .stTextInput input {
    #     background-color: #f0f2f6 !important;
    #     border: none !important;
    #     border-radius: 5px !important;
    #     padding: 10px 15px !important;
    #     font-size: 16px !important;
    # }
    
    .stButton button {
        background-color: white !important;
        color: #424242 !important;
        width: 100% !important;
        border: 1px solid #ccc !important;
        border-radius: 5px !important;
        padding: 6px 12px !important;
        font-size: 14px !important;
        margin-top: 2px !important;
        margin-bottom: 2px !important;
        transition: all 0.3s !important;
    }
    
    .stButton button:hover {
        color: #1E88E5 !important;
        border-color: #1E88E5 !important;
    }
    
    .stButton button[kind="primary"] {
        background-color: #1E88E5 !important;
        color: white !important;
        border: 1px solid #1E88E5 !important;
    }

    .stButton button[kind="primary"]:hover {
        background-color: #1976D2 !important;
        color: white !important;
        border-color: #1976D2 !important;
    }
            
    .main-header {
        font-size: 2.5rem;
        margin-bottom: 1.5rem;
        margin-top: 1rem;
        font-weight: 600;
        color: #333;
        line-height: 1.2;
        padding-top: 0.5rem;
        overflow: visible;
    }
            
    .sub-header {
        font-size: 1.5rem;
        margin-bottom: 1rem;
        font-weight: 500;
        color: #424242;
    }
    
    .dashboard-card {
        background-color: white;
        border-radius: 10px;
        box-shadow: 0 2px 5px rgba(0,0,0,0.1);
        padding: 1rem;
        margin-bottom: 1rem;
    }
    
    .upload-box {
        border: 2px dashed #1E88E5;
        border-radius: 10px;
        padding: 2rem;
        text-align: center;
        margin: 1rem 0;
    }
    
    .report-container {
        background-color: #f8f9fa;
        border-radius: 8px;
        padding: 1rem;
        margin-bottom: 1rem;
    }
    
    .dataframe {
        width: 100%;
        border-collapse: collapse;
    }
    
    .dataframe th {
        background-color: #f0f2f6;
        padding: 8px;
        text-align: left;
    }
    
    .dataframe td {
        padding: 8px;
        border-bottom: 1px solid #f0f2f6;
    }
</style>
""", unsafe_allow_html=True)

if 'active_menu' not in st.session_state:
    st.session_state.active_menu = '대시보드'

def set_menu(menu_name):
    st.session_state.active_menu = menu_name
    st.rerun()

def init_db():
    conn = sqlite3.connect('test_data.db')
    c = conn.cursor()

    # 사용자 테이블 생성
    c.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT UNIQUE NOT NULL,
            password_hash TEXT,
            name TEXT NOT NULL,
            role TEXT DEFAULT 'user',
            login_type TEXT NOT NULL,
            google_id TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            last_login TIMESTAMP
        )
    ''')

    admin_email = 'admin@admin.com'
    admin_pw = 'admin123'
    admin_hash = hashlib.sha256(admin_pw.encode()).hexdigest()

    c.execute('''
        INSERT OR IGNORE INTO users (email, password_hash, name, role, login_type)
        VALUES (?, ?, ?, ?, ?)
    ''', (admin_email, admin_hash, "관리자", "admin", "email"))

    conn.commit()
    conn.close()

if 'db_init' not in st.session_state:
    init_db()
    st.session_state.db_init = True

def hash_pw(pw):
    return hashlib.sha256(pw.encode()).hexdigest()

def auth_email_user(email, password):
    conn = sqlite3.connect('test_data.db')
    c = conn.cursor()

    pw_hash = hash_pw(password)

    c.execute('''
        SELECT id, email, name, role FROM users 
        WHERE email = ? AND password_hash = ? AND login_type = 'email'
    ''', (email, pw_hash))

    user = c.fetchone()

    if user:
        # 마지막 로그인 시간 업데이트
        c.execute('''
            UPDATE users SET last_login = CURRENT_TIMESTAMP 
            WHERE email = ?
        ''', (email,))

        conn.commit()
    conn.close()

    return user

def handle_google_user(google_user_info):
    conn = sqlite3.connect('test_data.db')
    c = conn.cursor()

    email = google_user_info['email']
    name = google_user_info['name']
    google_id = google_user_info['sub']

    # 기존 구글 사용자 확인
    c.execute('''
        SELECT id, email, name, role FROM users 
        WHERE google_id = ? OR (email = ? AND login_type = 'google')
    ''', (google_id, email))

    user = c.fetchone()

    if user:
        # 기존 사용자 로그인 시간 업데이트
        c.execute('''
            UPDATE users SET last_login = CURRENT_TIMESTAMP 
            WHERE email = ?
        ''', (email,))
    else:
        # 새 구글 사용자 등록
        c.execute('''
            INSERT INTO users (email, name, role, login_type, google_id)
            VALUES (?, ?, ?, ?, ?)
        ''', (email, name, "user", "google", google_id))
        
        c.execute('''
            SELECT id, email, name, role FROM users 
            WHERE email = ? AND login_type = 'google'
        ''', (email,))

    conn.commit()
    conn.close()

    return user

def show_login_page():
    st.markdown('<h1 style = "text-align:center;">\
                로그인 테스트</h1>'
                , unsafe_allow_html=True)
    
    email = st.text_input('이메일 또는 아이디 입력'
                , placeholder='이메일 또는 아이디 입력'
                , key='login_email'
                , label_visibility="collapsed")

    password = st.text_input('비밀번호 입력'
                , placeholder='비밀번호 입력'
                , type='password'
                , key='password'
                , max_chars=16
                , label_visibility="collapsed")

    if st.button('로그인', type='primary'
            , key='email_login_btn'):
        if email and password:
            user = auth_email_user(email, password)
            
            if user:
                st.session_state.user_info = {
                    'id':user[0], 'email':user[1], 'name':user[2], 'role':user[3]
                }
                st.session_state.login_type = 'email'
                st.success('로그인 성공')
                print('로그인 성공')
                st.rerun()
            else:
                st.error('이메일 또는 비밀번호가 올바르지 않습니다.')
        else:
            st.error('이메일과 비밀번호를 입력해주세요.')

    st.markdown('<div style = "text-align:center;">또는</div>'
                , unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    with col1:
        if hasattr(st,'user') and hasattr(st.user, 'is_logged_in'):
            if not st.user.is_logged_in:
                if st.button('Google 로그인', type='primary', key='google_login'):
                    st.login()
            else:
                g_user_info = dict(st.user)
                user = handle_google_user(g_user_info)

                if user:
                    st.session_state.user_info = {
                        'id':user[0], 'email':user[1], 'name':user[2], 'role':user[3]
                    }
                    st.session_state.login_type = 'google'
                    st.success('Google 로그인 성공')
                    print('Google 로그인 성공')
                    st.rerun()
    with col2:
        if st.button('Microsoft 로그인', type='primary', key='ms_login'):
            pass
    
    st.markdown('<div style="text-align:center;">계정이 없으신가요?</div>'
                , unsafe_allow_html=True)

    st.button('회원가입', type='primary', key='reg_btn')

if 'user_info' not in st.session_state:
    show_login_page()
    st.stop()
else:
    with st.sidebar:
        st.write('로그인 성공')

        st.divider()

        st.write(f'{st.user.name}님 환영합니다.')

        col1, col2 = st.columns([0.2, 0.8])

        with col1:
            st.image(st.user.picture)
        with col2:
            st.write(f'{st.user.email}')
        
        st.divider()

        st.subheader('메인메뉴')
        
        if st.button('대시보드'
                    , type='primary' if st.session_state.active_menu == '대시보드'\
                        else 'secondary'):
            set_menu('대시보드')
        elif st.button('판매 데이터 분석', type='primary' if st.session_state.active_menu == '판매 데이터 분석'\
                        else 'secondary'):
            set_menu('판매 데이터 분석')
        elif st.button('고객 데이터 분석', type='primary' if st.session_state.active_menu == '고객 데이터 분석'\
                        else 'secondary'):
            set_menu('고객 데이터 분석')
        elif st.button('문서 분석기', type='primary' if st.session_state.active_menu == '문서 분석기'\
                        else 'secondary'):
            set_menu('문서 분석기')
        elif st.button('트렌드 모니터링', type='primary' if st.session_state.active_menu == '트렌드 모니터링'\
                        else 'secondary'):
            set_menu('트렌드 모니터링')
        elif st.button('보고서', type='primary' if st.session_state.active_menu == '보고서'\
                        else 'secondary'):
            set_menu('보고서')
        elif st.button('설정', type='primary' if st.session_state.active_menu == '설정'\
                        else 'secondary'):
            set_menu('설정')

        st.divider()

        if st.button('로그아웃', type='primary'):
            st.logout()

    if st.session_state.active_menu == '대시보드':
        # show_dashboard_content()
        st.write('대시보드')
        # st.dataframe(st.session_state.sales_data)
        # st.dataframe(st.session_state.customer_data)
        # st.dataframe(st.session_state.trend_data)
    elif st.session_state.active_menu == '판매 데이터 분석':
        # show_sales_analysis()
        st.write('판매 데이터 분석')
    elif st.session_state.active_menu == '고객 데이터 분석':
        st.write('고객 데이터 분석')
    elif st.session_state.active_menu == '문서 분석기':
        st.write('문서 분석기')
    elif st.session_state.active_menu == '트렌드 모니터링':
        st.write('트렌드 모니터링')
    elif st.session_state.active_menu == '보고서':
        st.write('보고서')
    elif st.session_state.active_menu == '설정':
        st.write('설정')