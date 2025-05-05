import pandas as pd
from nicegui import ui
import sqlite3
import random

db_name = "data/KYC_DataBase.db"
table_name = "OnboardingData"

def retrieve_data_with_column_name(case_id=None):
    """
    Retrieves data from the SQLite table. If case_id is provided, filters by outreach_agent_status.
    Returns each row with its corresponding column names as a dictionary.
    """
    try:
        with sqlite3.connect(db_name) as conn:
            cursor = conn.cursor()
            if case_id:
                cursor.execute(f"SELECT * FROM {table_name} WHERE outreach_agent_status = ?", (case_id,))
            else:
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

# Convert KycRefresh_created_date to datetime and calculate case_sla_date
df['KycRefresh_created_date'] = pd.to_datetime(df['KycRefresh_created_date'], errors='coerce')
df['case_sla_date'] = df['KycRefresh_created_date'] + pd.Timedelta(days=90)

# Add computed column for CASE STATUS
df['case_status_display'] = df['refresh_status'].apply(
    lambda x: "KYC status Refreshed" if str(x).lower() == "yes" else "Profile updates absorbed" if str(x).lower() == "no" else x
)

# Convert relevant columns to strings
df['document_name'] = df['document_name'].astype(str)
df['refresh_status'] = df['refresh_status'].astype(str)
df['case_status_display'] = df['case_status_display'].astype(str)
df['entity_legal_name'] = df['entity_legal_name'].astype(str)
df['outreach_agent_status'] = df['outreach_agent_status'].astype(str)

# Pagination settings
ITEMS_PER_PAGE = 5
current_page = 1
total_pages = (len(df) + ITEMS_PER_PAGE - 1) // ITEMS_PER_PAGE

# Function to filter the DataFrame
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

# Function to update the table
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
        total_pages = 1
    paginated_df = get_paginated_data(filtered_df, current_page)
    grid.options['rowData'] = paginated_df.to_dict(orient='records')
    grid.update()
    update_pagination_controls()

# Function to update pagination controls
def update_pagination_controls():
    pagination_label.set_text(f"Page {current_page} of {total_pages}")
    prev_button.props('disabled' if current_page == 1 else '')
    next_button.props('disabled' if current_page == total_pages else '')

# Main page UI
@ui.page('/')
def main_page():
    with ui.header():
        ui.label("Event driven KYC Review process : Intelligent Automation using AI agents").style("font-size: 2.0em; font-weight: bold")
        ui.space()
        ui.label("KYC Data with Column Filters").style("font-size: 1.2em;")

    # Filter inputs
    with ui.row().classes('w-full gap-4'):
        global name_input, change_input, status_input, case_id_input, data_source_input
        name_input = ui.input(label='CLIENT NAME Filter', placeholder='Enter client name').classes('flex-grow')
        change_input = ui.input(label='MATERIAL CHANGE Filter', placeholder='Yes/No').classes('flex-grow')
        status_input = ui.input(label='CASE STATUS Filter', placeholder='Enter status').classes('flex-grow')
        case_id_input = ui.input(label='CASE ID Filter', placeholder='Enter case ID').classes('flex-grow')
        data_source_input = ui.input(label='DATA SOURCE Filter', placeholder='Enter data source').classes('flex-grow')

    with ui.row().classes('w-full gap-4'):
        global creation_date_input, sla_date_input, complete_date_input
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

    # Define table columns with clickable CLIENT NAME
    column_defs = [
        {
            'headerName': 'CLIENT NAME',
            'field': 'entity_legal_name',
            'filter': 'agTextColumnFilter',
            'cellRenderer': lambda params: f'<a href="/client/{params.data["outreach_agent_status"]}" target="_self">{params.value}</a>'
        },
        {'headerName': 'MATERIAL CHANGE', 'field': 'refresh_status', 'filter': 'agTextColumnFilter'},
        {'headerName': 'CASE STATUS', 'field': 'case_status_display', 'filter': 'agTextColumnFilter'},
        {'headerName': 'CASE ID', 'field': 'outreach_agent_status', 'filter': 'agTextColumnFilter'},
        {'headerName': 'DATA SOURCE', 'field': 'document_name', 'filter': 'agTextColumnFilter'},
        {'headerName': 'CASE CREATION DATE', 'field': 'KycRefresh_created_date', 'filter': 'agDateColumnFilter'},
        {'headerName': 'CASE SLA DATE', 'field': 'case_sla_date', 'filter': 'agDateColumnFilter'},
        {'headerName': 'CASE COMPLETE DATE', 'field': 'KycRefresh_updated_date', 'filter': 'agDateColumnFilter'},
    ]

    # Create the table
    global grid
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
        global prev_button, pagination_label, next_button
        prev_button = ui.button('Previous', on_click=lambda: update_table(current_page - 1)).classes('w-32')
        pagination_label = ui.label(f"Page {current_page} of {total_pages}").classes('mx-4')
        next_button = ui.button('Next', on_click=lambda: update_table(current_page + 1)).classes('w-32')

    # Initial table update
    update_table()

