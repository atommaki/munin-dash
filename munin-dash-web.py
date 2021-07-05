#!/usr/bin/env python3

import glob
import rrdtool
import pandas as pd
import sqlite3
from datetime import datetime
from pprint import pprint

import plotly.graph_objects as go

import dash
import dash_core_components as dcc
import dash_html_components as html

import os
import pickle

munin_data_dir = '/var/lib/munin'
munin_datafile = munin_data_dir+'/datafile'
sqlite_data_dir = 'sqlite-data'


def get_df_from_sqlite(sqlite_file_pattern):
    #print(f'{sqlite_data_dir}/{sqlite_file_pattern}*sqlite')
    sqlite_file_list = glob.glob(f'{sqlite_data_dir}/{sqlite_file_pattern}*sqlite')
    #print(sqlite_file_list)
    sqlite_file = sqlite_file_list[0]
    table_name = 'data'
    conn = sqlite3.connect(sqlite_file)
    # df = pd.read_sql_table(table_name, conn) # <-- NotImplementedError: read_sql_table only supported for SQLAlchemy connectable.
    df = pd.read_sql_query(f"SELECT * FROM {table_name}", conn)
    conn.close()
    return df

def get_dash_figure(sqlite_file_pattern, linelabel, linedraw):
    df = get_df_from_sqlite(sqlite_file_pattern)
    #if df['value'].isnull().all():
    if df[df['value'] < 0].empty and df[df['value'] > 0].empty:
        return None
    if linedraw in [ 'AREA', 'STACK', 'AREASTACK' ]:
        stgroup = 'one'
    else:
        stgroup = None
    return go.Scatter(  x = df['time'],
                        y = df['value'],
                        mode = 'lines',
                        stackgroup = stgroup,
                        line = dict(width = 2),
                        name = linelabel )

def get_munin_datafile_info(munin_datafile):
    # Would be better to use the datafile.storable instead, but:
    #
    #    >>> from storable import retrieve
    #    >>> x = retrieve('datafile.storable')
    #    Traceback (most recent call last):
    #      File "<stdin>", line 1, in <module>
    #      File "/home/qji/.local/lib/python3.8/site-packages/storable/core.py", line 433, in retrieve
    #        data = deserialize(fh)
    #      File "/home/qji/.local/lib/python3.8/site-packages/storable/core.py", line 504, in deserialize
    #        data = process_item(fh, cache)
    #      File "/home/qji/.local/lib/python3.8/site-packages/storable/core.py", line 414, in process_item
    #        data = engine[magic_type](fh, cache)
    #      File "/home/qji/.local/lib/python3.8/site-packages/storable/core.py", line 132, in SX_HASH
    #        value = process_item(fh, cache)
    #      File "/home/qji/.local/lib/python3.8/site-packages/storable/core.py", line 414, in process_item
    #        data = engine[magic_type](fh, cache)
    #      File "/home/qji/.local/lib/python3.8/site-packages/storable/core.py", line 140, in SX_REF
    #        return process_item(fh, cache)
    #      File "/home/qji/.local/lib/python3.8/site-packages/storable/core.py", line 414, in process_item
    #        data = engine[magic_type](fh, cache)
    #      File "/home/qji/.local/lib/python3.8/site-packages/storable/core.py", line 132, in SX_HASH
    #        value = process_item(fh, cache)
    #      File "/home/qji/.local/lib/python3.8/site-packages/storable/core.py", line 414, in process_item
    #        data = engine[magic_type](fh, cache)
    #    KeyError: b'\x1b'

    def parse_line(line):
        # ' '
        nonvalue = line.split(' ')[0]
        value = ' '.join(line.split(' ')[1:]).rstrip()
        # ';'
        domain = nonvalue.split(';')[0]
        second = nonvalue.split(';')[1]
        # ':'
        host =   second.split(':')[0]
        second2 =  second.split(':')[1]
        # '.'
        graph = '.'.join(second2.split('.')[:-1])
        attr = second2.split('.')[-1]

        return domain, host, graph, attr, value

    def get_graph_attr(attr):
        valid_graph_attrs = [ 'title', 'category', 'vlabel', 'info', 'order' ]
        attr_split_list = attr.split('graph_')
        if attr_split_list[0] != '':
            return None
        if len(attr_split_list) != 2:
            return None
        graph_attr = attr_split_list[1]
        if graph_attr in valid_graph_attrs:
            return graph_attr
        else:
            return None
    
    def get_line_infos(domain, host, graph, graphlines):
        lines_info = []
        for gline in graphlines:
            line_info = { gline: {} }
            with open(munin_datafile) as datafile:
                for line in datafile:
                    if line.split(' ')[0] == 'version':
                        continue
                    xdomain, xhost, xgraph, xattr, xvalue = parse_line(line)
                    if domain == xdomain and host == xhost and f'{graph}.{gline}' == xgraph:
                        if xattr in [ 'draw' , 'label' ]:
                            line_info[gline][xattr] = xvalue 
            lines_info.append(line_info)
        return lines_info
         

    def get_graph_info(domain, host, graph):
        graph_info = {}
        with open(munin_datafile) as datafile:
            for line in datafile:
                if line.split(' ')[0] == 'version':
                    continue
                xdomain, xhost, xgraph, xattr, xvalue = parse_line(line)
                if domain == xdomain and host == xhost and graph == xgraph:
                    graph_attr = get_graph_attr(xattr)
                    if graph_attr != None:
                        if graph_attr == 'order':
                           graph_info[graph_attr] = get_line_infos(domain, host, graph, xvalue.split(' '))
                        else:
                           graph_info[graph_attr] = xvalue 
        return graph_info
            

