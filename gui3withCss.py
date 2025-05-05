import pandas as pd
from nicegui import ui
import sqlite3

db_name = "data/KYC_DataBase.db"
table_name = "OnboardingData"

def retrieve_data_with_column_name():
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

# Date conversion and computed columns
df['KycRefresh_created_date'] = pd.to_datetime(df['KycRefresh_created_date'], errors='coerce')
df['case_sla_date'] = df['KycRefresh_created_date'] + pd.Timedelta(days=90)
df['case_status_display'] = df['refresh_status'].apply(
    lambda x: "KYC status Refreshed" if str(x).lower() == "yes" else "Profile updates absorbed" if str(x).lower() == "no" else x
)

# Cast relevant columns
for col in ['document_name', 'refresh_status', 'case_status_display', 'entity_legal_name', 'outreach_agent_status']:
    df[col] = df[col].astype(str)

# Pagination settings
ITEMS_PER_PAGE = 5
current_page = 1
total_pages = (len(df) + ITEMS_PER_PAGE - 1) // ITEMS_PER_PAGE

# Filtering logic
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

    # Date filters
    def apply_date_filter(df, column, date_filter):
        try:
            date_range = date_filter.split(' to ')
            if len(date_range) == 2:
                start = pd.to_datetime(date_range[0].strip())
                end = pd.to_datetime(date_range[1].strip())
                return df[(df[column] >= start) & (df[column] <= end)]
        except Exception:
            ui.notify(f"Invalid date format in {column}. Use 'YYYY-MM-DD to YYYY-MM-DD'", type='error')
        return df

    if creation_date_filter:
        filtered_df = apply_date_filter(filtered_df, 'KycRefresh_created_date', creation_date_filter)
    if sla_date_filter:
        filtered_df = apply_date_filter(filtered_df, 'case_sla_date', sla_date_filter)
    if complete_date_filter:
        filtered_df = apply_date_filter(filtered_df, 'KycRefresh_updated_date', complete_date_filter)

    return filtered_df

# Pagination logic
def get_paginated_data(filtered_df, page):
    start = (page - 1) * ITEMS_PER_PAGE
    end = start + ITEMS_PER_PAGE
    return filtered_df.iloc[start:end]

# Table update logic
def update_table(page=1):
    global current_page, total_pages
    current_page = page
    filtered_df = filter_data(
        name_input.value, change_input.value, status_input.value, case_id_input.value,
        data_source_input.value, creation_date_input.value, sla_date_input.value, complete_date_input.value
    )
    total_pages = max(1, (len(filtered_df) + ITEMS_PER_PAGE - 1) // ITEMS_PER_PAGE)
    paginated_df = get_paginated_data(filtered_df, current_page)
    grid.options['rowData'] = paginated_df.to_dict(orient='records')
    grid.update()
    update_pagination_controls()

def update_pagination_controls():
    pagination_label.set_text(f"Page {current_page} of {total_pages}")
    prev_button.props('disabled' if current_page == 1 else '')
    next_button.props('disabled' if current_page == total_pages else '')

# ---------------- UI ----------------

# Inject CSS
ui.add_head_html("""
<style>
    .input-style input {
        border: 1px solid #ccc;
        padding: 8px;
        border-radius: 8px;
        width: 100%;
        font-size: 14px;
    }
    .button-style {
        background-color: #1976d2;
        color: white;
        padding: 10px 16px;
        border-radius: 6px;
        font-weight: bold;
        border: none;
        cursor: pointer;
        transition: background-color 0.3s ease;
    }
    .button-style:hover {
        background-color: #125aa0;
    }
    .pagination-button {
        background-color: #555;
        color: white;
        padding: 6px 14px;
        border-radius: 4px;
        font-weight: bold;
    }
    .pagination-button:disabled {
        background-color: #aaa;
    }
</style>
""")

with ui.header().classes('bg-white shadow-md p-4'):
    ui.label("Event driven KYC Review process: Intelligent Automation using AI agents").style("font-size: 2em; font-weight: bold; color: #2e3b55;")
    ui.label("KYC Data with Column Filters").style("font-size: 1.2em; margin-top: 0.5em; color: #444;")

# Filter inputs
with ui.row().classes('w-full gap-4'):
    name_input = ui.input(label='CLIENT NAME Filter', placeholder='Enter client name').classes('input-style flex-grow')
    change_input = ui.input(label='MATERIAL CHANGE Filter', placeholder='Yes/No').classes('input-style flex-grow')
    status_input = ui.input(label='CASE STATUS Filter', placeholder='Enter status').classes('input-style flex-grow')
    case_id_input = ui.input(label='CASE ID Filter', placeholder='Enter case ID').classes('input-style flex-grow')
    data_source_input = ui.input(label='DATA SOURCE Filter', placeholder='Enter data source').classes('input-style flex-grow')

with ui.row().classes('w-full gap-4'):
    creation_date_input = ui.input(label='CASE CREATION DATE Filter', placeholder='YYYY-MM-DD to YYYY-MM-DD').classes('input-style flex-grow')
    sla_date_input = ui.input(label='CASE SLA DATE Filter', placeholder='YYYY-MM-DD to YYYY-MM-DD').classes('input-style flex-grow')
    complete_date_input = ui.input(label='CASE COMPLETE DATE Filter', placeholder='YYYY-MM-DD to YYYY-MM-DD').classes('input-style flex-grow')

# Buttons
with ui.row().classes('w-full justify-center gap-4 mt-2'):
    ui.button('Apply Filters', on_click=lambda: update_table(1)).classes('button-style')
    ui.button('Reset Filters', on_click=lambda: [
        name_input.set_value(''), change_input.set_value(''), status_input.set_value(''),
        case_id_input.set_value(''), data_source_input.set_value(''),
        creation_date_input.set_value(''), sla_date_input.set_value(''), complete_date_input.set_value(''),
        update_table(1)
    ]).classes('button-style')

# Table
column_defs = [
    {'headerName': 'CLIENT NAME', 'field': 'entity_legal_name'},
    {'headerName': 'MATERIAL CHANGE', 'field': 'refresh_status'},
    {'headerName': 'CASE STATUS', 'field': 'case_status_display'},
    {'headerName': 'CASE ID', 'field': 'outreach_agent_status'},
    {'headerName': 'DATA SOURCE', 'field': 'document_name'},
    {'headerName': 'CASE CREATION DATE', 'field': 'KycRefresh_created_date'},
    {'headerName': 'CASE SLA DATE', 'field': 'case_sla_date'},
    {'headerName': 'CASE COMPLETE DATE', 'field': 'KycRefresh_updated_date'},
]

grid = ui.aggrid(
    {
        'columnDefs': column_defs,
        'rowData': get_paginated_data(df, current_page).to_dict(orient='records'),
        'defaultColDef': {'sortable': True, 'filter': True, 'resizable': True},
    },
    theme='ag-theme-material'
).classes('w-full h-64 mt-4')

# Pagination
with ui.row().classes('w-full justify-center mt-4 gap-4'):
    prev_button = ui.button('Previous', on_click=lambda: update_table(current_page - 1)).classes('pagination-button')
    pagination_label = ui.label(f"Page {current_page} of {total_pages}").classes('text-lg')
    next_button = ui.button('Next', on_click=lambda: update_table(current_page + 1)).classes('pagination-button')

# Initial table load
update_table()

ui.run()
