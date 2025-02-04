import streamlit as st
import pandas as pd
import requests
import base64
import json
from PIL import Image
from io import BytesIO, StringIO

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
            return pd.read_csv(StringIO(file_content.decode("utf-8")))  # Use io.StringIO
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

    # Define the folder and file paths
    folder_path = f"images/{contact}"  # Folder for contact
    file_path = f"{folder_path}/{file_name}"

    headers = {"Authorization": f"Bearer {GITHUB_TOKEN}"}
    file_url = f"https://api.github.com/repos/{GITHUB_REPO}/contents/{file_path}"
    
    # Upload the image directly
    payload = {
        "message": f"Add image {file_name} for customer {contact}",
        "content": base64.b64encode(file_content).decode("utf-8"),
        "branch": "main",
    }
    response = requests.put(file_url, headers=headers, data=json.dumps(payload))
    if response.status_code in [200, 201]:
        return file_path
    else:
        st.error(f"Failed to upload image {file_name}.")
        st.error(f"Error Response: {response.json()}")
        return None


# Display images in gallery
def display_gallery(contact):
    st.title(f"Image Gallery for Contact: {contact}")
    folder_path = f"images/{contact}"
    headers = {"Authorization": f"Bearer {GITHUB_TOKEN}"}
    folder_url = f"https://api.github.com/repos/{GITHUB_REPO}/contents/{folder_path}"

    response = requests.get(folder_url, headers=headers)
    if response.status_code == 200:
        files = response.json()
        for file in files:
            if file["type"] == "file":  # Ensure it's a file
                image_url = file["download_url"]
                response = requests.get(image_url)
                if response.status_code == 200:
                    image = Image.open(BytesIO(response.content))
                    st.image(image, use_container_width=True)
                else:
                    st.warning(f"Could not load image: {image_url}")
    else:
        st.error("No images found for this customer.")


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
        # Convert columns to strings to safely apply .str.contains
        df["Name"] = df["Name"].astype(str)
        df["Contact"] = df["Contact"].astype(str)
        
        # Perform search
        results = df[
            df["Name"].str.contains(search_query, case=False, na=False) |
            df["Contact"].str.contains(search_query, case=False, na=False)
        ]
        if not results.empty:
            st.dataframe(results)
            selected_contact = st.selectbox("Select a customer to view details", results["Contact"].values)
            if selected_contact:
                customer = df[df["Contact"] == selected_contact].iloc[0]
                st.write("Name:", customer["Name"])
                st.write("Contact:", customer["Contact"])
                st.write("Bill Number:", customer["Bill Number"])
                display_gallery(selected_contact)
        else:
            st.warning("No matching customers found.")


def view_customers_page():
    st.title("View All Customers")
    global df
    if df.empty:
        st.warning("No customer data available. Please add customers.")
    else:
        st.dataframe(df)
        st.download_button(
            label="Download CSV",
            data=df.to_csv(index=False),
            file_name="Customers.csv",
            mime="text/csv"
        )
#--------------------------------------------------------

