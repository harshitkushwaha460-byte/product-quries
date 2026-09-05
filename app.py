import streamlit as st
import re

from rag_engine import (
    ask_bis_api,
    reset_conversation,
    get_source_url
)


st.set_page_config(
    page_title="BIS Sahayak",
    layout="centered"
)


st.markdown("""
<style>

.main-title {
    text-align: center;
    font-size: 38px;
    font-weight: 700;
    margin-top: 10px;
    margin-bottom: 4px;
}

.subtitle {
    text-align: center;
    color: #888;
    font-size: 16px;
    margin-bottom: 28px;
}

.answer-box {
    padding: 18px;
    border-radius: 14px;
    border: 1px solid #777;
    background: #000000;
    line-height: 1.7;
    margin-bottom: 15px;
}

.source-card {
    padding: 16px;
    border-radius: 12px;
    border: 1px solid #444;
    background: #111111;
    margin-top: 10px;
    margin-bottom: 10px;
}

.follow-title {
    font-size: 18px;
    font-weight: 600;
    margin-top: 20px;
    margin-bottom: 10px;
}

</style>
""", unsafe_allow_html=True)


st.markdown(
    '<div class="main-title">BIS Sahayak</div>',
    unsafe_allow_html=True
)

st.markdown(
    '<div class="subtitle">'
    'AI-powered assistant for Indian Standards and BIS Services'
    '</div>',
    unsafe_allow_html=True
)


if "messages" not in st.session_state:
    st.session_state.messages = []

if "pending_question" not in st.session_state:
    st.session_state.pending_question = None


with st.sidebar:

    st.header("BIS Sahayak")

    st.write(
        "Ask questions about Indian Standards, "
        "BIS certification, licences, testing "
        "and laboratories."
    )

    st.divider()

    if st.button(
        "🗑️ Clear Chat",
        use_container_width=True
    ):

        st.session_state.messages = []

        st.session_state.pending_question = None

        reset_conversation()

        st.rerun()

    st.divider()

    st.caption(
        "✓ Source-backed information from the "
        "BIS knowledge base."
    )


def clean_answer(answer):

    if not answer:
        return ""


    answer = re.sub(
        r"\s*\[Source\s*\d+\]",
        "",
        answer,
        flags=re.IGNORECASE
    )


    answer = re.split(
        r"\n\s*Sources\s*:",
        answer,
        flags=re.IGNORECASE
    )[0]


    answer = re.sub(
        r"[,;]+\s*$",
        "",
        answer
    )

    return answer.strip()


def detect_app_query_type(question):

    q = question.lower()


    application_words = [
        "apply",
        "application",
        "how to apply",
        "apply for",
        "application process",
        "documents required",
        "manakonline",

        "आवेदन",
        "अप्लाई",
        "मैनकऑनलाइन"
    ]

    if any(
        word in q
        for word in application_words
    ):
        return "application"


    lab_words = [
        "lab",
        "labs",
        "laboratory",
        "laboratories",
        "testing laboratory",
        "recognized laboratory",

        "लैब",
        "प्रयोगशाला"
    ]

    if any(
        word in q
        for word in lab_words
    ):
        return "labs"


    test_words = [
        "test",
        "tests",
        "testing",
        "test method",
        "testing requirement",
        "testing requirements",
        "required test",
        "required tests",

        "परीक्षण",
        "टेस्ट",
        "जांच",
        "जाँच"
    ]

    if any(
        word in q
        for word in test_words
    ):
        return "tests"


    certification_words = [
        "certification",
        "certifications",
        "certificate",
        "certificates",
        "certify",
        "certified",
        "licence",
        "license",

        "प्रमाणपत्र",
        "सर्टिफिकेशन",
        "सर्टिफिकेट",
        "लाइसेंस"
    ]

    if any(
        word in q
        for word in certification_words
    ):
        return "certification"


    standard_words = [
        "standard",
        "standards",
        "is number",
        "which standard",
        "applicable standard",

        "मानक",
        "आईएस नंबर"
    ]

    if any(
        word in q
        for word in standard_words
    ):
        return "standard"

    return "general"


