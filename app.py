import streamlit as st
import requests
import pandas as pd
import plotly.express as px

st.set_page_config(
    page_title="InterviewPilot AI",
    page_icon="🚀",
    layout="wide"
)

st.title("🚀 InterviewPilot AI")
st.subheader("LeetCode Interview Readiness Analyzer")

@st.cache_data(ttl=3600)
def fetch_leetcode(username):
    query = """
    query getUserProfile($username: String!) {
      matchedUser(username: $username) {
        submitStats: submitStatsGlobal {
          acSubmissionNum {
            difficulty
            count
          }
        }
        tagProblemCounts {
          fundamental {
            tagName
            problemsSolved
          }
          intermediate {
            tagName
            problemsSolved
          }
        }
      }
    }
    """

    response = requests.post(
        "https://leetcode.com/graphql",
        json={
            "query": query,
            "variables": {"username": username}
        }
    )

    data = response.json()
    user = data["data"]["matchedUser"]

    solved = {
        item["difficulty"]: item["count"]
        for item in user["submitStats"]["acSubmissionNum"]
    }

    topics = []

    for section in ["fundamental", "intermediate"]:
        for item in user["tagProblemCounts"][section]:
            topics.append({
                "topic": item["tagName"],
                "solved": item["problemsSolved"]
            })

    return solved, pd.DataFrame(topics)

username = st.text_input("Enter LeetCode username")

if st.button("Import Stats") and username:
    try:
        solved, df = fetch_leetcode(username)

        easy = solved.get("Easy", 0)
        medium = solved.get("Medium", 0)
        hard = solved.get("Hard", 0)

        col1, col2, col3 = st.columns(3)

        col1.metric("Easy", easy)
        col2.metric("Medium", medium)
        col3.metric("Hard", hard)

        # Readiness score
        readiness = min(100, int(
            easy * 0.15 +
            medium * 0.45 +
            hard * 0.25
        ))

        st.markdown("---")
        st.subheader("🎯 Readiness Score")

        col1, col2 = st.columns([3, 1])

        with col1:
            st.progress(readiness / 100)

        with col2:
            st.metric("Score", f"{readiness}/100")

        if readiness >= 80:
            st.success("🔥 Strong candidate for medium-level coding interviews")
        elif readiness >= 60:
            st.warning("⚡ Good progress. Focus on weak topics to improve")
        else:
            st.error("📚 Build stronger foundations before mock interviews")

        # Weak topics
        st.markdown("---")
        st.subheader("📉 Weak Topics")

        df = df.sort_values("solved")
        weakest = df.head(5)

        fig = px.bar(
            weakest,
            x="topic",
            y="solved",
            title="Topics with Lowest Solved Count"
        )

        st.plotly_chart(fig, use_container_width=True)

        # Radar chart
        st.markdown("---")
        st.subheader("🕸️ Topic Radar Chart")

        top_topics = df.sort_values("solved", ascending=False).head(6)

        radar_fig = px.line_polar(
            top_topics,
            r="solved",
            theta="topic",
            line_close=True
        )

        radar_fig.update_traces(fill="toself")

        st.plotly_chart(radar_fig, use_container_width=True)

        # Study plan
        st.markdown("---")
        st.subheader("📅 Personalized 7-Day Study Plan")

        study_hours = 3

        for day, (_, row) in enumerate(weakest.iterrows(), start=1):
            st.info(
                f"Day {day}: {row['topic']} • Practice for {study_hours} hours • Solve 3 Easy + 2 Medium problems"
            )

        st.success("Reserve Day 7 for a full 30-minute mock interview and revision.")

        # Company recommendations
        st.markdown("---")
        st.subheader("🏢 Company-wise Recommendations")

        company_focus = {
            "Amazon": ["Graph", "Heap", "Sliding Window"],
            "Google": ["DP", "Graph", "Binary Search"],
            "Infosys": ["Array", "String", "Hashing"],
            "Microsoft": ["Tree", "DP", "Graph"]
        }

        weak_topic_names = weakest["topic"].tolist()

        for company, topics in company_focus.items():
            matching = [t for t in topics if t in weak_topic_names]

            if matching:
                st.warning(f"{company}: Focus on {', '.join(matching)}")
            else:
                st.success(f"{company}: You are doing well in the main focus areas")

        # Mock interview
        st.markdown("---")
        st.subheader("🎤 Mock Interview Simulator")

        if st.button("Start 30-min Mock Interview"):
            weak_topics = weakest["topic"].tolist()

            st.info("⏱️ 30 minutes started! Try solving these questions.")

            if "Dynamic Programming" in weak_topics or "DP" in weak_topics:
                st.write("Q1 (Medium - DP): House Robber")
            else:
                st.write("Q1 (Medium - Array): 3Sum")

            if "Graph" in weak_topics:
                st.write("Q2 (Medium - Graph): Number of Islands")
            else:
                st.write("Q2 (Easy - Tree): Maximum Depth of Binary Tree")

            st.write("Q3 (Easy - Stack): Valid Parentheses")

            st.success("After 30 minutes, review your solutions and time complexity.")

        # Strongest topics
        st.markdown("---")
        st.subheader("🏆 Strongest Topics")

        strongest = df.sort_values("solved", ascending=False).head(5)

        st.dataframe(strongest, use_container_width=True)

        pie_fig = px.pie(
            strongest,
            names="topic",
            values="solved",
            title="Top Topic Distribution"
        )

        st.plotly_chart(pie_fig, use_container_width=True)

    except Exception as e:
        st.error("Could not fetch data. Make sure the username is correct and the profile is public.")
        st.exception(e)

st.markdown("---")
st.caption("🚀 Built by Darpana S • InterviewPilot AI • 2026")