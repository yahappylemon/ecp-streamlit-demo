from __future__ import annotations

import csv
import html
import math
import re
import tempfile
from collections import Counter, defaultdict
from pathlib import Path
from typing import DefaultDict, Dict, List, NamedTuple, Optional, Sequence, Tuple

import streamlit as st
import streamlit.components.v1 as components


DATA_PATH = Path("ECP_v6_streamlit_clean.csv")
GROUP_LIMIT = 120
GUIDEWORD_PLACEHOLDER = "- Select -"
POS_PLACEHOLDER = "- Select -"
GROUP_SORT_FIELDS = {"collocates", "guideword", "level", "pos"}
DETAIL_SORT_FIELDS = {"collocation", "level", "frequency", "mi"}
LEVELS = ["A1", "A2", "B1", "B2", "C1", "C2"]
LEVEL_RANK = {level: index for index, level in enumerate(LEVELS)}
SEARCH_LIMIT = 300
TEXT_WINDOW_SIZE = 4
TEXT_CANDIDATE_LIMIT = 400
POS_OPTIONS = {
    "verb + noun": "VN",
    "adjective + noun": "AN",
    "noun + noun": "NN",
    "adverb + verb": "ADV+V",
    "adverb + adjective": "ADV+ADJ",
}
CORE_DISPLAY_STRUCTURES = set(POS_OPTIONS.values())
LEVEL_COLORS = {
    "A1": ("#ff7a00", "#ffffff"),
    "A2": ("#00a0a8", "#ffffff"),
    "B1": ("#ff1212", "#ffffff"),
    "B2": ("#00853d", "#ffffff"),
    "C1": ("#315df4", "#ffffff"),
    "C2": ("#a62ba8", "#ffffff"),
}
ALL_LEVEL_COLOR = ("#005b8f", "#ffffff")
POS_CODE_LABELS = {
    "SCONJ": "subordinating conjunction",
    "PROPN": "proper noun",
    "PRON": "pronoun",
    "PART": "particle",
    "INTJ": "interjection",
    "AUX": "auxiliary",
    "ADP": "adposition",
    "ADV": "adverb",
    "ADJ": "adjective",
    "NUM": "number",
    "DET": "determiner",
    "VERB": "verb",
    "NOUN": "noun",
    "V": "verb",
    "N": "noun",
    "A": "adjective",
    "X": "other",
}

LEVEL_SELECTOR_HTML = r"""<!doctype html>
<html lang="en">
  <head>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1" />
    <style>
      html,
      body {
        background: transparent;
        margin: 0;
        min-height: 64px;
        padding: 0;
        overflow: hidden;
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
      }

      .selector {
        display: inline-flex;
        align-items: stretch;
        border-radius: 8px;
        overflow: hidden;
        white-space: nowrap;
      }

      button {
        appearance: none;
        box-sizing: border-box;
        border: 0;
        color: #fff;
        cursor: pointer;
        font-size: 22px;
        font-weight: 400;
        line-height: 1;
        min-width: 0;
        padding: 12px 0;
        transition: filter 120ms ease, opacity 120ms ease;
        width: 66px;
      }

      button.unselected {
        filter: grayscale(0.85);
        opacity: 0.28;
      }

      button:hover {
        filter: brightness(0.95);
      }

      button:focus-visible {
        outline: 3px solid rgba(0, 91, 143, 0.35);
        outline-offset: -3px;
      }
    </style>
  </head>
  <body>
    <div id="root"></div>

    <script>
      const MESSAGE_PREFIX = "streamlit:";
      const LEVELS = ["A1", "A2", "B1", "B2", "C1", "C2"];
      let selected = [...LEVELS];
      let colors = {
        A1: "#ff7a00",
        A2: "#00a0a8",
        B1: "#ff1212",
        B2: "#00853d",
        C1: "#315df4",
        C2: "#a62ba8",
      };
      let allColor = "#005b8f";
      let initialized = false;

      const Streamlit = {
        setComponentReady() {
          window.parent.postMessage(
            {
              isStreamlitMessage: true,
              type: `${MESSAGE_PREFIX}componentReady`,
              apiVersion: 1,
            },
            "*",
          );
        },
        setFrameHeight(height) {
          window.parent.postMessage(
            {
              isStreamlitMessage: true,
              type: `${MESSAGE_PREFIX}setFrameHeight`,
              height,
            },
            "*",
          );
        },
        setComponentValue(value) {
          window.parent.postMessage(
            {
              isStreamlitMessage: true,
              type: `${MESSAGE_PREFIX}setComponentValue`,
              value,
              dataType: "json",
            },
            "*",
          );
        },
      };

      function sanitizeLevels(value) {
        const incoming = Array.isArray(value) ? value : [];
        const kept = LEVELS.filter((level) => incoming.includes(level));
        return kept.length ? kept : [...LEVELS];
      }

      function toggleLevel(level) {
        const set = new Set(selected);
        if (set.has(level) && set.size > 1) {
          set.delete(level);
        } else {
          set.add(level);
        }
        selected = LEVELS.filter((item) => set.has(item));
        render();
        Streamlit.setComponentValue(selected);
      }

      function selectAll() {
        selected = [...LEVELS];
        render();
        Streamlit.setComponentValue(selected);
      }

      function button(label, isSelected, color, onClick) {
        const element = document.createElement("button");
        element.type = "button";
        element.textContent = label;
        element.style.background = color;
        element.setAttribute("aria-pressed", String(isSelected));
        if (!isSelected) {
          element.className = "unselected";
        }
        element.addEventListener("click", onClick);
        return element;
      }

      function render() {
        const root = document.getElementById("root");
        root.innerHTML = "";
        const selector = document.createElement("div");
        selector.className = "selector";

        for (const level of LEVELS) {
          selector.appendChild(
            button(level, selected.includes(level), colors[level], () =>
              toggleLevel(level),
            ),
          );
        }

        selector.appendChild(
          button("All", selected.length === LEVELS.length, allColor, selectAll),
        );
        root.appendChild(selector);
        Streamlit.setFrameHeight(64);
      }

      window.addEventListener("message", (event) => {
        const data = event.data || {};
        if (data.type !== `${MESSAGE_PREFIX}render`) {
          return;
        }

        const args = data.args || {};
        colors = args.colors || colors;
        allColor = args.all_color || allColor;
        if (!initialized) {
          selected = sanitizeLevels(args.selected || args.default);
          initialized = true;
        }
        render();
      });

      Streamlit.setComponentReady();
      render();
      Streamlit.setComponentValue(selected);
    </script>
  </body>
</html>
"""


