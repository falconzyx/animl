import numpy as np
import pandas as pd
import graphviz
from numpy.distutils.system_info import f2py_info
from sklearn import tree
from sklearn.datasets import load_boston, load_iris
import string
import re
import matplotlib.pyplot as plt
import seaborn as sns
from animl.trees import *
from numbers import Number

YELLOW = "#fefecd" # "#fbfbd0" # "#FBFEB0"
BLUE = "#D9E6F5"
GREEN = "#cfe2d4"
DARKBLUE = '#313695'
LIGHTORANGE = '#fee090'

color_blind_friendly_colors = {
    'redorange': '#f46d43',
    'orange': '#fdae61', 'yellow': '#fee090', 'sky': '#e0f3f8',
    'babyblue': '#abd9e9', 'lightblue': '#74add1', 'blue': '#4575b4'
}

color_blind_friendly_colors = [
    None, # 0 classes
    None, # 1 class
    [YELLOW,BLUE], # 2 classes
    [YELLOW,BLUE,GREEN], # 3 classes
    [YELLOW,BLUE,GREEN,'#a1dab4'], # 4
    [YELLOW,BLUE,GREEN,'#a1dab4','#41b6c4'], # 5
    [YELLOW,'#c7e9b4','#7fcdbb','#41b6c4','#2c7fb8','#253494'], # 6
    [YELLOW,'#c7e9b4','#7fcdbb','#41b6c4','#1d91c0','#225ea8','#0c2c84'], # 7
    [YELLOW,'#edf8b1','#c7e9b4','#7fcdbb','#41b6c4','#1d91c0','#225ea8','#0c2c84'], # 8
    [YELLOW,'#ece7f2','#d0d1e6','#a6bddb','#74a9cf','#3690c0','#0570b0','#045a8d','#023858'], # 9
    [YELLOW,'#e0f3f8','#313695','#fee090','#4575b4','#fdae61','#abd9e9','#74add1','#d73027','#f46d43'] # 10
]

# for x in color_blind_friendly_colors[2:]:
#     print(x)

max_class_colors = len(color_blind_friendly_colors)-1