def edit_customer_page():
    st.title("Edit Customer")

    # Check if the DataFrame is empty
    if df.empty:
        st.warning("No customers available. Please add customers first.")
        return

    # Search for a customer by name or contact
    search_query = st.text_input("Search by Name or Contact Number")
    search_results = df[
        df["Name"].astype(str).str.contains(search_query, case=False, na=False) |
        df["Contact"].astype(str).str.contains(search_query, case=False, na=False)
    ] if search_query else pd.DataFrame()

    if search_query and not search_results.empty:
        st.dataframe(search_results)
        selected_contact = st.selectbox("Select a customer to edit", search_results["Contact"].values)
    elif search_query:
        st.warning("No matching customers found.")
        return
    else:
        st.info("Search for a customer to edit.")
        return

    if selected_contact:
        # Fetch customer details
        customer = df[df["Contact"] == selected_contact].iloc[0]

        # Editable fields
        name = st.text_input("Customer Name", value=customer["Name"])

        # Safely handle "Bill Number" and ensure it's treated as a string
        existing_bills = str(customer["Bill Number"]).split(",") if pd.notna(customer["Bill Number"]) else []
        bill_numbers = st.text_area(
            "Bill Numbers (Comma-Separated)", 
            value=",".join(existing_bills)
        )

        # Display existing images in a gallery grid
        st.subheader("Existing Images")
        existing_images = str(customer["Image Links"]).split(",") if pd.notna(customer["Image Links"]) else []
        existing_images = [img for img in existing_images if img]  # Filter out empty or None values
        images_to_remove = []

        if existing_images:
            cols = st.columns(4)  # Display images in a 4-column grid
            for index, image_link in enumerate(existing_images):
                with cols[index % 4]:
                    # Display a small thumbnail
                    st.image(image_link, caption=image_link.split("/")[-1], use_container_width=True)

                    # Remove button for each image
                    if st.button(f"Remove {image_link.split('/')[-1]}", key=f"remove_{index}"):
                        confirm = st.warning(
                            f"Are you sure you want to delete {image_link.split('/')[-1]}? This action cannot be undone."
                        )
                        if st.button(f"Yes, delete {image_link.split('/')[-1]}", key=f"confirm_remove_{index}"):
                            delete_image_from_github(image_link)
                            st.success(f"{image_link.split('/')[-1]} has been deleted.")
                            st.experimental_rerun()  # Reboot the app to reflect changes

        else:
            st.warning("No images found for this customer.")

        # Upload new images
        st.subheader("Upload New Images")
        uploaded_files = st.file_uploader("Choose files to upload", accept_multiple_files=True)
        new_image_links = []
        for uploaded_file in uploaded_files:
            file_path = upload_image(selected_contact, uploaded_file)
            if file_path:
                new_image_links.append(file_path)
        
        # Save changes
        if st.button("Save Changes"):
            # Ensure all lists contain valid strings
            new_image_links = [img for img in new_image_links if img]
            
            # Update customer data in DataFrame
            df.loc[df["Contact"] == selected_contact, "Name"] = name
            df.loc[df["Contact"] == selected_contact, "Bill Number"] = bill_numbers
            updated_images = list(set(existing_images + new_image_links))  # Add new images
            df.loc[df["Contact"] == selected_contact, "Image Links"] = ",".join(updated_images)
            
            # Save updated data to GitHub
            save_data(df)
            st.success("Customer data updated successfully!")
            st.experimental_rerun()  # Reboot the app to reflect changes


def delete_image_from_github(image_link):
    """Delete an image from the GitHub repository."""
    headers = {"Authorization": f"Bearer {GITHUB_TOKEN}"}
    response = requests.get(image_link.replace("https://raw.githubusercontent.com/", 
                                               "https://api.github.com/repos/").replace("/main/", "/contents/"), 
                            headers=headers)
    if response.status_code == 200:
        sha = response.json().get("sha")
        file_url = response.url
        payload = {
            "message": f"Delete image {image_link.split('/')[-1]}",
            "sha": sha,
            "branch": "main",
        }
        delete_response = requests.delete(file_url, headers=headers, data=json.dumps(payload))
        if delete_response.status_code in [200, 204]:
            return True
        else:
            st.error(f"Failed to delete {image_link}. Error: {delete_response.json()}")
            return False
    else:
        st.error(f"Failed to fetch file information for {image_link}. Error: {response.json()}")
        return False



#--------------------------------------------------------
# Main function
def main():
    global df
    df = load_data()

    st.sidebar.title("Navigation")
    pages = {
        "Home": home_page,
        "Add Customer": add_customer_page,
        "Search Customer": search_customer_page,
        "View All Customers": view_customers_page,
        "Edit Customer": edit_customer_page,
    }
    choice = st.sidebar.radio("Go to", list(pages.keys()))
    pages[choice]()


if __name__ == "__main__":
    main()