def ensure_level_selector_component() -> Path:
    component_path = Path(tempfile.gettempdir()) / "ecp_cefr_level_selector"
    component_path.mkdir(parents=True, exist_ok=True)
    index_path = component_path / "index.html"
    if not index_path.exists() or index_path.read_text(encoding="utf-8") != LEVEL_SELECTOR_HTML:
        index_path.write_text(LEVEL_SELECTOR_HTML, encoding="utf-8")
    return component_path


cefr_level_selector_component = components.declare_component(
    "cefr_level_selector",
    path=str(ensure_level_selector_component()),
)


class Entry(NamedTuple):
    collocation: str
    word1: str
    word2: str
    relation: str
    level: str
    guideword: str
    pos1: str
    pos2: str
    frequency: Optional[float]
    mi: Optional[float]


class Dataset(NamedTuple):
    entries: Tuple[Entry, ...]
    word1_index: Dict[str, Tuple[int, ...]]
    word2_index: Dict[str, Tuple[int, ...]]
    pair_index: Dict[Tuple[str, str], int]


LEMMA_OVERRIDES = {
    "made": "make",
    "makes": "make",
    "making": "make",
    "took": "take",
    "taken": "take",
    "takes": "take",
    "taking": "take",
    "had": "have",
    "has": "have",
    "having": "have",
    "did": "do",
    "does": "do",
    "doing": "do",
    "gave": "give",
    "given": "give",
    "gives": "give",
    "giving": "give",
    "paid": "pay",
    "pays": "pay",
    "paying": "pay",
    "earned": "earn",
    "earns": "earn",
    "earning": "earn",
}


def clean_text(value: object) -> str:
    text = str(value or "").strip()
    return "" if text.lower() == "nan" else text


def as_optional_float(value: object) -> Optional[float]:
    text = clean_text(value)
    if not text:
        return None
    try:
        number = float(text)
    except ValueError:
        return None
    return number if math.isfinite(number) else None


def normalize_word(value: str) -> str:
    return re.sub(r"[,()%]", " ", value).strip().lower()


def simple_lemma(token: str) -> str:
    word = clean_text(token).lower()
    if not word:
        return ""
    if word in LEMMA_OVERRIDES:
        return LEMMA_OVERRIDES[word]
    if len(word) > 4 and word.endswith("ies"):
        return f"{word[:-3]}y"
    if len(word) > 4 and word.endswith("ing"):
        stem = word[:-3]
        if re.search(r"([b-df-hj-np-tv-z])\1$", stem):
            stem = stem[:-1]
        return stem
    if len(word) > 3 and word.endswith("ed"):
        stem = word[:-2]
        if re.search(r"([b-df-hj-np-tv-z])\1$", stem):
            stem = stem[:-1]
        return stem
    if len(word) > 4 and word.endswith(("ches", "shes", "xes", "zes", "oes", "ses")):
        return word[:-2]
    if len(word) > 3 and word.endswith("s") and not word.endswith("ss"):
        return word[:-1]
    return word


def search_terms(value: str) -> Tuple[str, ...]:
    keyword = normalize_word(value)
    terms = [keyword, simple_lemma(keyword)]
    return tuple(dict.fromkeys(term for term in terms if term))


def tokenize_text(value: str) -> List[str]:
    normalized = value.lower().replace("’", "'").replace("‘", "'").replace("-", " ")
    normalized = re.sub(r"[^a-z'\s]", " ", normalized)
    return [token.strip("'") for token in normalized.split() if token.strip("'")]


def is_text_search(value: str) -> bool:
    return len(tokenize_text(value)) > 1


def token_variants(token: str) -> Tuple[str, ...]:
    return tuple(dict.fromkeys(value for value in (token, simple_lemma(token)) if value))


def extract_text_candidate_pairs(value: str) -> List[Tuple[str, str]]:
    tokens = tokenize_text(value)
    candidates: List[Tuple[str, str]] = []
    seen: set[Tuple[str, str]] = set()

    for left_index, token1 in enumerate(tokens):
        right_limit = min(len(tokens), left_index + TEXT_WINDOW_SIZE + 1)
        for right_index in range(left_index + 1, right_limit):
            token2 = tokens[right_index]
            for word1 in token_variants(token1):
                for word2 in token_variants(token2):
                    pair = (word1, word2)
                    if pair not in seen:
                        seen.add(pair)
                        candidates.append(pair)
                    if len(candidates) >= TEXT_CANDIDATE_LIMIT:
                        return candidates
    return candidates


@st.cache_resource(show_spinner="Loading the ECP dataset...")
def load_dataset(path_text: str, modified_ns: int) -> Dataset:
    del modified_ns
    path = Path(path_text)
    entries: List[Entry] = []
    word1_lists: DefaultDict[str, List[int]] = defaultdict(list)
    word2_lists: DefaultDict[str, List[int]] = defaultdict(list)
    pair_index: Dict[Tuple[str, str], int] = {}

    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        required = {
            "collocation",
            "word1",
            "word2",
            "relation",
            "final_cefr",
            "guideword",
            "pos1",
            "pos2",
            "teacher_gappy_count",
            "mi_gappy",
        }
        missing = required.difference(reader.fieldnames or [])
        if missing:
            raise ValueError(
                f"Dataset is missing required columns: {', '.join(sorted(missing))}"
            )

        for row in reader:
            collocation = clean_text(row.get("collocation"))
            word1 = clean_text(row.get("word1")).lower()
            word2 = clean_text(row.get("word2")).lower()
            level = clean_text(row.get("final_cefr")).upper()
            if not collocation or not word1 or not word2 or level not in LEVEL_RANK:
                continue

            entry = Entry(
                collocation=collocation,
                word1=word1,
                word2=word2,
                relation=clean_text(row.get("relation")),
                level=level,
                guideword=clean_text(row.get("guideword")),
                pos1=clean_text(row.get("pos1")),
                pos2=clean_text(row.get("pos2")),
                frequency=as_optional_float(row.get("teacher_gappy_count")),
                mi=as_optional_float(row.get("mi_gappy")),
            )
            index = len(entries)
            entries.append(entry)
            word1_lists[word1].append(index)
            word2_lists[word2].append(index)
            pair_index[(word1, word2)] = index

    return Dataset(
        entries=tuple(entries),
        word1_index={key: tuple(values) for key, values in word1_lists.items()},
        word2_index={key: tuple(values) for key, values in word2_lists.items()},
        pair_index=pair_index,
    )


