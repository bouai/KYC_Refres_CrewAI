import pandas as pd
from nicegui import ui
import sqlite3

db_name = "data/KYC_DataBase.db"
table_name = "OnboardingData"

def retrieve_data_with_column_name():
    """
    Retrieves all data from a specified SQLite table and returns each row with its corresponding column names as a dictionary.
    """
    try:
        with sqlite3.connect(db_name) as conn:
            cursor = conn.cursor()
            cursor.execute(f"SELECT * FROM {table_name}")
            rows = cursor.fetchall()
            column_names = [description[0] for description in cursor.description]
            row_data = [dict(zip(column_names, row)) for row in rows]
            return row_data
    except sqlite3.Error as e:
        print(e)
        return []

# Load data from DB into a DataFrame
data = retrieve_data_with_column_name()
df = pd.DataFrame(data)

# Convert KycRefresh_created_date to datetime and calculate case_sla_date as KycRefresh_created_date + 90 days
df['KycRefresh_created_date'] = pd.to_datetime(df['KycRefresh_created_date'], errors='coerce')
df['case_sla_date'] = df['KycRefresh_created_date'] + pd.Timedelta(days=90)

# Add computed column for CASE STATUS based on refresh_status
df['case_status_display'] = df['refresh_status'].apply(
    lambda x: "KYC status Refreshed" if str(x).lower() == "yes" else "Profile updates absorbed" if str(x).lower() == "no" else x
)

# Convert relevant columns to strings to avoid issues during filtering
df['document_name'] = df['document_name'].astype(str)
df['refresh_status'] = df['refresh_status'].astype(str)
df['case_status_display'] = df['case_status_display'].astype(str)
df['entity_legal_name'] = df['entity_legal_name'].astype(str)
df['outreach_agent_status'] = df['outreach_agent_status'].astype(str)

# Pagination settings
ITEMS_PER_PAGE = 5
current_page = 1
total_pages = (len(df) + ITEMS_PER_PAGE - 1) // ITEMS_PER_PAGE

# Function to filter the DataFrame based on user inputs
def filter_data(name_filter, change_filter, status_filter, case_id_filter, data_source_filter, creation_date_filter, sla_date_filter, complete_date_filter):
    filtered_df = df.copy()

    if name_filter:
        filtered_df = filtered_df[filtered_df['entity_legal_name'].str.contains(name_filter, case=False, na=False)]

    if change_filter:
        filtered_df = filtered_df[filtered_df['refresh_status'].str.contains(change_filter, case=False, na=False)]

    if status_filter:
        filtered_df = filtered_df[filtered_df['case_status_display'].str.contains(status_filter, case=False, na=False)]

    if case_id_filter:
        filtered_df = filtered_df[filtered_df['outreach_agent_status'].str.contains(case_id_filter, case=False, na=False)]

    if data_source_filter:
        filtered_df = filtered_df[filtered_df['document_name'].str.contains(data_source_filter, case=False, na=False)]

    if creation_date_filter:
        try:
            date_range = creation_date_filter.split(' to ')
            if len(date_range) == 2:
                start_date = pd.to_datetime(date_range[0].strip())
                end_date = pd.to_datetime(date_range[1].strip())
                filtered_df = filtered_df[
                    (filtered_df['KycRefresh_created_date'] >= start_date) &
                    (filtered_df['KycRefresh_created_date'] <= end_date)
                ]
        except (ValueError, TypeError):
            ui.notify("Invalid CASE CREATION DATE range. Use format 'YYYY-MM-DD to YYYY-MM-DD'", type='error')
            return pd.DataFrame()

    if sla_date_filter:
        try:
            date_range = sla_date_filter.split(' to ')
            if len(date_range) == 2:
                start_date = pd.to_datetime(date_range[0].strip())
                end_date = pd.to_datetime(date_range[1].strip())
                filtered_df = filtered_df[
                    (filtered_df['case_sla_date'] >= start_date) &
                    (filtered_df['case_sla_date'] <= end_date)
                ]
        except (ValueError, TypeError):
            ui.notify("Invalid CASE SLA DATE range. Use format 'YYYY-MM-DD to YYYY-MM-DD'", type='error')
            return pd.DataFrame()

    if complete_date_filter:
        try:
            date_range = complete_date_filter.split(' to ')
            if len(date_range) == 2:
                start_date = pd.to_datetime(date_range[0].strip())
                end_date = pd.to_datetime(date_range[1].strip())
                filtered_df = filtered_df[
                    (filtered_df['KycRefresh_updated_date'] >= start_date) &
                    (filtered_df['KycRefresh_updated_date'] <= end_date)
                ]
        except (ValueError, TypeError):
            ui.notify("Invalid CASE COMPLETE DATE range. Use format 'YYYY-MM-DD to YYYY-MM-DD'", type='error')
            return pd.DataFrame()

    return filtered_df

# Function to paginate the filtered data
def get_paginated_data(filtered_df, page):
    start = (page - 1) * ITEMS_PER_PAGE
    end = start + ITEMS_PER_PAGE
    return filtered_df.iloc[start:end]

