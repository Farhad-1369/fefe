import dash
from dash import Dash, dcc, html, Input, Output, callback, State
import pandas as pd
import numpy as np
import dash_bootstrap_components as dbc
import plotly.graph_objects as go
import math

dash.register_page(__name__,
                   path='/map',  # represents the url text
                   name='Map View',  # name of page, commonly used as name of link
                   title='Map View'  # represents the title of browser's tab
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
            dbc.Row([
                dbc.Col([
                    dbc.Row([
                        # Line chart for ticket trend
                        dbc.Col([
                            html.Label('Map View'),
                        ], width=3),

                        dbc.Col([
                            dcc.DatePickerSingle(
                                id='map_date_picker',  # ID to be used for callback
                                first_day_of_week=6,  # Display of calendar when open (0 = Sunday)
                                clearable=True,  # whether or not the user can clear the dropdown
                                placeholder='Select a Date',
                                number_of_months_shown=1,  # number of months shown when calendar is open
                                min_date_allowed=ticket_df["REPORTED"].min(),
                                # minimum date allowed on the DatePickerRange component
                                max_date_allowed=ticket_df["REPORTED"].max(),
                                # maximum date allowed on the DatePickerRange component
                                initial_visible_month=ticket_df["REPORTED"].max(),
                                # the month initially presented when the user opens the calendar
                                display_format='MMM Do, YY',
                                # how selected dates are displayed in the DatePickerRange component.
                                month_format='MMMM, YYYY',
                                # how calendar headers are displayed when the calendar is opened.

                            ),

                        ], width=2, ),

                        dbc.Col([
                            dcc.Dropdown([x for x in sorted(ticket_df["Index"].unique())],
                                         multi=False,
                                         id='pro_map_dpdn',
                                         placeholder='Province',
                                         value='KH',
                                         style={
                                             'borderWidth': '0px',
                                             'font-size': '13px'},
                                         ),
                        ], width=2, ),

                        dbc.Col([
                            dcc.Dropdown(sorted(
                                ['open-street-map', 'carto-positron', 'carto-darkmatter', 'stamen-terrain',
                                 'stamen-toner',
                                 'stamen-watercolor', 'basic', 'streets', 'outdoors', 'light', 'dark', 'satellite',
                                 'satellite-streets']),
                                         multi=False,
                                         id='type_map_dpdn',
                                         placeholder='Map Style',
                                         value='light',
                                         style={
                                             'borderWidth': '0px',
                                             'font-size': '13px'},
                                         ),
                        ], width=2, ),

                    ], ),  # className='mt-6'

                    dbc.Row([
                        html.Hr(),
                        dcc.Graph(id='map_sites',
                                  config={'displayModeBar': True, 'scrollZoom': True, 'displaylogo': False}),
                    ], ), ],  # className='ms-0'
                    className='shadow bg-white rounded'), ]),  # ms-0 me-0
        ], fluid=True,
        )
    ], id="page-content", )


# --------------------------------------------------------------------------------------
# functions for drawing sector
def degree2rad(degrees):
    return degrees * np.pi / 180


def sec_poly(long, lat, bearing, radius=0.5, vbw=60):
    R = 6378.1  # Radius of the Earth
    rad_bearing = degree2rad(bearing)

    site_lat = math.radians(lat)  # site lat point converted to radians
    site_lon = math.radians(long)  # site long point converted to radians

    coords = []
    n = 5
    t = np.linspace(degree2rad(bearing - (vbw / 2)), degree2rad(bearing + (vbw / 2)), n)
    for brg in t:
        bor_lat = math.asin(
            math.sin(site_lat) * math.cos(radius / R) + math.cos(site_lat) * math.sin(radius / R) * math.cos(brg))
        bor_lon = site_lon + math.atan2(math.sin(brg) * math.sin(radius / R) * math.cos(site_lat),
                                        math.cos(radius / R) - math.sin(site_lat) * math.sin(bor_lat))

        bor_lat = math.degrees(bor_lat)
        bor_lon = math.degrees(bor_lon)

        coords.append([bor_lon, bor_lat])

    coords.insert(0, [long, lat])
    coords.append([long, lat])

    return (coords)


# --------------------------------------------------------------------------------------
#                                         callbacks
# --------------------------------------------------------------------------------------
# Mapbox for site locations
@callback(Output('map_sites', 'figure'),
          [Input('map_date_picker', 'date'),
           Input('pro_map_dpdn', 'value'),
           Input('type_map_dpdn', 'value'),
           Input("map_sites", "clickData")])
