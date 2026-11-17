import os
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from app.config import settings
from app.services.llm_service import llm_service
from app.utils.logger import logger

class DataAnalystAgent:
    def __init__(self):
        self.name = "Data Analyst Agent"
        self.role = "Statistical Analysis, Pattern Recognition & Data Visualization"

    def analyze(self, user_instruction: str, research_notes: str, csv_file_path: str = None) -> dict:
        logger.info(f"[{self.name}] Starting analytical processing...")
        
        stats_summary = ""
        chart_path = None
        
        # If a CSV dataset is provided, execute real statistical EDA and generate a chart
        if csv_file_path and os.path.exists(csv_file_path):
            try:
                df = pd.read_csv(csv_file_path)
                numeric_cols = df.select_dtypes(include=["number"]).columns.tolist()
                
                stats_summary = (
                    f"Dataset Shape: {df.shape[0]} rows, {df.shape[1]} columns.\n"
                    f"Columns: {', '.join(df.columns.tolist())}\n"
                    f"Missing Values: {df.isnull().sum().to_dict()}\n"
                )
                if numeric_cols:
                    stats_summary += f"Descriptive Statistics:\n{df[numeric_cols].describe().to_string()}\n"
                    
                    # Generate automated summary bar/line chart for the first numeric column
                    plt.figure(figsize=(8, 4))
                    df[numeric_cols[0]].head(20).plot(kind="bar", color="#2563EB")
                    plt.title(f"Distribution of {numeric_cols[0]} (Top 20 Records)")
                    plt.xlabel("Record Index")
                    plt.ylabel(numeric_cols[0])
                    plt.tight_layout()
                    
                    chart_filename = f"analysis_chart_{os.path.basename(csv_file_path)}.png"
                    chart_path = str(settings.reports_dir / chart_filename)
                    plt.savefig(chart_path)
                    plt.close()
                    logger.info(f"[{self.name}] Saved visualization chart to {chart_path}")
            except Exception as e:
                logger.error(f"[{self.name}] CSV analysis error: {str(e)}")
                stats_summary = f"CSV analysis encountered an error: {str(e)}"

        system_prompt = (
            "You are the Data Analyst Agent. Analyze the provided research findings and statistical summaries. "
            "Identify key trends, anomalies, comparative metrics, and actionable insights using clear Markdown bullet points and tables."
        )
        
        prompt = f"""
User Goal: {user_instruction}

Research Findings:
{research_notes}

Statistical Dataset Summary:
{stats_summary if stats_summary else 'No tabular CSV dataset attached; perform qualitative & quantitative trend synthesis from research notes.'}

Provide comprehensive analytical insights:
"""
        insights = llm_service.generate_text(prompt, system_instruction=system_prompt, temperature=0.2)
        
        return {
            "analysis_insights": insights,
            "stats_summary": stats_summary,
            "chart_path": chart_path
        }

analyst_agent = DataAnalystAgent()