def extract_standard(text):

    if not text:
        return ""

    patterns = [

        r"\bIS\s+\d{3,6}:\d{4}\b",

        r"\bIS\s+\d{3,6}\b"
    ]

    for pattern in patterns:

        match = re.search(
            pattern,
            text,
            flags=re.IGNORECASE
        )

        if match:

            return match.group(0).upper()

    return ""


def normalize_standard(standard):

    if not standard:
        return ""

    standard = standard.strip().upper()

    if standard.startswith("IS 14543"):
        return "IS 14543:2024"

    if standard.startswith("IS 13428"):
        return "IS 13428:2024"

    if standard.startswith("IS 4151"):
        return "IS 4151:2015"

    if standard.startswith("IS 9873"):
        return "IS 9873"

    if standard.startswith("IS 16102"):
        return "IS 16102"

    if standard.startswith("IS 10325:2026"):
        return "IS 10325:2026"

    if standard.startswith("IS 10325"):
        return "IS 10325:2000"

    if standard.startswith("IS 1011"):
        return "IS 1011:2002"

    return standard


def get_result_standard(
    result,
    answer,
    question
):


    standard = result.get(
        "standard",
        ""
    )

    if standard:

        return normalize_standard(
            standard
        )


    standard = extract_standard(
        answer
    )

    if standard:

        return normalize_standard(
            standard
        )


    standard = extract_standard(
        question
    )

    if standard:

        return normalize_standard(
            standard
        )


    for message in reversed(
        st.session_state.messages
    ):

        if message.get("role") != "assistant":
            continue

        previous_answer = message.get(
            "answer",
            ""
        )

        standard = extract_standard(
            previous_answer
        )

        if standard:

            return normalize_standard(
                standard
            )

    return ""


def is_manakonline_query(
    question,
    query_type
):

    q = question.lower().strip()

    application_words = [
        "apply",
        "application",
        "apply for",
        "how to apply",
        "application process",
        "manakonline",

        "आवेदन",
        "आवेदन कैसे",
        "कैसे आवेदन",
        "कैसे अप्लाई",
        "मैनकऑनलाइन"
    ]

    certification_words = [
        "certification",
        "certifications",
        "certificate",
        "certificates",
        "certify",
        "certified",
        "licence",
        "license",

        "सर्टिफिकेशन",
        "सर्टिफिकेट",
        "प्रमाणपत्र",
        "लाइसेंस"
    ]

    has_application = any(
        word in q
        for word in application_words
    )

    has_certification = any(
        word in q
        for word in certification_words
    )


    if (
        has_application
        and has_certification
    ):
        return True


    if query_type == "application":
        return True

    return False


def get_correct_source_url(
    result,
    standard,
    query_type
):


    source_url = result.get(
        "source_url",
        ""
    )

    if source_url:
        return source_url


    if standard:

        source_url = get_source_url(
            standard,
            query_type
        )

        if source_url:
            return source_url


    if standard:

        return get_source_url(
            standard,
            "standard"
        )

    return ""


def prepare_sources(
    result,
    question,
    answer
):


    rag_query_type = result.get(
        "query_type",
        ""
    )

    detected_query_type = detect_app_query_type(
        question
    )

    if detected_query_type != "general":

        query_type = detected_query_type

    elif rag_query_type:

        query_type = rag_query_type

    else:

        query_type = "general"


    standard = get_result_standard(
        result,
        answer,
        question
    )

    sources = []


    if standard:

        source_url = get_correct_source_url(
            result,
            standard,
            query_type
        )

        if source_url:


            if query_type == "standard":

                document = (
                    f"BIS Standard – {standard}"
                )

            elif query_type == "tests":

                document = (
                    f"BIS Testing Information – {standard}"
                )

            elif query_type == "labs":

                document = (
                    f"BIS Laboratory Information – {standard}"
                )

            elif query_type == "certification":

                document = (
                    f"BIS Certification – {standard}"
                )

            elif query_type == "application":

                document = (
                    f"BIS Application Information – {standard}"
                )

            else:

                document = (
                    f"Official BIS Source – {standard}"
                )

            sources.append({

                "document":
                    document,

                "location":
                    query_type,

                "standard":
                    standard,

                "url":
                    source_url
            })


    for source in result.get(
        "sources",
        []
    ):

        if not isinstance(
            source,
            dict
        ):
            continue

        document = source.get(
            "document",
            source.get(
                "source_document",
                ""
            )
        )

        location = source.get(
            "location",
            source.get(
                "source_location",
                ""
            )
        )

        url = source.get(
            "url",
            source.get(
                "source_url",
                ""
            )
        )

        if not url:
            continue

        sources.append({

            "document":
                document,

            "location":
                location,

            "standard":
                source.get(
                    "standard",
                    standard
                ),

            "url":
                url
        })


    if is_manakonline_query(
        question,
        query_type
    ):

        sources.append({

            "document":
                "Manakonline – BIS Online Application Portal",

            "location":
                "Online BIS application",

            "standard":
                standard,

            "url":
                "https://www.manakonline.in"
        })

    return sources


