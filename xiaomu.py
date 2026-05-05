# 小沐AI 最终版
import streamlit as st
from openai import OpenAI
from datetime import datetime
import os

# ====================== 基础配置 ======================
st.set_page_config(page_title="小沐AI", page_icon="💛", layout="wide")

# 从环境变量读取 API Key，不上传代码！
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY", "")
client = OpenAI(
    api_key=DEEPSEEK_API_KEY,
    base_url="https://api.deepseek.com"
)

# ====================== 样式（居中气泡 + 两端对齐） ======================
st.markdown("""
<style>
.chat-container {
    max-width: 700px;
    margin: 0 auto;
    padding: 0 20px;
}
.bubble-user {
    background: #d7faff;
    padding: 10px 14px;
    border-radius: 16px 0 16px 16px;
    max-width: 75%;
    margin-left: auto;
    margin-bottom: 10px;
}
.bubble-ai {
    background: #fff;
    padding: 10px 14px;
    border-radius: 0 16px 16px 16px;
    max-width: 75%;
    margin-right: auto;
    margin-bottom: 10px;
    box-shadow: 0 1px 3px #00000010;
}
.time {
    font-size:11px;
    color:#999;
    margin:4px 0;
    text-align: right;
}
.name {
    font-size:13px;
    color:#444;
    margin-bottom:4px;
    font-weight:500;
}
.highlight-red {
    background: #ffebee;
    border-left: 4px solid #f44336;
    padding: 10px 14px;
    border-radius: 0 16px 16px 16px;
    max-width: 75%;
    margin-right: auto;
    margin-bottom: 10px;
}
.badge {
    background: #ff4d4d;
    color: white;
    font-size: 12px;
    padding: 2px 6px;
    border-radius: 10px;
    min-width: 18px;
    text-align: center;
    display: inline-block;
}
.auto-message {
    opacity: 0;
    animation: popIn 1s ease-out forwards;
}
@keyframes popIn {
    0% { opacity:0; transform: translateY(15px); }
    100% { opacity:1; transform: translateY(0); }
}
</style>
""", unsafe_allow_html=True)

# ====================== 初始化 ======================
if "current_chat" not in st.session_state:
    st.session_state.current_chat = "小沐"
if "current_time" not in st.session_state:
    st.session_state.current_time = "2026-05-06 09:00"
if "user_msgs" not in st.session_state:
    st.session_state.user_msgs = {}
if "sent_auto_msg" not in st.session_state:
    st.session_state.sent_auto_msg = set()

if "task_1" not in st.session_state: st.session_state.task_1 = False
if "task_2" not in st.session_state: st.session_state.task_2 = False
if "task_3" not in st.session_state: st.session_state.task_3 = False
if "task_3_enable" not in st.session_state:
    st.session_state.task_3_enable = False

# 未读：加入“当前任务清单”的未读支持
if "unread" not in st.session_state:
    st.session_state.unread = {
        "小沐": 0,
        "通知群": 0,
        "交流群": 0,
        "小A": 0,
        "小B": 0,
        "当前任务清单": 0
    }

# 情绪记忆
if "has_negative_history" not in st.session_state:
    st.session_state.has_negative_history = False

if "last_help_time" not in st.session_state:
    st.session_state.last_help_time = None
if "help_type" not in st.session_state:
    st.session_state.help_type = None

if "scroll_to_task" not in st.session_state:
    st.session_state.scroll_to_task = False
if "auto_delay" not in st.session_state:
    st.session_state.auto_delay = True


# ====================== 时间工具 ======================
def is_before_or_equal(msg_time, current_time):
    try:
        t1 = datetime.strptime(msg_time, "%Y-%m-%d %H:%M")
        t2 = datetime.strptime(current_time, "%Y-%m-%d %H:%M")
        return t1 <= t2
    except:
        return True


