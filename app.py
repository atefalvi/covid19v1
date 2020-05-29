import base64
import datetime

import dash
import dash_bootstrap_components as dbc
import dash_core_components as dcc
import dash_html_components as html
import dash_table
import numpy as np
import pandas as pd
import plotly.graph_objs as go
import requests
from bs4 import BeautifulSoup

# Loading Data
url = 'https://www.worldometers.info/coronavirus/#countries'
r = requests.get(url)
soup = BeautifulSoup(r.text, "html.parser") # Parse html

table = soup.find("table", {"id": "main_table_countries_today"}).find_all("tbody") # table
tr_elems = table[0].find_all("tr")

data = []
for tr in tr_elems: # Loop through rows
    td_elems = tr.find_all("td") # Each column in row
    data.append([td.text.strip() for td in td_elems])

np_array = np.array(data)

columns = ['country', 'total_cases', 'new_cases', 'total_deaths', 'new_deaths', 'total_recovered', 'new_recovered',
         'active_cases', 'serious_critical', '1M_total_case', '1M_death', 'total_tests', '1M_test', 'population', 'continent']

df = pd.DataFrame(data=np_array[1:, 1:16], index=np_array[1:, 0])

df.columns = columns

#df.reset_index(drop=True, inplace=True)
dfclean = df[(df['country'] != df['continent'])
             & (df['country'] != 'Oceania')
             & (df['country']!='')]

dfclean.iloc[:, 1:14] = dfclean.iloc[:, 1:14].replace('[\D^.]', '', regex=True)
dfclean.iloc[:, 1:14] = dfclean.iloc[:, 1:14].replace('', 0)

dfclean.iloc[:, 1:14] = dfclean.iloc[:, 1:14].astype('float')

# Setting up the display
pd.set_option('display.float_format', lambda x: '%.0f' % x)

#ETL date time
etl = datetime.datetime.now()
etl = etl.strftime("%x")+' @ '+etl.strftime("%X")

# KPI Cards
total_cases = dfclean.loc[:, ['total_cases']][dfclean['country'] == 'World'].values[0]
total_deaths = dfclean.loc[:, ['total_deaths']][dfclean['country'] == 'World'].values[0]
total_recovered = dfclean.loc[:, ['total_recovered']][dfclean['country'] == 'World'].values[0]
total_tests = dfclean['total_tests'].sum()

# Population Graph Data
dfp = dfclean.loc[:, ['country', 'population', 'total_cases', 'total_deaths']][dfclean['population'] != 0]
dfp['cases_per'] = dfp.total_cases.div(dfp.population) * 100
dfp['death_per'] = dfp.total_deaths.div(dfp.population) * 100

# total cases
x = dfp['population']
yc = dfp['total_cases']
cc = dfp['country']
sizec = dfp['cases_per'] * 100
sizec = sizec.astype(int)
# death
yd = dfp['total_deaths']
sized = dfp['death_per'] * 1000
sized = sized.astype(int)

# Table Data
df_table = dfclean.loc[:,
           ['continent', 'country', 'population', 'total_tests', 'total_cases', 'total_recovered', 'total_deaths',
            'active_cases']][dfclean['country'] != 'World']

#####-[ Dash App ]-#####
app = dash.Dash(external_stylesheets=[dbc.themes.SLATE])
server = app.server
app.title = 'Covid19'

# Covid Image
image_filename = 'covidart.png'
encoded_image = base64.b64encode(open(image_filename, 'rb').read())


# KPI
def kpi_card_format(num):
    place_value = 0
    while abs(num) >= 1000:
        place_value += 1
        num /= 1000.0
    # add more suffixes if you need them
    return '%.2f%s' % (num, ['', 'K', 'M', 'G', 'T', 'P'][place_value])