def unique_indices(groups: Sequence[Sequence[int]]) -> List[int]:
    output: List[int] = []
    seen: set[int] = set()
    for group in groups:
        for index in group:
            if index not in seen:
                seen.add(index)
                output.append(index)
    return output


def find_word_matches(dataset: Dataset, query: str) -> Tuple[List[int], List[int]]:
    terms = search_terms(query)
    first = unique_indices([dataset.word1_index.get(term, ()) for term in terms])
    first_set = set(first)
    second = [
        index
        for index in unique_indices([dataset.word2_index.get(term, ()) for term in terms])
        if index not in first_set
    ]
    return first, second


def find_text_matches(dataset: Dataset, text: str) -> List[int]:
    return unique_indices(
        [
            (dataset.pair_index[pair],)
            for pair in extract_text_candidate_pairs(text)
            if pair in dataset.pair_index
        ]
    )


def structure_label(entry: Entry) -> str:
    relation = entry.relation.strip().upper()
    relation_map = {
        "V:OBJ:N": "VN",
        "N:MOD:A": "AN",
        "A:SUBJ:N": "AN",
        "N:NN:N": "NN",
        "N:APPO:N": "NN",
        "N:OF:N": "NN",
        "N:IN:N": "NN",
        "N:WITH:N": "NN",
        "N:FOR:N": "NN",
        "A:MOD:A": "ADV+ADJ",
        "A:MOD:ADV": "ADV+ADJ",
        "V:MOD:A": "ADV+V",
        "V:MOD:ADV": "ADV+V",
    }
    return relation_map.get(relation, f"{pos_short(entry.pos1)}{pos_short(entry.pos2)}")


def display_semantic_tag(entry: Entry) -> str:
    label = entry.guideword.strip()
    parts = label.split(maxsplit=1)
    if len(parts) == 2 and simple_lemma(parts[0]) == simple_lemma(entry.word1):
        return parts[1].strip().upper()
    return label


def pos_short(value: str) -> str:
    return {
        "ADJ": "A",
        "ADJECTIVE": "A",
        "ADV": "ADV",
        "ADVERB": "ADV",
        "NOUN": "N",
        "N": "N",
        "VERB": "V",
        "V": "V",
    }.get(value.strip().upper(), value.strip().upper())


def compact_number(value: float) -> str:
    if value >= 1_000_000:
        return f"{value / 1_000_000:.1f}M"
    if value >= 1_000:
        return f"{value / 1_000:.1f}K"
    return f"{value:,.0f}"


class SemanticGroup(NamedTuple):
    headword: str
    semantic_tag: str
    structure: str
    collocate_side: str
    indices: Tuple[int, ...]


GroupKey = Tuple[str, str, str, str]
GroupLevelLookup = Dict[GroupKey, str]


def resolve_data_path() -> Path:
    return (Path(__file__).resolve().parent / DATA_PATH).resolve()


