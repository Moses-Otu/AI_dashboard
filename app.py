import streamlit as st
import pandas as pd
from databricks import sql
import os
from dotenv import load_dotenv
from datetime import datetime
import plotly.express as px
import re

# Load environment variables from .env
load_dotenv()

# Page setup
st.set_page_config(page_title="Shuttlers AI Analytics", page_icon="🚘", layout="wide")
st.markdown('<h1 class="main-header">🚘 Shuttlers AI Analytics Dashboard</h1>', unsafe_allow_html=True)

# CSS Styling
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

# Databricks connection handler
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
            self.connection = sql.connect(
                server_hostname=server_hostname,
                http_path=http_path,
                access_token=access_token
            )
            self.cursor = self.connection.cursor()
            return True
        except Exception as e:
            st.error(f"Connection failed: {str(e)}")
            return False

    def clean_sql_query(self, query):
        """
        Clean markdown-style output to extract raw SQL.
        """
        if not query:
            return ""
        query = query.strip()
        query = query.replace("```sql", "").replace("```", "")
        query = re.sub(r'^\s*Generated SQL:\s*', '', query, flags=re.IGNORECASE)
        return query.strip().rstrip(';')

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

# App main function
def main():
    st.sidebar.title("📖 About")
    st.sidebar.markdown("""
### Democratization of Data
Empower everyone in the organization to ask data questions using natural language.

### Secured by Databricks
Data access is enforced with Databricks token auth and governed via workspace permissions.

### AI Powered Insights
This app uses Meta Llama 3.3 on Databricks to generate SQL from questions. No SQL skills needed!
    """)

    if 'db_connector' not in st.session_state:
        st.session_state.db_connector = DatabricksConnector()
    if 'connected' not in st.session_state:
        st.session_state.connected = False

    if not st.session_state.connected:
        with st.spinner("Connecting to Databricks..."):
            if st.session_state.db_connector.connect_from_env():
                st.session_state.connected = True

    if st.session_state.get("active_tab") != "ai":
        st.session_state.pop("generated_sql", None)
        st.session_state.pop("selected_question", None)

    if st.session_state.connected:
        tab1, tab2, tab3 = st.tabs(["🤖 AI Query Assistant", "📊 Quick Analytics", "🔍 Custom SQL"])

        with tab1:
            st.session_state.active_tab = "ai"
            question = st.text_area("Ask a question about your data:", value=st.session_state.get('selected_question', ''), height=100)
            if st.button("🔮 Generate SQL") and question:
                with st.spinner("Generating SQL..."):
                    generated_sql = st.session_state.db_connector.get_ai_query(question)
                    st.session_state.generated_sql = generated_sql
                    st.session_state.selected_question = question
                    if generated_sql:
                        st.success("✅ SQL generated")
                    else:
                        st.error("❌ Failed to generate SQL")

            if st.session_state.get("generated_sql"):
                st.subheader("Generated SQL:")
                st.code(st.session_state.generated_sql, language="sql")

                if st.button("▶️ Execute Query"):
                    with st.spinner("Running query..."):
                        results = st.session_state.db_connector.execute_query(st.session_state.generated_sql)
                        if results is not None and not results.empty:
                            st.subheader("Results:")
                            st.dataframe(results, use_container_width=True)
                            csv = results.to_csv(index=False)
                            st.download_button("📥 Download CSV", data=csv, file_name="query_results.csv", mime="text/csv")
                        elif results is not None:
                            st.info("✅ Query executed, no rows returned.")

        with tab2:
            col1, col2, col3, col4 = st.columns(4)

            with col1:
                if st.button("📊 Rides Today"):
                    q = "SELECT COUNT(*) AS total_rides FROM agent.shuttler.ride_bookings WHERE DATE(ScheduledTime) = CURRENT_DATE()"
                    r = st.session_state.db_connector.execute_query(q)
                    if r is not None and not r.empty:
                        st.metric("Total Rides", r.iloc[0]['total_rides'])

            with col2:
                if st.button("💰 Revenue Today"):
                    q = "SELECT SUM(Fare) AS revenue FROM agent.shuttler.ride_bookings WHERE DATE(ScheduledTime) = CURRENT_DATE() AND Status = 'completed'"
                    r = st.session_state.db_connector.execute_query(q)
                    if r is not None and not r.empty:
                        st.metric("Revenue", f"₦{r.iloc[0]['revenue']:,.2f}")

            with col3:
                if st.button("👥 Weekly Active Users"):
                    q = "SELECT COUNT(DISTINCT UserID) as active_users FROM agent.shuttler.ride_bookings WHERE DATE(ScheduledTime) >= DATE_SUB(CURRENT_DATE(), 7)"
                    r = st.session_state.db_connector.execute_query(q)
                    if r is not None and not r.empty:
                        st.metric("7-Day Active", r.iloc[0]['active_users'])

            with col4:
                if st.button("⭐ Avg Rating (30d)"):
                    q = "SELECT AVG(Rating) as avg_rating FROM agent.shuttler.feedback WHERE DATE(Timestamp) >= DATE_SUB(CURRENT_DATE(), 30)"
                    r = st.session_state.db_connector.execute_query(q)
                    if r is not None and not r.empty:
                        st.metric("Avg Rating", f"{r.iloc[0]['avg_rating']:.2f}")

        with tab3:
            sql_query = st.text_area("Enter a SQL query to run:", height=200)
            if st.button("Execute Custom Query") and sql_query.strip():
                with st.spinner("Running..."):
                    results = st.session_state.db_connector.execute_query(sql_query)
                    if results is not None and not results.empty:
                        st.dataframe(results, use_container_width=True)
                    elif results is not None:
                        st.info("✅ No rows returned.")

    else:
        st.warning("⚠️ Connect to Databricks via environment variables to get started.")

if __name__ == "__main__":
    main()
