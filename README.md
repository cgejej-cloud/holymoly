# 창세기 퀴즈 · Genesis Quiz

창세기(Genesis) 30문항 퀴즈 자료 — 질문 · 힌트 · 정답 포함.

### 산출물

- `genesis_quiz.pdf` — Adobe Acrobat 호환 PDF (한글 TrueType 폰트 서브셋 임베드, ToUnicode CMap 포함)

## 빌드

Python 3 + ReportLab + Nanum TTF 폰트가 필요합니다.

```bash
pip install reportlab
sudo apt-get install -y fonts-nanum
python3 scripts/build_pdf.py
```

빌드 결과는 저장소 루트의 `genesis_quiz.pdf` 로 생성됩니다.

## Adobe 호환성 메모

원본 PDF는 PostScript-outline OTF(예: Noto CJK)를 사용해 일부 Adobe Reader 환경에서
한글이 빈 칸/박스로 표시되거나 텍스트 추출이 깨지는 문제가 있었습니다. 이 빌드는 다음을
적용해 Adobe Acrobat / Reader 전 버전에서 한글이 정상 표시·검색·복사되도록 합니다.

- TrueType outline 한글 폰트(나눔명조 · 나눔고딕) 사용
- 모든 폰트를 본문에 **서브셋 임베드**
- 각 폰트에 대해 **ToUnicode CMap** 자동 생성 (텍스트 추출/검색용)
- PDF 1.7 출력, 표준 메타데이터(`Title`, `Author`, `Subject`, `Keywords`, `Lang=ko-KR`)
- 시스템 설치 폰트에 의존하지 않도록 모든 글리프를 문서 내부에 포함

## 보완 사항

원본과 비교해 다음을 다듬었습니다.

- 8페이지 마지막 파트 헤더의 누락된 로마 숫자 보완: `Part` → `Part VII`
- 본문 폰트 통일 및 한글 자간/행간 가독성 보정
- 페이지 머리·꼬리말의 좌우 정렬 및 가운데 페이지 번호 일관화


## 노래 → MP3 파이프라인

가사 텍스트(`lyrics/NN_제목.txt`)를 받아 한국어 VITS 음성 + 드론 톤이 깔린 MP3
(`audio/NN_제목.mp3`)를 만들어 줍니다. 아이폰·갤럭시에서 모두 재생됩니다.

### 1회 설치

```bash
bash scripts/setup.sh
```

- `ffmpeg` (brew / apt 자동 설치)
- Python: `sherpa-onnx`, `soundfile`, `numpy`
- 한국어 음성 모델 `vits-mimic3-ko_KO-kss_low` (약 60MB, sherpa-onnx 공식 릴리스에서 받음)

### 가사 모으기 (반자동)

```bash
python3 scripts/gather_lyrics.py
```

- 곡별로 멜론 검색 페이지가 자동으로 열림
- 가사 페이지에서 복사 → 터미널에 붙여넣기
- 빈 줄에 `END` 입력 후 Enter → `lyrics/NN_제목.txt` 로 저장
- 이미 저장된 곡은 자동 스킵, `--start 3` 처럼 특정 번호부터 다시 시작 가능

가사 파일(`lyrics/`)은 저작권 보호 자료라 `.gitignore` 로 빠져 있어요 — 저장소에 커밋되지 않습니다.

### MP3 일괄 합성

```bash
python3 scripts/build_all.py
```

- `lyrics/*.txt` 전부 → `audio/*.mp3`
- 옵션:
  - `--freq 196` 드론 음정 변경 (기본 220 = A3)
  - `--speed 1.0` TTS 속도 조정 (기본 0.95)
  - `--force` 기존 MP3 무시하고 재생성

### 한 곡만 따로 만들 때

```bash
bash scripts/make_song.sh  lyrics/02_실로암.txt  audio/02_실로암.mp3  220  0.95
```
