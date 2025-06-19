import streamlit as st
import pandas as pd
from databricks import sql
import os
from dotenv import load_dotenv
from datetime import datetime
import plotly.express as px
import re

# Load environment variables
load_dotenv()

# Page config & header
st.set_page_config(page_title="Shuttlers AI Analytics", page_icon="🚘", layout="wide")
st.markdown('<h1 class="main-header">🚘 Shuttlers AI Analytics Dashboard</h1>', unsafe_allow_html=True)

# CSS styling
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 2rem;
    }
</style>
""", unsafe_allow_html=True)

# Databricks connection class
class DatabricksConnector:
    def __init__(self):
        self.connection = None
        self.cursor = None

    def connect_from_env(self):
        try:
            server_hostname = os.getenv('DATABRICKS_SERVER_HOSTNAME')
            http_path = os.getenv('DATABRICKS_HTTP_PATH')
            access_token = os.getenv('DATABRICKS_TOKEN')
            if not all([server_hostname, http_path, access_token]):
                st.error("Missing Databricks credentials in environment.")
                return False
            return self.connect(server_hostname, http_path, access_token)
        except Exception as e:
            st.error(f"Environment connection failed: {str(e)}")
            return False

    def connect(self, server_hostname, http_path, access_token):
        try:
            self.connection = sql.connect(server_hostname=server_hostname, http_path=http_path, access_token=access_token)
            self.cursor = self.connection.cursor()
            return True
        except Exception as e:
            st.error(f"Connection failed: {str(e)}")
            return False

    def clean_sql_query(self, query):
        if not query:
            return ""
        query = re.sub(r'^```(?:sql)?\s*', '', query.strip(), flags=re.IGNORECASE)
        query = re.sub(r'\s*```$', '', query, flags=re.IGNORECASE)
        query = re.sub(r'^Generated SQL:\s*', '', query, flags=re.IGNORECASE)
        return query.strip()

    def execute_query(self, query):
        try:
            if not self.cursor:
                st.error("No database connection established")
                return None
            clean_query = self.clean_sql_query(query)
            self.cursor.execute(clean_query)
            columns = [desc[0] for desc in self.cursor.description]
            results = self.cursor.fetchall()
            return pd.DataFrame(results, columns=columns) if results else pd.DataFrame()
        except Exception as e:
            st.error(f"Query execution failed: {str(e)}")
            return None

    def get_ai_query(self, question):
        try:
            escaped_question = question.replace("'", "''")
            ai_query = f"SELECT agent.ai.shuttlers_insight('{escaped_question}') as generated_query"
            if not self.cursor:
                st.error("No database connection established")
                return None
            self.cursor.execute(ai_query)
            results = self.cursor.fetchall()
            return self.clean_sql_query(results[0][0]) if results else None
        except Exception as e:
            st.error(f"AI query generation failed: {str(e)}")
            return None

    def close(self):
        if self.cursor:
            self.cursor.close()
        if self.connection:
            self.connection.close()

# Main app
def main():
    # Connection init
    if 'db_connector' not in st.session_state:
        st.session_state.db_connector = DatabricksConnector()
    if 'connected' not in st.session_state:
        st.session_state.connected = False

    if not st.session_state.connected:
        with st.spinner("Connecting to Databricks..."):
            if st.session_state.db_connector.connect_from_env():
                st.session_state.connected = True

    # Reset session state if switching away from AI tab
    if st.session_state.get("active_tab") != "ai":
        st.session_state.pop("generated_sql", None)
        st.session_state.pop("selected_question", None)

    if st.session_state.connected:
        tab1, tab2, tab3 = st.tabs(["🤖 AI Query Assistant", "📊 Quick Analytics", "🔍 Custom SQL"])

        with tab1:
            st.session_state.active_tab = "ai"
            question = st.text_area("What would you like to know?", value=st.session_state.get('selected_question', ''), height=100)
            if st.button("🔮 Generate Query") and question:
                with st.spinner("Generating SQL query..."):
                    generated_sql = st.session_state.db_connector.get_ai_query(question)
                    st.session_state.generated_sql = generated_sql
                    st.session_state.selected_question = question
                    if generated_sql:
                        st.success("✅ SQL query generated.")
                    else:
                        st.error("❌ Failed to generate SQL.")

            if st.session_state.get("generated_sql"):
                st.subheader("Generated SQL Query:")
                st.code(st.session_state.generated_sql, language="sql")
                if st.button("▶️ Execute Query"):
                    with st.spinner("Executing query..."):
                        results = st.session_state.db_connector.execute_query(st.session_state.generated_sql)
                        if results is not None and not results.empty:
                            st.subheader("Query Results:")
                            st.dataframe(results, use_container_width=True)
                            csv = results.to_csv(index=False)
                            st.download_button("📥 Download Results", data=csv, file_name="results.csv", mime="text/csv")
                        elif results is not None:
                            st.info("✅ Query executed, but returned no results.")

        with tab2:
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                if st.button("📊 Total Rides Today"):
                    q = "SELECT COUNT(*) as total_rides FROM agent.shuttler.ride_bookings WHERE DATE(ScheduledTime) = CURRENT_DATE()"
                    r = st.session_state.db_connector.execute_query(q)
                    if r is not None and not r.empty:
                        st.metric("Total Rides Today", r.iloc[0]['total_rides'])

            with col2:
                if st.button("💰 Today's Revenue"):
                    q = "SELECT SUM(Fare) as revenue FROM agent.shuttler.ride_bookings WHERE DATE(ScheduledTime) = CURRENT_DATE() AND Status = 'completed'"
                    r = st.session_state.db_connector.execute_query(q)
                    if r is not None and not r.empty:
                        st.metric("Today's Revenue", f"₦{r.iloc[0]['revenue']:,.2f}")

            with col3:
                if st.button("👥 Active Users"):
                    q = "SELECT COUNT(DISTINCT UserID) as active_users FROM agent.shuttler.ride_bookings WHERE DATE(ScheduledTime) >= DATE_SUB(CURRENT_DATE(), 7)"
                    r = st.session_state.db_connector.execute_query(q)
                    if r is not None and not r.empty:
                        st.metric("Active Users (7 days)", r.iloc[0]['active_users'])

            with col4:
                if st.button("⭐ Avg Rating"):
                    q = "SELECT AVG(Rating) as avg_rating FROM agent.shuttler.feedback WHERE DATE(Timestamp) >= DATE_SUB(CURRENT_DATE(), 30)"
                    r = st.session_state.db_connector.execute_query(q)
                    if r is not None and not r.empty:
                        st.metric("Avg Rating (30 days)", f"{r.iloc[0]['avg_rating']:.2f}")

        with tab3:
            sql_query = st.text_area("Enter your SQL query:", height=200)
            if st.button("Execute Custom Query") and sql_query.strip():
                with st.spinner("Executing query..."):
                    results = st.session_state.db_connector.execute_query(sql_query)
                    if results is not None and not results.empty:
                        st.subheader("Query Results:")
                        st.dataframe(results, use_container_width=True)
                    elif results is not None:
                        st.info("✅ Query ran, but returned no results.")
    else:
        st.warning("Please connect to your Databricks workspace using the sidebar to begin.")

if __name__ == "__main__":
    main()
