import streamlit as st
import pandas as pd
import os

# Define paths in Google Drive
BASE_DIR = '/app/data'  # Replace with the path where Google Drive is mounted
CUSTOMERS_FILE = os.path.join(BASE_DIR, 'customers.csv')
DATABASE_DIR = os.path.join(BASE_DIR, 'Database')

# Ensure directories exist
os.makedirs(DATABASE_DIR, exist_ok=True)

# Load or create the customer data CSV
if os.path.exists(CUSTOMERS_FILE):
    df = pd.read_csv(CUSTOMERS_FILE)
else:
    df = pd.DataFrame(columns=["Name", "Contact", "Bill Number", "Image Links"])
    df.to_csv(CUSTOMERS_FILE, index=False)

def save_data():
    """Save the updated DataFrame to the CSV file."""
    df.to_csv(CUSTOMERS_FILE, index=False)

def ensure_customer_folder(contact_number):
    """Ensure a folder for the customer exists in the Database directory."""
    customer_folder = os.path.join(DATABASE_DIR, str(contact_number))
    os.makedirs(customer_folder, exist_ok=True)
    return customer_folder

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

        # Create customer folder
        customer_folder = ensure_customer_folder(contact)
        image_links = []

        # Save uploaded images
        for uploaded_file in uploaded_files:
            file_path = os.path.join(customer_folder, uploaded_file.name)
            with open(file_path, "wb") as f:
                f.write(uploaded_file.read())
            image_links.append(file_path)

        # Update DataFrame
        df = df.append(
            {"Name": name, "Contact": contact, "Bill Number": bill, "Image Links": ','.join(image_links)},
            ignore_index=True,
        )
        save_data()
        st.success("Customer added successfully!")

def search_customer_page():
    st.title("Search Customer")
    search = st.text_input("Enter Name or Contact Number")
    if st.button("Search"):
        results = df[(df['Name'].str.contains(search, na=False)) | (df['Contact'].str.contains(search, na=False))]
        if not results.empty:
            for _, row in results.iterrows():
                st.write(f"Name: {row['Name']}")
                st.write(f"Contact: {row['Contact']}")
                st.write(f"Bill Number: {row['Bill Number']}")
                st.write("Images:")
                for link in row['Image Links'].split(','):
                    st.image(link, use_column_width=True)
        else:
            st.warning("No customer found!")

def view_customers_page():
    st.title("All Customers")
    st.dataframe(df)
    st.download_button("Download CSV", df.to_csv(index=False), "customers.csv", "text/csv")

# Streamlit App Navigation
def main():
    st.sidebar.title("Boutique Management")
    pages = {
        "Home": home_page,
        "Add Customer": add_customer_page,
        "Search Customer": search_customer_page,
        "View All Customers": view_customers_page,
    }
    choice = st.sidebar.radio("Navigation", list(pages.keys()))
    pages[choice]()

if __name__ == "__main__":
    main()
