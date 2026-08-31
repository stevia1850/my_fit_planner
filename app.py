import json
import os
from calendar import monthcalendar
from datetime import date, datetime, timedelta

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
    [data-testid="stSidebarCollapsedControl"],
    [data-testid="collapsedControl"] {
        display: none !important;
    }
    header[data-testid="stHeader"] {
        pointer-events: none !important;
        background: transparent !important;
    }
    header[data-testid="stHeader"] * {
        pointer-events: none !important;
    }
    .block-container { padding-top: 2.4rem; padding-bottom: 3rem; max-width: 860px; }
    h1 { font-size: 1.3rem !important; }
    .hint { color: #667085; font-size: 0.86rem; margin-bottom: 0.8rem; }
    .brick {
        background: #f8fafc;
        border: 1px solid #e4e7ec;
        border-radius: 14px;
        padding: 0.85rem 0.9rem 0.35rem;
        margin-bottom: 0.8rem;
    }
    .brick-sub { color: #667085; font-size: 0.8rem; margin: 0.15rem 0 0.4rem; }
    .prev { color: #344054; font-size: 0.8rem; margin-bottom: 0.35rem; }
    .cal { width: 100%; border-collapse: collapse; table-layout: fixed; }
    .cal th { font-size: 0.75rem; color: #667085; padding: 0.25rem; }
    .cal td {
        vertical-align: top; height: 72px; border: 1px solid #eef0f3;
        border-radius: 8px; padding: 0.28rem; font-size: 0.72rem;
    }
    .cal .num { font-weight: 700; font-size: 0.8rem; }
    .cal .today { background: #eff8ff; border-color: #84caff; }
    .cal .done { background: #ecfdf3; }
    .cal .plan { color: #344054; }
    .weekbox { display: flex; gap: 0.4rem; overflow-x: auto; padding-bottom: 0.4rem; }
    .wday {
        min-width: 92px; flex: 1; background: #f8fafc; border: 1px solid #e4e7ec;
        border-radius: 12px; padding: 0.55rem 0.5rem;
    }
    .wday.on { background: #eff8ff; border-color: #84caff; }
    .wday.ok { background: #ecfdf3; }
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
    "mid_fat": 18.0,
    "cut_weeks": 8,
    "protein_target": 125,
    "kcal_target": 1800,
}
WEEKDAY = ["월", "화", "수", "목", "금", "토", "일"]
PARTS = ["하체", "가슴", "어깨", "등", "팔", "코어", "유산소"]
PAGES = ["오늘", "달력", "운동선택", "피드백", "기록", "몸", "식단", "도감", "설정"]
ID_PARTS = {
    "arm_circle": ["어깨"], "scapular_pushup": ["어깨"], "band_er": ["어깨"],
    "face_pull_wu": ["어깨"], "face_pull": ["어깨", "등"],
    "leg_press": ["하체"], "squat_machine": ["하체"], "rdl": ["하체"],
    "leg_extension": ["하체"], "leg_curl": ["하체"], "dumbbell_lunge": ["하체"],
    "calf_raise": ["하체"], "bench_press": ["가슴", "어깨", "팔"],
    "incline_dumbbell_press": ["가슴", "어깨"], "pec_deck": ["가슴"],
    "shoulder_press_machine": ["어깨"], "ohp_machine": ["어깨"],
    "lateral_raise": ["어깨"], "dips": ["가슴", "팔"], "pushup": ["가슴", "팔", "코어"],
    "lat_pulldown": ["등", "팔"], "pullup": ["등", "팔"], "seated_row": ["등"],
    "dumbbell_row": ["등"], "bicep_curl": ["팔"], "treadmill": ["유산소"],
    "treadmill_walk": ["유산소"], "stair_climber": ["유산소", "하체"],
    "rowing": ["유산소", "등"], "plank": ["코어"], "dead_bug": ["코어"],
}
MEALS = {
    "닭가슴+밥": "닭가슴살, 현미밥, 샐러드",
    "계란+밥": "계란 2개, 밥, 김치",
    "요거트": "그릭요거트, 바나나",
    "프로틴": "프로틴 쉐이크",
    "외식": "덮밥",
}
WARMUP_IDS = {"arm_circle", "scapular_pushup", "band_er", "face_pull_wu"}


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
    items = sorted(load_json(WORKOUT_FILE), key=lambda x: x.get("timestamp", x.get("date", "")), reverse=True)
    for w in items:
        for row in w.get("details") or []:
            if row.get("name") == name:
                return row
    return None


def format_prev(row):
    if not row:
        return ""
    if row.get("set_logs"):
        bits = [f"{s.get('weight', 0)}kg×{s.get('reps', 0)}" for s in row["set_logs"]]
        return "지난번 " + " / ".join(bits)
    return f"지난번 {row.get('weight', 0)}kg · {row.get('sets', 0)}세트 × {row.get('reps', 0)}회"


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
            for pt in ID_PARTS.get(eid or "", []):
                if pt in counts:
                    counts[pt] += 1
    missing = [pt for pt in PARTS if counts[pt] == 0]
    rec_map = {
        "하체": "레그프레스, RDL, 레그컬",
        "가슴": "인클라인 덤벨 프레스, 버터플라이",
        "어깨": "사이드 레터럴, 페이스 풀",
        "등": "랫풀다운, 시티드 로우",
        "팔": "이두 컬, 푸쉬업",
        "코어": "플랭크",
        "유산소": "트레드밀 경사 걷기 15~20분",
    }
    suggest = [f"{pt}: {rec_map[pt]}" for pt in missing]
    n = len(week_workouts())
    if n == 0:
        summary = "이번 주 기록이 없습니다."
    elif n < 3:
        summary = f"이번 주 {n}회. 주 3회가 최소입니다."
    else:
        summary = f"이번 주 {n}회. 횟수는 충분합니다."
    return {"counts": counts, "missing": missing, "suggest": suggest, "summary": summary, "n": n}


def render_ex(ex, prefix):
    prev = last_detail(ex["name"])
    prev_sets = (prev or {}).get("set_logs") or []
    default_n = min(6, max(1, len(prev_sets) or 3))
    st.markdown('<div class="brick">', unsafe_allow_html=True)
    done = st.checkbox(
        ex["name"] + ("  ·어깨주의" if not ex.get("shoulder_safe", True) else ""),
        key=f"{prefix}_on_{ex['id']}",
    )
    st.markdown(f'<div class="brick-sub">{ex["equipment"]} · {ex["muscles"]}</div>', unsafe_allow_html=True)
    prev_txt = format_prev(prev)
    if prev_txt:
        st.markdown(f'<div class="prev">{prev_txt}</div>', unsafe_allow_html=True)
    with st.expander("방법"):
        st.write(ex["how_to"])
        st.caption(ex["tip"])
    n_sets = st.number_input("세트 수", 1, 6, default_n, key=f"{prefix}_n_{ex['id']}")
    set_logs = []
    for i in range(int(n_sets)):
        pw = float(prev_sets[i]["weight"]) if i < len(prev_sets) else float((prev or {}).get("weight") or 0)
        pr = int(prev_sets[i]["reps"]) if i < len(prev_sets) else int((prev or {}).get("reps") or 10)
        c1, c2, c3 = st.columns([0.8, 1.2, 1.2])
        c1.markdown(f"**{i+1}세트**")
        w = c2.number_input("무게 kg", 0.0, 400.0, pw, 2.5, key=f"{prefix}_{ex['id']}_w{i}")
        r = c3.number_input("횟수", 0, 50, pr, key=f"{prefix}_{ex['id']}_r{i}")
        set_logs.append({"weight": float(w), "reps": int(r)})
    st.markdown("</div>", unsafe_allow_html=True)
    used = done or any(s["reps"] > 0 or s["weight"] > 0 for s in set_logs)
    return {
        "id": ex["id"],
        "name": ex["name"],
        "done": used,
        "set_logs": set_logs,
        "sets": len(set_logs),
        "weight": set_logs[0]["weight"] if set_logs else 0,
        "reps": set_logs[-1]["reps"] if set_logs else 0,
        "warmup": ex["id"] in WARMUP_IDS,
        "caution": not ex.get("shoulder_safe", True),
    }


def save_workout(rows, notes, plan="", require_warmup=False, pain=False):
    logged = [r for r in rows if r["done"]]
    if not logged:
        st.warning("체크하거나 세트 무게/횟수를 입력하세요.")
        return
    if require_warmup and not any(r["warmup"] for r in logged):
        st.error("밀기 날에는 워밍업을 하나 이상 기록하세요.")
        return
    if pain:
        logged = [r for r in logged if not r.get("caution")]
        notes = ("어깨 통증. 주의 동작 제외. " + (notes or "")).strip()
    data = load_json(WORKOUT_FILE)
    data.append({
        "date": str(date.today()),
        "plan": plan,
        "exercises": [r["name"] for r in logged],
        "exercise_ids": [r["id"] for r in logged],
        "details": [{
            "name": r["name"],
            "set_logs": r["set_logs"],
            "sets": r["sets"],
            "weight": r["weight"],
            "reps": r["reps"],
        } for r in logged],
        "notes": notes,
        "timestamp": datetime.now().isoformat(),
    })
    save_json(WORKOUT_FILE, data)
    st.success("저장했습니다.")
    st.rerun()


def short_plan(title):
    if "하체" in title:
        return "하체"
    if "밀기" in title:
        return "밀기"
    if "당기기" in title:
        return "당기기"
    if "전신" in title:
        return "전신"
    if "휴식" in title:
        return "휴식"
    return title[:4]


def records_by_date():
    wmap, dmap, bmap = {}, {}, {}
    for w in load_json(WORKOUT_FILE):
        wmap.setdefault(w.get("date"), []).append(w)
    for d in load_json(DIET_FILE):
        dmap.setdefault(d.get("date"), []).append(d)
    for b in load_json(BODY_FILE):
        bmap[b.get("date")] = b
    return wmap, dmap, bmap


def week_dates(anchor):
    start = anchor - timedelta(days=anchor.weekday())
    return [start + timedelta(days=i) for i in range(7)]


def render_week_strip(anchor):
    wmap, _, _ = records_by_date()
    days = week_dates(anchor)
    parts = []
    for d in days:
        rec_d = RECOMMENDED[d.weekday()]
        cls = "wday"
        if d == date.today():
            cls += " on"
        if d.isoformat() in wmap:
            cls += " ok"
        mark = "기록됨" if d.isoformat() in wmap else short_plan(rec_d["title"])
        parts.append(
            f'<div class="{cls}"><div>{WEEKDAY[d.weekday()]} {d.day}</div>'
            f"<div>{mark}</div></div>"
        )
    st.markdown('<div class="weekbox">' + "".join(parts) + "</div>", unsafe_allow_html=True)


def render_month(year, month):
    wmap, dmap, bmap = records_by_date()
    names = "".join(f"<th>{n}</th>" for n in WEEKDAY)
    rows = []
    for week in monthcalendar(year, month):
        tds = []
        for i, day in enumerate(week):
            if day == 0:
                tds.append("<td></td>")
                continue
            d = date(year, month, day)
            key = d.isoformat()
            cls = []
            if d == date.today():
                cls.append("today")
            if key in wmap:
                cls.append("done")
            plan = short_plan(RECOMMENDED[i]["title"])
            bits = [f'<div class="num">{day}</div>', f'<div class="plan">{plan}</div>']
            if key in wmap:
                bits.append("<div>운동 ✓</div>")
            if key in dmap:
                bits.append("<div>식단 ✓</div>")
            if key in bmap:
                bits.append(f"<div>{bmap[key].get('weight', '')}kg</div>")
            tds.append(f'<td class="{" ".join(cls)}">{"".join(bits)}</td>')
        rows.append("<tr>" + "".join(tds) + "</tr>")
    st.markdown(f'<table class="cal"><tr>{names}</tr>{"".join(rows)}</table>', unsafe_allow_html=True)


today = date.today()
rec = RECOMMENDED[today.weekday()]
fb = analyze_week()
push_day = "밀기" in rec["title"]
CUT_END = today + timedelta(weeks=8)
CUT_TARGET = 18.0

page = st.selectbox("화면", PAGES)
st.caption("위 목록을 눌러 화면을 바꾸세요.")

if page == "오늘":
    st.title("오늘")
    st.markdown(
        f'<div class="hint">{today.strftime("%m.%d")} ({WEEKDAY[today.weekday()]}) · {rec["title"]} · 이번 주 {fb["n"]}회</div>',
        unsafe_allow_html=True,
    )
    a, b, c, d = st.columns(4)
    a.metric("체중", f"{p['weight']}kg")
    b.metric("체지방", f"{p['body_fat']}%")
    c.metric("8주 목표", f"{CUT_TARGET}%")
    d.metric("최종", f"{p['goal_fat']}%")
    left = float(p["body_fat"]) - CUT_TARGET
    st.caption(f"2개월({CUT_END.strftime('%m.%d')}까지) 체지방 {left:.1f}%p 감량 · 주 0.4~0.5kg · 하루 약 1800kcal / 단백질 125g")
    st.subheader("이번 주 플랜")
    render_week_strip(today)
    st.info(fb["summary"])
    pain = st.checkbox("오늘 어깨가 불편하다")
    rows = []
    for title, ids in [("워밍업", rec["warmup"]), ("본운동", rec["main"]), ("유산소", rec["cardio"])]:
        if not ids:
            continue
        st.subheader(title)
        for eid in ids:
            ex = get_exercise_by_id(eid)
            if not ex:
                continue
            if pain and not ex.get("shoulder_safe", True):
                continue
            rows.append(render_ex(ex, title[:2]))
    notes = st.text_input("메모")
    if st.button("오늘 운동 저장", type="primary", use_container_width=True):
        save_workout(rows, notes, rec["title"], require_warmup=push_day, pain=pain)

elif page == "달력":
    st.title("달력")
    st.caption("초록 = 운동 기록 있음 / 파란 칸 = 오늘 / 각 칸은 그날 플랜")
    st.subheader("이번 주")
    render_week_strip(today)
    for d in week_dates(today):
        plan = RECOMMENDED[d.weekday()]
        names = []
        for eid in plan["warmup"] + plan["main"] + plan["cardio"][:1]:
            ex = get_exercise_by_id(eid)
            if ex:
                names.append(ex["name"])
        mark = " ✓" if d.isoformat() in records_by_date()[0] else ""
        with st.expander(f"{WEEKDAY[d.weekday()]} {d.strftime('%m.%d')} · {plan['title']}{mark}", expanded=(d == today)):
            if not names:
                st.write("휴식")
            else:
                for n in names:
                    st.write("· " + n)
    st.subheader(f"{today.year}.{today.month:02d} 월간")
    render_month(today.year, today.month)
    prev_m = (today.replace(day=1) - timedelta(days=1))
    st.subheader(f"{prev_m.year}.{prev_m.month:02d} 지난달")
    render_month(prev_m.year, prev_m.month)

elif page == "운동선택":
    st.title("운동 선택")
    q = st.text_input("검색", placeholder="하체, 어깨, 랫풀다운")
    rows = []
    for cat, items in EXERCISES.items():
        shown = items
        if q:
            ql = q.lower()
            shown = [e for e in items if ql in e["name"].lower() or ql in e["equipment"].lower() or ql in cat.lower()]
        if not shown:
            continue
        with st.expander(f"{cat} ({len(shown)})", expanded=bool(q)):
            for ex in shown:
                rows.append(render_ex(ex, "x" + cat[:2]))
    notes = st.text_input("메모")
    if st.button("선택 운동 저장", type="primary", use_container_width=True):
        save_workout(rows, notes, "직접 선택")

elif page == "피드백":
    st.title("이번 주 피드백")
    st.write(fb["summary"])
    st.bar_chart(pd.DataFrame({"횟수": fb["counts"]}))
    if fb["missing"]:
        st.warning("빠진 부위: " + ", ".join(fb["missing"]))
        for s in fb["suggest"]:
            st.write("· " + s)
    else:
        st.success("주요 부위는 한 번씩 했습니다.")

elif page == "기록":
    st.title("기록")
    workouts = load_json(WORKOUT_FILE)
    if not workouts:
        st.info("아직 없습니다.")
    else:
        for w in sorted(workouts, key=lambda x: x.get("timestamp", x["date"]), reverse=True):
            title = w["date"] + (f" · {w['plan']}" if w.get("plan") else "")
            with st.expander(title):
                rows = []
                for d in w.get("details") or []:
                    if d.get("set_logs"):
                        txt = " / ".join(f"{s.get('weight',0)}kg×{s.get('reps',0)}" for s in d["set_logs"])
                    else:
                        txt = f"{d.get('weight',0)}kg {d.get('sets',0)}x{d.get('reps',0)}"
                    rows.append({"운동": d.get("name"), "세트": txt})
                if rows:
                    st.dataframe(pd.DataFrame(rows), hide_index=True, use_container_width=True)
                if w.get("notes"):
                    st.caption(w["notes"])
                if st.button("삭제", key="del_" + w.get("timestamp", w["date"])):
                    save_json(WORKOUT_FILE, [x for x in workouts if x.get("timestamp") != w.get("timestamp")])
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
    cols = st.columns(len(MEALS))
    for col, (label, text) in zip(cols, MEALS.items()):
        if col.button(label, use_container_width=True):
            st.session_state.diet_text = text
            st.rerun()
    meal = st.selectbox("끼니", ["아침", "점심", "저녁", "간식"])
    content = st.text_area("먹은 것", value=st.session_state.diet_text)
    guess = estimate_meal(content) if str(content).strip() else {"kcal": 0, "protein": 0, "note": "적으면 대략 계산합니다."}
    st.caption("추정 · " + guess["note"])
    c1, c2 = st.columns(2)
    protein = c1.number_input("단백질 g", 0, 250, int(guess["protein"]))
    kcal = c2.number_input("칼로리 kcal", 0, 3000, int(guess["kcal"]))
    if st.button("식단 저장", type="primary", use_container_width=True):
        diet = load_json(DIET_FILE)
        diet.append({"date": str(today), "meal": meal, "content": content, "protein": protein, "kcal": kcal, "timestamp": datetime.now().isoformat()})
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
            shown = [e for e in items if ql in e["name"].lower() or ql in e["equipment"].lower() or ql in cat.lower()]
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
    st.caption("클라우드에선 기록이 지워질 수 있어 가끔 백업하세요.")
    with st.form("prof"):
        name = st.text_input("이름", p.get("name", "나"))
        goal = st.number_input("목표 체지방 %", 8.0, 30.0, float(p.get("goal_fat", 15.0)), 0.5)
        protein = st.number_input("단백질 목표 g", 50, 250, int(p.get("protein_target", 120)))
        kcal_t = st.number_input("칼로리 목표", 1200, 4000, int(p.get("kcal_target", 2000)))
        if st.form_submit_button("저장", use_container_width=True):
            st.session_state.profile.update({"name": name, "goal_fat": goal, "protein_target": protein, "kcal_target": kcal_t})
            save_json(PROFILE_FILE, st.session_state.profile)
            st.success("저장했습니다.")
    blob = json.dumps({
        "profile": load_json(PROFILE_FILE, st.session_state.profile),
        "workouts": load_json(WORKOUT_FILE),
        "body": load_json(BODY_FILE),
        "diet": load_json(DIET_FILE),
    }, ensure_ascii=False, indent=2)
    st.download_button("기록 백업 받기", blob, file_name="my_fit_backup.json")
