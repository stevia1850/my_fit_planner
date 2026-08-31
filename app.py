import json
import os
from datetime import date, datetime

import pandas as pd
import streamlit as st

from exercises import EXERCISES, RECOMMENDED, get_exercise_by_id
from food import estimate_meal

st.set_page_config(
    page_title="My Fit",
    page_icon="💪",
    layout="centered",
    initial_sidebar_state="collapsed",
)

st.markdown(
    """
<style>
    [data-testid="stSidebar"],
    [data-testid="stSidebarNav"],
    [data-testid="stSidebarContent"],
    section[data-testid="stSidebar"],
    [data-testid="stSidebarCollapsedControl"],
    [data-testid="collapsedControl"],
    button[kind="header"],
    button[data-testid="baseButton-header"],
    div[data-testid="stDecoration"] {
        display: none !important;
        width: 0 !important;
        min-width: 0 !important;
        visibility: hidden !important;
    }
    header[data-testid="stHeader"] {
        background: transparent;
    }
    .block-container { padding-top: 0.6rem; padding-bottom: 3.2rem; max-width: 740px; }
    h1 { font-size: 1.35rem !important; margin-bottom: 0.2rem !important; }
    h2, h3 { font-size: 1.02rem !important; }
    div[data-testid="stMetricValue"] { font-size: 1.2rem; }
    .hint { color: #667085; font-size: 0.86rem; margin: 0.15rem 0 0.7rem; }
    .prev { color: #344054; font-size: 0.82rem; margin: 0 0 0.35rem; }
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
    "protein_target": 120,
    "kcal_target": 2000,
}
WEEKDAY = ["월", "화", "수", "목", "금", "토", "일"]
PARTS = ["하체", "가슴", "어깨", "등", "팔", "코어", "유산소"]
ID_PARTS = {
    "arm_circle": ["어깨"],
    "scapular_pushup": ["어깨"],
    "band_er": ["어깨"],
    "face_pull_wu": ["어깨"],
    "face_pull": ["어깨", "등"],
    "leg_press": ["하체"],
    "squat_machine": ["하체"],
    "rdl": ["하체"],
    "leg_extension": ["하체"],
    "leg_curl": ["하체"],
    "dumbbell_lunge": ["하체"],
    "calf_raise": ["하체"],
    "bench_press": ["가슴", "어깨", "팔"],
    "incline_dumbbell_press": ["가슴", "어깨"],
    "pec_deck": ["가슴"],
    "shoulder_press_machine": ["어깨"],
    "ohp_machine": ["어깨"],
    "lateral_raise": ["어깨"],
    "dips": ["가슴", "팔"],
    "pushup": ["가슴", "팔", "코어"],
    "lat_pulldown": ["등", "팔"],
    "pullup": ["등", "팔"],
    "seated_row": ["등"],
    "dumbbell_row": ["등"],
    "bicep_curl": ["팔"],
    "treadmill": ["유산소"],
    "treadmill_walk": ["유산소"],
    "stair_climber": ["유산소", "하체"],
    "rowing": ["유산소", "등"],
    "plank": ["코어"],
    "dead_bug": ["코어"],
}
MEALS = {
    "닭가슴 + 밥 + 채소": "닭가슴살, 현미밥, 샐러드",
    "계란 + 밥": "계란 2개, 밥, 김치",
    "그릭요거트 + 과일": "그릭요거트, 바나나",
    "프로틴": "프로틴 쉐이크",
    "외식 한 끼": "덮밥",
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
if "diet_text" not in st.session_state:
    st.session_state.diet_text = ""

p = st.session_state.profile


def last_detail(name):
    items = load_json(WORKOUT_FILE)
    items = sorted(items, key=lambda x: x.get("timestamp", x.get("date", "")), reverse=True)
    for w in items:
        for row in w.get("details") or []:
            if row.get("name") == name and (row.get("sets") or row.get("weight")):
                return row
    return None


def parts_of(ex_id=None, name=""):
    found = list(ID_PARTS.get(ex_id or "", []))
    return found or ["기타"]


def week_workouts():
    today = date.today()
    out = []
    for w in load_json(WORKOUT_FILE):
        try:
            d = datetime.strptime(w["date"], "%Y-%m-%d").date()
            if d.isocalendar()[:2] == today.isocalendar()[:2]:
                out.append(w)
        except Exception:
            pass
    return out


def analyze_week():
    counts = {k: 0 for k in PARTS}
    for w in week_workouts():
        ids = w.get("exercise_ids", [])
        details = w.get("details") or [{"name": n} for n in w.get("exercises", [])]
        for i, row in enumerate(details):
            eid = ids[i] if i < len(ids) else None
            for pt in parts_of(eid, row.get("name", "")):
                if pt in counts:
                    counts[pt] += 1
    missing = [pt for pt in PARTS if counts[pt] == 0]
    rec_map = {
        "하체": "레그프레스, 루마니안 데드리프트, 레그컬",
        "가슴": "인클라인 덤벨 프레스, 버터플라이",
        "어깨": "사이드 레터럴, 페이스 풀 (가볍게)",
        "등": "랫풀다운, 시티드 로우",
        "팔": "이두 컬, 푸쉬업",
        "코어": "플랭크",
        "유산소": "트레드밀 경사 걷기 15~20분",
    }
    suggest = [f"{pt}: {rec_map[pt]}" for pt in missing if pt in rec_map]
    n = len(week_workouts())
    if n == 0:
        summary = "이번 주 기록이 없습니다. 오늘 루틴부터 저장하세요."
    elif n < 3:
        summary = f"이번 주 {n}회. 주 3회가 최소입니다."
    else:
        summary = f"이번 주 {n}회. 횟수는 충분합니다."
    return {"counts": counts, "missing": missing, "suggest": suggest, "summary": summary, "n": n}


def render_ex(ex, prefix, hide_if_pain=False):
    prev = last_detail(ex["name"])
    label = ex["name"]
    if not ex.get("shoulder_safe", True):
        label += "  · 어깨주의"
    done = st.checkbox(label, key=f"{prefix}_on_{ex['id']}")
    st.caption(f"{ex['equipment']} · {ex['muscles']}")
    if prev:
        st.markdown(
            f'<div class="prev">지난번 {prev.get("weight", 0)}kg · {prev.get("sets", 0)}세트 × {prev.get("reps", 0)}회. 같거나 조금만 올리세요.</div>',
            unsafe_allow_html=True,
        )
    with st.expander("방법"):
        st.write(ex["how_to"])
        st.caption(ex["tip"])
    dw = float(prev.get("weight", 0) or 0) if prev else 0.0
    ds = int(prev.get("sets", 3) or 3) if prev else 0
    dr = int(prev.get("reps", 10) or 10) if prev else 0
    c1, c2, c3 = st.columns(3)
    w = c1.number_input("무게 kg", 0.0, 400.0, dw, 2.5, key=f"{prefix}_w_{ex['id']}")
    s = c2.number_input("세트", 0, 10, ds, key=f"{prefix}_s_{ex['id']}")
    r = c3.number_input("횟수", 0, 50, dr, key=f"{prefix}_r_{ex['id']}")
    return {
        "id": ex["id"],
        "name": ex["name"],
        "done": bool(done or s > 0),
        "weight": w,
        "sets": int(s),
        "reps": int(r),
        "warmup": ex.get("category") == "워밍업 (어깨 필수)" or ex["id"].endswith("_wu") or ex["id"] in {
            "arm_circle",
            "scapular_pushup",
            "band_er",
            "face_pull_wu",
        },
        "caution": not ex.get("shoulder_safe", True),
    }


def save_workout(rows, notes, plan="", require_warmup=False, pain=False):
    logged = [r for r in rows if r["done"] or r["sets"] > 0]
    if not logged:
        st.warning("운동을 체크하거나 세트를 입력하세요.")
        return
    if require_warmup and not any(r["warmup"] and (r["done"] or r["sets"] > 0) for r in logged):
        st.error("밀기 운동 전 워밍업을 하나 이상 체크하세요.")
        return
    if pain:
        logged = [r for r in logged if not r.get("caution")]
        notes = (("어깨 통증 있음. 주의 동작 제외. ") + (notes or "")).strip()
    data = load_json(WORKOUT_FILE)
    data.append(
        {
            "date": str(date.today()),
            "plan": plan,
            "exercises": [r["name"] for r in logged],
            "exercise_ids": [r["id"] for r in logged],
            "details": [
                {"name": r["name"], "weight": r["weight"], "sets": r["sets"], "reps": r["reps"]}
                for r in logged
            ],
            "notes": notes,
            "timestamp": datetime.now().isoformat(),
        }
    )
    save_json(WORKOUT_FILE, data)
    st.success("저장했습니다.")
    st.rerun()


today = date.today()
rec = RECOMMENDED[today.weekday()]
fb = analyze_week()
push_day = "밀기" in rec["title"]

page = st.radio(
    "메뉴",
    ["오늘", "운동선택", "피드백", "기록", "몸", "식단", "도감", "설정"],
    horizontal=True,
    label_visibility="collapsed",
)

if page == "오늘":
    st.title("오늘")
    st.markdown(
        f'<div class="hint">{today.strftime("%m.%d")} ({WEEKDAY[today.weekday()]}) · {rec["title"]} · 이번 주 {fb["n"]}회</div>',
        unsafe_allow_html=True,
    )
    a, b, c = st.columns(3)
    a.metric("체중", f"{p['weight']}kg")
    b.metric("체지방", f"{p['body_fat']}%")
    c.metric("목표", f"{p['goal_fat']}%")
    st.info(fb["summary"])
    pain = st.checkbox("오늘 어깨가 불편하다")
    if pain:
        st.warning("벤치, 숄더프레스, 딥스는 건너뛰세요.")

    rows = []
    sections = [("워밍업", rec["warmup"]), ("본운동", rec["main"]), ("유산소 · 하나만", rec["cardio"])]
    for title, ids in sections:
        if not ids:
            continue
        st.subheader(title)
        for eid in ids:
            ex = get_exercise_by_id(eid)
            if not ex:
                continue
            if pain and not ex.get("shoulder_safe", True):
                st.caption(f"{ex['name']} — 통증 있어 숨김")
                continue
            rows.append(render_ex(ex, title[:2]))
            st.divider()
    notes = st.text_input("메모")
    if st.button("저장", type="primary", use_container_width=True):
        save_workout(rows, notes, rec["title"], require_warmup=push_day, pain=pain)


elif page == "운동선택":
    st.title("운동 선택")
    st.caption("부위 칸만 열면 됩니다. 화면을 가리는 왼쪽 메뉴는 제거했습니다.")
    q = st.text_input("검색", placeholder="하체, 어깨, 랫풀다운")
    rows = []
    for cat, items in EXERCISES.items():
        shown = items
        if q:
            ql = q.lower()
            shown = [
                e
                for e in items
                if ql in e["name"].lower()
                or ql in e["equipment"].lower()
                or ql in e["muscles"].lower()
                or ql in cat.lower()
            ]
        if not shown:
            continue
        with st.expander(f"{cat} ({len(shown)})", expanded=bool(q)):
            for ex in shown:
                rows.append(render_ex(ex, "p" + cat[:2]))
                st.divider()
    notes = st.text_input("메모")
    if st.button("저장", type="primary", use_container_width=True):
        save_workout(rows, notes, "직접 선택")


elif page == "피드백":
    st.title("이번 주")
    st.write(fb["summary"])
    st.bar_chart(pd.DataFrame({"횟수": fb["counts"]}))
    if fb["missing"]:
        st.warning("빠진 부위: " + ", ".join(fb["missing"]))
        st.subheader("다음 운동")
        for s in fb["suggest"]:
            st.write("· " + s)
    else:
        st.success("주요 부위는 한 번씩 했습니다. 지난번 무게를 유지하거나 2.5kg만 올리세요.")


elif page == "기록":
    st.title("기록")
    workouts = load_json(WORKOUT_FILE)
    if not workouts:
        st.info("아직 없습니다.")
    else:
        for w in sorted(workouts, key=lambda x: x.get("timestamp", x["date"]), reverse=True):
            title = w["date"] + (f" · {w['plan']}" if w.get("plan") else "")
            with st.expander(title):
                if w.get("details"):
                    st.dataframe(pd.DataFrame(w["details"]), hide_index=True, use_container_width=True)
                if w.get("notes"):
                    st.caption(w["notes"])
                if st.button("삭제", key="del_" + w.get("timestamp", w["date"])):
                    save_json(
                        WORKOUT_FILE,
                        [x for x in workouts if x.get("timestamp") != w.get("timestamp")],
                    )
                    st.rerun()


elif page == "몸":
    st.title("몸")
    body_logs = load_json(BODY_FILE)
    with st.form("body"):
        c1, c2 = st.columns(2)
        weight = c1.number_input("몸무게 kg", 40.0, 150.0, float(p["weight"]), 0.1)
        fat = c2.number_input("체지방 %", 5.0, 50.0, float(p["body_fat"]), 0.1)
        if st.form_submit_button("저장", use_container_width=True):
            body_logs.append({"date": str(today), "weight": weight, "body_fat": fat})
            save_json(BODY_FILE, body_logs)
            st.session_state.profile.update({"weight": weight, "body_fat": fat})
            save_json(PROFILE_FILE, st.session_state.profile)
            st.rerun()
    if body_logs:
        df = pd.DataFrame(body_logs).sort_values("date")
        st.line_chart(df.set_index("date")[["weight", "body_fat"]])


elif page == "식단":
    st.title("식단")
    st.caption("자주 먹는 구성을 누르면 자동으로 채워집니다.")
    cols = st.columns(len(MEALS))
    for col, (label, text) in zip(cols, MEALS.items()):
        if col.button(label, use_container_width=True):
            st.session_state.diet_text = text
            st.rerun()
    meal = st.selectbox("끼니", ["아침", "점심", "저녁", "간식"])
    content = st.text_area("먹은 것", value=st.session_state.diet_text)
    guess = estimate_meal(content) if content.strip() else {"kcal": 0, "protein": 0, "note": "적으면 대략 계산합니다."}
    st.caption("추정 · " + guess["note"])
    c1, c2 = st.columns(2)
    protein = c1.number_input("단백질 g", 0, 250, int(guess["protein"]))
    kcal = c2.number_input("칼로리 kcal", 0, 3000, int(guess["kcal"]))
    if st.button("식단 저장", type="primary", use_container_width=True):
        diet = load_json(DIET_FILE)
        diet.append(
            {
                "date": str(today),
                "meal": meal,
                "content": content,
                "protein": protein,
                "kcal": kcal,
                "timestamp": datetime.now().isoformat(),
            }
        )
        save_json(DIET_FILE, diet)
        st.session_state.diet_text = ""
        st.success("저장했습니다.")
        st.rerun()
    diet = load_json(DIET_FILE)
    today_diet = [d for d in diet if d["date"] == str(today)]
    tp = sum(int(d.get("protein", 0) or 0) for d in today_diet)
    tk = sum(int(d.get("kcal", 0) or 0) for d in today_diet)
    m1, m2 = st.columns(2)
    m1.metric("오늘 단백질", f"{tp}g / {int(p.get('protein_target', 120))}g")
    m2.metric("오늘 칼로리", f"{tk}kcal / {int(p.get('kcal_target', 2000))}kcal")
    for d in today_diet:
        st.write(f"**{d['meal']}** · {d['content']} ({d.get('protein', 0)}g, {d.get('kcal', 0)}kcal)")


elif page == "도감":
    st.title("도감")
    q = st.text_input("검색", placeholder="어깨, 스미스")
    for cat, items in EXERCISES.items():
        shown = items
        if q:
            ql = q.lower()
            shown = [
                e
                for e in items
                if ql in e["name"].lower() or ql in e["equipment"].lower() or ql in cat.lower()
            ]
        if not shown:
            continue
        with st.expander(f"{cat} ({len(shown)})"):
            for ex in shown:
                st.markdown(f"**{ex['name']}**")
                st.caption(f"{ex['equipment']} · {ex['muscles']}")
                st.write(ex["how_to"])
                st.divider()


elif page == "설정":
    st.title("설정")
    st.caption("클라우드에선 기록이 사라질 수 있어 가끔 백업하세요.")
    with st.form("prof"):
        name = st.text_input("이름", p.get("name", "나"))
        goal = st.number_input("목표 체지방 %", 8.0, 30.0, float(p.get("goal_fat", 15.0)), 0.5)
        protein = st.number_input("단백질 목표 g", 50, 250, int(p.get("protein_target", 120)))
        kcal_t = st.number_input("칼로리 목표", 1200, 4000, int(p.get("kcal_target", 2000)))
        if st.form_submit_button("저장", use_container_width=True):
            st.session_state.profile.update(
                {"name": name, "goal_fat": goal, "protein_target": protein, "kcal_target": kcal_t}
            )
            save_json(PROFILE_FILE, st.session_state.profile)
            st.success("저장했습니다.")
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
    st.download_button("기록 백업 받기", blob, file_name="my_fit_backup.json")