app.layout = html.Div([html.Div([html.H1(children='Covid 19 Dashboard', style={'padding-left': 15}),
                                 html.Img(src='data:image/png;base64,{}'.format(encoded_image.decode()),
                                          style={'height': 70, 'position': 'fixed', 'top': 20, 'right': 15})],
                                className='row'),

                       html.H6(children='Last Updated: {a}'.format(a=etl)),
                       ### KPI Cards Deck
                       html.Div(id='KPI', children=[
                           html.Div(id='kpi_deck',
                                    children=[
                                        html.Div(id='conf-ind',
                                                 children=[html.H5(
                                                     children='Confirmed Cases',
                                                     className='card-header:first-child'),
                                                     html.H3(children=kpi_card_format(total_cases),
                                                             className='card-header:first-child')
                                                 ],
                                                 className='card text-white bg-secondary',
                                                 style={'padding': '10px'}),

                                        html.Div(id='death-ind',
                                                 children=[html.H5(
                                                     children='Death Cases',
                                                     className='card-header:first-child'),
                                                     html.H3(children=kpi_card_format(total_deaths),
                                                             className='card-header:first-child')
                                                 ],
                                                 className='card text-white bg-secondary',
                                                 style={'padding': '10px'}),

                                        html.Div(id='recov-ind',
                                                 children=[html.H5(
                                                     children='Recovered',
                                                     className='card-header:last-child'),
                                                     html.H3(children=kpi_card_format(total_recovered),
                                                             className='card-header:last-child')
                                                 ],
                                                 className='card text-white bg-secondary',
                                                 style={'padding': '10px'}),

                                        html.Div(id='test-ind',
                                                 children=[html.H5(
                                                     children='Total Tested',
                                                     className='card-title'),
                                                     html.H3(children=kpi_card_format(total_tests),
                                                             className='card-header:last-child')
                                                 ],
                                                 className='card text-white bg-secondary',
                                                 style={'padding': '10px'}
                                                 )
                                    ], className='card-deck', style={'margin': 15, 'textAlign': 'center'})

                       ]),
                       ### 1st Graph
                       html.Div(id='1st row Graph',
                                children=[html.Div(id='Graph_deck',
                                                   children=[html.Div(id='graphcard1x1',
                                                                      children=[
                                                                          dcc.Graph(id='Total Cases vs Population',
                                                                                    figure={
                                                                                        'data': [
                                                                                            go.Scatter(
                                                                                                x=x,
                                                                                                y=yc,
                                                                                                mode='markers',
                                                                                                hovertext=cc,
                                                                                                marker=dict(
                                                                                                    color=np.random.randn(
                                                                                                        216),
                                                                                                    colorscale='Viridis',
                                                                                                    size=sizec,
                                                                                                    opacity=.7,
                                                                                                    showscale=False)
                                                                                            )
                                                                                        ],
                                                                                        'layout': go.Layout(
                                                                                            title='Total Cases vs Population',
                                                                                            xaxis={
                                                                                                'title': 'Population',
                                                                                                'type': 'log'},
                                                                                            yaxis={
                                                                                                'title': 'Total Cases',
                                                                                                'type': 'log'},
                                                                                            hovermode='closest',
                                                                                            template='seaborn',
                                                                                            plot_bgcolor='rgb(122, 130, 136)',
                                                                                            paper_bgcolor='rgb(122, 130, 136)',
                                                                                            font={'color': 'white'}
                                                                                        )
                                                                                    })],
                                                                      className='card text-white bg-secondary'),
                                                             html.Div(id='graphcard1X2',
                                                                      children=[
                                                                          dcc.Graph(id='Total Death vs Population',
                                                                                    figure={
                                                                                        'data': [
                                                                                            go.Scatter(
                                                                                                x=x,
                                                                                                y=yd,
                                                                                                mode='markers',
                                                                                                hovertext=cc,
                                                                                                marker=dict(
                                                                                                    color=np.random.randn(
                                                                                                        216),
                                                                                                    colorscale='Hot',
                                                                                                    size=sized,
                                                                                                    opacity=.7,
                                                                                                    showscale=False)
                                                                                            )
                                                                                        ],
                                                                                        'layout': go.Layout(
                                                                                            title='Total Death vs Population',
                                                                                            xaxis={
                                                                                                'title': 'Population',
                                                                                                'type': 'log',
                                                                                                'color': 'white'},
                                                                                            yaxis={
                                                                                                'title': 'Total Death',
                                                                                                'type': 'log',
                                                                                                'color': 'white'},
                                                                                            hovermode='closest',
                                                                                            template='seaborn',
                                                                                            plot_bgcolor='rgb(122, 130, 136)',
                                                                                            paper_bgcolor='rgb(122, 130, 136)',
                                                                                            font={'color': 'white'}
                                                                                        )
                                                                                    })],
                                                                      className='card text-white bg-secondary')
                                                             ], className='card-deck', style={'margin': 15})
                                          ]),
                       ### Data Table
                       html.Div(id='datatable_deck',
                                children=[html.Div(id='datatable_card',
                                                   children=[html.Div(id='datatable_1x1',
                                                                      children=[dash_table.DataTable(
                                                                          id='datatable-advanced-filtering',
                                                                          columns=[
                                                                              {'name': i, 'id': i} for i in
                                                                              df_table.columns
                                                                              if i != 'id'
                                                                          ],
                                                                          data=df_table.to_dict('records'),
                                                                          editable=True,
                                                                          page_action='native',
                                                                          page_size=25,
                                                                          filter_action="native",
                                                                          style_header={
                                                                              'backgroundColor': 'rgb(30, 30, 30)'},
                                                                          style_cell={
                                                                              'backgroundColor': 'rgb(50, 50, 50)',
                                                                              'color': 'white'}
                                                                      )], className='card text-white bg-secondary'
                                                                      )], className='card-deck', style={'margin': 30}
                                                   )]
                                ),
                       ### Footer
                       html.Div(id='footer',
                                children=html.P(id='footer-notes', children='Dashboard designed by Syed Atef Alvi'),
                                style={'testAlign': 'center'})
                       ],
                      style={'margin': 15})

if __name__ == '__main__':
    app.run_server()
