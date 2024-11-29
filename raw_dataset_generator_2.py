import streamlit as st
import pandas as pd
import random
import json
from datetime import datetime, timedelta

# Function to load configuration from a CSV file
def load_csv_config(file_path):
    try:
        config_df = pd.read_csv(file_path)
        return config_df.groupby("Category")["Test"].apply(list).to_dict()
    except FileNotFoundError:
        st.error("Configuration file not found. Generating random configuration.")
        return None

# Function to generate random categories and tests
def randomize_config(num_categories=3, num_tests_per_category=5):
    categories = [f"Category_{i+1}" for i in range(num_categories)]
    test_pool = [f"Test_{j+1}" for j in range(num_categories * num_tests_per_category)]
    return {category: random.sample(test_pool, k=num_tests_per_category) for category in categories}

# Save configuration to a CSV file
def save_config_to_csv(config, file_path):
    rows = [{"Category": category, "Test": test} for category, tests in config.items() for test in tests]
    config_df = pd.DataFrame(rows)
    config_df.to_csv(file_path, index=False)

# Function to generate random date within a range
def random_date(start_date, end_date):
    delta = end_date - start_date
    random_days = random.randint(0, delta.days)
    return start_date + timedelta(days=random_days)

# Generate LAB_CATEGORY and LAB_TEST data based on dynamic column names
def generate_lab_test_data(num_rows, category_test_mapping, num_subjects, subject_prefix, subject_start, category_column, test_column, custom_columns):
    # Generate subject IDs with user-defined format
    subject_ids = [f"{subject_prefix}{subject_start + i}" for i in range(num_subjects)]
    
    # Assign random records to subjects
    subject_data = random.choices(subject_ids, k=num_rows)
    
    # Generate lab categories and tests
    lab_categories = list(category_test_mapping.keys())
    category_data = [random.choice(lab_categories) for _ in range(num_rows)]
    lab_test_data = [
        random.choice(category_test_mapping[category]) for category in category_data
    ]
    
    # Generate custom columns data
    custom_column_data = {}
    for col_name, col_info in custom_columns.items():
        col_type = col_info['type']
        if col_type == 'int':
            custom_column_data[col_name] = [random.randint(*col_info['range']) for _ in range(num_rows)]
        elif col_type == 'float':
            custom_column_data[col_name] = [random.uniform(*col_info['range']) for _ in range(num_rows)]
        elif col_type == 'str':
            custom_column_data[col_name] = [random.choice(col_info['values']) for _ in range(num_rows)]
        elif col_type == 'date':
            # Generate dates within the specified range
            start_date = col_info['start_date']
            end_date = col_info['end_date']
            custom_column_data[col_name] = [
                random_date(start_date, end_date) for _ in range(num_rows)
            ]

    return subject_data, category_data, lab_test_data, custom_column_data

# Streamlit app
def main():
    st.title("Raw Dataset Generator Tool with Configurable Categories, Tests, and Custom Columns")
    st.write("Generate synthetic datasets based on category-test mappings and additional customizable columns.")

    # Step 1: Load or Create Configuration
    st.header("Configuration Setup")
    uploaded_file = st.file_uploader("Upload Category-Test Mapping (CSV)", type="csv")
    if uploaded_file:
        category_test_mapping = load_csv_config(uploaded_file)
    else:
        st.warning("No configuration file uploaded. Generating random configuration.")
        num_categories = st.number_input("Number of Categories", min_value=1, max_value=20, value=3)
        num_tests_per_category = st.number_input("Number of Tests per Category", min_value=1, max_value=10, value=5)
        category_test_mapping = randomize_config(num_categories, num_tests_per_category)
        if st.button("Save Configuration to CSV"):
            save_config_to_csv(category_test_mapping, "generated_config.csv")
            st.success("Configuration saved to 'generated_config.csv'. You can download it.")

    st.write("### Current Category-Test Mapping:")
    st.json(category_test_mapping)

    # Step 2: Custom Columns Setup
    st.header("Add Custom Columns")
    custom_columns = {}
    add_more_columns = True
    column_index = 0  # Initialize column index to ensure unique keys
    while add_more_columns:
        col_name = st.text_input(f"Custom Column Name #{column_index+1}", "", key=f"col_name_{column_index}")
        col_type = st.selectbox(f"Select Data Type for {col_name}", ['int', 'float', 'str', 'date'], key=f"col_type_{column_index}")
        
        if col_type == 'int' or col_type == 'float':
            col_range = st.slider(f"Select Range for {col_name}", min_value=0, max_value=100, value=(10, 50), key=f"col_range_{column_index}")
            custom_columns[col_name] = {'type': col_type, 'range': col_range}
        elif col_type == 'str':
            col_values = st.text_area(f"Enter possible values for {col_name} (comma separated)", "", key=f"col_values_{column_index}")
            custom_columns[col_name] = {'type': col_type, 'values': col_values.split(',')}
        elif col_type == 'date':
            start_date = st.date_input(f"Start Date for {col_name}", value=datetime(2022, 1, 1), key=f"start_date_{column_index}")
            end_date = st.date_input(f"End Date for {col_name}", value=datetime(2023, 12, 31), key=f"end_date_{column_index}")
            custom_columns[col_name] = {'type': col_type, 'start_date': start_date, 'end_date': end_date}
        
        add_more_columns = st.checkbox("Add more columns", value=False, key=f"add_more_{column_index}")
        column_index += 1

    # Step 3: Dataset Generation
    st.header("Generate Dataset")
    num_rows = st.number_input("Number of Rows", min_value=1, max_value=100000, value=1000)
    num_subjects = st.number_input("Number of Subjects", min_value=1, max_value=1000, value=100)
    
    # Customizable Subject ID
    subject_prefix = st.text_input("Subject ID Prefix", value="SUBJ_")
    subject_start = st.number_input("Subject ID Starting Number", min_value=1, value=1)

    # Customizable Column Names
    category_column = st.text_input("Column Name for Category", value="LAB_CATEGORY_RAW")
    test_column = st.text_input("Column Name for Test", value="LAB_TEST_RAW")

    if st.button("Generate Dataset"):
        # Generate data based on category-test mapping and subject ID format
        subject_data, lab_category_data, lab_test_data, custom_column_data = generate_lab_test_data(
            num_rows, category_test_mapping, num_subjects, subject_prefix, subject_start, category_column, test_column, custom_columns
        )
        data = {
            "SUBJECT_ID": subject_data,
            category_column: lab_category_data,
            test_column: lab_test_data,
        }
        
        # Add custom columns to the dataset
        for col_name, col_data in custom_column_data.items():
            data[col_name] = col_data

        # Create and display dataset
        dataset = pd.DataFrame(data)
        st.write(dataset)

        # Export dataset as CSV
        st.download_button(
            label="Download Dataset as CSV",
            data=dataset.to_csv(index=False).encode("utf-8"),
            file_name="generated_dataset.csv",
            mime="text/csv",
        )

if __name__ == "__main__":
    main()
