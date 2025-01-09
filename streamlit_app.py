import streamlit as st
import pandas as pd
import requests
import base64
import json
from PIL import Image
from io import BytesIO

# GitHub repository details
GITHUB_TOKEN = st.secrets["GITHUB_TOKEN"]
GITHUB_REPO = "ShamshuddinKhaja/Bismillah"
GITHUB_FILE_PATH = "Customers.csv"

# GitHub API endpoints
API_BASE_URL = f"https://api.github.com/repos/{GITHUB_REPO}/contents/{GITHUB_FILE_PATH}"

# Load the CSV file from GitHub
@st.cache_data
def load_data():
    headers = {"Authorization": f"Bearer {GITHUB_TOKEN}"}
    response = requests.get(API_BASE_URL, headers=headers)

    if response.status_code == 200:
        try:
            file_content = base64.b64decode(response.json()["content"])
            return pd.read_csv(pd.compat.StringIO(file_content.decode("utf-8")))
        except Exception as e:
            st.error(f"Error reading the dataset: {e}")
            return pd.DataFrame(columns=["Name", "Contact", "Bill Number", "Image Links"])
    else:
        st.warning("No existing data found. Starting with an empty dataset.")
        return pd.DataFrame(columns=["Name", "Contact", "Bill Number", "Image Links"])


# Save the CSV file back to GitHub
def save_data(df):
    headers = {"Authorization": f"Bearer {GITHUB_TOKEN}"}
    response = requests.get(API_BASE_URL, headers=headers)

    if response.status_code == 200:
        sha = response.json().get("sha")
    else:
        sha = None

    csv_content = df.to_csv(index=False)

    payload = {
        "message": "Update Customers.csv",
        "content": base64.b64encode(csv_content.encode("utf-8")).decode("utf-8"),
        "branch": "main",
    }
    if sha:
        payload["sha"] = sha

    response = requests.put(API_BASE_URL, headers=headers, data=json.dumps(payload))
    if response.status_code in [200, 201]:
        st.success("Data saved successfully!")
    else:
        st.error("Failed to save data. Please check your GitHub configuration.")
        st.error(f"Status Code: {response.status_code}")
        st.error(f"Response: {response.json()}")


# Upload images to GitHub
def upload_image(contact, file):
    file_content = file.read()
    file_name = file.name

    folder_path = f"images/{contact}"  # Folder for contact
    file_path = f"{folder_path}/{file_name}"

    headers = {"Authorization": f"Bearer {GITHUB_TOKEN}"}
    payload = {
        "message": f"Add image {file_name} for customer {contact}",
        "content": base64.b64encode(file_content).decode("utf-8"),
        "branch": "main",
    }

    # Create folder if it doesn't exist
    folder_url = f"https://api.github.com/repos/{GITHUB_REPO}/contents/{folder_path}"
    folder_response = requests.get(folder_url, headers=headers)
    if folder_response.status_code != 200:  # Folder doesn't exist
        payload["message"] = f"Create folder {folder_path}"
        requests.put(folder_url, headers=headers, data=json.dumps(payload))

    # Upload the image
    file_url = f"https://api.github.com/repos/{GITHUB_REPO}/contents/{file_path}"
    response = requests.put(file_url, headers=headers, data=json.dumps(payload))
    if response.status_code in [200, 201]:
        return file_path
    else:
        st.error(f"Failed to upload image {file_name}.")
        st.error(f"Error Response: {response.json()}")
        return None


# Display images in gallery
def display_gallery(image_links):
    st.title("Image Gallery")
    for link in image_links.split(","):
        image_url = f"https://raw.githubusercontent.com/{GITHUB_REPO}/main/{link}"
        response = requests.get(image_url)
        if response.status_code == 200:
            image = Image.open(BytesIO(response.content))
            st.image(image, use_column_width=True)
        else:
            st.error(f"Failed to load image: {link}")


# Pages
def home_page():
    st.title("Welcome to Boutique Management App")
    st.markdown("Manage customer details, bills, and uploaded images with ease.")


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

        # Upload images to GitHub and get their links
        image_links = []
        for uploaded_file in uploaded_files:
            file_path = upload_image(contact, uploaded_file)
            if file_path:
                image_links.append(file_path)

        # Add new customer
        new_customer = pd.DataFrame([{
            "Name": name,
            "Contact": contact,
            "Bill Number": bill,
            "Image Links": ','.join(image_links),
        }])
        df = pd.concat([df, new_customer], ignore_index=True)
        save_data(df)


def search_customer_page():
    st.title("Search Customer")
    search_query = st.text_input("Search by Name or Contact")
    if search_query:
        results = df[(df["Name"].str.contains(search_query, case=False, na=False)) |
                     (df["Contact"].str.contains(search_query, case=False, na=False))]
        if not results.empty:
            st.dataframe(results)
            selected_contact = st.selectbox("Select a customer to view details", results["Contact"].values)
            if selected_contact:
                customer = df[df["Contact"] == selected_contact].iloc[0]
                st.write("Name:", customer["Name"])
                st.write("Contact:", customer["Contact"])
                st.write("Bill Number:", customer["Bill Number"])
                display_gallery(customer["Image Links"])
        else:
            st.warning("No matching customers found.")


def edit_customer_page():
    st.title("Edit Customer")
    contact = st.selectbox("Select Customer by Contact", df["Contact"].unique())
    if contact:
        customer = df[df["Contact"] == contact].iloc[0]
        name = st.text_input("Customer Name", value=customer["Name"])
        bill = st.text_input("Bill Receipt Number", value=customer["Bill Number"])
        uploaded_files = st.file_uploader("Upload New Images", accept_multiple_files=True)

        if st.button("Save Changes"):
            df.loc[df["Contact"] == contact, "Name"] = name
            df.loc[df["Contact"] == contact, "Bill Number"] = bill

            # Upload new images
            for uploaded_file in uploaded_files:
                file_path = upload_image(contact, uploaded_file)
                if file_path:
                    df.loc[df["Contact"] == contact, "Image Links"] += f",{file_path}"

            save_data(df)
            st.success("Customer updated successfully!")


# Main function
def main():
    global df
    df = load_data()

    st.sidebar.title("Navigation")
    pages = {
        "Home": home_page,
        "Add Customer": add_customer_page,
        "Search Customer": search_customer_page,
        "Edit Customer": edit_customer_page,
    }
    choice = st.sidebar.radio("Go to", list(pages.keys()))
    pages[choice]()


if __name__ == "__main__":
    main()
