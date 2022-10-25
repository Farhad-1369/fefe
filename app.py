import dash
import dash_bootstrap_components as dbc
from dash import html
# ----------------------------------------------------------------------------------
app = dash.Dash(
    __name__,
    use_pages=True,
    external_stylesheets=[dbc.themes.BOOTSTRAP],
)
# ----------------------------------------------------------------------------------
NAVBAR_STYLE = {
    "top": 0,
    "left": 0,
    "right": 0,
    "height": 64,
    # "padding": "0rem 0rem",
}
# ----------------------------------------------------------------------------------
navbar = dbc.NavbarSimple(
    dbc.Nav(
        [
            dbc.NavLink(page["name"], href=page["path"])
            for page in dash.page_registry.values()
            if page.get("top_nav")
        ],
    ),
    brand="Data Driven Services",
    color="dark",
    dark=True,
    className="lead",
    fixed="top",
    style=NAVBAR_STYLE,
)
# ----------------------------------------------------------------------------------
SIDEBAR_STYLE = {
    "position": "fixed",
    "top": 64,
    "left": 0,
    "bottom": 0,
    "width": "13rem",
    "height": "100%",
    "padding": "0.5rem",
    "background-color": "#EAEAEA",
    # "overflow": "scroll",
    # "z-index": 1,
    # "overflow-x": "hidden",
    # "transition": "all 0.5s",
}
# ----------------------------------------------------------------------------------
sidebar = html.Div([
    html.Div([
        # adding logo to sidebar
        dbc.Col(html.Img(src='assets/STS_Logo.png', height="80px", style={"width": "10rem"}), )
    ],
    ),
    html.Hr(),
    dbc.Nav(
        [
            dbc.NavLink(
                [
                    html.Div(page["name"], className="ms-2"),
                ],
                href=page["path"],
                active="exact",
            )
            for page in dash.page_registry.values()
        ],
        vertical=True,
        pills=True,
    )
], style=SIDEBAR_STYLE)
# ----------------------------------------------------------------------------------
CONTENT_STYLE = {
    # "transition": "margin-left .5s",
    #"margin-left": "2rem",
    #"margin-right": "2rem",
    #"padding": "2rem 1rem",
    # "top": 300,
    "margin-top": "5rem",
    # "background-color": "#878787",
}
# ----------------------------------------------------------------------------------
app.layout = dbc.Container([
    dbc.Row([
        dbc.Col(navbar, width=12)
    ]),
    dbc.Row([
        dbc.Col(sidebar, width=2),
        dbc.Col([dash.page_container], style=CONTENT_STYLE, width=10),
    ]),
],
    fluid=True,
)
# ----------------------------------------------------------------------------------
if __name__ == "__main__":
    app.run_server(debug=False)