# ====================== 自动触发 ======================
def auto_trigger():
    t = st.session_state.current_time
    key = f"auto_{t}"
    if key in st.session_state.sent_auto_msg:
        return

    # 5.7 09:00 群主通知
    if t == "2026-05-07 09:00":
        msg = {"name": "群主", "text": "大家 5.9 12:00 前把发的信息表填完上交。", "time": "2026-05-07 09:00", "auto": True}
        st.session_state.user_msgs.setdefault("通知群", []).append(msg)
        st.session_state.task_3_enable = True
        if st.session_state.current_chat != "通知群":
            st.session_state.unread["通知群"] += 1
        st.session_state.unread["当前任务清单"] += 1

    # 5.7 09:00 智能问候
    if t == "2026-05-07 09:00":
        need_greet = False
        greet_text = ""

        if st.session_state.has_negative_history:
            greet_text = "今天感觉怎么样了呀，有没有开心一点🥺"
            need_greet = True

        if not need_greet and st.session_state.last_help_time is not None:
            try:
                t_now = datetime.strptime(t, "%Y-%m-%d %H:%M")
                t_help = datetime.strptime(st.session_state.last_help_time, "%Y-%m-%d %H:%M")
                delta = t_now - t_help
                if 0 < delta.total_seconds() < 48 * 3600:
                    if st.session_state.help_type == "study":
                        greet_text = "昨天学习的内容都掌握了吗？要不要我陪你复习一下～"
                    else:
                        greet_text = "昨天的事情有没有搞定呀？还需要我帮忙吗？"
                    need_greet = True
            except:
                pass

        if need_greet:
            st.session_state.user_msgs.setdefault("小沐", []).append({
                "name": "小沐", "text": greet_text, "time": t, "auto": True
            })
            if st.session_state.current_chat != "小沐":
                st.session_state.unread["小沐"] += 1

    if t == "2026-05-06 09:00":
        txt = "早上好呀！今天感觉怎么样了呀，有没有开心一点🥺"
        st.session_state.user_msgs.setdefault("小沐", []).append({"name": "小沐", "text": txt, "time": t, "auto": True})
        if st.session_state.current_chat != "小沐":
            st.session_state.unread["小沐"] += 1

    if t == "2026-05-06 14:00":
        txt = "别忘了今天晚上要交demo咯，如果有还没搞定的地方，小沐可以帮忙哟～"
        st.session_state.user_msgs.setdefault("小沐", []).append({"name": "小沐", "text": txt, "time": t, "auto": True})
        if st.session_state.current_chat != "小沐":
            st.session_state.unread["小沐"] += 1

    if t == "2026-05-07 14:00":
        txt = "别忘了明天之前要交活动策划案啦，如果有还没搞定的地方，小沐可以帮忙哟～"
        st.session_state.user_msgs.setdefault("小沐", []).append({"name": "小沐", "text": txt, "time": t, "auto": True})
        if st.session_state.current_chat != "小沐":
            st.session_state.unread["小沐"] += 1

    st.session_state.sent_auto_msg.add(key)


auto_trigger()

# ====================== 侧边栏 ======================
with st.sidebar:
    st.title("💛 小沐")
    st.subheader("⏰ 当前时间")
    time_opts = ["2026-05-06 09:00", "2026-05-06 14:00", "2026-05-07 09:00", "2026-05-07 14:00"]
    selected_time = st.selectbox("切换时间", time_opts, index=0)
    if selected_time != st.session_state.current_time:
        st.session_state.current_time = selected_time
        st.session_state.auto_delay = True
        st.rerun()

    st.markdown("---")
    st.subheader("💬 聊天")
    chat_list = ["小沐", "通知群", "交流群", "小A", "小B", "当前任务清单"]
    for item in chat_list:
        c1, c2 = st.columns([7, 1])
        with c1:
            if st.button(item, use_container_width=True):
                st.session_state.current_chat = item
                if item in st.session_state.unread:
                    st.session_state.unread[item] = 0
                if item in ["通知群", "小B"]:
                    st.session_state.scroll_to_task = True
                st.rerun()
        with c2:
            if item in st.session_state.unread and st.session_state.unread[item] > 0:
                show = str(st.session_state.unread[item]) if st.session_state.unread[item] <= 9 else "9+"
                st.markdown(f"<div class='badge'>{show}</div>", unsafe_allow_html=True)

    st.markdown("---")
    st.subheader("⚙️ 设置")
    temp = st.slider("温柔度", 0.3, 1.0, 0.7)

    # 清空按钮
    if st.button("🗑 清空当前聊天", use_container_width=True):
        c = st.session_state.current_chat
        if c in st.session_state.user_msgs:
            st.session_state.user_msgs[c] = []

        # 重置情绪
        st.session_state.has_negative_history = False
        st.session_state.last_help_time = None
        st.session_state.help_type = None

        # 重置自动消息（可重新发送）
        st.session_state.sent_auto_msg = set()

        # 重置任务
        st.session_state.task_3_enable = False

        # 重置界面状态
        st.session_state.auto_delay = True
        st.session_state.scroll_to_task = False

        st.rerun()

# ====================== 主界面 ======================
current = st.session_state.current_chat
now_time = st.session_state.current_time
st.header(f"💬 {current}")
st.divider()

