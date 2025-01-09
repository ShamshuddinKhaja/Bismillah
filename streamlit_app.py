import streamlit as st
import pandas as pd
import os
from google.colab import drive

# Mount Google Drive
drive.mount('/content/drive')

# Define folder paths
BASE_DIR = '/content/drive/My Drive'
CUSTOMERS_DIR = os.path.join(BASE_DIR, 'Customers')
DATABASE_DIR = os.path.join(BASE_DIR, 'Database')
CSV_FILE = os.path.join(CUSTOMERS_DIR, 'customers.csv')

# Ensure directories exist
os.makedirs(CUSTOMERS_DIR, exist_ok=True)
os.makedirs(DATABASE_DIR, exist_ok=True)

# Load or create the customer data CSV
try:
    df = pd.read_csv(CSV_FILE)
except FileNotFoundError:
    df = pd.DataFrame(columns=["Name", "Contact", "Bill Number", "Image Links"])
    df.to_csv(CSV_FILE, index=False)

def save_data():
    """Save the updated DataFrame to the customers.csv file."""
    df.to_csv(CSV_FILE, index=False)

def ensure_customer_folder(contact_number):
    """Ensure a folder for the customer exists in the Database folder."""
    customer_folder = os.path.join(DATABASE_DIR, str(contact_number))
    os.makedirs(customer_folder, exist_ok=True)
    return customer_folder

# ---------------------------------------------------------------------------------------

def home_page():
    st.title("Welcome to Boutique Management App")
    st.image("https://via.placeholder.com/800x300?text=Boutique+Management", use_column_width=True)
    st.markdown("""
    This application helps the boutique manage customer details, bills, and uploaded images.
    Navigate through the options in the sidebar to explore features.
    """)

# ---------------------------------------------------------------------------------------

def add_customer_page():
    st.title("Add New Customer")
    name = st.text_input("Customer Name")
    contact = st.text_input("Contact Number")
    bill = st.text_input("Bill Receipt Number")
    uploaded_files = st.file_uploader("Upload Images", accept_multiple_files=True)

    if st.button("Save Customer"):
        if not contact.isdigit():
            st.error("Please enter a valid contact number.")
            return

        # Ensure customer folder exists
        customer_folder = ensure_customer_folder(contact)
        image_links = []

        # Save uploaded images to customer folder
        if uploaded_files:
            for uploaded_file in uploaded_files:
                file_path = os.path.join(customer_folder, uploaded_file.name)
                with open(file_path, "wb") as f:
                    f.write(uploaded_file.read())
                image_links.append(file_path)

        # Save customer details to CSV
        global df
        df = df.append(
            {"Name": name, "Contact": contact, "Bill Number": bill, "Image Links": ','.join(image_links)},
            ignore_index=True
        )
        save_data()
        st.success("Customer added successfully!")

# ---------------------------------------------------------------------------------------

def search_customer_page():
    st.title("Search Customer")
    search = st.text_input("Enter Name or Contact Number")
    if st.button("Search"):
        results = df[(df['Name'].str.contains(search, na=False)) | (df['Contact'].str.contains(search, na=False))]
        if not results.empty:
            for _, row in results.iterrows():
                st.write(f"**Name:** {row['Name']}")
                st.write(f"**Contact:** {row['Contact']}")
                st.write(f"**Bill Number:** {row['Bill Number']}")
                st.write("**Images:**")
                links = row['Image Links'].split(',')
                for link in links:
                    st.image(link.strip(), width=200)
        else:
            st.warning("No customer found!")

# ---------------------------------------------------------------------------------------

def edit_customer_page():
    st.title("Edit Customer Details")
    search = st.text_input("Enter Name or Contact Number")
    if st.button("Search to Edit"):
        results = df[(df['Name'].str.contains(search, na=False)) | (df['Contact'].str.contains(search, na=False))]
        if not results.empty:
            row = results.iloc[0]
            st.write(f"Editing details for: {row['Name']} ({row['Contact']})")
            name = st.text_input("Customer Name", row['Name'])
            contact = st.text_input("Contact Number", row['Contact'])
            bill = st.text_input("Bill Receipt Number", row['Bill Number'])
            uploaded_files = st.file_uploader("Upload More Images", accept_multiple_files=True)

            # Ensure customer folder exists
            customer_folder = ensure_customer_folder(contact)
            new_image_links = row['Image Links'].split(',')

            # Save new images to customer folder
            if uploaded_files:
                for uploaded_file in uploaded_files:
                    file_path = os.path.join(customer_folder, uploaded_file.name)
                    with open(file_path, "wb") as f:
                        f.write(uploaded_file.read())
                    new_image_links.append(file_path)

            if st.button("Save Changes"):
                global df
                df.loc[df['Contact'] == row['Contact'], ['Name', 'Contact', 'Bill Number', 'Image Links']] = [
                    name, contact, bill, ','.join(new_image_links)
                ]
                save_data()
                st.success("Customer details updated!")
        else:
            st.warning("No customer found!")

# ---------------------------------------------------------------------------------------

def view_customers_page():
    st.title("All Customers")
    st.dataframe(df)
    st.download_button("Download CSV", df.to_csv(index=False), "customers.csv", "text/csv")

# ---------------------------------------------------------------------------------------

def main():
    st.sidebar.title("Boutique Management")
    pages = ["Home", "Add Customer", "Search Customer", "Edit Customer", "View All Customers"]
    choice = st.sidebar.radio("Go to", pages)

    if choice == "Home":
        home_page()
    elif choice == "Add Customer":
        add_customer_page()
    elif choice == "Search Customer":
        search_customer_page()
    elif choice == "Edit Customer":
        edit_customer_page()
    elif choice == "View All Customers":
        view_customers_page()

# ---------------------------------------------------------------------------------------

if __name__ == "__main__":
    main()

# ---------------------------------------------------------------------------------------