# Client details page
@ui.page('/client/{case_id}')
def client_details_page(case_id: str):
    # Fetch client data
    client_data = retrieve_data_with_column_name(case_id)
    if not client_data:
        ui.notify(f"No data found for Case ID: {case_id}", type='error')
        ui.navigate.to('/')
        return

    client = client_data[0]  # Expecting one record

    # Header
    with ui.header():
        ui.label(f"Client Details: {client['entity_legal_name']}").style("font-size: 2.0em; font-weight: bold")
        ui.space()
        ui.button('Back to Dashboard', on_click=lambda: ui.navigate.to('/')).classes('w-40')

    # Main content
    with ui.column().classes('w-full max-w-6xl mx-auto mt-4'):
        # Client Information (Top Left)
        with ui.card().classes('w-full p-4'):
            ui.label('Client Information').style('font-size: 1.5em; font-weight: bold; color: #1976D2')
            ui.separator()
            with ui.column().classes('w-full'):
                ui.label(f"Client Name: {client['entity_legal_name']}").style('font-size: 1.1em')
                ui.label(f"Client Identifier: {client['outreach_agent_status']}").style('font-size: 1.1em')
                ui.label(f"Client Type: Bank").style('font-size: 1.1em')
                ui.label(f"Client Domicile Country: N/A").style('font-size: 1.1em')
                ui.label(f"Client Specific Documents: {client['document_name']}").style('font-size: 1.1em')

        # Client Profile Before and After (Middle Row)
        with ui.row().classes('w-full gap-4'):
            # Before KYC Refresh (Left)
            with ui.card().classes('w-1/2 p-4'):
                ui.label('Client Profile Before KYC Refresh').style('font-size: 1.5em; font-weight: bold; color: #1976D2')
                ui.separator()
                ui.label(f"Refresh Status: {client['refresh_status']}").style('font-size: 1.1em')
                ui.label(f"Created Date: {client['KycRefresh_created_date']}").style('font-size: 1.1em')
                ui.label(f"Updated Date: {client['KycRefresh_updated_date']}").style('font-size: 1.1em')

            # Post KYC Refresh (Right)
            with ui.card().classes('w-1/2 p-4'):
                ui.label('Client Profile Post KYC Refresh').style('font-size: 1.5em; font-weight: bold; color: #1976D2')
                ui.separator()
                ui.label(f"Refresh Status: {client['refresh_status']}").style('font-size: 1.1em')
                ui.label(f"Case Status: {client['case_status_display']}").style('font-size: 1.1em; color: green; font-weight: bold')  # Highlighted
                ui.label(f"SLA Date: {client['case_sla_date']}").style('font-size: 1.1em')

        # Screening Details and Workflow (Bottom Row)
        with ui.row().classes('w-full gap-4'):
            # Screening Details (Left)
            with ui.card().classes('w-1/2 p-4'):
                ui.label('Screening Details').style('font-size: 1.5em; font-weight: bold; color: #1976D2')
                ui.separator()
                ui.label(f"HIT Number: {random.randint(1000, 9999)}").style('font-size: 1.1em')
                ui.label(f"HIT Type: True match").style('font-size: 1.1em')
                ui.label(f"User Investigates: True match").style('font-size: 1.1em')
                ui.label(f"Comment: No screening hit received").style('font-size: 1.1em')

            # Workflow Diagram (Right)
            with ui.card().classes('w-1/2 p-4'):
                ui.label('Workflow').style('font-size: 1.5em; font-weight: bold; color: #1976D2')
                ui.separator()
                # Custom HTML for the flowchart
                ui.element('div').html("""
                    <style>
                        .flowchart {
                            display: flex;
                            align-items: center;
                            justify-content: space-between;
                            width: 100%;
                        }
                        .flowchart-step {
                            background-color: #4CAF50;
                            color: white;
                            border-radius: 50%;
                            width: 80px;
                            height: 80px;
                            display: flex;
                            align-items: center;
                            justify-content: center;
                            text-align: center;
                            font-size: 0.8em;
                            padding: 5px;
                            position: relative;
                        }
                        .flowchart-step:not(:last-child)::after {
                            content: '→';
                            position: absolute;
                            right: -20px;
                            color: #4CAF50;
                            font-size: 1.5em;
                        }
                    </style>
                    <div class="flowchart">
                        <div class="flowchart-step">Data fetched from external sources</div>
                        <div class="flowchart-step">Material changes</div>
                        <div class="flowchart-step">No information gaps</div>
                        <div class="flowchart-step">Profile updated</div>
                        <div class="flowchart-step">Screening completed</div>
                    </div>
                """).classes('w-full')

ui.run()