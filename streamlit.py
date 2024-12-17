import streamlit as st
import pandas as pd
import plotly.express as px
import requests
from datetime import datetime

# Function to fetch scheduling data from the API endpoint
def fetch_scheduled_operations():
    url = "http://localhost:4567/api/scheduled-operations"
    response = requests.get(url)
    if response.status_code == 200:
        return response.json()
    else:
        st.error(f"Error fetching data: {response.status_code}")
        return []

# Convert list of scheduled operations into a DataFrame
def create_gantt_df(scheduled_operations):
    df = pd.DataFrame(scheduled_operations)
    # Convert datetime columns to appropriate formats
    df['start_time'] = pd.to_datetime(df['start_time'])
    df['end_time'] = pd.to_datetime(df['end_time'])
    return df

# Function to display Gantt chart using Plotly
def plot_gantt_chart(df):
    fig = px.timeline(df,
                       x_start="start_time",
                       x_end="end_time",
                       y="machine",
                       color="part_number",
                       title="Scheduled Operations Machine-Wise",
                       labels={"machine": "Machine", "part_number": "Part Number"},
                       hover_name="operation_description",
                       hover_data=["operation_id", "start_time", "end_time", "launched_quantity"])
    fig.update_yaxes(categoryorder="total ascending")  # Sort machines
    fig.update_layout(xaxis_title="Time", yaxis_title="Machine")
    st.plotly_chart(fig)

# Main function to display Streamlit app
def main():
    st.title("Scheduled Operations - Gantt Chart Machine-Wise")
    
    # Fetch the scheduled operations from the API
    scheduled_operations = fetch_scheduled_operations()
    
    if scheduled_operations:
        # Create a DataFrame from the fetched data
        df = create_gantt_df(scheduled_operations)
        
        # Display the raw data in a table
        st.subheader("Scheduled Operations Data")
        st.dataframe(df)
        
        # Display the Gantt chart
        st.subheader("Machine-Wise Gantt Chart")
        plot_gantt_chart(df)
    else:
        st.warning("No scheduled operations found.")

if __name__ == "__main__":
    main()
