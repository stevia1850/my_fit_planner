import json
import os
from datetime import date, datetime

import pandas as pd
import streamlit as st

from exercises import EXERCISES, RECOMMENDED, get_all_exercises, get_exercise_by_id

st.set_page_config(
    page_title="My Fit Planner",
    page_icon="💪",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown(
    """
<style>
    .main-header { font-size: 2rem; font-weight: 700; margin-bottom: 0.2rem; }
    .sub-header { font-size: 1rem; color: #666; margin-bottom: 1.2rem; }
    .muscle-tag {
        display: inline-block; background: #eef2ff; color: #4f46e5;
        padding: 0.2rem 0.65rem; border-radius: 16px; font-size: 0.8rem; margin-right: 0.3rem;
    }
    .safe-tag {
        display: inline-block; background: #ecfdf5; color: #059669;
        padding: 0.2rem 0.65rem; border-radius: 16px; font-size: 0.8rem;
    }
    .caution-tag {
        display: inline-block; background: #fef3c7; color: #d97706;
        padding: 0.2rem 0.65rem; border-radius: 16px; font-size: 0.8rem;
    }
    .feedback-box {
        background: #f0f9ff; border-left: 4px solid #0ea5e9;
        padding: 0.9rem 1.1rem; border-radius: 0 10px 10px 0; margin: 0.8rem 0;
    }
</style>
""",
    unsafe_allow_html=True,
)

DATA_DIR = "data"
os.makedirs(DATA_DIR, exist_ok=True)
WORKOUT_FILE = os.path.join(DATA_DIR, "workouts.json")
BODY_FILE = os.path.join(DATA_DIR, "body.json")
DIET_FILE = os.path.join(DATA_DIR, "diet.json")
PROFILE_FILE = os.path.join(DATA_DIR, "profile.json")

DEFAULT_PROFILE = {
    "name": "동휘",
    "age": 35,
    "height": 167,
    "weight": 67.0,
    "body_fat": 22.0,
    "goal_fat": 15.0,
    "gender": "남성",
    "protein_target": 120,
}


def load_json(path, default=None):
    if default is None:
        default = []
    if os.path.exists(path):
        try:
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return default
    return default


def save_json(path, data):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


if "profile" not in st.session_state:
    st.session_state.profile = load_json(PROFILE_FILE, DEFAULT_PROFILE)
    for k, v in DEFAULT_PROFILE.items():
        st.session_state.profile.setdefault(k, v)

if "selected_exercises" not in st.session_state:
    st.session_state.selected_exercises = []


def week_workouts():
    workouts = load_json(WORKOUT_FILE)
    today = date.today()
    out = []
    for w in workouts:
        try:
            d = datetime.strptime(w["date"], "%Y-%m-%d").date()
            if d.isocalendar()[1] == today.isocalendar()[1] and d.year == today.year:
                out.append(w)
        except Exception:
            continue
    return out


def badge(ex):
    if ex.get("shoulder_safe", True):
        return '<span class="safe-tag">어깨 안전</span>'
    return '<span class="caution-tag">어깨 주의</span>'


WEEKDAY_KR = ["월", "화", "수", "목", "금", "토", "일"]

with st.sidebar:
    st.markdown("## 💪 My Fit Planner")
    st.caption("개인 전용 운동 플래너")
    st.markdown("---")
    menu = st.radio(
        "메뉴",
        [
            "🏠 홈",
            "📅 오늘의 추천 루틴",
            "💪 운동 선택·체크",
            "📋 운동 기록",
            "📊 신체 기록",
            "🍎 식단",
            "🔥 운동 도감",
            "⚙️ 설정",
        ],
        label_visibility="collapsed",
    )
    st.markdown("---")
    p = st.session_state.profile
    st.markdown(f"**목표**  체지방 {p['goal_fat']}%")
    st.markdown(f"**현재**  {p['body_fat']}%")
    span = max(0.1, 22.0 - float(p["goal_fat"]))
    done = max(0.0, min(1.0, (22.0 - float(p["body_fat"])) / span))
    st.progress(done)
    st.caption(f"남은 체지방 약 {float(p['body_fat']) - float(p['goal_fat']):.1f}%p")


if menu == "🏠 홈":
    today = date.today()
    rec = RECOMMENDED[today.weekday()]
    st.markdown(f'<p class="main-header">안녕하세요, {p.get("name", "나")}님 👋</p>', unsafe_allow_html=True)
    st.markdown(
        f'<p class="sub-header">{today.strftime("%Y.%m.%d")} ({WEEKDAY_KR[today.weekday()]}) · 오늘 추천: {rec["title"]}</p>',
        unsafe_allow_html=True,
    )

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("체중", f"{p['weight']} kg")
    c2.metric("체지방", f"{p['body_fat']}%")
    c3.metric("목표까지", f"{float(p['body_fat']) - float(p['goal_fat']):.1f}%p")
    this_week = week_workouts()
    c4.metric("이번 주 운동", f"{len(this_week)}회")

    if len(this_week) >= 3:
        feedback = "이번 주 횟수가 충분합니다. 자세와 점진적 과부하만 챙기면 됩니다."
    elif len(this_week) >= 1:
        feedback = "좋습니다. 주 3회가 최소 목표입니다. 오늘 루틴을 하나 완료해보세요."
    else:
        feedback = "이번 주 기록이 아직 없습니다. 어깨 워밍업부터 가볍게 시작하세요."
    st.markdown(f'<div class="feedback-box">{feedback}</div>', unsafe_allow_html=True)

    st.info(
        "회전근개 이력이 있으니 **밀기 운동 전 워밍업 10~15분**은 빼지 마세요. "
        "통증이 있으면 그 동작은 건너뛰면 됩니다."
    )

    workouts = load_json(WORKOUT_FILE)
    if workouts:
        st.markdown("### 최근 운동")
        for w in sorted(workouts, key=lambda x: x["date"], reverse=True)[:5]:
            names = ", ".join(w.get("exercises", [])[:6])
            extra = " ..." if len(w.get("exercises", [])) > 6 else ""
            st.markdown(f"- **{w['date']}** · {names}{extra}")


elif menu == "📅 오늘의 추천 루틴":
    today = date.today()
    rec = RECOMMENDED[today.weekday()]
    st.markdown('<p class="main-header">오늘의 추천 루틴</p>', unsafe_allow_html=True)
    st.markdown(
        f'<p class="sub-header">{WEEKDAY_KR[today.weekday()]}요일 · {rec["title"]}</p>',
        unsafe_allow_html=True,
    )

    if not rec["main"] and not rec["cardio"]:
        st.success("오늘은 완전 휴식일입니다. 걷거나 스트레칭만 해도 충분합니다.")
    else:
        sections = [
            ("1. 워밍업", rec["warmup"]),
            ("2. 본 운동", rec["main"]),
            ("3. 유산소 (선택)", rec["cardio"]),
        ]
        for title, ids in sections:
            if not ids:
                continue
            st.markdown(f"### {title}")
            for eid in ids:
                ex = get_exercise_by_id(eid)
                if not ex:
                    continue
                checked = st.checkbox(
                    f"{ex['name']}  ({ex['equipment']})",
                    key=f"rec_{eid}",
                    value=eid in st.session_state.selected_exercises,
                )
                if checked and eid not in st.session_state.selected_exercises:
                    st.session_state.selected_exercises.append(eid)
                elif not checked and eid in st.session_state.selected_exercises:
                    st.session_state.selected_exercises.remove(eid)
                with st.expander("타겟 근육 · 방법 보기"):
                    st.markdown(f"**타겟**  {ex['muscles']}")
                    st.markdown(f"**방법**  {ex['how_to']}")
                    st.markdown(f"**팁**  {ex['tip']}")
                    st.markdown(badge(ex), unsafe_allow_html=True)

        notes = st.text_area("오늘 메모 (무게/횟수/컨디션)", placeholder="예: 레그프레스 80kg 12x3, 어깨 컨디션 좋음")
        if st.button("이 루틴 완료로 저장", type="primary", use_container_width=True):
            names = []
            for eid in st.session_state.selected_exercises:
                ex = get_exercise_by_id(eid)
                if ex:
                    names.append(ex["name"])
            if not names:
                st.warning("체크한 운동이 없습니다.")
            else:
                workouts = load_json(WORKOUT_FILE)
                workouts.append(
                    {
                        "date": str(today),
                        "exercises": names,
                        "exercise_ids": list(st.session_state.selected_exercises),
                        "notes": notes,
                        "plan": rec["title"],
                        "timestamp": datetime.now().isoformat(),
                    }
                )
                save_json(WORKOUT_FILE, workouts)
                st.session_state.selected_exercises = []
                st.success("저장했습니다. 수고했어요!")
                st.rerun()


elif menu == "💪 운동 선택·체크":
    st.markdown('<p class="main-header">운동 선택 · 체크</p>', unsafe_allow_html=True)
    st.markdown('<p class="sub-header">헬스장에서 기구를 보고 골라 체크하면 됩니다.</p>', unsafe_allow_html=True)

    cats = list(EXERCISES.keys())
    selected_cat = st.selectbox("카테고리", ["전체"] + cats)
    q = st.text_input("검색 (운동/기구 이름)", placeholder="예: 레그프레스, 덤벨, 랫풀다운")

    items = get_all_exercises()
    if selected_cat != "전체":
        items = [e for e in items if e["category"] == selected_cat]
    if q:
        ql = q.lower()
        items = [e for e in items if ql in e["name"].lower() or ql in e["equipment"].lower()]

    for ex in items:
        col_c, col_i = st.columns([0.08, 0.92])
        with col_c:
            checked = st.checkbox(
                "선택",
                key=f"chk_{ex['id']}",
                value=ex["id"] in st.session_state.selected_exercises,
                label_visibility="collapsed",
            )
            if checked and ex["id"] not in st.session_state.selected_exercises:
                st.session_state.selected_exercises.append(ex["id"])
            elif not checked and ex["id"] in st.session_state.selected_exercises:
                st.session_state.selected_exercises.remove(ex["id"])
        with col_i:
            st.markdown(
                f"**{ex['name']}**  {badge(ex)}  \n"
                f"<span class='muscle-tag'>{ex['muscles']}</span>  \n"
                f"기구: {ex['equipment']}",
                unsafe_allow_html=True,
            )
            with st.expander("어떻게 하면 효과적일까?"):
                st.markdown(f"**타겟 근육**  \n{ex['muscles']}")
                st.markdown(f"**올바른 방법**  \n{ex['how_to']}")
                st.markdown(f"**팁**  \n{ex['tip']}")

    st.markdown("---")
    if st.session_state.selected_exercises:
        st.markdown("### 오늘 선택한 운동")
        log_rows = []
        for eid in st.session_state.selected_exercises:
            ex = get_exercise_by_id(eid)
            if not ex:
                continue
            st.markdown(f"**{ex['name']}**")
            c1, c2, c3 = st.columns(3)
            w = c1.number_input("무게(kg)", 0.0, 500.0, 0.0, 2.5, key=f"w_{eid}")
            s = c2.number_input("세트", 0, 10, 3, key=f"s_{eid}")
            r = c3.number_input("횟수", 0, 50, 10, key=f"r_{eid}")
            log_rows.append({"name": ex["name"], "weight": w, "sets": s, "reps": r})

        notes = st.text_area("추가 메모")
        if st.button("운동 완료로 저장하기", type="primary", use_container_width=True):
            workouts = load_json(WORKOUT_FILE)
            workouts.append(
                {
                    "date": str(date.today()),
                    "exercises": [x["name"] for x in log_rows],
                    "details": log_rows,
                    "exercise_ids": list(st.session_state.selected_exercises),
                    "notes": notes,
                    "timestamp": datetime.now().isoformat(),
                }
            )
            save_json(WORKOUT_FILE, workouts)
            st.session_state.selected_exercises = []
            st.success("저장되었습니다!")
            st.rerun()
    else:
        st.info("위에서 오늘 할 운동을 선택하세요.")


elif menu == "📋 운동 기록":
    st.markdown('<p class="main-header">운동 기록</p>', unsafe_allow_html=True)
    workouts = load_json(WORKOUT_FILE)
    if not workouts:
        st.info("아직 기록이 없습니다. 오늘의 추천 루틴에서 시작해보세요.")
    else:
        for w in sorted(workouts, key=lambda x: x.get("timestamp", x["date"]), reverse=True):
            title = f"📅 {w['date']} · {len(w.get('exercises', []))}개"
            if w.get("plan"):
                title += f" · {w['plan']}"
            with st.expander(title):
                for name in w.get("exercises", []):
                    st.markdown(f"- {name}")
                if w.get("details"):
                    st.dataframe(pd.DataFrame(w["details"]), hide_index=True, use_container_width=True)
                if w.get("notes"):
                    st.markdown(f"**메모**  \n{w['notes']}")
                if st.button("이 기록 삭제", key=f"del_{w.get('timestamp', w['date'])}"):
                    left = [x for x in workouts if x.get("timestamp") != w.get("timestamp")]
                    save_json(WORKOUT_FILE, left)
                    st.rerun()


elif menu == "📊 신체 기록":
    st.markdown('<p class="main-header">신체 기록</p>', unsafe_allow_html=True)
    body_logs = load_json(BODY_FILE)
    with st.form("body_form"):
        c1, c2 = st.columns(2)
        weight = c1.number_input("몸무게 (kg)", 40.0, 150.0, float(p["weight"]), 0.1)
        body_fat = c2.number_input("체지방률 (%)", 5.0, 50.0, float(p["body_fat"]), 0.1)
        memo = st.text_input("메모", placeholder="측정 장소, 컨디션 등")
        if st.form_submit_button("기록 저장", type="primary"):
            body_logs.append({"date": str(date.today()), "weight": weight, "body_fat": body_fat, "memo": memo})
            save_json(BODY_FILE, body_logs)
            st.session_state.profile["weight"] = weight
            st.session_state.profile["body_fat"] = body_fat
            save_json(PROFILE_FILE, st.session_state.profile)
            st.success("저장했습니다.")
            st.rerun()

    if body_logs:
        df = pd.DataFrame(body_logs).sort_values("date")
        c1, c2 = st.columns(2)
        c1.line_chart(df.set_index("date")["weight"], height=240)
        c1.caption("몸무게")
        c2.line_chart(df.set_index("date")["body_fat"], height=240)
        c2.caption("체지방률")
        st.dataframe(df.sort_values("date", ascending=False), use_container_width=True, hide_index=True)


elif menu == "🍎 식단":
    st.markdown('<p class="main-header">식단 기록</p>', unsafe_allow_html=True)
    target = int(p.get("protein_target", 120))
    st.caption(f"목표 단백질 약 {target}g / 하루 (체중 67kg 기준 1.6~2.0g/kg)")
    diet_logs = load_json(DIET_FILE)

    with st.form("diet_form"):
        meal = st.selectbox("끼니", ["아침", "점심", "저녁", "간식"])
        content = st.text_area("내용", placeholder="예: 닭가슴살 200g, 밥, 채소")
        protein = st.number_input("대략 단백질 (g)", 0, 200, 0)
        if st.form_submit_button("저장", type="primary"):
            diet_logs.append(
                {
                    "date": str(date.today()),
                    "meal": meal,
                    "content": content,
                    "protein": protein,
                    "timestamp": datetime.now().isoformat(),
                }
            )
            save_json(DIET_FILE, diet_logs)
            st.success("저장했습니다.")
            st.rerun()

    today_diet = [d for d in diet_logs if d["date"] == str(date.today())]
    if today_diet:
        st.markdown("### 오늘")
        total = sum(int(d.get("protein", 0) or 0) for d in today_diet)
        st.metric("오늘 대략 단백질", f"{total} g / {target} g")
        st.progress(min(1.0, total / max(target, 1)))
        for d in today_diet:
            st.markdown(f"**{d['meal']}** · {d['content']} _(단백질 {d.get('protein', 0)}g)_")


elif menu == "🔥 운동 도감":
    st.markdown('<p class="main-header">운동 도감</p>', unsafe_allow_html=True)
    st.markdown('<p class="sub-header">기구를 보고 운동을 찾으면 됩니다.</p>', unsafe_allow_html=True)
    search = st.text_input("검색", placeholder="예: 스미스, 덤벨, 랫풀다운")
    all_ex = get_all_exercises()
    if search:
        sl = search.lower()
        all_ex = [e for e in all_ex if sl in e["name"].lower() or sl in e["equipment"].lower() or sl in e["muscles"].lower()]

    for cat in EXERCISES.keys():
        cat_ex = [e for e in all_ex if e["category"] == cat]
        if not cat_ex:
            continue
        st.markdown(f"### {cat}")
        for ex in cat_ex:
            with st.expander(f"{ex['name']} · {ex['equipment']}"):
                st.markdown(f"**타겟 근육**  \n{ex['muscles']}")
                st.markdown(f"**사용 기구**  \n{ex['equipment']}")
                st.markdown(f"**올바른 방법**  \n{ex['how_to']}")
                st.markdown(f"**팁**  \n{ex['tip']}")
                st.markdown(badge(ex), unsafe_allow_html=True)


elif menu == "⚙️ 설정":
    st.markdown('<p class="main-header">설정</p>', unsafe_allow_html=True)
    with st.form("profile_form"):
        name = st.text_input("이름", value=str(p.get("name", "나")))
        age = st.number_input("나이", 15, 80, int(p.get("age", 35)))
        height = st.number_input("키 (cm)", 140, 220, int(p.get("height", 167)))
        goal_fat = st.number_input("목표 체지방률 (%)", 8.0, 30.0, float(p.get("goal_fat", 15.0)), 0.5)
        protein_target = st.number_input("하루 단백질 목표 (g)", 50, 250, int(p.get("protein_target", 120)))
        if st.form_submit_button("저장", type="primary"):
            st.session_state.profile.update(
                {"name": name, "age": age, "height": height, "goal_fat": goal_fat, "protein_target": protein_target}
            )
            save_json(PROFILE_FILE, st.session_state.profile)
            st.success("저장했습니다.")

    st.markdown("### 데이터 내보내기")
    st.caption("클라우드에 올리면 재시작 때 기록이 지워질 수 있습니다. 가끔 내보내기 하세요.")
    blob = json.dumps(
        {
            "profile": load_json(PROFILE_FILE, st.session_state.profile),
            "workouts": load_json(WORKOUT_FILE),
            "body": load_json(BODY_FILE),
            "diet": load_json(DIET_FILE),
        },
        ensure_ascii=False,
        indent=2,
    )
    st.download_button("전체 기록 JSON 다운로드", blob, file_name="my_fit_backup.json", mime="application/json")

    uploaded = st.file_uploader("백업 JSON 가져오기", type=["json"])
    if uploaded and st.button("가져오기 적용"):
        try:
            data = json.load(uploaded)
            if "profile" in data:
                save_json(PROFILE_FILE, data["profile"])
                st.session_state.profile = data["profile"]
            if "workouts" in data:
                save_json(WORKOUT_FILE, data["workouts"])
            if "body" in data:
                save_json(BODY_FILE, data["body"])
            if "diet" in data:
                save_json(DIET_FILE, data["diet"])
            st.success("가져왔습니다.")
            st.rerun()
        except Exception:
            st.error("파일 형식을 확인하세요.")