builtin = {
    "小沐": [
        {"name": "我", "text": "假期要过完了，但是感觉我的demo还差点意思，呜呜呜，感觉压力好大。", "time": "2026-05-05 17:00"},
        {"name": "小沐", "text": "ddl临近确实会容易感到焦虑。我来帮你放一首舒缓的歌曲吧，听一听歌压力会缓解一点，效率也会Up！Up！Up！", "time": "2026-05-05 17:00"},
        {"name": "我", "text": "来首歌吧，今天应该是要加班加点赶工咯", "time": "2026-05-05 17:00"},
        {"name": "小沐", "text": "【为您播放歌曲】嗯嗯，加油加油，小沐相信你肯定能克服困难顺利完成任务的，如果有还没搞定的地方，小沐可以做你的军师。", "time": "2026-05-05 17:00"},
        {"name": "我", "text": "小沐，我不开心，好想哭", "time": "2026-05-05 18:00"},
        {"name": "小沐", "text": "抱抱！不哭不哭，我在呢，跟我说说怎么了？", "time": "2026-05-05 18:00"},
    ],
    "通知群": [
        {"name": "群主", "text": "demo记得在5月6日23点59前交上来", "time": "2026-05-01 13:14"},
        {"name": "小A", "text": "收到", "time": "2026-05-01 13:15"},
        {"name": "我", "text": "收到", "time": "2026-05-01 13:15"},
        {"name": "小B", "text": "收到", "time": "2026-05-01 13:15"},
    ],
    "交流群": [
        {"name": "小A", "text": "我去深圳大鹏半岛看海，好漂亮呀", "time": "2026-05-03 15:20"},
        {"name": "小B", "text": "这么棒！下次我也要去。", "time": "2026-05-03 15:21"},
    ],
    "小A": [
        {"name": "小A", "text": "姐妹，我从深圳给你带了点好吃的，明天给你送过去呀", "time": "2026-05-03 20:30"},
        {"name": "我", "text": "啊，这也太棒了！", "time": "2026-05-03 20:30"},
        {"name": "我", "text": "爱你，爱你，明天晚上我请你吃饭呀", "time": "2026-05-03 20:31"},
    ],
    "小B": [
        {"name": "小B", "text": "5月8日前把今年团建的活动策划案给我", "time": "2026-04-28 09:52"},
        {"name": "我", "text": "好的好的", "time": "2026-04-28 09:52"},
    ]
}

# -------------------- 任务清单 --------------------
if current == "当前任务清单":
    st.subheader("✅ 当前任务")
    t1 = st.checkbox("2026.5.6 23:59 前上交demo", value=st.session_state.task_1)
    c1, c2 = st.columns([9, 2])
    with c2:
        if st.button("前往查看", key="goto1"):
            st.session_state.current_chat = "通知群"
            st.session_state.scroll_to_task = True
            st.rerun()
    if t1 and not st.session_state.task_1:
        st.session_state.task_1 = True
        st.session_state.user_msgs.setdefault("小沐", []).append({
            "name": "小沐", "text": "太棒啦！你已完成：2026.5.6 23:59前上交demo ✅", "time": now_time
        })
        if st.session_state.current_chat != "小沐":
            st.session_state.unread["小沐"] += 1
        st.rerun()

    st.write("")
    t2 = st.checkbox("2026.5.8 前完成活动策划案", value=st.session_state.task_2)
    c1, c2 = st.columns([9, 2])
    with c2:
        if st.button("前往查看", key="goto2"):
            st.session_state.current_chat = "小B"
            st.session_state.scroll_to_task = True
            st.rerun()
    if t2 and not st.session_state.task_2:
        st.session_state.task_2 = True
        st.session_state.user_msgs.setdefault("小沐", []).append({
            "name": "小沐", "text": "太棒啦！你已完成：2026.5.8前完成活动策划案 ✅", "time": now_time
        })
        if st.session_state.current_chat != "小沐":
            st.session_state.unread["小沐"] += 1
        st.rerun()

    st.write("")
    if st.session_state.task_3_enable:
        t3 = st.checkbox("2026.5.9 12:00 前完成信息表填写上交", value=st.session_state.task_3)
        c1, c2 = st.columns([9, 2])
        with c2:
            if st.button("前往查看", key="goto3"):
                st.session_state.current_chat = "通知群"
                st.session_state.scroll_to_task = True
                st.rerun()
        if t3 and not st.session_state.task_3:
            st.session_state.task_3 = True
            st.session_state.user_msgs.setdefault("小沐", []).append({
                "name": "小沐", "text": "太棒啦！你已完成：2026.5.9 12:00前完成信息表填写上交 ✅", "time": now_time
            })
            if st.session_state.current_chat != "小沐":
                st.session_state.unread["小沐"] += 1
            st.rerun()
    st.stop()

