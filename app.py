import re, random
from collections import Counter
import fitz
import streamlit as st

st.set_page_config(page_title="LearnMate AI", page_icon="📚", layout="wide")

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700;800&display=swap');
html,body,[class*="css"]{font-family:Inter,sans-serif}
.stApp{background:linear-gradient(135deg,#eef2ff,#fdf2f8,#eff6ff)}
.block-container{max-width:1400px;padding-top:1.5rem}
[data-testid="stSidebar"]{background:linear-gradient(180deg,#171c48,#4338ca)}
[data-testid="stSidebar"] *{color:white}
.hero{padding:30px;border-radius:22px;background:linear-gradient(110deg,#4f46e5,#9333ea,#db2777);color:white;margin-bottom:22px}
.hero h1{color:white;font-weight:800;font-size:2.4rem}
.hero p{color:#f5f3ff}
.card{background:white;border:1px solid #e0e7ff;border-radius:17px;padding:20px;min-height:130px;box-shadow:0 5px 20px #4338ca0c}
.card h3{color:#4338ca;font-size:1.05rem}
.card p{color:#64748b;font-size:.9rem}
div[data-testid="stMetric"]{background:white;border:1px solid #e0e7ff;padding:15px;border-radius:14px}
div[data-testid="stMetricValue"]{color:#4f46e5;font-weight:800}
.stButton>button{border-radius:10px;font-weight:700}
.footer{text-align:center;color:#64748b;padding:25px}
</style>
""", unsafe_allow_html=True)

# ---------------- STATE ----------------

DEFAULTS = {
    "pages": [], "filename": "", "scores": [], "quiz": [],
    "result": None, "cards": [], "card": 0, "summary": ""
}
for k, v in DEFAULTS.items():
    if k not in st.session_state:
        st.session_state[k] = v

STOP = set("""
the a an and or but is are was were be been being to of in on
for from with by as at this that these those it its into about
than then their they them we you your our can could will would
should may might have has had do does did not no so if also
which who what when where why how all any each more most very
use used using one two three such only other same through
""".split())

def words(text):
    return [w for w in re.findall(r"\b[a-zA-Z][a-zA-Z0-9_-]*\b", text.lower())
            if w not in STOP and len(w) > 1]

def sentences(text):
    return [re.sub(r"\s+", " ", s).strip()
            for s in re.split(r"(?<=[.!?])\s+|\n+", text)
            if len(s.split()) >= 5]

def extract_pdf(file):
    try:
        with fitz.open(stream=file.getvalue(), filetype="pdf") as pdf:
            return [{"page": i, "text": p.get_text().strip()}
                    for i, p in enumerate(pdf, 1) if p.get_text().strip()]
    except Exception as e:
        st.error(f"PDF error: {e}")
        return []

def document():
    return "\n".join(p["text"] for p in st.session_state.pages)

def relevant(query, limit=6):
    q = set(words(query))
    results = []
    for p in st.session_state.pages:
        for s in sentences(p["text"]):
            overlap = q & set(words(s))
            if overlap:
                results.append((len(overlap) / max(len(q), 1), p["page"], s))
    return sorted(results, reverse=True)[:limit]

def summarize(text, limit=7):
    ss = sentences(text)
    if len(ss) <= limit:
        return "\n\n".join(ss) if ss else "No readable sentences found."
    freq = Counter(words(text))
    ranked = []
    for i, s in enumerate(ss):
        ws = words(s)
        score = sum(freq[w] for w in ws) / max(len(ws), 1)
        ranked.append((score, i, s))
    return "\n\n".join(s for _, _, s in sorted(
        sorted(ranked, reverse=True)[:limit], key=lambda x: x[1]))

def keywords(text, limit=15):
    return Counter(words(text)).most_common(limit)

def make_quiz(count=5):
    ss = sentences(document())
    pool = list(set(re.findall(r"\b[A-Za-z][A-Za-z0-9-]{3,}\b", document())))
    random.shuffle(ss)
    quiz, used = [], set()
    for s in ss:
        candidates = [w for w in re.findall(r"\b[A-Za-z][A-Za-z0-9-]*\b", s)
                      if len(w) >= 5 and w.lower() not in STOP and w.lower() not in used]
        if len(s.split()) < 7 or not candidates:
            continue
        answer = random.choice(candidates)
        question = re.sub(rf"\b{re.escape(answer)}\b", "________", s,
                          count=1, flags=re.I)
        distractors = [w for w in pool if w.lower() != answer.lower()]
        random.shuffle(distractors)
        opts, seen = [answer], {answer.lower()}
        for w in distractors:
            if w.lower() not in seen:
                opts.append(w)
                seen.add(w.lower())
            if len(opts) == 4:
                break
        if len(opts) < 4:
            continue
        random.shuffle(opts)
        quiz.append({"q": question, "a": answer, "opts": opts})
        used.add(answer.lower())
        if len(quiz) >= count:
            break
    return quiz

# ---------------- NAVIGATION ----------------

with st.sidebar:
    st.markdown("# 📚 LearnMate AI")
    st.caption("YOUR PERSONAL LEARNING SPACE")
    section = st.radio("NAVIGATION", [
        "🏠 Dashboard", "📂 Study Materials", "🤖 Study Assistant",
        "🧠 Topic Explorer", "📝 Smart Quiz", "🗂️ Flashcards",
        "📊 My Progress"
    ])
    st.markdown("---")
    st.caption("Learn • Practise • Improve")
    if st.session_state.pages:
        st.success(f"📄 {st.session_state.filename}")
        st.caption(f"{len(st.session_state.pages)} pages loaded")
    else:
        st.info("Upload a PDF to get started.")

# ---------------- DASHBOARD ----------------

if section == "🏠 Dashboard":
    scores = st.session_state.scores
    avg = round(sum(x["pct"] for x in scores) / len(scores)) if scores else 0
    st.markdown("""<div class="hero"><h1>📚 LearnMate AI</h1>
    <p>Your personalized learning assistant</p>
    <p>Explore your notes, discover key concepts, practise quizzes,
    and track your learning journey in one place.</p></div>""", unsafe_allow_html=True)
    a, b, c, d = st.columns(4)
    a.metric("📚 Material", "Ready" if st.session_state.pages else "Not uploaded")
    b.metric("📄 Pages", len(st.session_state.pages))
    c.metric("📝 Quizzes", len(scores))
    d.metric("🎯 Average", f"{avg}%")
    st.subheader("✨ Your Learning Toolkit")
    cols = st.columns(3)
    features = [
        ("📂 Study Materials", "Upload PDF notes and read extracted content."),
        ("🤖 Study Assistant", "Find relevant information with source pages."),
        ("🧠 Topic Explorer", "Discover frequently used terms in your notes."),
        ("📝 Smart Quiz", "Test your knowledge with practice questions."),
        ("🗂️ Flashcards", "Revise concepts with quick learning cards."),
        ("📊 Learning Analytics", "Track your scores and identify revision needs.")
    ]
    for i, (title, desc) in enumerate(features):
        with cols[i % 3]:
            st.markdown(f'<div class="card"><h3>{title}</h3><p>{desc}</p></div>',
                        unsafe_allow_html=True)
    st.markdown("### 🚀 Quick Start")
    st.write("1. Upload a PDF in Study Materials.")
    st.write("2. Review summaries and explore topics.")
    st.write("3. Ask questions using Study Assistant.")
    st.write("4. Generate quizzes and flashcards.")
    st.write("5. Monitor your results in My Progress.")

# ---------------- STUDY MATERIALS ----------------

elif section == "📂 Study Materials":
    st.title("📂 Study Materials")
    file = st.file_uploader("Upload your study PDF", type=["pdf"])
    if file and st.button("✨ Process PDF", type="primary"):
        with st.spinner("Extracting your notes..."):
            pages = extract_pdf(file)
        if pages:
            st.session_state.pages, st.session_state.filename = pages, file.name
            st.session_state.quiz, st.session_state.result = [], None
            st.session_state.cards, st.session_state.card = [], 0
            st.session_state.summary = ""
            st.success(f"Loaded {len(pages)} pages successfully.")
            st.rerun()
        else:
            st.warning("No selectable text found. Scanned PDFs need OCR.")
    if st.session_state.pages:
        text = document()
        a, b, c = st.columns(3)
        a.metric("Pages", len(st.session_state.pages))
        b.metric("Words", len(text.split()))
        c.metric("Reading Time", f"{max(1, round(len(text.split())/200))} min")
        st.info(f"Current file: {st.session_state.filename}")
        with st.expander("✨ Generate Summary"):
            n = st.slider("Summary sentences", 3, 15, 7)
            if st.button("Create Summary"):
                st.session_state.summary = summarize(text, n)
            if st.session_state.summary:
                st.write(st.session_state.summary)
                st.download_button("⬇️ Download Summary",
                                   st.session_state.summary,
                                   file_name="learnmate_summary.txt")
        p = st.selectbox("Read a page", st.session_state.pages,
                         format_func=lambda x: f"Page {x['page']}")
        st.text_area("Extracted text", p["text"], height=250, disabled=True)
        if st.button("🗑️ Remove PDF"):
            for k, v in {"pages": [], "filename": "", "quiz": [],
                         "result": None, "cards": [], "card": 0,
                         "summary": ""}.items():
                st.session_state[k] = v
            st.rerun()

# ---------------- STUDY ASSISTANT ----------------

elif section == "🤖 Study Assistant":
    st.title("🤖 Study Assistant")
    st.write("Search your uploaded notes and find relevant passages.")
    if not st.session_state.pages:
        st.info("Upload a PDF first.")
    else:
        with st.form("ask_form"):
            query = st.text_input("Ask about your notes",
                                  placeholder="Example: Explain embedded systems")
            ask = st.form_submit_button("🔍 Find Information", type="primary")
        if ask:
            matches = relevant(query)
            if matches:
                for i, (score, page, text) in enumerate(matches, 1):
                    with st.container(border=True):
                        st.markdown(f"**Relevant passage {i}**")
                        st.write(text)
                        st.caption(f"📄 Source: Page {page} · Match score: {score:.2f}")
            else:
                st.warning("No matching passages. Try other keywords.")
            st.caption("This prototype retrieves text by keyword overlap; it does not generate AI answers.")

# ---------------- TOPIC EXPLORER ----------------

elif section == "🧠 Topic Explorer":
    st.title("🧠 Topic Explorer")
    if not st.session_state.pages:
        st.info("Upload a PDF to discover important topics.")
    else:
        terms = keywords(document(), 30)
        st.subheader("📌 Frequent Terms")
        st.bar_chart({word: count for word, count in terms[:15]})
        st.markdown("### Explore a topic")
        topic = st.selectbox("Choose a keyword", [w for w, _ in terms])
        matches = relevant(topic, 8)
        for score, page, text in matches:
            st.markdown(f"**Page {page}**")
            st.write(text)
            st.divider()

# ---------------- SMART QUIZ ----------------

elif section == "📝 Smart Quiz":
    st.title("📝 Smart Quiz")
    if not st.session_state.pages:
        st.info("Upload a PDF before generating a quiz.")
    else:
        count = st.selectbox("Questions", [5, 10, 15])
        if st.button("🎯 Generate Quiz", type="primary"):
            st.session_state.quiz = make_quiz(count)
            st.session_state.result = None
            if not st.session_state.quiz:
                st.warning("Not enough suitable text. Try a longer PDF.")
        quiz = st.session_state.quiz
        if quiz:
            with st.form("quiz_form"):
                answers = {}
                for i, item in enumerate(quiz):
                    st.markdown(f"**Question {i+1}.** {item['q']}")
                    answers[str(i)] = st.radio("Select an answer", item["opts"],
                                               index=None, key=f"ans_{i}")
                    st.divider()
                submit = st.form_submit_button("✅ Submit Quiz", type="primary")
            if submit:
                score = sum(answers[str(i)] is not None and
                            answers[str(i)].lower() == item["a"].lower()
                            for i, item in enumerate(quiz))
                result = {"score": score, "total": len(quiz),
                          "pct": round(100*score/len(quiz)),
                          "file": st.session_state.filename}
                st.session_state.scores.append(result)
                st.session_state.result = result
            if st.session_state.result:
                r = st.session_state.result
                st.metric("Your Score", f"{r['score']}/{r['total']} ({r['pct']}%)")
                st.progress(r["pct"]/100)
                if r["pct"] < 50:
                    st.warning("Revise the basics and try another quiz.")
                elif r["pct"] < 80:
                    st.info("Good effort. Review the key concepts.")
                else:
                    st.success("Excellent! Try another topic.")
                with st.expander("📖 Review Correct Answers"):
                    for i, item in enumerate(quiz, 1):
                        st.write(f"{i}. {item['q']}")
                        st.write(f"Correct answer: {item['a']}")

# ---------------- FLASHCARDS ----------------

elif section == "🗂️ Flashcards":
    st.title("🗂️ Revision Flashcards")
    if not st.session_state.pages:
        st.info("Upload a PDF to create flashcards.")
    else:
        if st.button("✨ Generate Flashcards", type="primary"):
            text = document()
            freq = Counter(words(text))
            ss = sentences(text)
            random.shuffle(ss)
            cards, used = [], set()
            for s in ss:
                candidates = [w for w in re.findall(r"\b[A-Za-z][A-Za-z0-9_-]*\b", s)
                              if len(w) >= 5 and w.lower() not in STOP
                              and w.lower() in freq and w.lower() not in used]
                if not candidates:
                    continue
                answer = max(candidates, key=lambda w: (freq[w.lower()], len(w)))
                cards.append({"q": re.sub(rf"\b{re.escape(answer)}\b", "________",
                                         s, count=1, flags=re.I), "a": answer})
                used.add(answer.lower())
                if len(cards) == 20:
                    break
            st.session_state.cards, st.session_state.card = cards, 0
        cards = st.session_state.cards
        if cards:
            i = st.session_state.card
            st.progress((i+1)/len(cards))
            st.caption(f"Card {i+1} of {len(cards)}")
            with st.container(border=True):
                st.subheader("💡 Complete the sentence")
                st.write(cards[i]["q"])
                if st.button("👀 Reveal Answer", key=f"reveal_{i}"):
                    st.session_state[f"revealed_{i}"] = True
                if st.session_state.get(f"revealed_{i}", False):
                    st.success(f"Answer: {cards[i]['a']}")
            a, b = st.columns(2)
            if a.button("⬅️ Previous", disabled=i == 0):
                st.session_state.card -= 1
                st.rerun()
            if b.button("Next ➡️", disabled=i >= len(cards)-1):
                st.session_state.card += 1
                st.rerun()

# ---------------- PROGRESS ----------------

elif section == "📊 My Progress":
    st.title("📊 Learning Analytics")
    scores = st.session_state.scores
    if not scores:
        st.info("Complete a quiz to view your learning progress.")
    else:
        avg = round(sum(s["pct"] for s in scores)/len(scores))
        a, b, c, d = st.columns(4)
        a.metric("Quizzes", len(scores))
        b.metric("Average", f"{avg}%")
        c.metric("Best", f"{max(s['pct'] for s in scores)}%")
        d.metric("Latest", f"{scores[-1]['pct']}%")
        st.subheader("📈 Performance Trend")
        st.line_chart([s["pct"] for s in scores], x_label="Quiz", y_label="Score (%)")
        st.subheader("📚 Quiz History")
        for i, s in enumerate(reversed(scores), 1):
            with st.expander(f"Quiz {len(scores)-i+1} — {s['pct']}%"):
                st.write(f"Material: {s['file']}")
                st.write(f"Score: {s['score']}/{s['total']}")
        latest = scores[-1]["pct"]
        st.subheader("🎯 Recommendation")
        if latest < 50:
            st.warning("Revisit your notes and revise the fundamentals.")
        elif latest < 80:
            st.info("Review missed questions and practise again.")
        else:
            st.success("Strong performance! Continue with a new topic.")
        st.download_button("⬇️ Export Quiz Results",
                           "Quiz,Score,Total,Percentage\n" +
                           "\n".join(f"{i+1},{s['score']},{s['total']},{s['pct']}"
                                     for i, s in enumerate(scores)),
                           file_name="learnmate_results.csv", mime="text/csv")

st.markdown('<div class="footer">📚 LearnMate AI · Learn Smarter, Every Day</div>',
            unsafe_allow_html=True)