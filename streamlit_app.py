import streamlit as st
import pandas as pd
import requests
import base64
import json

# GitHub repository details
GITHUB_TOKEN = st.secrets["GITHUB_TOKEN"]  # Add your token in Streamlit Secrets
GITHUB_REPO = "ShamshuddinKhaja/Bismillah"  # Replace with your repo
GITHUB_FILE_PATH = "Customers.csv"  # Path to the CSV file in your repository

# GitHub API endpoints
API_BASE_URL = f"https://api.github.com/repos/{GITHUB_REPO}/contents/{GITHUB_FILE_PATH}"


# Load the CSV file from GitHub
@st.cache_data
def load_data():
    headers = {"Authorization": f"Bearer {GITHUB_TOKEN}"}
    response = requests.get(API_BASE_URL, headers=headers)
    if response.status_code == 200:
        file_content = base64.b64decode(response.json()["content"])
        return pd.read_csv(pd.compat.StringIO(file_content.decode("utf-8")))
    else:
        # If the file does not exist, return an empty DataFrame
        return pd.DataFrame(columns=["Name", "Contact", "Bill Number", "Image Links"])


# Save the CSV file back to GitHub
def save_data(df):
    headers = {"Authorization": f"Bearer {GITHUB_TOKEN}"}
    response = requests.get(API_BASE_URL, headers=headers)
    if response.status_code == 200:
        sha = response.json()["sha"]  # Get the file's SHA for updating
    else:
        sha = None  # File doesn't exist, so we'll create it

    # Convert DataFrame to CSV
    csv_content = df.to_csv(index=False)

    # Prepare payload for the API request
    payload = {
        "message": "Update customers.csv",
        "content": base64.b64encode(csv_content.encode("utf-8")).decode("utf-8"),
        "branch": "main",  # Replace with your branch name
    }
    if sha:
        payload["sha"] = sha

    # Make the API request to create or update the file
    response = requests.put(API_BASE_URL, headers=headers, data=json.dumps(payload))
    if response.status_code in [200, 201]:
        st.success("Data saved successfully!")
    else:
        st.error("Failed to save data. Please check your GitHub configuration.")


# Streamlit pages
def home_page():
    st.title("Welcome to Boutique Management App")
    st.markdown("Manage customer details, bills, and uploaded images.")


def add_customer_page():
    global df
    st.title("Add New Customer")
    name = st.text_input("Customer Name")
    contact = st.text_input("Contact Number")
    bill = st.text_input("Bill Receipt Number")
    uploaded_files = st.file_uploader("Upload Images", accept_multiple_files=True)

    if st.button("Save Customer"):
        if not contact.isdigit():
            st.error("Please enter a valid contact number.")
            return

        # Save uploaded images as file names (placeholder, actual implementation can differ)
        image_links = [f"image_placeholder/{uploaded_file.name}" for uploaded_file in uploaded_files]

        # Add new customer to DataFrame
        df = df.append(
            {"Name": name, "Contact": contact, "Bill Number": bill, "Image Links": ','.join(image_links)},
            ignore_index=True,
        )

        # Save data to GitHub
        save_data(df)


def view_customers_page():
    st.title("All Customers")
    st.dataframe(df)
    st.download_button(
        "Download CSV", df.to_csv(index=False), file_name="Customers.csv", mime="text/csv"
    )


# Main function
def main():
    global df
    df = load_data()

    st.sidebar.title("Boutique Management")
    pages = {"Home": home_page, "Add Customer": add_customer_page, "View All Customers": view_customers_page}
    choice = st.sidebar.radio("Navigation", list(pages.keys()))
    pages[choice]()


if __name__ == "__main__":
    main()