def dtreeviz(tree_model, X_train, y_train, feature_names, target_name, class_names=None, precision=1, orientation="TD"):
    def round(v,ndigits=precision):
        return format(v, '.' + str(ndigits) + 'f')

    def node_name(node : ShadowDecTreeNode) -> str:
        if node.feature_name() is None:
            return f"node{node.id}"
        node_name = ''.join(c for c in node.feature_name() if c not in string.punctuation)+str(node.id)
        node_name = re.sub("["+string.punctuation+string.whitespace+"]", '_', node_name)
        return node_name

    def dec_node(name, node_name, split):
        # html = f"""<font face="Helvetica" color="#444443" point-size="12">{name}<br/>@{split}</font>"""
        # return f'{node_name} [shape=none label=<{html}>]'
        html = f"""<table border="0">
        <tr>
                <td port="img" fixedsize="true" width="140" height="45"><img src="/tmp/node{node.id}.png"/></td>
        </tr>
        <tr>
                <td port="label"><font face="Helvetica" color="#444443" point-size="12">{name}@{split}</font></td>
        </tr>
        </table>"""
        return f'{node_name} [margin="0" shape=none label=<{html}>]'


    def regressor_leaf_node(node):
        value = node.prediction()
        # html = f"""<font face="Helvetica" color="#444443" point-size="11">{round(value)}</font>"""
        # margin = prop_size(node.nsamples())
        # return f'leaf{node.id} [margin="{margin}" style=filled fillcolor="{YELLOW}" shape=circle label=<{html}>]'
        html = f"""<table border="0">
        <tr>
                <td fixedsize="true" width="27" height="60"><img src="/tmp/node{node.id}.png"/></td>
        </tr>
        <tr>
                <td><font face="Helvetica" color="#444443" point-size="12">{target_name}={round(value)}</font></td>
        </tr>
        </table>"""
        return f'leaf{node.id} [margin="0" shape=plain label=<{html}>]'

    def prop_size(n):
        leaf_sample_counts = shadow_tree.leaf_sample_counts()
        min_samples = min(leaf_sample_counts)
        max_samples = max(leaf_sample_counts)
        sample_count_range = max_samples - min_samples

        margin_range = (0.00, 0.3)
        if sample_count_range>0:
            zero_to_one = (n - min_samples) / sample_count_range
            return zero_to_one * (margin_range[1] - margin_range[0]) + margin_range[0]
        else:
            return margin_range[0]

    ranksep = ".22"
    if orientation=="TD":
        ranksep = ".35"


    shadow_tree = ShadowDecTree(tree_model, X_train, feature_names=feature_names, class_names=class_names)

    n_classes = shadow_tree.nclasses()
    color_values = color_blind_friendly_colors[n_classes]

    figsize = (5, 1.6)

    y_range = (min(y_train)*1.03, max(y_train)*1.03) # same y axis for all

    internal = []
    for node in shadow_tree.internal:
        nname = node_name(node)
        # st += dec_node_box(name, nname, split=round(threshold[i]))
        gr_node = dec_node(node.feature_name(), nname, split=round(node.split()))
        internal.append( gr_node )

        regr_split_viz(node, X_train, y_train, filename=f"/tmp/node{node.id}.png",
                       target_name=target_name,
                       figsize=figsize,
                       y_range=y_range,
                       show_ylabel=node == shadow_tree.root,
                       showx=False)

    leaves = []
    for node in shadow_tree.leaves:
        regr_leaf_viz(node, y_train, filename=f"/tmp/node{node.id}.png",
                      y_range=y_range,
                      figsize=(4,2))

        if shadow_tree.isclassifier():
            counts = node.class_counts()
            predicted_class = np.argmax(counts)
            predicted = predicted_class
            if class_names is not None:
                predicted = class_names[predicted_class]
            ratios = counts / node.nsamples()  # convert counts to ratios totalling 1.0
            ratios = [round(r, 3) for r in ratios]
            color_spec = ["{c};{r}".format(c=color_values[i], r=r) for i, r in
                          enumerate(ratios)]
            color_spec = ':'.join(color_spec)
            if n_classes > max_class_colors:
                color_spec = YELLOW
            html = f"""<font face="Helvetica" color="black" point-size="12">{predicted}<br/>&nbsp;</font>"""
            margin = prop_size(node.nsamples())
            style = 'wedged' if n_classes <= max_class_colors else 'filled'
            leaves.append( f'leaf{node.id} [height=0 width="0.4" margin="{margin}" style={style} fillcolor="{color_spec}" shape=circle label=<{html}>]' )
        else:
            leaves.append( regressor_leaf_node(node) )

    if orientation=="TD":
        ldistance = "1.1"
        rdistance = "1.1"
        langle = "-28"
        rangle = "28"
        port = "label:s"
    else:
        ldistance = "1.3" # not used in LR mode; just label not taillable.
        rdistance = "1.3"
        langle = "-90"
        rangle = "90"
        port = "img:e"

    edges = []
    # non leaf edges with > and <=
    for node in shadow_tree.internal:
        nname = node_name(node)
        left_node_name = node_name(node.left)
        if node.left.isleaf():
            left_node_name ='leaf%d' % node.left.id
        right_node_name = node_name(node.right)
        if node.right.isleaf():
            right_node_name ='leaf%d' % node.right.id
        edges.append( f'{nname}:{port} -> {left_node_name} [labelangle="{langle}" labeldistance="{ldistance}" taillabel=<&lt;>]' )
        edges.append( f'{nname}:{port} -> {right_node_name} [labelangle="{rangle}" labeldistance="{rdistance}" taillabel=<&ge;>]' )

    newline = "\n\t"
    st = f"""
digraph G {{splines=line;
    nodesep=0.1;
    ranksep={ranksep};
    rankdir={orientation};
    node [margin="0.03" penwidth="0.5" width=.1, height=.1];
    edge [arrowsize=.4 penwidth="0.5"]
    
    {newline.join(internal)}
    {newline.join(edges)}
    {newline.join(leaves)}
}}
    """

    return graphviz.Source(st)