def remove_duplicate_sources(
    sources
):

    unique = []

    seen = set()

    for source in sources:

        if not isinstance(
            source,
            dict
        ):
            continue

        url = source.get(
            "url",
            ""
        )

        if not url:
            continue

        if url in seen:
            continue

        seen.add(url)

        unique.append(
            source
        )

    return unique


def show_sources(
    sources
):

    if not sources:
        return

    sources = remove_duplicate_sources(
        sources
    )

    if not sources:
        return


    st.markdown(
        "### 📚 Sources"
    )


    for source in sources:

        document = source.get(
            "document",
            "Official BIS Source"
        )

        location = source.get(
            "location",
            ""
        )

        url = source.get(
            "url",
            ""
        )

        if not url:
            continue


        if "manakonline.in" in url.lower():

            with st.container(
                border=True
            ):

                st.markdown(
                    "### 🚀 Manakonline"
                )

                st.caption(
                    "BIS Online Application Portal"
                )

                st.link_button(
                    "🚀 Open Manakonline",
                    url,
                    use_container_width=True
                )


        else:

            with st.container(
                border=True
            ):

                st.markdown(
                    f"**{document}**"
                )

                if location:

                    st.caption(
                        f"Type: {location}"
                    )

                st.link_button(
                    "🔗 Open official BIS source",
                    url,
                    use_container_width=True
                )


def get_follow_up_questions(
    question,
    answer
):

    q = question.lower()


    if any(
        word in q
        for word in [
            "apply",
            "application",
            "how to apply",
            "apply for",
            "manakonline",
            "आवेदन",
            "अप्लाई"
        ]
    ):

        return [

            "📄 What documents are required?",

            "🧪 What tests are required?",

            "🔬 Which laboratories can test it?",

            "📘 What is the applicable standard?"
        ]


    if any(
        word in q
        for word in [
            "test",
            "tests",
            "testing",
            "test method",
            "testing requirement",
            "required test",
            "required tests",
            "परीक्षण",
            "टेस्ट"
        ]
    ):

        return [

            "🔬 Which laboratories can perform these tests?",

            "🏭 How do I apply for BIS certification?",

            "📘 What is the applicable standard?",

            "📄 What documents are required?"
        ]


    if any(
        word in q
        for word in [
            "lab",
            "labs",
            "laboratory",
            "laboratories",
            "testing laboratory",
            "recognized laboratory",
            "प्रयोगशाला",
            "लैब"
        ]
    ):

        return [

            "🧪 What tests are required?",

            "📘 What is the applicable standard?",

            "🏭 How do I apply for BIS certification?",

            "📄 What documents are required?"
        ]


    if any(
        word in q
        for word in [
            "certification",
            "certificate",
            "certify",
            "certified",
            "licence",
            "license",
            "प्रमाणपत्र",
            "सर्टिफिकेशन",
            "लाइसेंस"
        ]
    ):

        return [

            "🏭 How do I apply for BIS certification?",

            "📄 What documents are required?",

            "🧪 What tests are required?",

            "🔬 Which laboratories can test it?"
        ]


    if any(
        word in q
        for word in [
            "standard",
            "standards",
            "is number",
            "which standard",
            "applicable standard",
            "मानक",
            "आईएस नंबर"
        ]
    ):

        return [

            "🧪 What tests are required?",

            "🔬 Which laboratories can test it?",

            "🏭 How do I apply for BIS certification?",

            "📄 What documents are required?"
        ]


    return [

        "📘 What is the applicable standard?",

        "🧪 What tests are required?",

        "🏭 How do I apply for BIS certification?",

        "🔬 Which laboratories can test it?"
    ]


