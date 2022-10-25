import dash
from dash import Dash, dcc, html, Input, Output, callback, State
import plotly.express as px
import pandas as pd
import numpy as np
import dash_bootstrap_components as dbc

dash.register_page(__name__,
                   path='/kpi',  # represents the url text
                   name='KPI Browser',  # name of page, commonly used as name of link
                   title='KPI Browser'  # represents the title of browser's tab
                   )

mapbox_access_token = 'pk.eyJ1IjoiaC1yLWdoYW5iYXJpIiwiYSI6ImNsMmZ3YnRzbDBldHozYm56MXBnaWdyY3YifQ.v8KZrsYNGTfg8x67b-sOVA'
# --------------------------------------------------------------------------------------
#Preparing the dataframes
print("reading sector db file. please wait...")
sector_df = pd.read_excel("Sector_DB.xlsx")

print("reading KPI file. please wait...")
kpi_df = pd.read_excel("2GKPI.xlsx", converters={'Date': pd.to_datetime})


KPI_List = [
    k for k in kpi_df.columns if k not in ("BSC", "CELL", "REGION", "PROVINCE", "LAC", "CID", "Date")
]

print("reading ticket file. please wait...")
ticket_df = pd.read_csv("Clarity_09.03.2022.csv")

ticket_df['REPORTED'] = pd.to_datetime(ticket_df['REPORTED'])

# Keeping only the required data
NE_List = ['BTS', 'ENODEB', 'NODEB', 'WBTS']
ticket_df = ticket_df[ticket_df['EQUP_EQUT_ABBREVIATION'].isin(NE_List)]
ticket_df["Issue_Type"] = "KPI_TT"

Avail_KPI = ['TCH_Availability(Nokia_SEG)', 'Cell_Availability_including_blocked_by_user_state(Nokia_UCell)',
             'Cell_Availability_Rate_Include_Blocking(UCell_Eric)', 'TCH_Availability(HU_Cell)',
             'TCH_Availability(Eric_Cell)', 'Radio_Network_Availability_Ratio(Hu_Cell)',
             'cell_availability_include_manual_blocking(Nokia_LTE_CELL_NO_NULL)',
             'Cell_Availability_Rate_Include_Blocking(Cell_EricLTE_NO_NULL)',
             'Cell_Availability_Rate_include_Blocking(Cell_Hu_NO_NULL)'
             ]

ticket_df.loc[ticket_df['DEGRADED_KPI'].isin(Avail_KPI), 'Issue_Type'] = "Avail_TT"
ticket_df = ticket_df.reset_index(drop=True)

# Extracting Site_ID from EQUP_INDEX column, adding Index column and merging with Lat and Long columns
temp = np.where((ticket_df["EQUP_INDEX"].apply(len) > 10),
                ticket_df['EQUP_INDEX'].str.split('|'), #Use the output of this if True
                ticket_df['EQUP_INDEX'].str.split('_') #Else use this.
                )

dft = pd.DataFrame(temp.tolist(), columns=["A", "Site"]) #create a new dataframe with the columns we need
dft['Site'] = dft['Site'].str.strip()

dft.fillna("XX", inplace=True)

#Extracting Site ID
site_temp = np.where((dft["Site"].apply(len) < 8),
                dft['Site'].str[:6], #Use the output of this if True
                dft['Site'].str[:2] + dft['Site'].str[4:8] #Else use this.
                )

site_temp = pd.DataFrame(site_temp.tolist()) # create a new dataframe with the columns we need
ticket_df["Site"] = site_temp
ticket_df["Cell"] = dft['Site']


#Adding Province Index columns
ticket_df["Index"] = ticket_df["Site"].str[:2]
sector_df["Index"] = sector_df["Site"].str[:2]

site_df = sector_df[['Site', 'LATITUDE', 'LONGITUDE', 'Index']].drop_duplicates(subset=['Site'])

ticket_df = ticket_df.merge(site_df[['Site', 'LATITUDE', 'LONGITUDE']], how='left', on='Site')

# dropping rows with no latitude and longitude
ticket_df.dropna(subset=['LATITUDE'], inplace=True)

#Extracting Sector ID
sector_temp = np.where((dft["Site"].apply(len) < 8),
                dft['Site'].str[:], #Use the output of this if True
                dft['Site'].str[:2] + dft['Site'].str[4:9] #Else use this.
                )

sector_temp = pd.DataFrame(sector_temp.tolist()) # create a new dataframe with the columns we need
ticket_df["Sector"] = sector_temp

# print(ticket_df.shape)

ticket_df = ticket_df.merge(sector_df[['Sector', 'AZIMUTH', 'TA', 'Coverage']], how='left', on='Sector')
ticket_df['TA'] = ticket_df['TA'].round(3)


#ticket_df.to_csv('test_output.csv', index=False)

avail_df = ticket_df[ticket_df["Issue_Type"]=="Avail_TT"]

ticket_df = ticket_df[ticket_df["Issue_Type"]=="KPI_TT"]