def render_styles() -> None:
    st.markdown(
        """
        <style>
        :root {
          --ecp-blue: #005b8f;
          --ecp-orange: #f4ad43;
          --ecp-text: #252525;
          --ecp-muted: #666;
          --ecp-line: #d7d7d7;
          --ecp-row: #f1f1f1;
        }
        .main .block-container {
          max-width: 1440px;
          padding-top: 1.35rem;
          padding-left: 1.5rem;
          padding-right: 1.5rem;
        }
        h1.ecp-title {
          color: var(--ecp-text);
          font-size: clamp(2.4rem, 4.2vw, 4.2rem);
          line-height: 1.05;
          font-weight: 800;
          margin: 0 0 0.9rem;
          letter-spacing: 0;
          border-bottom: 1px solid #ddd;
          padding-bottom: 0.7rem;
        }
        .filter-label {
          color: #2a2a2a;
          font-size: 1.05rem;
          font-weight: 800;
          margin-bottom: 0.15rem;
        }
        .level-caption {
          color: #2a2a2a;
          font-size: 1.05rem;
          font-weight: 800;
          padding-top: 0.55rem;
          text-align: right;
        }
        .search-panel {
          border: 1px solid #d7d7d7;
          border-radius: 8px;
          padding: 1.25rem 1.45rem 1.4rem;
          margin: 1.35rem 0 1rem;
        }
        div[data-testid="stTextInput"] input,
        div[data-testid="stTextArea"] textarea,
        div[data-testid="stSelectbox"] div[data-baseweb="select"] > div {
          min-height: 3rem;
          border-radius: 4px;
          border-color: #dedede;
          box-shadow: none;
          font-size: 1.05rem;
        }
        div[data-testid="stTextArea"] textarea {
          line-height: 1.45;
          resize: vertical;
        }
        div[data-testid="stButton"] > button {
          min-height: 3.15rem;
          border-radius: 4px;
          border: 0;
          font-size: 1.05rem;
          font-weight: 800;
        }
        div[data-testid="stButton"] > button[kind="primary"] {
          background: var(--ecp-blue);
          color: #fff;
        }
        div[data-testid="stButton"] > button[kind="primary"]:hover {
          background: #00466e;
          color: #fff;
        }
        .level-strip {
          display: flex;
          flex-wrap: wrap;
          gap: 0;
          align-items: center;
          padding-top: 0.2rem;
        }
        .level-chip {
          display: inline-block;
          color: #fff;
          font-weight: 800;
          min-width: 2.8rem;
          text-align: center;
          padding: 0.65rem 0.9rem;
          line-height: 1;
        }
        .level-chip-muted {
          filter: grayscale(0.75);
          opacity: 0.38;
        }
        .level-segment-strip {
          display: flex;
          flex-wrap: wrap;
          gap: 0;
          padding-top: 0.15rem;
        }
        .level-segment {
          color: #fff;
          display: inline-block;
          font-size: 1.18rem;
          font-weight: 800;
          line-height: 1;
          min-width: 4rem;
          padding: 0.95rem 1.05rem;
          text-align: center;
          text-decoration: none !important;
        }
        .level-segment:first-child {
          border-bottom-left-radius: 8px;
          border-top-left-radius: 8px;
        }
        .level-segment:last-child {
          border-bottom-right-radius: 8px;
          border-top-right-radius: 8px;
        }
        .level-segment.unselected {
          filter: grayscale(0.75);
          opacity: 0.28;
        }
        .level-segment:hover,
        .level-segment:visited,
        .level-segment:active {
          color: #fff;
          text-decoration: none !important;
        }
        .result-meta {
          color: #666;
          font-size: 0.95rem;
          margin: 1.2rem 0 0.55rem;
        }
        .ecp-header, .ecp-row {
          display: grid;
          grid-template-columns: minmax(5.5rem, 0.7fr) minmax(18rem, 2.2fr) minmax(8rem, 1fr) minmax(5rem, 0.55fr) minmax(9rem, 1fr) minmax(5rem, 0.48fr);
          gap: 1.1rem;
          align-items: center;
        }
        .ecp-header {
          color: #2b2b2b;
          font-weight: 800;
          padding: 0.2rem 0.55rem 0.55rem;
        }
        .ecp-header-label {
          color: #2b2b2b;
          font-size: 1rem;
          font-weight: 800;
          padding: 0.38rem 0;
        }
        .ecp-sort-header div[data-testid="stButton"] > button,
        .detail-sort-header div[data-testid="stButton"] > button {
          background: transparent;
          border: 0;
          color: #2b2b2b;
          font-size: 1rem;
          font-weight: 800;
          min-height: 1.8rem;
          padding: 0;
          text-align: left;
        }
        .ecp-sort-header div[data-testid="stButton"] > button:hover,
        .detail-sort-header div[data-testid="stButton"] > button:hover {
          background: transparent;
          color: var(--ecp-blue);
        }
        .ecp-sort-header div[data-testid="stButton"] > button p,
        .detail-sort-header div[data-testid="stButton"] > button p {
          text-align: left;
          width: 100%;
        }
        .ecp-row {
          border-top: 1px solid var(--ecp-line);
          padding: 0.72rem 0.55rem;
          color: #2a2a2a;
          font-size: clamp(1rem, 1.8vw, 1.55rem);
        }
        .ecp-row:nth-of-type(even) {
          background: var(--ecp-row);
        }
        .collocates {
          color: #222;
          font-style: italic;
          line-height: 1.35;
          overflow-wrap: anywhere;
        }
        .semantic-tag {
          font-weight: 500;
          letter-spacing: 0;
          overflow-wrap: anywhere;
        }
        .pos-pattern {
          white-space: nowrap;
        }
        .level-badge {
          display: inline-block;
          border-radius: 4px;
          color: #fff;
          font-size: 1rem;
          font-weight: 800;
          line-height: 1;
          min-width: 3.2rem;
          padding: 0.55rem 0.8rem;
          text-align: center;
        }
        .level-range {
          display: inline-block;
          background: #eef2f4;
          border-radius: 4px;
          color: #304155;
          font-size: 0.95rem;
          font-weight: 800;
          padding: 0.48rem 0.75rem;
          white-space: nowrap;
        }
        .detail-cell button {
          background: var(--ecp-orange);
          border: 0;
          border-radius: 4px;
          color: #fff;
          font-weight: 800;
          min-height: 2.7rem;
          width: 100%;
        }
        .streamlit-row-rule {
          border-top: 1px solid var(--ecp-line);
          margin: 0.35rem 0 0.45rem;
        }
        .detail-box {
          background: #fff;
          border-top: 1px solid #e5e5e5;
          padding: 0 0.55rem 0.85rem;
        }
        .detail-table {
          width: 100%;
          border-collapse: collapse;
          font-size: 0.96rem;
          color: #303030;
        }
        .detail-table th,
        .detail-table td {
          border-bottom: 1px solid #ececec;
          padding: 0.45rem 0.55rem;
          text-align: left;
        }
        .detail-table th {
          background: #f8f8f8;
          font-weight: 800;
        }
        .detail-sort-header {
          background: #f8f8f8;
          border-bottom: 1px solid #ececec;
          border-top: 1px solid #ececec;
          padding: 0.45rem 0.55rem;
        }
        .detail-grid-row {
          display: grid;
          grid-template-columns: 1.4fr 0.55fr 1.15fr 0.55fr;
          gap: 0;
          align-items: center;
        }
        .detail-grid-row > div {
          padding: 0.45rem 0.55rem;
        }
        .detail-data-row {
          border-bottom: 1px solid #ececec;
          color: #303030;
          font-size: 0.96rem;
        }
        .stars {
          color: #f4ad43;
          font-size: 0.95rem;
          letter-spacing: 0.03rem;
          white-space: nowrap;
        }
        .freq-value {
          white-space: nowrap;
        }
        @media (max-width: 840px) {
          .ecp-header { display: none; }
          .ecp-row {
            grid-template-columns: 1fr;
            gap: 0.35rem;
            font-size: 1.1rem;
          }
          .pos-pattern { white-space: normal; }
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def level_badge_html(level: str) -> str:
    background, color = LEVEL_COLORS.get(level, ("#a7b2bd", "#ffffff"))
    return (
        f"<span class='level-badge' "
        f"style='background:{background};color:{color}'>{html.escape(level)}</span>"
    )


def set_live_levels(levels: Sequence[str]) -> None:
    st.session_state["evp_style_live_levels"] = [
        level for level in LEVELS if level in set(levels)
    ]


def render_level_controls(default_levels: Sequence[str]) -> List[str]:
    st.session_state.setdefault("evp_style_live_levels", list(default_levels))
    current_levels = list(st.session_state.get(
        "evp_style_live_levels", LEVELS))
    colors = {level: LEVEL_COLORS[level][0] for level in LEVELS}
    selected_levels = cefr_level_selector_component(
        selected=current_levels,
        colors=colors,
        all_color=ALL_LEVEL_COLOR[0],
        key="evp_style_cefr_level_selector",
        default=current_levels,
    )
    if isinstance(selected_levels, list):
        cleaned_levels = [
            level for level in LEVELS if level in set(selected_levels)
        ]
        if cleaned_levels:
            set_live_levels(cleaned_levels)
    return list(st.session_state.get("evp_style_live_levels", LEVELS))


def structure_to_pos_pattern(structure: str) -> str:
    normalized = structure.strip().upper()
    mapped = {
        "VN": "verb + noun",
        "AN": "adjective + noun",
        "NN": "noun + noun",
        "ADV+V": "adverb + verb",
        "ADV+ADJ": "adverb + adjective",
        "VA": "verb + adjective",
        "VV": "verb + verb",
        "NA": "noun + adjective",
        "NV": "noun + verb",
        "AV": "adjective + verb",
    }.get(normalized)
    if mapped:
        return mapped

    compact = normalized.replace("+", "")
    compact_mapped = {
        "ADVA": "adverb + adjective",
        "ADVADJ": "adverb + adjective",
        "ADWADJ": "adverb + adjective",
        "ADVV": "adverb + verb",
        "ADWV": "adverb + verb",
        "ADVN": "adverb + noun",
        "ADWN": "adverb + noun",
        "VA": "verb + adjective",
        "VV": "verb + verb",
        "VN": "verb + noun",
        "VADV": "verb + adverb",
        "VADW": "verb + adverb",
        "NA": "noun + adjective",
        "NV": "noun + verb",
        "NN": "noun + noun",
        "NADV": "noun + adverb",
        "NADW": "noun + adverb",
        "AA": "adjective + adjective",
        "AV": "adjective + verb",
        "AN": "adjective + noun",
        "AADV": "adjective + adverb",
        "AADW": "adjective + adverb",
    }.get(compact)
    if compact_mapped:
        return compact_mapped
    parsed = parse_compact_pos_pattern(compact)
    if parsed:
        return parsed
    return html.escape(structure.lower())


def canonical_structure_label(entry: Entry) -> str:
    raw = structure_label(entry).strip().upper()
    compact = raw.replace("+", "")
    if compact in {"ADVA", "ADVADJ", "ADWADJ"}:
        return "ADV+ADJ"
    if compact in {"ADVV", "ADWV"}:
        return "ADV+V"
    return raw


def parse_compact_pos_pattern(value: str) -> str:
    tokens = []
    index = 0
    codes = sorted(POS_CODE_LABELS, key=len, reverse=True)
    while index < len(value):
        match = None
        for code in codes:
            if value.startswith(code, index):
                match = code
                break
        if match is None:
            return ""
        tokens.append(POS_CODE_LABELS[match])
        index += len(match)
    if len(tokens) < 2:
        return ""
    return " + ".join(tokens)


def format_number(value: Optional[float]) -> str:
    if value is None:
        return "-"
    return compact_number(value)


def format_mi(value: Optional[float]) -> str:
    if value is None:
        return "-"
    return f"{value:.2f}"


def frequency_stars_html(value: Optional[float]) -> str:
    if value is None:
        return "-"
    if value >= 100_000:
        stars = 5
    elif value >= 20_000:
        stars = 4
    elif value >= 5_000:
        stars = 3
    elif value >= 1_000:
        stars = 2
    else:
        stars = 1
    return (
        f"<span class='freq-value'>{html.escape(format_number(value))}</span> "
        f"<span class='stars'>{'★' * stars}{'☆' * (5 - stars)}</span>"
    )


def get_sort_state(
    namespace: str,
    default_field: str,
    default_direction: str = "asc",
) -> Tuple[str, str]:
    field_key = f"{namespace}:sort_field"
    direction_key = f"{namespace}:sort_direction"
    field = st.session_state.get(field_key, default_field)
    direction = st.session_state.get(direction_key, default_direction)
    return str(field), str(direction)


def toggle_sort_state(namespace: str, field: str) -> None:
    field_key = f"{namespace}:sort_field"
    direction_key = f"{namespace}:sort_direction"
    current_field = st.session_state.get(field_key)
    current_direction = st.session_state.get(direction_key, "asc")
    if current_field == field:
        st.session_state[direction_key] = (
            "desc" if current_direction == "asc" else "asc"
        )
    else:
        st.session_state[field_key] = field
        st.session_state[direction_key] = "asc"


def sort_button_label(
    namespace: str,
    field: str,
    label: str,
    default_field: str,
    default_direction: str = "asc",
) -> str:
    current_field, current_direction = get_sort_state(
        namespace,
        default_field,
        default_direction,
    )
    if current_field != field:
        return f"{label} ↕"
    return f"{label} {'▲' if current_direction == 'asc' else '▼'}"


def render_sort_button(
    namespace: str,
    field: str,
    label: str,
    default_field: str,
    default_direction: str = "asc",
) -> None:
    button_label = sort_button_label(
        namespace,
        field,
        label,
        default_field,
        default_direction,
    )
    st.button(
        button_label,
        key=f"{namespace}:sort:{field}",
        use_container_width=True,
        on_click=toggle_sort_state,
        args=(namespace, field),
    )


@st.cache_data(show_spinner=False)
def guideword_options(path_text: str, modified_ns: int) -> Tuple[str, ...]:
    dataset = load_dataset(path_text, modified_ns)
    values = {
        display_semantic_tag(entry)
        for entry in dataset.entries
        if display_semantic_tag(entry)
    }
    return tuple(sorted(values, key=str.lower))


def build_semantic_groups(
    indices: Sequence[int],
    dataset: Dataset,
    collocate_side: str = "word2",
) -> List[SemanticGroup]:
    grouped: DefaultDict[Tuple[str, str, str, str],
                         List[int]] = defaultdict(list)
    for index in indices:
        entry = dataset.entries[index]
        structure = canonical_structure_label(entry)
        if structure not in CORE_DISPLAY_STRUCTURES:
            continue
        if collocate_side == "word1":
            headword = entry.word2
        elif collocate_side == "word1_list":
            headword = entry.word2
        else:
            headword = entry.word1
        key = (
            headword,
            display_semantic_tag(entry),
            structure,
            collocate_side,
        )
        grouped[key].append(index)

    groups = [
        SemanticGroup(
            headword=headword,
            semantic_tag=semantic_tag,
            structure=structure,
            collocate_side=collocate_side,
            indices=tuple(member_indices),
        )
        for (
            headword,
            semantic_tag,
            structure,
            collocate_side,
        ), member_indices in grouped.items()
    ]
    groups.sort(key=lambda group: group_sort_key(group, dataset))
    return groups


def group_lookup_key(group: SemanticGroup) -> GroupKey:
    return (
        group.headword,
        group.semantic_tag,
        group.structure,
        group.collocate_side,
    )


def group_sort_key(group: SemanticGroup, dataset: Dataset) -> Tuple[int, str, str]:
    levels = group_levels(group, dataset)
    minimum_level = LEVEL_RANK.get(levels[0], 99) if levels else 99
    return minimum_level, group.semantic_tag.lower(), group.headword


def ordered_group_members(
    group: SemanticGroup,
    dataset: Dataset,
) -> List[Entry]:
    entries = [dataset.entries[index] for index in group.indices]
    entries.sort(
        key=lambda entry: (
            -(entry.frequency if entry.frequency is not None else -1),
            entry.word2,
        )
    )
    return entries


def sorted_detail_members(
    group: SemanticGroup,
    dataset: Dataset,
    namespace: str,
) -> List[Entry]:
    field, direction = get_sort_state(namespace, "collocation", "asc")
    if field not in DETAIL_SORT_FIELDS:
        field = "collocation"
    entries = [dataset.entries[index] for index in group.indices]

    def key(entry: Entry) -> object:
        if field == "level":
            return LEVEL_RANK.get(entry.level, 99)
        if field == "frequency":
            return entry.frequency if entry.frequency is not None else -1
        if field == "mi":
            return entry.mi if entry.mi is not None else -1
        return entry.collocation.lower()

    entries.sort(key=key, reverse=(direction == "desc"))
    return entries


def group_levels(group: SemanticGroup, dataset: Dataset) -> List[str]:
    return sorted(
        {dataset.entries[index].level for index in group.indices},
        key=lambda level: LEVEL_RANK.get(level, 99),
    )


def normalized_phrase(value: str) -> str:
    return " ".join(str(value or "").strip().lower().split())


def representative_level_from_entries(
    entries: Sequence[Entry],
    semantic_tag: str,
) -> str:
    ordered = sorted(
        entries,
        key=lambda entry: (
            LEVEL_RANK.get(entry.level, 99),
            -(entry.frequency if entry.frequency is not None else -1),
            entry.word2,
        ),
    )
    normalized_tag = normalized_phrase(semantic_tag)
    for entry in ordered:
        if normalized_phrase(entry.guideword) == normalized_phrase(entry.collocation):
            return entry.level
    for entry in ordered:
        if normalized_phrase(entry.collocation) == normalized_tag:
            return entry.level
    for entry in ordered:
        if normalized_phrase(entry.word2) == normalized_tag:
            return entry.level
    counts = Counter(entry.level for entry in ordered)
    if not counts:
        return ""
    return min(
        counts,
        key=lambda level: (
            -counts[level],
            LEVEL_RANK.get(level, 99),
        ),
    )


@st.cache_data(show_spinner=False)
def build_group_level_lookup(
    path_text: str,
    modified_ns: int,
) -> GroupLevelLookup:
    dataset = load_dataset(path_text, modified_ns)
    grouped: DefaultDict[GroupKey, List[Entry]] = defaultdict(list)
    for entry in dataset.entries:
        structure = canonical_structure_label(entry)
        if structure not in CORE_DISPLAY_STRUCTURES:
            continue
        semantic_tag = display_semantic_tag(entry)
        for collocate_side, headword in (
            ("word2", entry.word1),
            ("word1_list", entry.word2),
        ):
            grouped[
                (
                    headword,
                    semantic_tag,
                    structure,
                    collocate_side,
                )
            ].append(entry)
    return {
        key: representative_level_from_entries(entries, key[1])
        for key, entries in grouped.items()
    }


def representative_group_level(
    group: SemanticGroup,
    dataset: Dataset,
    group_level_lookup: Optional[GroupLevelLookup] = None,
) -> str:
    if group_level_lookup is not None:
        level = group_level_lookup.get(group_lookup_key(group))
        if level:
            return level
    members = ordered_group_members(group, dataset)
    return representative_level_from_entries(members, group.semantic_tag)


def group_collocates_text(group: SemanticGroup, dataset: Dataset) -> str:
    if group.collocate_side == "word1_list":
        return ", ".join(entry.word1 for entry in ordered_group_members(group, dataset))
    if group.collocate_side == "word1":
        return ", ".join(entry.word1 for entry in ordered_group_members(group, dataset))
    return ", ".join(entry.word2 for entry in ordered_group_members(group, dataset))


def group_headword_text(group: SemanticGroup, dataset: Dataset) -> str:
    if group.collocate_side == "word1_list":
        return group.headword
    return group.headword


def sorted_semantic_groups(
    groups: Sequence[SemanticGroup],
    dataset: Dataset,
    namespace: str,
    group_level_lookup: GroupLevelLookup,
) -> List[SemanticGroup]:
    field, direction = get_sort_state(namespace, "level", "asc")
    if field not in GROUP_SORT_FIELDS:
        field = "level"

    def key(group: SemanticGroup) -> object:
        if field == "collocates":
            return group_collocates_text(group, dataset).lower()
        if field == "guideword":
            return group.semantic_tag.lower()
        if field == "pos":
            return structure_to_pos_pattern(group.structure).lower()
        level = representative_group_level(group, dataset, group_level_lookup)
        return LEVEL_RANK.get(level, 99)

    output = list(groups)
    output.sort(key=key, reverse=(direction == "desc"))
    return output


def filter_indices(
    indices: Sequence[int],
    dataset: Dataset,
    selected_guideword: str,
    selected_pos: str,
) -> List[int]:
    structure_filter = POS_OPTIONS.get(selected_pos)
    output: List[int] = []
    for index in indices:
        entry = dataset.entries[index]
        if (
            selected_guideword != GUIDEWORD_PLACEHOLDER
            and display_semantic_tag(entry) != selected_guideword
        ):
            continue
        structure = canonical_structure_label(entry)
        if structure not in CORE_DISPLAY_STRUCTURES:
            continue
        if structure_filter and structure != structure_filter:
            continue
        output.append(index)
    return output


def render_group_header(namespace: str, collocate_side: str = "word2") -> None:
    st.markdown("<div class='ecp-sort-header'>", unsafe_allow_html=True)
    header_widths = (
        [2.4, 0.5, 1, 0.55, 1, 0.48]
        if collocate_side == "word1_list"
        else [0.7, 2.2, 1, 0.55, 1, 0.48]
    )
    header = st.columns(header_widths)
    if collocate_side == "word1_list":
        with header[0]:
            render_sort_button(namespace, "collocates", "Collocates", "level")
        header[1].markdown(
            "<div class='ecp-header-label'>Headword</div>",
            unsafe_allow_html=True,
        )
    else:
        header[0].markdown(
            "<div class='ecp-header-label'>Headword</div>",
            unsafe_allow_html=True,
        )
        with header[1]:
            render_sort_button(namespace, "collocates", "Collocates", "level")
    with header[2]:
        render_sort_button(namespace, "guideword", "Guideword", "level")
    with header[3]:
        render_sort_button(namespace, "level", "Level", "level")
    with header[4]:
        render_sort_button(namespace, "pos", "Part of Speech", "level")
    header[5].markdown("", unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)


def render_detail_panel(
    group: SemanticGroup,
    dataset: Dataset,
    namespace: str,
    display_level: str,
) -> None:
    rows = []
    display_level_rank = LEVEL_RANK.get(display_level, 99)
    for entry in ordered_group_members(group, dataset):
        frequency = entry.frequency if entry.frequency is not None else -1
        mi = entry.mi if entry.mi is not None else -1
        rows.append(
            "<tr "
            f"data-collocation='{html.escape(entry.collocation.lower(), quote=True)}' "
            f"data-level='{display_level_rank}' "
            f"data-frequency='{frequency}' "
            f"data-mi='{mi}'>"
            f"<td>{html.escape(entry.collocation)}</td>"
            f"<td>{level_badge_html(display_level)}</td>"
            f"<td>{frequency_stars_html(entry.frequency)}</td>"
            f"<td>{html.escape(format_mi(entry.mi))}</td>"
            "</tr>"
        )
    table_html = f"""
    <!doctype html>
    <html>
    <head>
      <meta charset="utf-8" />
      <style>
        html, body {{
          margin: 0;
          padding: 0;
          background: #fff;
          color: #303030;
          font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
        }}
        table {{
          width: 100%;
          border-collapse: collapse;
          table-layout: fixed;
          font-size: 15px;
        }}
        th, td {{
          border: 1px solid #e7e7e7;
          padding: 8px 10px;
          text-align: left;
          vertical-align: middle;
        }}
        th {{
          background: #f8f8f8;
          color: #2b2b2b;
          cursor: pointer;
          font-weight: 800;
          user-select: none;
        }}
        th:hover {{
          color: #005b8f;
        }}
        tr:nth-child(even) td {{
          background: #fcfcfc;
        }}
        .level-badge {{
          display: inline-block;
          border-radius: 4px;
          color: #fff;
          font-size: 14px;
          font-weight: 800;
          line-height: 1;
          min-width: 38px;
          padding: 7px 9px;
          text-align: center;
        }}
        .freq-value {{
          white-space: nowrap;
        }}
        .stars {{
          color: #f4ad43;
          font-size: 13px;
          letter-spacing: 0.02rem;
          margin-left: 8px;
          white-space: nowrap;
        }}
        th:nth-child(1), td:nth-child(1) {{ width: 37%; }}
        th:nth-child(2), td:nth-child(2) {{ width: 15%; }}
        th:nth-child(3), td:nth-child(3) {{ width: 30%; }}
        th:nth-child(4), td:nth-child(4) {{ width: 18%; }}
      </style>
    </head>
    <body>
      <table id="detail-table">
        <thead>
          <tr>
            <th data-sort="collocation" data-type="text">Collocation ▲</th>
            <th data-sort="level" data-type="number">Level ↕</th>
            <th data-sort="frequency" data-type="number">Gappy frequency ↕</th>
            <th data-sort="mi" data-type="number">Gappy MI ↕</th>
          </tr>
        </thead>
        <tbody>
          {''.join(rows)}
        </tbody>
      </table>
      <script>
        const table = document.getElementById("detail-table");
        const tbody = table.querySelector("tbody");
        const headers = Array.from(table.querySelectorAll("th"));
        const baseLabels = headers.map((header) => header.textContent.replace(/[↕▲▼]/g, "").trim());
        let current = "collocation";
        let direction = "asc";

        function sortRows(field, type) {{
          if (current === field) {{
            direction = direction === "asc" ? "desc" : "asc";
          }} else {{
            current = field;
            direction = "asc";
          }}
          const rows = Array.from(tbody.querySelectorAll("tr"));
          rows.sort((a, b) => {{
            let av = a.dataset[field] || "";
            let bv = b.dataset[field] || "";
            if (type === "number") {{
              av = Number(av);
              bv = Number(bv);
            }}
            if (av < bv) return direction === "asc" ? -1 : 1;
            if (av > bv) return direction === "asc" ? 1 : -1;
            return 0;
          }});
          rows.forEach((row) => tbody.appendChild(row));
          headers.forEach((header, index) => {{
            const suffix = header.dataset.sort === current ? (direction === "asc" ? " ▲" : " ▼") : " ↕";
            header.textContent = baseLabels[index] + suffix;
          }});
        }}

        headers.forEach((header) => {{
          header.addEventListener("click", () => {{
            sortRows(header.dataset.sort, header.dataset.type);
          }});
        }});
      </script>
    </body>
    </html>
    """
    height = min(760, 58 * len(rows) + 76)
    components.html(table_html, height=height, scrolling=len(rows) > 11)


def render_group_row(
    group: SemanticGroup,
    dataset: Dataset,
    group_level_lookup: GroupLevelLookup,
    key_prefix: str,
    row_number: int,
) -> None:
    members = ordered_group_members(group, dataset)
    collocates = html.escape(group_collocates_text(group, dataset))
    representative_level = representative_group_level(
        group,
        dataset,
        group_level_lookup,
    )
    button_key = (
        f"{key_prefix}:detail:{group.headword}:{group.semantic_tag}:"
        f"{group.structure}:{group.collocate_side}"
    )
    state_key = f"{button_key}:open"
    st.markdown("<div class='streamlit-row-rule'></div>",
                unsafe_allow_html=True)
    row_widths = (
        [2.4, 0.5, 1, 0.55, 1, 0.48]
        if group.collocate_side == "word1_list"
        else [0.7, 2.2, 1, 0.55, 1, 0.48]
    )
    row = st.columns(row_widths)
    if group.collocate_side == "word1_list":
        row[0].markdown(
            f"<div class='collocates'>{collocates}</div>",
            unsafe_allow_html=True,
        )
        row[1].markdown(
            f"<div class='headword'>{html.escape(group_headword_text(group, dataset))}</div>",
            unsafe_allow_html=True,
        )
    else:
        row[0].markdown(
            f"<div class='headword'>{html.escape(group_headword_text(group, dataset))}</div>",
            unsafe_allow_html=True,
        )
        row[1].markdown(
            f"<div class='collocates'>{collocates}</div>",
            unsafe_allow_html=True,
        )
    row[2].markdown(
        f"<div class='semantic-tag'>{html.escape(group.semantic_tag)}</div>",
        unsafe_allow_html=True,
    )
    row[3].markdown(level_badge_html(representative_level),
                    unsafe_allow_html=True)
    row[4].markdown(
        f"<div class='pos-pattern'>{structure_to_pos_pattern(group.structure)}</div>",
        unsafe_allow_html=True,
    )
    with row[5]:
        st.markdown("<div class='detail-cell'>", unsafe_allow_html=True)
        if st.button("Details", key=button_key, use_container_width=True):
            st.session_state[state_key] = not st.session_state.get(
                state_key, False)
        st.markdown("</div>", unsafe_allow_html=True)
    if st.session_state.get(state_key, False):
        render_detail_panel(
            group,
            dataset,
            f"{button_key}:sort",
            representative_level,
        )


def render_groups_section(
    title: str,
    indices: Sequence[int],
    dataset: Dataset,
    group_level_lookup: GroupLevelLookup,
    selected_levels: Sequence[str],
    key_prefix: str,
    collocate_side: str = "word2",
) -> None:
    selected_level_set = set(selected_levels)
    all_groups = build_semantic_groups(indices, dataset, collocate_side)
    groups = [
        group for group in all_groups
        if representative_group_level(group, dataset, group_level_lookup)
        in selected_level_set
    ]
    sort_namespace = f"{key_prefix}:groups"
    collocation_count = sum(len(group.indices) for group in groups)

    st.markdown(
        f"<div class='result-meta'><strong>{html.escape(title)}</strong> · "
        f"{len(groups):,} groups · {collocation_count:,} collocations"
        + (f" · showing first {GROUP_LIMIT:,}" if len(groups)
           > GROUP_LIMIT else "")
        + "</div>",
        unsafe_allow_html=True,
    )
    if not groups:
        st.info("No semantic groups matched the selected filters.")
        return

    render_group_header(sort_namespace, collocate_side)
    shown_groups = sorted_semantic_groups(
        groups,
        dataset,
        sort_namespace,
        group_level_lookup,
    )[:GROUP_LIMIT]
    for row_number, group in enumerate(shown_groups):
        render_group_row(group, dataset, group_level_lookup,
                         key_prefix, row_number)


def clear_results() -> None:
    for key in (
        "evp_style_query",
        "evp_style_levels",
        "evp_style_guideword",
        "evp_style_pos",
    ):
        st.session_state.pop(key, None)
    for key in list(st.session_state):
        if key.startswith("first:detail:") or key.startswith("second:detail:"):
            st.session_state.pop(key, None)


def main() -> None:
    st.set_page_config(
        page_title="English Collocation Profile Online", layout="wide")
    render_styles()
    st.markdown(
        "<h1 class='ecp-title'>English Collocation Profile Online</h1>",
        unsafe_allow_html=True,
    )

    path = resolve_data_path()
    if not path.is_file():
        st.error(f"ECP dataset not found: {path}")
        st.stop()

    try:
        dataset = load_dataset(str(path), path.stat().st_mtime_ns)
        group_level_lookup = build_group_level_lookup(
            str(path),
            path.stat().st_mtime_ns,
        )
        all_guidewords = guideword_options(str(path), path.stat().st_mtime_ns)
    except Exception as error:  # noqa: BLE001
        st.error(f"Could not load the ECP dataset. {error}")
        st.stop()

    default_levels = st.session_state.get("evp_style_levels", LEVELS)
    default_guideword = st.session_state.get(
        "evp_style_guideword", GUIDEWORD_PLACEHOLDER)
    default_pos = st.session_state.get("evp_style_pos", POS_PLACEHOLDER)

    # st.markdown("<div class='search-panel'>", unsafe_allow_html=True)
    query_col, label_col, levels_col = st.columns([4.2, 0.75, 3.1])
    if (
        "evp_style_query_input" not in st.session_state
        and "evp_style_query" in st.session_state
    ):
        st.session_state["evp_style_query_input"] = st.session_state[
            "evp_style_query"
        ]
    with query_col:
        raw_query = st.text_area(
            "Search word or short text",
            key="evp_style_query_input",
            placeholder="Search...",
            height=72,
            label_visibility="collapsed",
        )
    with label_col:
        st.markdown("<div class='level-caption'>Levels</div>",
                    unsafe_allow_html=True)
    with levels_col:
        selected_levels = render_level_controls(default_levels)

    guide_col, pos_col = st.columns([1.2, 1.0])
    with guide_col:
        st.markdown("<div class='filter-label'>Guideword</div>",
                    unsafe_allow_html=True)
        guideword_values = (GUIDEWORD_PLACEHOLDER, *all_guidewords)
        selected_guideword = st.selectbox(
            "Guideword",
            guideword_values,
            index=guideword_values.index(default_guideword)
            if default_guideword in guideword_values
            else 0,
            label_visibility="collapsed",
        )
    with pos_col:
        st.markdown("<div class='filter-label'>Part of Speech</div>",
                    unsafe_allow_html=True)
        pos_values = (POS_PLACEHOLDER, *POS_OPTIONS.keys())
        selected_pos = st.selectbox(
            "Part of Speech",
            pos_values,
            index=pos_values.index(default_pos)
            if default_pos in pos_values
            else 0,
            label_visibility="collapsed",
        )

    submitted = st.button("Search", type="primary", use_container_width=True)
    st.markdown("</div>", unsafe_allow_html=True)

    query = raw_query.strip()
    if submitted:
        if not query:
            st.warning("Enter a core word or paste a short text first.")
            st.stop()
        st.session_state["evp_style_query"] = query
        st.session_state["evp_style_levels"] = selected_levels
        st.session_state["evp_style_guideword"] = selected_guideword
        st.session_state["evp_style_pos"] = selected_pos
    elif st.session_state.get("evp_style_query"):
        query = str(st.session_state["evp_style_query"])
    else:
        st.info("Enter a core word to explore ECP collocation groups.")
        return

    if not selected_levels:
        st.warning("Select at least one CEFR level.")
        return

    keyword = normalize_word(query)
    if is_text_search(query):
        all_indices = find_text_matches(dataset, query)
        first_selected = filter_indices(
            all_indices, dataset, selected_guideword, selected_pos)
        second_selected: List[int] = []
        title = "Collocation groups found in your text"
    else:
        first_all, second_all = find_word_matches(dataset, keyword)
        first_selected = filter_indices(
            first_all, dataset, selected_guideword, selected_pos)
        second_selected = filter_indices(
            second_all, dataset, selected_guideword, selected_pos)
        title = f"{keyword} + word"

    total = len(first_selected) + len(second_selected)
    if total == 0:
        st.info("No collocation groups matched this search and filter selection.")
        return

    render_groups_section(title, first_selected, dataset,
                          group_level_lookup, selected_levels, "first")
    if second_selected:
        render_groups_section(
            f"word + {keyword}",
            second_selected,
            dataset,
            group_level_lookup,
            selected_levels,
            "second",
            collocate_side="word1_list",
        )


if __name__ == "__main__":
    main()