# Function to update the table with filtered and paginated data
def update_table(page=1):
    global current_page, total_pages
    current_page = page
    name_filter = name_input.value
    change_filter = change_input.value
    status_filter = status_input.value
    case_id_filter = case_id_input.value
    data_source_filter = data_source_input.value
    creation_date_filter = creation_date_input.value
    sla_date_filter = sla_date_input.value
    complete_date_filter = complete_date_input.value
    filtered_df = filter_data(name_filter, change_filter, status_filter, case_id_filter, data_source_filter, creation_date_filter, sla_date_filter, complete_date_filter)
    total_pages = (len(filtered_df) + ITEMS_PER_PAGE - 1) // ITEMS_PER_PAGE
    if len(filtered_df) == 0:
        total_pages = 1  # Set total_pages to 1 if filtered DataFrame is empty
    paginated_df = get_paginated_data(filtered_df, current_page)
    grid.options['rowData'] = paginated_df.to_dict(orient='records')
    grid.update()
    update_pagination_controls()

# Function to update pagination controls
def update_pagination_controls():
    pagination_label.set_text(f"Page {current_page} of {total_pages}")
    prev_button.props('disabled' if current_page == 1 else '')
    next_button.props('disabled' if current_page == total_pages else '')

# UI elements
with ui.header():
    ui.label("Event driven KYC Review process : Intelligent Automation using AI agents").style("font-size: 2.0em; font-weight: bold")
    ui.space()
    ui.label("KYC Data with Column Filters").style("font-size: 1.2em;")

# Filter inputs for all columns
with ui.row().classes('w-full gap-4'):
    name_input = ui.input(label='CLIENT NAME Filter', placeholder='Enter client name').classes('flex-grow')
    change_input = ui.input(label='MATERIAL CHANGE Filter', placeholder='Yes/No').classes('flex-grow')
    status_input = ui.input(label='CASE STATUS Filter', placeholder='Enter status').classes('flex-grow')
    case_id_input = ui.input(label='CASE ID Filter', placeholder='Enter case ID').classes('flex-grow')
    data_source_input = ui.input(label='DATA SOURCE Filter', placeholder='Enter data source').classes('flex-grow')

with ui.row().classes('w-full gap-4'):
    creation_date_input = ui.input(label='CASE CREATION DATE Filter', placeholder='YYYY-MM-DD to YYYY-MM-DD').classes('flex-grow')
    sla_date_input = ui.input(label='CASE SLA DATE Filter', placeholder='YYYY-MM-DD to YYYY-MM-DD').classes('flex-grow')
    complete_date_input = ui.input(label='CASE COMPLETE DATE Filter', placeholder='YYYY-MM-DD to YYYY-MM-DD').classes('flex-grow')

# Filter and reset buttons
with ui.row().classes('w-full justify-center'):
    filter_button = ui.button('Apply Filters', on_click=lambda: update_table(1)).classes('w-40')
    reset_button = ui.button('Reset Filters', on_click=lambda: [
        name_input.set_value(''),
        change_input.set_value(''),
        status_input.set_value(''),
        case_id_input.set_value(''),
        data_source_input.set_value(''),
        creation_date_input.set_value(''),
        sla_date_input.set_value(''),
        complete_date_input.set_value(''),
        update_table(1)
    ]).classes('w-40')

# Define table columns based on the image
column_defs = [
    {'headerName': 'CLIENT NAME', 'field': 'entity_legal_name', 'filter': 'agTextColumnFilter'},
    {'headerName': 'MATERIAL CHANGE', 'field': 'refresh_status', 'filter': 'agTextColumnFilter'},
    {'headerName': 'CASE STATUS', 'field': 'case_status_display', 'filter': 'agTextColumnFilter'},
    {'headerName': 'CASE ID', 'field': 'outreach_agent_status', 'filter': 'agTextColumnFilter'},
    {'headerName': 'DATA SOURCE', 'field': 'document_name', 'filter': 'agTextColumnFilter'},
    {'headerName': 'CASE CREATION DATE', 'field': 'KycRefresh_created_date', 'filter': 'agDateColumnFilter'},
    {'headerName': 'CASE SLA DATE', 'field': 'case_sla_date', 'filter': 'agDateColumnFilter'},
    {'headerName': 'CASE COMPLETE DATE', 'field': 'KycRefresh_updated_date', 'filter': 'agDateColumnFilter'},
]

# Create the table (ag-grid)
grid = ui.aggrid(
    {
        'columnDefs': column_defs,
        'rowData': get_paginated_data(df, current_page).to_dict(orient='records'),
        'defaultColDef': {'sortable': True, 'filter': True, 'resizable': True},
    },
    theme='ag-theme-material'
).classes('w-full h-64')

# Pagination controls
with ui.row().classes('w-full justify-center mt-4'):
    prev_button = ui.button('Previous', on_click=lambda: update_table(current_page - 1)).classes('w-32')
    pagination_label = ui.label(f"Page {current_page} of {total_pages}").classes('mx-4')
    next_button = ui.button('Next', on_click=lambda: update_table(current_page + 1)).classes('w-32')

# Initial update of the table
update_table()

ui.run()