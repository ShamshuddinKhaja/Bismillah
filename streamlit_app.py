import streamlit as st
import pandas as pd
import os
from subprocess import run

# Set up repository details
REPO_URL = "https://github.com/your-username/boutique-app.git"
CSV_FILE = "customers.csv"

# Clone the repository (only if it hasn't been cloned already)
if not os.path.exists("repo"):
    run(["git", "clone", REPO_URL, "repo"])

# Change to the repository directory
os.chdir("repo")

# Load or create the customer data CSV
if os.path.exists(CSV_FILE):
    df = pd.read_csv(CSV_FILE)
else:
    df = pd.DataFrame(columns=["Name", "Contact", "Bill Number", "Image Links"])
    df.to_csv(CSV_FILE, index=False)

def save_data():
    """Save the updated DataFrame to the CSV file and push changes to GitHub."""
    global df
    df.to_csv(CSV_FILE, index=False)
    run(["git", "add", CSV_FILE])
    run(["git", "commit", "-m", "Update customers.csv"])
    run(["git", "push", f"https://{os.getenv('GITHUB_TOKEN')}@github.com/your-username/boutique-app.git"])

# Streamlit Pages
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

        # Update DataFrame
        image_links = [f"images/{uploaded_file.name}" for uploaded_file in uploaded_files]
        df = df.append(
            {"Name": name, "Contact": contact, "Bill Number": bill, "Image Links": ','.join(image_links)},
            ignore_index=True,
        )
        save_data()
        st.success("Customer added successfully!")

def view_customers_page():
    st.title("All Customers")
    st.dataframe(df)
    st.download_button("Download CSV", df.to_csv(index=False), "customers.csv", "text/csv")

def main():
    st.sidebar.title("Boutique Management")
    pages = {"Home": home_page, "Add Customer": add_customer_page, "View All Customers": view_customers_page}
    choice = st.sidebar.radio("Navigation", list(pages.keys()))
    pages[choice]()

if __name__ == "__main__":
    main()
