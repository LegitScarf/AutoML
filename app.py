import streamlit as st
import requests
import os

st.set_page_config(
    page_title="Agentic AutoML Dashboard",
    page_icon="🤖",
    layout="wide"
)

st.title("Agentic AutoML Orchestrator")
st.markdown("Upload a dataset, specify the target column, and let the AI system profile, generate, execute, and self-correct your ML training pipeline.")

# Input fields
webhook_url = st.text_input(
    "n8n Webhook URL",
    value="http://localhost:5678/webhook-test/trigger-automl",
    help="Enter your local or public ngrok n8n webhook URL."
)

col1, col2 = st.columns(2)

with col1:
    dataset_path = st.text_input(
        "Dataset Path (Local to host)",
        value="./sample_dataset.csv",
        help="The local file path that the Sandbox container/MCP servers can read."
    )

with col2:
    target_variable = st.text_input(
        "Target Variable",
        value="purchased",
        help="The column name you want the model to predict."
    )

if st.button("🚀 Trigger AutoML Pipeline", type="primary"):
    if not webhook_url:
        st.error("Please enter a valid webhook URL.")
    elif not dataset_path:
        st.error("Please enter a dataset path.")
    elif not target_variable:
        st.error("Please enter a target variable.")
    else:
        st.info("Triggering n8n workflow...")
        
        payload = {
            "file_path": dataset_path,
            "target_variable": target_variable
        }
        
        try:
            with st.spinner("Pipeline is running... Check n8n dashboard for real-time progress."):
                response = requests.post(webhook_url, json=payload, timeout=300)
            
            if response.status_code == 200:
                st.success("AutoML pipeline finished successfully!")
                res_data = response.json()
                st.subheader("Pipeline Response:")
                st.json(res_data)
                
                # Retrieve download URL
                download_url = None
                if isinstance(res_data, dict):
                    download_url = res_data.get("download_url")
                elif isinstance(res_data, list) and len(res_data) > 0:
                    download_url = res_data[0].get("download_url")
                
                if download_url:
                    # Map host.docker.internal to localhost for host browser access
                    local_url = download_url.replace("host.docker.internal", "localhost")
                    st.subheader("🎉 Your Model is Ready!")
                    st.link_button("📥 Download AutoML Bundle (.zip)", local_url, type="primary")
            else:
                st.error(f"Error triggering pipeline. Status code: {response.status_code}")
                st.text(response.text)
                
        except Exception as e:
            st.error(f"Failed to connect to webhook: {str(e)}")
            st.info("Make sure n8n is running and 'Listen for test event' or 'Execute workflow' is active.")
