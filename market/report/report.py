from reportlab.platypus import BaseDocTemplate, Frame, PageTemplate, Table, Paragraph, PageBreak, Image, Spacer
from reportlab.lib import colors
import matplotlib.colors as mcolors
from reportlab.lib.units import inch
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import getSampleStyleSheet
import io, copy
from pprint import pp
import pandas as pd
from datetime import datetime
import matplotlib.pyplot as plt
import numpy as np

class Report():
    __padding = dict(
        leftPadding=30, 
        rightPadding=30,
        topPadding=10,
        bottomPadding=10)
    
    __styles = getSampleStyleSheet()
    
    @staticmethod
    def __onPage(canvas, doc, pagesize=A4):
        pageNum = canvas.getPageNumber()
        canvas.drawCentredString(pagesize[0]/2, 20, str(pageNum))
    
    @staticmethod
    def __onPageLandscape(canvas, doc):
        Report.__onPage(canvas, doc, pagesize=landscape(A4))
        return None
    
    __portraitTemplate = PageTemplate(
        id = 'portrait', 
        frames = Frame(0, 0, *A4, **__padding),
        onPage = __onPage, 
        pagesize = A4)

    __landscapeTemplate = PageTemplate(
        id = 'landscape', 
        frames = Frame(0, 0, *landscape(A4), **__padding), 
        onPage=__onPageLandscape, 
        pagesize = landscape(A4))

    @staticmethod
    def __fig2image(f):
        buf = io.BytesIO()
        f.savefig(buf, format='png', dpi=300)
        buf.seek(0)
        x, y = f.get_size_inches()
        return Image(buf, x * inch, y * inch)

    @staticmethod
    def __df2table(df, round_digits=None):
        tableData = [[col for col in df.columns]]
        values = df.values.tolist()
        if round_digits:
            for row in values:
                for idx in range(len(row)):
                    if isinstance(row[idx], float):
                        row[idx] = round(row[idx], round_digits)

            tableData += values
        else:
            tableData += values
        return Table(
            tableData,
            style=[
            ('FONT', (0,0), (-1,0), 'Helvetica-Bold', 8),
            ('FONT', (0,1), (-1,-1), 'Helvetica', 8),
            ('LINEBELOW',(0,0), (-1,0), 1, colors.black),
            ('INNERGRID', (0,0), (-1,-1), 0.25, colors.black),
            ('BOX', (0,0), (-1,-1), 1, colors.black),
            # ('ROWBACKGROUNDS', (0,0), (-1,-1), [colors.lightgrey, colors.white]),
            ('BACKGROUND', (0,0), (-1,0), colors.lightgrey),
        ],
        hAlign = 'LEFT')
    @staticmethod
    def __s2table(s):
        tableData = [[x,y] for x,y in s.items()]
        return Table(
            [[x,y] for x,y in s.items()],
            # rowHeights=[15] * len(tableData),
            style=[
            ('FONT', (0,0), (0,-1), 'Helvetica-Bold', 10),
            ('FONT', (0,1), (-1,-1), 'Helvetica', 10),
            # ('LINEBELOW',(0,0), (-1,0), 1, colors.black),
            ('INNERGRID', (0,0), (-1,-1), 0.25, colors.black),
            ('BOX', (0,0), (-1,-1), 1, colors.black),
            # ('ROWBACKGROUNDS', (0,0), (-1,-1), [colors.lightgrey, colors.white]),
            ('BACKGROUND', (0,0), (0,-1), colors.lightgrey),
        ],
        hAlign = 'LEFT')
    
    def __init__(self, name):
        self.doc = BaseDocTemplate(
            'reports/%s.pdf' % name,
            pageTemplates=[
                self.__portraitTemplate,
            ]
        )
        self.story = []
    
    @property
    def colors(self):
        return colors

    def printStyles(self):
        self.__styles.list()
    
    def printColors(self):
        colors = list(mcolors.CSS4_COLORS.keys())
        colors.sort()
        pp(colors)

    def getStyle(self, name):
        return copy.deepcopy(self.__styles[name])

    def addParagraph(self, text, style=__styles['Normal']):
        self.story.append(Paragraph(text, style))

    def addTable(self, df, round=None):
        self.story.append( self.__df2table(df, round) )

    def addSpace(self, inches):
        self.story.append( Spacer(1,inches * inch) )
    
    def addChartFigure(self, chartFig):
        self.story.append( self.__fig2image(chartFig) )
        
    def plotLineDF(self, dataFrame, y=[], labels=None, ylabel=None, divLine=None, colors=None, grid=True, legend_size=10, add_labels=False, height=3):
        dataFrame = dataFrame.copy()
        if isinstance(dataFrame.index[0],type(datetime.now().date())):
            dataFrame.index = pd.to_datetime(dataFrame.index)
        chartFig, ax = plt.subplots(dpi=300, figsize=(7, height))
        if len(y) == 0:
            y = dataFrame.columns.to_list()
        dataFrame.plot(y=y, ax=ax, kind='line', linewidth=1, label=labels, color=colors)
        if ylabel != None:
            ax.set_ylabel(ylabel)
        if divLine != None:
            ax.axhline(y=divLine, color='green', linestyle='--')
        # plt.xticks(rotation=45, fontsize=6)
        if add_labels:
            line_count = 0
            for line in plt.gca().lines:
                color = line.get_color()
                xdata = line.get_xdata()
                ydata = line.get_ydata()
                last_x = xdata[-1]
                last_y = ydata[-1]
                if hasattr(ydata, 'mask'): last_y = ydata.compressed()[-1]
                plt.annotate('  ' + y[line_count],
                            xy=(last_x, last_y),
                            xytext=(last_x, last_y),
                            # arrowprops=dict(facecolor='black', shrink=0.005),
                            color = color,
                            fontsize=int(legend_size * 0.7))
                line_count += 1
        plt.legend(fontsize=legend_size)
        plt.xticks(fontsize=6)
        plt.yticks(fontsize=6)
        plt.grid(grid)
        # plt.tight_layout()
        self.story.append( self.__fig2image(chartFig) )
        plt.close(chartFig)

    def plotBarsDF(self, dataFrame, ybars,
            barLabels=None, yBarsLabel=None, barsWidth=0.5, barColors=None,
            divLine=None, grid=True, plotHeight=3.0):
        dataFrame = dataFrame.copy()
        if isinstance(dataFrame.index[0],type(datetime.now().date())):
            dataFrame.index = pd.to_datetime(dataFrame.index)
            dataFrame.index = dataFrame.index.strftime('%m-%d-%y')
        
        # create plot figure
        chartFig, ax = plt.subplots(dpi=300, figsize=(7, plotHeight))
        
        # plot bar data
        dataFrame.plot(y=ybars, ax=ax, kind='bar', label=barLabels, color=barColors, width=barsWidth)
        if yBarsLabel != None:
            ax.set_ylabel(yBarsLabel)
        if divLine != None:
            ax.axhline(y=divLine, color='green', linestyle='--')
        ax.set_axisbelow(True)
        plt.xticks(rotation=45, fontsize=6)
        plt.yticks(fontsize=6)
        plt.grid(grid)

        # add figure to story
        self.story.append( self.__fig2image(chartFig) )
        plt.close(chartFig)

    def plotBarsLineDF(self, dataFrame, ybars, yline,
            barLabels=None, yBarsLabel=None, barsWidth=0.5, barColors=None,
            yLineLabel=None, lineColor=None,
            divLine=None, grid=True, plotHeight=3.0):
        dataFrame = dataFrame.copy()
        if isinstance(dataFrame.index[0],type(datetime.now().date())):
            dataFrame.index = pd.to_datetime(dataFrame.index)
            dataFrame.index = dataFrame.index.strftime('%m-%d-%y')
        # create plot figure
        chartFig, ax = plt.subplots(dpi=300, figsize=(7, plotHeight))
        
        # plot bar data
        dataFrame.plot(y=ybars, ax=ax, kind='bar', label=barLabels, color=barColors, width=barsWidth)
        if yBarsLabel != None:
            ax.set_ylabel(yBarsLabel)
        if divLine != None:
            ax.axhline(y=divLine, color='green', linestyle='--')
        ax.set_axisbelow(True)
        plt.xticks(rotation=45, fontsize=6)
        plt.yticks(fontsize=6)
        plt.grid(grid)

        # plot line data
        axl = plt.twinx(ax)
        dataFrame.plot(y=yline, ax=axl, kind='line', linewidth=1, color=lineColor)
        axl.legend()
        axl.get_legend().remove()
        if yLineLabel != None:
            axl.set_ylabel(yLineLabel, color=lineColor)
        plt.yticks(fontsize=6)
        plt.grid(grid)
        plt.tight_layout()
        
        # add figure to story
        self.story.append( self.__fig2image(chartFig) )
        plt.close(chartFig)
    
    def addPageBreak(self):
        self.story.append(PageBreak())
    
    def buildDoc(self):
        self.doc.build(self.story)