def handle_follow_up_click(
    follow_up
):

    clean_question = re.sub(
        r"^[^\w]+",
        "",
        follow_up
    ).strip()

    st.session_state.pending_question = (
        clean_question
    )

    st.rerun()


def show_follow_up_questions(
    question,
    answer,
    message_index
):

    follow_ups = get_follow_up_questions(
        question,
        answer
    )

    if not follow_ups:
        return

    st.markdown(
        '<div class="follow-title">'
        '💡 You may also want to know'
        '</div>',
        unsafe_allow_html=True
    )


    col1, col2 = st.columns(2)

    for i, follow_up in enumerate(
        follow_ups
    ):

        if i % 2 == 0:

            with col1:

                if st.button(
                    follow_up,
                    key=f"follow_{message_index}_{i}",
                    use_container_width=True
                ):

                    handle_follow_up_click(
                        follow_up
                    )

        else:

            with col2:

                if st.button(
                    follow_up,
                    key=f"follow_{message_index}_{i}",
                    use_container_width=True
                ):

                    handle_follow_up_click(
                        follow_up
                    )


for index, message in enumerate(
    st.session_state.messages
):

    with st.chat_message(
        message["role"]
    ):


        if message["role"] == "user":

            st.markdown(
                message["content"]
            )


        else:

            st.markdown(
                f'<div class="answer-box">'
                f'{message["answer"]}'
                f'</div>',
                unsafe_allow_html=True
            )


            show_sources(
                message.get(
                    "sources",
                    []
                )
            )


            if message.get(
                "follow_ups"
            ):

                show_follow_up_questions(
                    message.get(
                        "original_question",
                        ""
                    ),
                    message.get(
                        "answer",
                        ""
                    ),
                    index
                )


question = st.chat_input(
    "Ask your question about BIS..."
)


if st.session_state.pending_question:

    question = (
        st.session_state.pending_question
    )

    st.session_state.pending_question = None


if question:


    st.session_state.messages.append({

        "role":
            "user",

        "content":
            question
    })

    with st.chat_message("user"):

        st.markdown(
            question
        )


    with st.chat_message("assistant"):

        with st.spinner(
            "Finding BIS information..."
        ):

            try:


                result = ask_bis_api(
                    question
                )


                answer = result.get(
                    "answer",
                    "I could not verify this information "
                    "from the available BIS sources."
                )

                answer = clean_answer(
                    answer
                )


                st.markdown(
                    f'<div class="answer-box">'
                    f'{answer}'
                    f'</div>',
                    unsafe_allow_html=True
                )


                sources = prepare_sources(
                    result,
                    question,
                    answer
                )


                show_sources(
                    sources
                )


                follow_ups = (
                    get_follow_up_questions(
                        question,
                        answer
                    )
                )

                show_follow_up_questions(
                    question,
                    answer,
                    len(
                        st.session_state.messages
                    )
                )


                st.session_state.messages.append({

                    "role":
                        "assistant",

                    "answer":
                        answer,

                    "sources":
                        sources,

                    "original_question":
                        question,

                    "follow_ups":
                        follow_ups
                })


            except Exception as e:

                error_message = (
                    "Sorry, I could not process "
                    "your question right now."
                )

                st.error(
                    error_message
                )

                print(
                    "APP ERROR:",
                    repr(e)
                )

                st.session_state.messages.append({

                    "role":
                        "assistant",

                    "answer":
                        error_message,

                    "sources":
                        [],

                    "original_question":
                        question,

                    "follow_ups":
                        []
                })