# -------------------- 消息展示 --------------------
all_msg = []
if current in builtin:
    for m in builtin[current]:
        if is_before_or_equal(m["time"], now_time):
            all_msg.append(m)
if current in st.session_state.user_msgs:
    for m in st.session_state.user_msgs[current]:
        if is_before_or_equal(m["time"], now_time):
            all_msg.append(m)

all_msg = sorted(all_msg, key=lambda x: datetime.strptime(x["time"], "%Y-%m-%d %H:%M"))

with st.container():
    for msg in all_msg:
        name = msg.get("name")
        text = msg.get("text")
        time = msg.get("time")
        is_auto = msg.get("auto", False) and st.session_state.auto_delay
        ani_class = "auto-message" if is_auto else ""
        highlight = False
        anchor = ""

        if current == "通知群" and name == "群主" and ("demo" in text or "信息表" in text):
            highlight = True
            anchor = "<a id='task_msg'></a>"
        if current == "小B" and name == "小B" and "策划案" in text:
            highlight = True
            anchor = "<a id='task_msg'></a>"

        if name == "我":
            st.markdown(f'<div class="time">{time}</div>', unsafe_allow_html=True)
            st.markdown(f'<div class="bubble-user">{text}</div>', unsafe_allow_html=True)
            continue

        st.markdown(f'<div class="name">{name}</div>', unsafe_allow_html=True)
        if highlight:
            st.markdown(f'{anchor}<div class="highlight-red {ani_class}">{text}</div>', unsafe_allow_html=True)
        else:
            st.markdown(f'<div class="bubble-ai {ani_class}">{text}</div>', unsafe_allow_html=True)
            st.markdown(f'<div class="time">{time}</div>', unsafe_allow_html=True)

        st.markdown("""""")
<script>
setTimeout(() => {
    window.parent.postMessage({type: "streamlit:setComponentValue", data: {value: true}}, "*");
}, 1800);
</script>
""", unsafe_allow_html=True)
            st.session_state.auto_delay = False

            st.markdown("""
<script>
window.addEventListener('load', function(){
    setTimeout(() => {
        window.scrollTo(0, document.body.scrollHeight);
    }, 100);
});
</script>
""", unsafe_allow_html=True)

            if st.session_state.scroll_to_task:
                st.markdown("""
    <script>
    setTimeout(()=>{
        let el = document.getElementById('task_msg');
        if(el) el.scrollIntoView({behavior:'smooth'});
    }, 100);
    </script>
    """, unsafe_allow_html=True)
            st.session_state.scroll_to_task = False

            # -------------------- 输入框 --------------------
            prompt = st.chat_input("输入消息...")
            st.markdown("""
<script>
const t = window.parent.document.querySelector('textarea');
if(t) t.focus();
</script>
""", unsafe_allow_html=True)

            if prompt:
                lower = prompt.lower()
            negative = ["不开心", "难过", "压力", "烦", "累", "哭", "焦虑", "崩"]
            study_words = ["学习", "复习", "知识点", "教我", "不会", "题目"]
            help_words = ["帮我", "帮忙", "怎么做", "代码"]

            for w in negative:
                if
            w in lower:
            st.session_state.has_negative_history = True

            if any(w in lower for w in study_words):
                st.session_state.last_help_time = now_time
            st.session_state.help_type = "study"
            elif any(w in lower for w in help_words):
            st.session_state.last_help_time = now_time
            st.session_state.help_type = "help"

            st.session_state.user_msgs.setdefault(current, []).append({"name": "我", "text": prompt, "time": now_time})

            if current == "小沐":
                with
            st.spinner("小沐正在输入..."):
            history = []
            for m in st.session_state.user_msgs.get("小沐", []):
                if
            is_before_or_equal(m["time"], now_time):
            history.append({
                "role": "user" if m["name"] == "我" else "assistant",
                "content": m["text"]
            })
            system = "你是小沐，温柔可爱、治愈、会共情、语气软、简短、不乱接话。"
            messages = [{"role": "system", "content": system}] + history
            res = client.chat.completions.create(
                model="deepseek-v4-flash",
                messages=messages,
                temperature=temp
            )
            ai_text = res.choices[0].message.content[:120]
            st.session_state.user_msgs["小沐"].append({"name": "小沐", "text": ai_text, "time": now_time})
            if st.session_state.current_chat != "小沐":
                st.session_state.unread["小沐"] += 1
            st.rerun()