def update_figure(chosen_date, chosen_province, chosen_map, click_data):
    poly_sec_list = []
    map_df = ticket_df
    avail_map_df = avail_df
    site_map_df = site_df
    if chosen_date is not None:
        map_df = map_df[map_df['REPORTED'].dt.strftime('%Y-%m-%d') == chosen_date]
        avail_map_df = avail_map_df[avail_map_df['REPORTED'].dt.strftime('%Y-%m-%d') == chosen_date]
    if chosen_province is not None:
        map_df = map_df[map_df['Index'] == chosen_province]
        avail_map_df = avail_map_df[avail_map_df['Index'] == chosen_province]
        site_map_df = site_map_df[site_map_df['Index'] == chosen_province]
    if click_data is not None:
        poly_sec_list = sec_poly(long=click_data["points"][0]["customdata"][29],
                                 lat=click_data["points"][0]["customdata"][28],
                                 bearing=click_data["points"][0]["customdata"][31],
                                 radius=click_data["points"][0]["customdata"][32])
        # print(poly_sec_list)
    if chosen_map is not None:
        map_style = chosen_map
    else:
        map_style = 'white-bg'

    fig = go.Figure()

    # showing sites on map
    fig.add_trace(go.Scattermapbox(
        lat=site_map_df['LATITUDE'],
        lon=site_map_df['LONGITUDE'],
        mode='markers',
        marker=go.scattermapbox.Marker(
            size=8,
            color='rgb(0, 0, 255)',
            opacity=1
        ),
        text="",
        hoverinfo='none',
        name="Sites",
        unselected={'marker': {'opacity': 1, 'size': 8}},
        selected={'marker': {'opacity': 0.5, 'size': 20}},
    ))

    # showing Avail. tickets on map
    fig.add_trace(go.Scattermapbox(
        lat=avail_map_df['LATITUDE'],
        lon=avail_map_df['LONGITUDE'],
        mode='markers',
        marker=go.scattermapbox.Marker(
            size=15,
            color='rgb(255, 0, 0)',
            opacity=1
        ),
        text="",
        hoverinfo='none',
        name="Availability",
        unselected={'marker': {'opacity': 1, 'size': 15}},
        selected={'marker': {'opacity': 0.5, 'size': 30}},
    ))

    # showing KPI tickets on map
    fig.add_trace(go.Scattermapbox(
        lat=map_df['LATITUDE'],
        lon=map_df['LONGITUDE'],
        mode='markers',
        marker=go.scattermapbox.Marker(
            size=10,
            color='rgb(255, 255, 0)',
            opacity=1
        ),
        name="KPI Issue",
        unselected={'marker': {'opacity': 1, 'size': 10}},
        selected={'marker': {'opacity': 0.5, 'size': 15}},
        hoverinfo='text',
        customdata=map_df,
        hovertemplate=
        "NE: %{customdata[26]}<br>" +
        "KPI: %{customdata[5]}<br>" +
        "Root Cause: %{customdata[14]}<br>" +
        "Alram Count: %{customdata[18]}<br>" +
        "TA(Km): %{customdata[32]}<br>" +
        "Coverage Type: %{customdata[33]}<br>" +
        "Azimuth: %{customdata[31]}<extra></extra>",
    ))

    fig.update_layout(
        uirevision='foo',  # preserves state of figure/map after callback activated
        showlegend=True,
        clickmode='event+select',
        hovermode='closest',
        hoverdistance=2,
        height=500,
        margin={'l': 0, 't': 0, 'b': 5, 'r': 0},
        legend=dict(
            x=0,
            y=1,
            title="",
            bgcolor='rgba(255, 255, 255, 0)',
            bordercolor='rgba(255, 255, 255, 0)',
            font=dict(color='blue')
        ),
        mapbox=dict(
            accesstoken=mapbox_access_token,
            layers=
            [{
                'source': {
                    'type': "FeatureCollection",
                    'features': [{
                        'type': "Feature",
                        'geometry': {
                            'type': "MultiPolygon",
                            'coordinates': [[poly_sec_list]]
                        }
                    }]
                },
                'type': "fill", 'below': "traces", 'color': "green", 'opacity': 0.3}],
            style=map_style,
            bearing=0,
            center=dict(
                lat=map_df['LATITUDE'].mean(),
                lon=map_df['LONGITUDE'].mean(),
            ),
            pitch=0,
            zoom=7
        ),
    )

    return fig
