# My Fit Planner

나만 쓰는 개인 운동 플래너 (Streamlit 웹앱)

## 기능
- 요일별 추천 루틴 (월 하체 / 수 밀기 / 금 당기기)
- 어깨 워밍업 체크
- 헬스장 기구 기준으로 운동 선택·완료 체크
- 각 운동의 타겟 근육 + 방법 + 팁
- 무게·세트·횟수 기록
- 몸무게·체지방 그래프
- 식단·단백질 기록
- 기록 백업 다운로드/가져오기

프로필 기본값: 35세 남성, 167cm, 67kg, 체지방 22% → 목표 15%

## 컴퓨터에서 실행 (제일 안정적)
1. Python 설치 (https://www.python.org )
2. 이 폴더에서 터미널 실행

```bash
pip install -r requirements.txt
streamlit run app.py
```

브라우저가 열리면 바로 사용하면 됩니다.

## 무료 배포 (Streamlit Cloud)
1. GitHub 계정 만들기
2. 새 Repository 생성 후 `app.py`, `exercises.py`, `requirements.txt` 업로드
3. https://share.streamlit.io 접속 후 New app → 해당 저장소 선택 → Deploy
4. 나온 주소를 핸드폰 홈 화면에 추가하면 앱처럼 씁니다.

주의: Cloud에서는 서버가 잠들면 기록이 초기화될 수 있습니다.
설정 페이지에서 JSON 백업을 가끔 받아두세요. 매일 쓰려면 컴퓨터에서 실행하는 편이 안전합니다.

## 파일
- app.py : 화면
- exercises.py : 운동 DB + 추천 루틴
- data/ : 실행 후 자동 생성되는 기록 폴더