# filling missing values
# sectors without azimuth will be -1
ticket_df['AZIMUTH'].fillna(-1, inplace=True)
# --------------------------------------------------------------------------------------
layout = html.Div(
    [
        dbc.Container([
            # KPI monitoring line chart
            dbc.Row([
                dbc.Row([
                    dbc.Col([
                        html.Label('KPI Monitoring'),
                    ], width=2),

                    dbc.Col([
                        html.Div(
                            [
                                dbc.Button("Filter", id="kpi-moni-offc-btn", color="secondary", size="sm", n_clicks=0),
                                dbc.Offcanvas(

                                    [
                                        dbc.Col(
                                            [
                                                dbc.RadioItems(
                                                    id="kpi-interval-radios",
                                                    className="btn-group",
                                                    inputClassName="btn-check",
                                                    labelClassName="btn btn-outline-secondary",
                                                    labelCheckedClassName="active",
                                                    options=[
                                                        {"label": "1D", "value": 1},
                                                        {"label": "2D", "value": 2},
                                                        {"label": "3D", "value": 3},
                                                        {"label": "1W", "value": 7},
                                                        {"label": "2W", "value": 14},
                                                        {"label": "3W", "value": 21},
                                                    ],
                                                    value=1,
                                                ),
                                            ],
                                            width={"offset": 2}, className="radio-group",
                                        ),
                                        dcc.Dropdown([x for x in sorted(kpi_df["CELL"].unique())],
                                                     multi=False,
                                                     placeholder='Select Cell',
                                                     id='cell_moni_dpdn',
                                                     style={
                                                         'borderWidth': '0px',
                                                         'font-size': '13px'},
                                                     ),
                                        dcc.Dropdown(sorted(KPI_List),
                                                     multi=False,
                                                     id='kpi_moni_dpdn',
                                                     placeholder='Select KPI',
                                                     style={
                                                         'borderWidth': '0px',
                                                         'font-size': '13px'},
                                                     ),
                                    ],
                                    id="kpi-moni-offc",
                                    title="KPI Monitoring Filters",
                                    placement='end',
                                    is_open=False,
                                ),
                            ]
                        ),
                    ], width=1),

                ], ),  # className='mt-1'

                dbc.Row([
                    html.Hr(),
                    dcc.Graph(id='line_kpi_trend', config={'displayModeBar': True, 'displaylogo': False})
                ], ),  # className='ms-0'
            ], className='shadow bg-white rounded '),  # ms-0 me-0
        ], fluid=True,
        )
    ], id="page-content", )
# --------------------------------------------------------------------------------------
#                                         callbacks
# --------------------------------------------------------------------------------------
@callback(
    Output("kpi-moni-offc", "is_open"),
    Input("kpi-moni-offc-btn", "n_clicks"),
    [State("kpi-moni-offc", "is_open")],
)
def toggle_offcanvas(n1, is_open):
    if n1:
        return not is_open
    return is_open
# --------------------------------------------------------------------------------------
# Line Chart for KPI trend
@callback(
    Output(component_id='line_kpi_trend', component_property='figure'),
    [Input(component_id='kpi-interval-radios', component_property='value'),
     Input(component_id='cell_moni_dpdn', component_property='value'),
     Input(component_id='kpi_moni_dpdn', component_property='value')])
def update_graph(chosen_interval, chosen_cell, chosen_kpi):
    if chosen_cell is not None and chosen_kpi is not None:
        kpi_moni_df = kpi_df[kpi_df["CELL"] == chosen_cell]
        kpi_moni_df = kpi_moni_df[['Date', chosen_kpi]]
        kpi_moni_df = kpi_moni_df.sort_values(by=['Date'])
        kpi_moni_df = kpi_moni_df.tail(24 * chosen_interval)
    else:
        kpi_moni_df = kpi_df

    kpi_moni_fig = px.line(kpi_moni_df, x='Date', y=chosen_kpi, markers=False)

    kpi_moni_fig.update_traces(hovertemplate='%{y}', line=dict(color='rgb(77, 207, 241)', width=1), )

    kpi_moni_fig.update_layout(
        xaxis=dict(
            title='',
            showline=True,
            showgrid=False,
            showticklabels=True,
            linecolor='rgb(204, 204, 204)',
            linewidth=1,
            ticks='outside',
            tickfont=dict(
                family='Arial',
                size=12,
                color='rgb(82, 82, 82)',
            ),
        ),
        yaxis=dict(
            title=chosen_kpi,
            showline=True,
            showgrid=False,
            showticklabels=True,
            linecolor='rgb(204, 204, 204)',
            linewidth=1,
            ticks='outside',
            tickfont=dict(
                family='Arial',
                size=12,
                color='rgb(82, 82, 82)',
            ),
        ),
        margin={'l': 0, 't': 10, 'b': 0, 'r': 10},
        plot_bgcolor='white',
        hovermode="x",
        height=500,
    )

    return (kpi_moni_fig)