#    datafile_info = []
#    with open(munin_datafile) as datafile:
#        for line in datafile:
#            if line.split(' ')[0] == 'version':
#                continue
#
#            # ' '
#            nonvalue = line.split(' ')[0]
#            value = ' '.join(line.split(' ')[1:]).rstrip()
#            # ';'
#            domain = nonvalue.split(';')[0]
#            second = nonvalue.split(';')[1]
#            # ':'
#            host =   second.split(':')[0]
#            second2 =  second.split(':')[1]
#            # '.'
#            graph = '.'.join(second2.split('.')[:-1])
#            attr = second2.split('.')[-1]
#
#            line_dict = { 'domain': domain, 'host': host, 'graph': graph, 'attr': attr, 'value': value }
#
#            datafile_info.append(line_dict)
#            #print(line_dict)

    if os.path.isfile('datafile.pickle'):
        print(f'datafile is taken from pickle file.')
        return pickle.load(open('datafile.pickle', 'rb'))


    datafile_info = {}
    with open(munin_datafile) as datafile:
        for line in datafile:
            if line.split(' ')[0] == 'version':
                continue
            domain, host, graph, attr, value = parse_line(line)
            graph_attr = get_graph_attr(attr)
            if graph_attr == 'category': # value = category name
                if domain not in datafile_info:
                    datafile_info[domain] = {}
                if host not in datafile_info[domain]:
                    datafile_info[domain][host] = {}
                if value not in datafile_info[domain][host]:
                    datafile_info[domain][host][value] = {}

                if len(graph.split('.')) != 1:
                    print(f'skipped: {graph}')
                    continue

                if graph not in datafile_info[domain][host][value]:
                    datafile_info[domain][host][value][graph] = get_graph_info(domain, host, graph)

    print(f'datafile is taken from original munin data.')

    pickle.dump(datafile_info, open('datafile.pickle', 'wb'))
    return datafile_info
    
            

datafile_info = get_munin_datafile_info(munin_datafile)
#pprint(datafile_info)
print(f'{ len(datafile_info) = }    { len(datafile_info["localdomain"]["localhost.localdomain"]) = }')

domainlist = []
toc = [ html.Img(src = 'http://127.0.0.1/munin/static/logo-h.png'), html.Br(), html.Ul(children = domainlist) ]
h_list = []
dash_figures = []
for domain in datafile_info:
    h_list.append(html.H2(domain, id = domain))
    hostlist = []
    domainlist.append(html.Li([html.A(domain, href = f'#{domain}'), html.Ul(hostlist)]))
    for host in datafile_info[domain]:
        h_list.append(html.H3(host, id = host))
        categorylist = []
        hostlist.append(html.Li([html.A(host, href = f'#{host}'), html.Ul(categorylist)]))
        
        for category in sorted(list(datafile_info[domain][host])):
            h_details = []
            graphlist = []
            for graph in sorted(list(datafile_info[domain][host][category])):
                dash_figures = []
                seen = set()
                for line in datafile_info[domain][host][category][graph]['order']:
                    linekey = list(line.keys())[0]
                    try:
                        linedraw = line[linekey]['draw']
                    except KeyError:
                        linedraw = None

                    try:
                        linelabel = line[linekey]['label']
                    except KeyError:
                        linelabel = linekey

                    # order has duplicates, but why?
                    if linekey in seen:
                        continue
                    seen.add(linekey)
                    line_norm = linekey.replace('.','-')
                    graph_norm = graph.replace('.','-')
                    sqlite_file_pattern = f"{domain}/{host}-{graph_norm}-{line_norm}"
                    dash_fig = get_dash_figure(sqlite_file_pattern, linelabel, linedraw)
                    if dash_fig != None:
                        dash_figures.append(dash_fig)
                if dash_figures == []:
                    continue
                fig = go.Figure(data = dash_figures)
                fig.update_layout(
                    yaxis_title = datafile_info[domain][host][category][graph]['vlabel'],
                    title = datafile_info[domain][host][category][graph]['title'],
                    height = 400,
                    width  = 1000,
                    hovermode = "x unified",
                    legend = dict(orientation = "h")
                )

                h_details.append(dcc.Graph(figure = fig, config= {'displaylogo': False}, id = f'{category}-{graph}'))
                graphlist.append(html.Li(html.A(graph, href=f'#{category}-{graph}')))
            n_graphs = len(h_details)
            if n_graphs > 0:
                categorylist.append(html.Li([html.A(category, href = f'#{category}'),html.Ul(graphlist)]))
                h_details.insert(0, html.Div(f'{category}', id = category))
                h_list.append(html.Div(h_details))


app = dash.Dash(__name__)
app.title = 'munin-dash'

app.layout = html.Div(className='content', children = [
                                        html.Div(className='left', children = toc),
                                        html.Div(className='right', children = h_list)
                                       ]
                    )

app.run_server(debug=True)

