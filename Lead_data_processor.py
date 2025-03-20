import streamlit as st
import pandas as pd
import datetime
import os
import io
import zipfile

def process_and_combine(uploaded_files):
    """Processes uploaded files, combines data, and removes duplicates."""
    combined_data = pd.DataFrame()
    for file in uploaded_files:
        try:
            if file.name.endswith('.csv'):
                df = pd.read_csv(file)
            elif file.name.endswith(('.xls', '.xlsx')):
                df = pd.read_excel(file)
            else:
                st.error(f"Unsupported file type: {file.name}")
                continue
            combined_data = pd.concat([combined_data, df], ignore_index=True)
        except Exception as e:
            st.error(f"Error processing {file.name}: {e}")
            return None
    if combined_data.empty:
        st.warning("No data to process.")
        return None

    # Deduplication logic
    if 'full_name' in combined_data.columns and 'linkedin' in combined_data.columns:
        combined_data = combined_data.drop_duplicates(subset=['full_name', 'linkedin'], keep='first')
    elif 'full_name' in combined_data.columns:
        combined_data = combined_data.drop_duplicates(subset=['full_name'], keep='first')
    elif 'linkedin' in combined_data.columns:
        combined_data = combined_data.drop_duplicates(subset=['linkedin'], keep='first')
    else:
        st.error("Neither 'full_name' nor 'linkedin' columns found. Cannot remove duplicates.")
        return None
    return combined_data

def download_csv(df, filename):
    """Generates a download link for a DataFrame as a CSV."""
    csv = df.to_csv(index=False).encode('utf-8')
    st.download_button(
        label="Download Combined Leads",
        data=csv,
        file_name=filename,
        mime='text/csv',
    )

def process_and_clean_single(uploaded_file):
    """Processes a single file and removes duplicates."""
    try:
        if uploaded_file.name.endswith('.csv'):
            df = pd.read_csv(uploaded_file)
        elif uploaded_file.name.endswith(('.xls', '.xlsx')):
            df = pd.read_excel(uploaded_file)
        else:
            st.error(f"Unsupported file type: {uploaded_file.name}")
            return None

        # Deduplication logic
        if 'full_name' in df.columns and 'linkedin' in df.columns:
            df = df.drop_duplicates(subset=['full_name', 'linkedin'], keep='first')
        elif 'full_name' in df.columns:
            df = df.drop_duplicates(subset=['full_name'], keep='first')
        elif 'linkedin' in df.columns:
            df = df.drop_duplicates(subset=['linkedin'], keep='first')
        else:
            st.error("Neither 'full_name' nor 'linkedin' columns found. Cannot remove duplicates.")
            return None
        return df
    except Exception as e:
        st.error(f"Error processing {uploaded_file.name}: {e}")
        return None

def download_cleaned_csv(df, filename):
    """Generates a download link for a cleaned DataFrame as a CSV."""
    csv = df.to_csv(index=False).encode('utf-8')
    st.download_button(
        label=f"Download {filename}",
        data=csv,
        file_name=filename,
        mime='text/csv',
    )

def check_and_clean(reference_df, files_to_check):
    """Checks files against reference, removes duplicates within files, and removes reference duplicates."""
    cleaned_files = []
    for file in files_to_check:
        try:
            if file.name.endswith('.csv'):
                df = pd.read_csv(file)
            elif file.name.endswith(('.xls', '.xlsx')):
                df = pd.read_excel(file)
            else:
                st.error(f"Unsupported file type: {file.name}")
                continue

            # Deduplicate within the file first
            if 'full_name' in df.columns and 'linkedin' in df.columns:
                df = df.drop_duplicates(subset=['full_name', 'linkedin'], keep='first')
            elif 'full_name' in df.columns:
                df = df.drop_duplicates(subset=['full_name'], keep='first')
            elif 'linkedin' in df.columns:
                df = df.drop_duplicates(subset=['linkedin'], keep='first')
            else:
                st.error("Neither 'full_name' nor 'linkedin' columns found in check file.")
                continue

            # Remove reference duplicates
            if 'full_name' in reference_df.columns and 'linkedin' in reference_df.columns and 'full_name' in df.columns and 'linkedin' in df.columns:
                df = df[~df.set_index(['full_name', 'linkedin']).index.isin(reference_df.set_index(['full_name', 'linkedin']).index)]
            elif 'full_name' in reference_df.columns and 'full_name' in df.columns:
                df = df[~df['full_name'].isin(reference_df['full_name'])]
            elif 'linkedin' in reference_df.columns and 'linkedin' in df.columns:
                df = df[~df['linkedin'].isin(reference_df['linkedin'])]
            else:
                st.error("Columns mismatch between reference and check files.")
                continue

            cleaned_files.append(df)
        except Exception as e:
            st.error(f"Error processing {file.name}: {e}")
    return cleaned_files

def inmail_and_invite_separator(uploaded_files):
    """Splits files by 'open' status (TRUE/FALSE) and provides download links."""
    split_files = {}
    for file in uploaded_files:
        try:
            if file.name.endswith('.csv'):
                df = pd.read_csv(file)
            elif file.name.endswith(('.xls', '.xlsx')):
                df = pd.read_excel(file)
            else:
                st.error(f"Unsupported file type: {file.name}")
                continue

            if 'open' not in df.columns:
                st.error(f"Column 'open' not found in {file.name}")
                continue

            true_df = df[df['open'] == True]
            false_df = df[df['open'] == False]

            split_files[file.name] = {'TRUE': true_df, 'FALSE': false_df}

        except Exception as e:
            st.error(f"Error processing {file.name}: {e}")
    return split_files

