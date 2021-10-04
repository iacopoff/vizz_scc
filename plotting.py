import seaborn as sns
import matplotlib.pyplot as plt
import plotly.express as px
import numpy as np
import plotly.graph_objs as go

from functools import partial

from ipyleaflet import Map, TileLayer, WMSLayer, basemaps, LayersControl,WidgetControl, GeoJSON,LayersControl
from ipywidgets import Layout,Text, HTML


def plot_totals(df,palette,variables,region):
    sns.set_theme(style="ticks")
    sns.set_context('paper')

    f, ax = plt.subplots(figsize = (18,10))
    plt.title("Soybean's physical area totals by country and farming system",fontdict={"fontsize":20})
    sns.barplot(data=df,x="value",y="country",hue="farming system",dodge=True,orient="h",palette=palette,hue_order=variables)
    ax.legend(loc = 'center right',fontsize=12)
    plt.xlabel("Log physical area (h)")
    plt.xscale("log")
    plt.axvline(x=1,color='red', linestyle='--',linewidth=1)
    plt.axvline(x=1000,color='red', linestyle='--',linewidth=1)
    plt.axvline(x=1_000_000,color='red', linestyle='--',linewidth=1)
    sns.despine(left = True, bottom = True)


    for i,c in enumerate(ax.containers):
        #s = slice(i*8,i*8+8)
        #lb = np.array(labels.iloc[s])
        ax.bar_label(c,fmt='%.0f', label_type='center',color="white")
        #ax.set(ylabel='Mean Time')

    
    for tick_label in ax.axes.get_yticklabels():
        l = tick_label.get_text()
        if l in region:
            tick_label.set_color("green")
        else:
            tick_label.set_color("orange")
        tick_label.set_fontsize("15")
    plt.show()
    
def plot_boxen(df,x,y,hue,palette,order=[],ylab="",title=""):
    g = sns.catplot(x="country", 
                y="value",
                hue="variable",
                data=df,
                kind="boxen",
                palette=palette,
                order=order,legend=False)
    plt.title(title,fontdict={"fontsize":20})
    g.set_axis_labels("Country", ylab)
    for tick_label in g.axes[0][0].get_xticklabels():
        l = tick_label.get_text()
        if l in order[:4]:
            tick_label.set_color("green")
        else:
            tick_label.set_color("orange")
        tick_label.set_fontsize("15")
    g.fig.set_size_inches(20,8)
    ax = g.fig.get_axes()[0] 
    ax.legend(bbox_to_anchor=(1,1),fontsize=12)#loc='upper right',
    
    
def plot_parcoords(df,country="India",variables=[],var_palette="area",title="Fraction .."):
    
    
    
    df_sub = df[df["country"]==country]
    
    values = np.log10(df_sub[var_palette])
    mn = min(values)
    mx = max(values)
    
    fig = go.Figure(data=
    go.Parcoords(
        line = dict(color = values,
                   colorscale = 'Bluered',
                   showscale = True,
                   cmin = mn,
                   cmax = mx,
                     colorbar=dict(
                    title="Log Area (h)"
                            )
                   ),
        dimensions = list([
            dict(range = [0,1],
                constraintrange = [0,1],
                label = variables[0], values = df_sub[variables[0]]),
            dict(range = [0,1],
                label = variables[1], values = df_sub[variables[1]]),
            dict(range = [0,1],
                label = variables[2], values = df_sub[variables[2]]),
            dict(range = [0,1],
                label = variables[3], values = df_sub[variables[3]])
        ])
    )
    )

    fig.update_layout(
        title=f"{country}: {title}",
        xaxis_title="Farming systems",
        yaxis_title="Area fraction",
        plot_bgcolor = 'white',
        #paper_bgcolor = 'white'

    )

    fig.show()
    

def plot_map(choro_layers,colormap,variables):
    
    #Initialize Leaflet map
    defaultLayout=Layout(width='960px', height='640px')
    m = Map(center=(52.3,8.0), zoom = 2, basemap= basemaps.OpenStreetMap.BlackAndWhite, layout=defaultLayout)

    #Add water transition layer (not fundamental for the analysis... but nice!)

    tlayer = TileLayer(url= "https://storage.googleapis.com/global-surface-water/tiles2020/transitions/{z}/{x}/{y}.png",
                      name="Transition")
    m.add_layer(tlayer)

    #Add Choropleth layers to map

    for l in choro_layers:
        m.add_layer(l)

    #Add events when hoovering on shapes, display country and soybeas area in hectars

    def update_html(v,feature,  **kwargs):
        html.value = '''
            <h3><b>Country: {}</b></h3>
            <h3><b>Hectars: {}</b></h3>
        '''.format(feature["properties"]["country"],feature["properties"][v])

    for l,v in zip(choro_layers,variables):
        l.on_hover(partial(update_html,v))

    html = HTML('''Hover over the active layer''')
    html.layout.margin = '0px 20px 20px 20px'
    control = WidgetControl(widget=html, position='bottomleft')
    m.add_control(control)

    control = LayersControl(position='topright')
    m.add_control(control)
    return m    