def regr_split_viz(node : ShadowDecTreeNode,
                   X : (pd.DataFrame,np.ndarray),
                   y : (pd.Series,np.ndarray),
                   target_name : str,
                   filename:str=None,
                   showx=True,
                   showy=True,
                   show_ylabel=True,
                   y_range=None,
                   figsize:Tuple[Number,Number]=None,
                   ticks_fontsize:int=18,
                   label_fontsize:int=24):
    fig, ax = plt.subplots(1, 1, figsize=figsize)

    feature_name = node.feature_name()
    if show_ylabel: showy=True
    if showx:
        ax.set_xlabel(feature_name, fontsize=label_fontsize, fontname="Arial")
    else:
        ax.xaxis.set_visible(False)
        ax.set_xticks([])
    if showy:
        ax.set_ylim(y_range)
        if show_ylabel:
            ax.set_ylabel(target_name, fontsize=label_fontsize, fontname="Arial")
    else:
        ax.yaxis.set_visible(False)
        ax.set_yticks([])

    if not showx and not showy:
        ax.axis('off')

    if isinstance(X,pd.DataFrame):
        X = X.values
    if isinstance(y,pd.Series):
        y = y.values

    X = X[:,node.feature()]
    X, y = X[node.samples()], y[node.samples()]

    ax.tick_params(axis='both', which='major', labelsize=ticks_fontsize)

    ax.scatter(X, y, s=2, c=DARKBLUE, alpha=.8)
    left, right = node.split_samples()
    left = y[left]
    right = y[right]
    split = node.split()
    ax.plot([min(X),split],[np.mean(left),np.mean(left)],'--', color='#444443', linewidth=1.3)
    ax.plot([split,split],[min(y),max(y)],'--', color='#444443', linewidth=1.3)
    ax.plot([split,max(X)],[np.mean(right),np.mean(right)],'--', color='#444443', linewidth=1.3)

    plt.tight_layout()
    if filename is not None:
        plt.savefig(filename, dpi=600, bbox_inches='tight', pad_inches=0)
        plt.close()


def regr_leaf_viz(node : ShadowDecTreeNode,
                  y : (pd.Series,np.ndarray),
                  filename:str=None,
                  y_range=None,
                  figsize:Tuple[Number,Number]=None,
                  ticks_fontsize:int=24):
    fig, ax = plt.subplots(1, 1, figsize=figsize)

    ax.xaxis.set_visible(False)
    ax.set_xticks([])

    if isinstance(y,pd.Series):
        y = y.values

    y = y[node.samples()]

    fig, ax = plt.subplots(1, 1, figsize=(1.35, 3))
    ax.xaxis.set_visible(False)
    ax.set_xticks([])

    ax.set_ylim(y_range)
    ax.tick_params(axis='both', which='major', labelsize=ticks_fontsize)
    meanprops = {'linewidth': 1.2, 'linestyle': '-', 'color': 'black'}
    bp = ax.boxplot(y, notch=False, medianprops={'linewidth': 0}, meanprops=meanprops,
                    widths=[.8], showmeans=True, meanline=True, sym='', patch_artist=True)
    for patch in bp['boxes']:
        patch.set(facecolor=LIGHTORANGE)

    plt.tight_layout()
    if filename is not None:
        plt.savefig(filename, dpi=600, bbox_inches='tight', pad_inches=0)
        plt.close()


def boston():
    regr = tree.DecisionTreeRegressor(max_depth=2, random_state=666)
    boston = load_boston()

    data = pd.DataFrame(boston.data)
    data.columns =boston.feature_names

    regr = regr.fit(data, boston.target)

    # st = dectreeviz(regr.tree_, data, boston.target)
    st = dtreeviz(regr, data, boston.target, target_name='price',
                  feature_names=data.columns, orientation="TD")

    with open("/tmp/t3.dot", "w") as f:
        f.write(st.source)

    return st
#
# def iris():
#     clf = tree.DecisionTreeClassifier(max_depth=2, random_state=666)
#     iris = load_iris()
#
#     print(iris.data.shape, iris.target.shape)
#
#     data = pd.DataFrame(iris.data)
#     data.columns = iris.feature_names
#
#     clf = clf.fit(data, iris.target)
#
#     # st = dectreeviz(clf.tree_, data, boston.target)
#     st = dtreeviz(clf, data, iris.target, orientation="TD", class_names=["setosa", "versicolor", "virginica"])
#
#     with open("/tmp/t3.dot", "w") as f:
#         f.write(st)
#
#     print(clf.tree_.value)
#     return st
#
#st = iris()
st = boston()
st.view()
#