def main():
    st.title("Lead Data Cleaning and Processing")

    program_choice = st.radio("Select Program:", ("Combine and Clean", "Clean Single Files", "Check Against Reference", "Inmail and Invite Separator"))

    if program_choice == "Combine and Clean":
        uploaded_files = st.file_uploader("Upload CSV or Excel files", type=['csv', 'xls', 'xlsx'], accept_multiple_files=True, key="combine_upload")
        if uploaded_files:
            st.subheader("Uploaded Files:")
            for file in uploaded_files:
                st.write(file.name)
            if st.button("Start Processing (Combine)"):
                combined_data = process_and_combine(uploaded_files)
                if combined_data is not None and not combined_data.empty:
                    now = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
                    filename = f"COMBINED_CLEAN_LEADS_{now}.csv"
                    download_csv(combined_data, filename)

    elif program_choice == "Clean Single Files":
        uploaded_files = st.file_uploader("Upload CSV or Excel files", type=['csv', 'xls', 'xlsx'], accept_multiple_files=True, key="clean_single_upload")
        if uploaded_files:
            st.subheader("Uploaded Files:")
            for file in uploaded_files:
                st.write(file.name)
            if st.button("Start Processing (Clean Single)"):
                for file in uploaded_files:
                    cleaned_data = process_and_clean_single(file)
                    if cleaned_data is not None and not cleaned_data.empty:
                        filename = f"{os.path.splitext(file.name)[0]}_CLEAN.csv"
                        download_cleaned_csv(cleaned_data, filename)

    elif program_choice == "Check Against Reference":
        reference_file = st.file_uploader("Upload Reference CSV or Excel file", type=['csv', 'xls', 'xlsx'], key="reference_upload")
        files_to_check = st.file_uploader("Upload CSV or Excel files to check", type=['csv', 'xls', 'xlsx'], accept_multiple_files=True, key="check_files_upload")

        if reference_file and files_to_check:
            st.subheader("Reference File:")
            st.write(reference_file.name)
            st.subheader("Files to Check:")
            for file in files_to_check:
                st.write(file.name)

            if st.button("Start Processing (Check Against Reference)"):
                try:
                    if reference_file.name.endswith('.csv'):
                        reference_df = pd.read_csv(reference_file)
                    elif reference_file.name.endswith(('.xls', '.xlsx')):
                        reference_df = pd.read_excel(reference_file)
                    else:
                        st.error(f"Unsupported file type for reference file: {reference_file.name}")
                        return

                    cleaned_files = check_and_clean(reference_df, files_to_check)
                    if cleaned_files:
                        now = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
                        zip_filename = f"CHECKED_CLEANED_LEADS_{now}.zip"
                        zip_buffer = io.BytesIO()
                        with zipfile.ZipFile(zip_buffer, 'w') as zip_file:
                            for i, cleaned_df in enumerate(cleaned_files):
                                if not cleaned_df.empty:  # Only create file if not empty
                                    filename = f"{os.path.splitext(files_to_check[i].name)[0]}_CHECKED_CLEANED.csv"
                                    csv_data = cleaned_df.to_csv(index=False).encode('utf-8')
                                    zip_file.writestr(filename, csv_data)
                        zip_buffer.seek(0)
                        st.download_button(
                            label="Download Checked and Cleaned Files (ZIP)",
                            data=zip_buffer,
                            file_name=zip_filename,
                            mime='application/zip',
                        )
                    else:
                        st.info("No files were cleaned or they were all empty after processing.")
                except Exception as e:
                    st.error(f"An error occurred during processing: {e}")

    elif program_choice == "Inmail and Invite Separator":
        uploaded_files = st.file_uploader("Upload CSV or Excel files", type=['csv', 'xls', 'xlsx'], accept_multiple_files=True, key="split_upload")

        if uploaded_files:
            if "download_data" not in st.session_state:
                st.session_state.download_data = {}

            if st.button("Split and Generate Download Buttons"):
                split_data = inmail_and_invite_separator(uploaded_files)
                st.session_state.download_data = {}  # Clear previous data

                for filename, status_dfs in split_data.items():
                    if not status_dfs['TRUE'].empty:
                        true_filename = f"{os.path.splitext(filename)[0]}_Inmail.csv"
                        true_csv = status_dfs['TRUE'].to_csv(index=False).encode('utf-8')
                        st.session_state.download_data[true_filename] = true_csv

                    if not status_dfs['FALSE'].empty:
                        false_filename = f"{os.path.splitext(filename)[0]}_Invite.csv"
                        false_csv = status_dfs['FALSE'].to_csv(index=False).encode('utf-8')
                        st.session_state.download_data[false_filename] = false_csv

            for filename, data in st.session_state.download_data.items():
                st.download_button(
                    label=f"Download {filename}",
                    data=data,
                    file_name=filename,
                    mime='text/csv',
                )

            if st.session_state.download_data:
                if st.button("Download All as ZIP"):
                    zip_buffer = io.BytesIO()
                    with zipfile.ZipFile(zip_buffer, 'w') as zip_file:
                        for filename, data in st.session_state.download_data.items():
                            zip_file.writestr(filename, data)

                    zip_buffer.seek(0)
                    st.download_button(
                        label="Download All Files.zip",
                        data=zip_buffer,
                        file_name="AllFiles.zip",
                        mime='application/zip',
                    )

    if st.button("Reset"):
        st.experimental_rerun()

if __name__ == "__main__":
    main()
