#!/usr/bin/env python
# -*- coding: utf-8 -*-

'''
Copyright (C) 2014-2015 Open Source Modelica Consortium
Copyright (C) 2011-2015 German Aerospace Center DLR
(Deutsches Zentrum fuer Luft- und Raumfahrt e.V.),
Institute of System Dynamics and Control
All rights reserved.

This file is part of PySimulator.

PySimulator is free software: you can redistribute it and/or modify
it under the terms of the GNU Lesser General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

PySimulator is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
GNU Lesser General Public License for more details.

You should have received a copy of the GNU Lesser General Public License
along with PySimulator. If not, see www.gnu.org/licenses.
'''

import os
from decimal import Decimal
import numpy
from bs4 import BeautifulSoup
import time
import datetime
import webbrowser



def htmloverview(fileouthtml,resultfile,file,file1,diff1,difftol,dircount,model1var,model2var,totalComparedvar,maxEstTol):
    '''This function is used to present the users with the overall comparison report of different models, The report includes, for each model the number of variables 
       differed, and a link is provided to inspect the differed variables, if there are no differed variables then no link is provided '''
    os.getcwd()
    filename,fileExtension = os.path.splitext(file)
    modelname=os.path.basename(file).replace(fileExtension,' ')
    modelname1=modelname+'res'+str(dircount)
    p=os.path.dirname(resultfile)
    os.chdir(p)
    filename=os.path.join(p,modelname1.replace(' ',''))
    fileerror=os.path.join(filename,'name.html').replace('\\','/')
    filetolerance=os.path.join(filename,'error.html').replace('\\','/')
    reference='<tr> <td align="right"> <b> Baseline Directory: </b> </td>'+'<td>'+' '+os.path.dirname(file1)+'</td></tr>'
    comparison='<tr> <td align="right"> <b> Testing Directory: </b> </td>'+'<td>'+' '+os.path.dirname(file)+'</td></tr>'
    comparedmodel='<tr> <td align="right"> <b> Compared Result file: </b> </td>'+ '<td>'+' '+os.path.basename(file)+'</td></tr>'
    maxerror="{:.1e}".format(Decimal(str(maxEstTol)))
    messcommon="""<html> <a href="../index.html"> Home </a> <head> <h2> List of Differed Variables </h2> </head> <table>"""
    messerr="""<table style="empty-cells: hide" border="1"> <tr> <th> <a href="name.html">Name</a> </th> <th> <a href="error.html">Detected Error</a> </th> """

    message1= '<a href=' + os.path.relpath(resultfile) + '>' + modelname +'-'+ model1var+'</a>' +' </td>'
    if(len(diff1)==0):
         emptyhref= model2var+' / '+ str(totalComparedvar) +' [' +str(maxerror)+ ']'
         s = '\n'.join(['<tr>','<td id=2>',message1,'<td id=2 bgcolor=#00FF00 align="center">',emptyhref,'</td>','</tr>']) 
         fileouthtml.write(s)
         fileouthtml.write('\n')   
    
    if(len(diff1)>0):         
         ## Html page to sort differed variable by name
         f=open(fileerror,'w')         
         for i in xrange(len(diff1)):
             var=diff1[i].split('-') 
             str1=''.join([modelname+'_'+var[0]+'.html'])
             x1='<td>'+'<a href='+str1.replace(' ','')+'>'+ str(var[0])+ '</a>'+'</td>'
             errval="{:.1e}".format(Decimal(var[1]))
             diff='<td>'+str(errval)+'</td>'+'</tr>'
             if(i==0):
               s = '\n'.join([messcommon,reference,comparison,comparedmodel,'</table>','<br>',messerr,'<tr>',x1,diff])
             else:
               s = '\n'.join(['<tr>',x1,diff]) 
             
             f.write(s)
             f.write('\n')
         closetags ='\n'.join(['</table>','</html>'])
         f.write(closetags)
         f.write('\n')
         f.close()
         
         ## Html page to sort differed variable by highest error tolerance
         tol=open(filetolerance,'w')         
         for i in xrange(len(difftol)):
             var=difftol[i][0]
             var1=difftol[i][1]             
             str1=''.join([modelname+'_'+var+'.html'])
             x1='<td>'+'<a href='+str1.replace(' ','')+'>'+ str(var)+ '</a>'+'</td>'
             errval="{:.1e}".format(Decimal(var1))
             diff='<td>'+str(errval)+'</td>'+'</tr>'
             if(i==0):
               s = '\n'.join([messcommon,reference,comparison,comparedmodel,'</table>','<br>',messerr,'<tr>',x1,diff])
             else:
               s = '\n'.join(['<tr>',x1,diff]) 
             
             tol.write(s)
             tol.write('\n')
         closetags ='\n'.join(['</table>','</html>'])
         tol.write(closetags)
         tol.write('\n')
         tol.close()
         
         
         #diff = '<a href='+ os.path.relpath(fileerror) +'>'+str(len(diff1))+'</a>'+ '(' + str(totalvar) +'variables)' + '[' +str(maxEstTol)+ ']' +'</td>'+'</tr>'      
         diff = model2var + ' / ' + str(totalComparedvar)+ ' / ' + '<a href='+ os.path.relpath(fileerror) +'>'+str(len(diff1))+'</a>'+ ' [' +str(maxerror)+ ']' +'</td>'+'</tr>'
         s = '\n'.join(['<tr>','<td id=2>',message1,'<td id=2 bgcolor=#FF0000 align="center">',diff])
         fileouthtml.write(s)
         fileouthtml.write('\n')
   
def checkrows(model):
   ''' This function used to delete duplicate rows in a numpy array'''
   column1=model[:,0]
   indices = numpy.setdiff1d(numpy.arange(len(column1)), numpy.unique(column1, return_index=True)[1])
   if len(indices>0):
      '''axis=0 represent the rows to be deleted from the obtained index '''
      model= numpy.delete(model, indices, axis=0)
   return model
    
def generatehtml(model1,model2,namesBoth,col1var,col2var,htmlfile,resultfile,dircount):
    '''This function is used to fetch the array of data from mat files and create the html graph for the differed variables which can be viewed in browser'''
    #get the modelname of the file                   
    filename,fileExtension = os.path.splitext(htmlfile)
    report=os.path.basename(str(htmlfile)).replace(fileExtension,' ')      
    err=report+'res'+str(dircount)
    report1='\''+report+'\''
    #create a new directory for the result_files which differ
    path=os.path.dirname(os.path.abspath(str(resultfile)))
    newpath=os.path.join(path,err.replace(' ',''))
    if not os.path.exists(newpath): 
        os.mkdir(newpath)
                
        
    model1=checkrows(model1)
    model2=checkrows(model2)
    i = numpy.intersect1d(model1[:,0], model2[:,0])   
    
    # Get the appropriate datas from model1 and model2 for the variables and create a new array which will be written in the javascript part of html file   
    for z in range(len(namesBoth)):
        name=namesBoth[z]
        var1=col1var[z]
        var2=col2var[z]
        if (name != 'Time'):
             try:
               #for each variable get the appropriate column datas from model1 and model2 
               fast_c = numpy.vstack([i, model1[numpy.in1d(model1[:,0], i), var1], model2[numpy.in1d(model2[:,0], i), var2]]).T
               dygraph_array= repr(fast_c).replace('array',' ').replace('(' ,' ').replace(')' ,' ')
               htmlreport=newpath+'\\'+report+'_'+name+'.html'     
               htmlreport=htmlreport.replace(' ','').replace('\\','/')
               with open(htmlreport, 'wb') as f:
                message = """<html>
<head>
<script type="text/javascript" src="../dygraph-combined.js"></script>
<style type="text/css">
    #graphdiv {
      position: absolute;
      left: 10px;
      right: 10px;
      top: 40px;
      bottom: 10px;
    }
    </style>
</head>
<body>
<div id="graphdiv"></div>
<p><input type=checkbox id="0" checked onClick="change(this)">
<label for="0">reference</label>
<input type=checkbox id="1" checked onClick="change(this)">
<label for="1">actual</label>
,  Parameters used for the comparison: Relative tolerance 1e-3 </p>
<script type="text/javascript">
g = new Dygraph(document.getElementById("graphdiv"),"""
              
                varname='title:'+'\''+name+'\''+','
                option="""xlabel: ['time'],
labels: ['time','reference','actual'],
visibility:[true,true,true]
}"""
                message2="""function change(el) {
g.setVisibility(parseInt(el.id), el.checked);
}
</script>
</body>
</html>"""

                s = '\n'.join([message,str(dygraph_array),",","{",varname,option,")",";",message2])
                f.write(s)
                f.close()
             except IndexError:
                pass

def directorysize(dirname):
  ## calculate the size of directory, traverses subdirectory and return the size in MB
  folder_size = 0
  for (path, dirs, files) in os.walk(dirname):
    for file in files:
      filename = os.path.join(path, file)
      folder_size += os.path.getsize(filename)
  size=folder_size/(1024*1024.0)
  return round(size,1)


def get_column(n,table):
   result = []
   for line in table:
      result.append(line[n])     
   return result

def genlogfilesreport(logfile):
  ''' Read the log files from the directory and write to a single log file as separate log files are used when running in parallel compare analysis '''
  dir1=os.path.dirname(logfile)
  dir2=os.path.join(dir1,'logfiles').replace('\\','/')
  if(os.path.isdir(dir2)):
      files=os.listdir(dir2)
      f=open(logfile,'w')
      for i in xrange(len(files)):
          os.chdir(dir2)      
          logfileopen=open(files[i])
          data=logfileopen.read()
          f.write(data)
          f.write('\n')
      logfileopen.close()    
      f.close()
     
def genregressionreport(logfile,totaldir,filecount,Time,resultdirsize,baselinedir):
  ''' the function is used to parse the html files and collect the table datas from different html files and finally generate single regression chart'''
  dir1=os.path.dirname(logfile)
  dir2=os.path.join(dir1,'rfiles').replace('\\','/')
  if(os.path.isdir(dir2)):
    files=os.listdir(dir2)
    ## sort the files to maintain the order of execution when reading from directory 
    sortedfiles = sorted(files, key=lambda x: int(x.split('_')[0]))
    percent=[]
    header=[]
    hreflist=[]
    dirname=[]
    for i in xrange(len(sortedfiles)):
         os.chdir(dir2)      
         soup = BeautifulSoup(open(sortedfiles[i]))
         h=soup.find_all('td',{"id":1})
         per=soup.find_all('td',{"id":100})
         data=soup.find_all('td',{"id":2})
         dir=soup.find_all('th',{"id":0})
         hreflist.append(data)
         dirname.append(dir)
         header.append(h)
         percent.append(per)
         
    os.chdir(dir1)
    filename,fileExtension = os.path.splitext(logfile)
    logfile1=logfile.replace(fileExtension,'.html')    
    f=open(logfile1,'w') 
    date_time_info = datetime.datetime.now().strftime("%I:%M%p on %B %d, %Y")
    date_time_info1 =' '.join(['<tr>','<td align="right">','<b>Generated: </td>','<td>',date_time_info,'by PySimulator','</td>','</tr>'])
    tolerance=' '.join(['<tr>','<td align="right"> <b>Given Error Tolerance: </b> </td>','<td>','1e-3','</td>','</tr>'])
    diskspace=' '.join(['<tr>','<td align="right"> <b>Disk space of all used result files: </b> </td>','<td>',str(resultdirsize),' ','MB','</td>','</tr>'])
    dircount=' '.join(['<tr>','<td align="right"> <b>Total number of compared files: </b></td>','<td>',str(int(totaldir)*int(filecount)),'against',str(filecount),'baseline files','</td>','</tr>'])
    comparedvariable=' '.join(['<tr>','<td align="right"> <b>Total number of Compared Variables: </b> </td>', '<td id=var> </td>','</tr>'])
    resultspace=' '.join(['<tr>','<td align="right"> <b>Disk space of full report directory: </b> </td>','<td id=resultdir> </td>','</tr>'])
    #filecounts=' '.join(['<h4>','Number of Files Compared:',str(filecount),'</h4>'])
    
    TotalTime =' '.join(['<tr>','<td align="right">','<b>Time Taken:</b></td>','<td>',time.strftime("%Hh:%Mm:%Ss", time.gmtime(Time)),'</td>','</tr>'])

    m1='''<body>
    <style>
      header {
      }
    nav {
    line-height:10px;   
    padding:20px;          
        }
    footer {
    margin-bottom:10px;    
    padding:0px;          
     }
    </style>'''

    head= '<header> <h1> Regression Report </h1> </header>'
    colorlegend='<p><a href="#color">Legend</a></p>'

    colorinfo='''<h3> <a name="color"> Coloring </a> </h3>
    <fieldset style="width:600px">
    <table border="0">
    <tr>
    <td>
    <font style="background-color:#FF0000"> Red: </font> </td> </tr>
    <tr> <td align="right"><b>Per File: </b> </td> <td>Comparison failed,(i.e.) at least one variable with large error </td> </tr>
    <tr> <td align="right"><b>Per Column or Row: </b> </td> <td>Only 0-50% of the corresponding files passed the test </td> </tr>
    <tr>
    <td> <font style="background-color:#FFA500">Orange:</font> </td> </tr>
    <tr> <td align="right"><b>Per Column or Row: </b> </td> <td>&gt; 50% and &lt; 100% of the corresponding files passed the test </td> </tr>
    <tr> <td align="right"> <b>Total: </b> </td> <td> &gt; 50% and &lt; 100% of all files passed the test </td></tr>
    <tr>
    <td> <font style="background-color:#00FF00"> Green: </font> </td> </tr>
    <tr> <td align="right"><b>Per File: </b> </td> <td> Comparison passed, (i.e.) all compared variables passed the test </td> </tr>
    <tr> <td align="right"> <b>Per Column or Row:</b> </td> <td> 100% of the corresponding files passed the test </td> </tr>
    </table>
    </fieldset>'''

    tabledata=''' <h3> Table Data </h3>
    <fieldset style="width:600px">
    <p align="left"><i>The example table presented below provides description on each identifier of the table data</i></p>
    <table border="1" style="empty-cells: hide">
    <tr> <th>Resultfile</th><th>Status</th><th>Baseline Directory </th> <th> Testing Directory1 </th> <th> Testing Directory2 </th></tr>
    <tr> <td> </td> <td align="center" bgcolor="#FFA500">  A  </td> <td> </td> <td align="center" bgcolor="#FF0000"> C </td>  <td align="center" bgcolor="#00FF00"> C </td> </tr>
    <tr> <td> </td> <td align="center" bgcolor="#FFA500">  B  </td> <td> </td> <td align="center" bgcolor="#FF0000"> D </td>  <td align="center" bgcolor="#00FF00"> D </td> </tr>
    <tr> <td> </td> <td> </td> <td align="center"> Baseline </td> </tr>
    <tr> <td>Filename1</td> <td align="center" bgcolor="#FF0000"> E </td> <td align="center"> F </td> <td align="center" bgcolor="#FF0000"> F / G / <a href> H </a> [I] </td>
    <td align="center" bgcolor="#00FF00"> F / G [I] </td>
    </tr>
    </table><br>
    <table>
    <tr>
    <td align="right"> <b>A-</b> </td> <td> Overall status of Number of total passed files / Number of total failed files </td> </tr>
    <tr>
    <td align="right"> <b>B- </b> </td> <td> Overall Percentage status of total passed files </td> </tr>
    <tr>
    <td align="right"> <b>C- </b> </td> <td> {Number of passed files / Number of  failed files}, in the corresponding directory eg:(Testing Directory1 or Testing Directory2) </td> </tr>
    <tr>
    <td align="right"> <b>D- </b> </td> <td> Percentage of total passed files,in the corresponding directory eg:(Testing Directory1 or Testing Directory2) </td> </tr>
    <tr>
    <td align="right"> <b>E- </b> </td> <td> {Number of passed files / Number of failed files} for this file eg: (Filename1) </td> </tr>
    <tr>
    <td align="right"> <b>F- </b> </td> <td> Number of variables contained in the File </td> </tr>
    <tr>
    <td align="right"> <b>G- </b> </td> <td> Number of variables compared </td> </tr>
    <tr>
    <td align="right"> <b>H- </b> </td> <td> Number of variables greater than given tolerance with link to the list of these variables </td> </tr>
    <tr>
    <td align="right"> <b>I- </b> </td> <td>  Maximum error of all compared variables </td> </tr>
    </table>
    </fieldset>
    <p align="center"><a href="index.html">Return</a></p>'''

    s='\n'.join(['<html>',m1,head,'<nav>','<table>',tolerance,diskspace,dircount,comparedvariable,resultspace,date_time_info1,TotalTime,'</table>','</nav>',colorlegend,'<footer>','<table style="empty-cells: hide" border="1">','<tr>','<th id=0>','Result Files','</th>','<th id=0>','Status','</th>''<th id=0>',os.path.basename(baselinedir),'</th>'])
    f.write(s)
    f.write('\n')
    
    ## loop for first row directory names           
    for m in xrange(len(dirname[0])):
       if(m>0):
         dname=get_column(m,dirname)   
         for n in xrange(len(dname)):
                if(n==(len(dname)-1)):
                   s=''.join([str(dname[n]),'</tr>'])
                else:
                   s=''.join([str(dname[n])])
                f.write(s)
                f.write('\n')
                
    ## loop for second row header status and regarding number of files passed and failed for each Directories of files
    pstatus=[]
    hstatus=[]
    for h in xrange(len(header[0])):
        hname=get_column(h,header)
        m1='<tr><td></td><td id=hstatus align="center"></td><td></td>'
        f.write(m1)
        
        passfiles=[]
        failfiles=[]
        for z in xrange(len(hname)):
          d=str(hname[z].string).split('/')
          passednumber=str(d[0]).split('passed')
          failednumber=str(d[1]).split('failed')
          passfiles.append(int(passednumber[0]))
          failfiles.append(int(failednumber[0])) 
               
        p1=int(sum(passfiles))+int(sum(failfiles))
        p2=int(sum(passfiles))*100/p1
        pstatus.append(str(p2))
        hstatus.append(str(sum(passfiles))+' / '+str(sum(failfiles)))
    
        for i in xrange(len(hname)):
           if(i==(len(hname)-1)):
              s=''.join([str(hname[i]),'</tr>'])
           else:
              s=''.join([str(hname[i])])
           f.write(s)
           f.write('\n')  
    
    ## loop for third row percentage status of number of files passed and failed for each Directories of files
          
    for p in xrange(len(percent[0])):    
       pname=get_column(p,percent)
       m1='<tr><td></td><td id=pstatus align="center"></td><td></td>'
       f.write(m1)
       for i in xrange(len(pname)):
          if(i==(len(pname)-1)):
             s=''.join([str(pname[i]),'</tr>'])
          else:
             s=''.join([str(pname[i])])
          f.write(s)
          f.write('\n')  
          
       baseheader='<tr><td></td><td></td><td align="center">Baseline<td>'
       f.write(baseheader)
    
    ## loop for fourth row for calculating status of number of files passed and failed for individual files
    status=[]
    ## list variables to count the number of total number of variables and differed variables 
    comparevar=[]
    differedvar=[]
    for i in xrange(len(hreflist[0])):                       
      if(i%2==0):
         x=get_column(i,hreflist)
         x1=x[0].find('a').string
         y=x1.split('-')
         #href='<a href='+os.path.basename(logfile)+'>'+ x1 +'</a>'         
         #s='\n'.join(['<tr>','<td>',href,'</td>'])
         s='\n'.join(['<tr>','<td>',str(y[0]),'</td>','<td id=status align="center">','</td>','<td align="center">',str(y[-1]),'</td>'])
         f.write(s)
         f.write('\n')
         
      if(i%2!=0):
        x=get_column(i,hreflist)
        green=[]
        red=[]
        ## loop for preparing status of the single file compared with several directory of the same file
        for k in xrange(len(x)):
          s=BeautifulSoup(str(x[k]))
          tag=s.td
          checkcolor=tag['bgcolor']
          if(checkcolor=="#00FF00"):
             green.append(checkcolor)
             #var1=str(x[k].find('a').string).split('[')
             var1=str(x[k]).split('[')
             var2=var1[0].split('/')
             comparevar.append(int(var2[-1]))
          else:
             red.append(checkcolor)
             var1=str(x[k]).split('<a')
             var2=str(var1[0]).split('/')
             comparevar.append(int(var2[1]))            
             diffvar=x[k].find('a').string
             differedvar.append(int(diffvar)) 
             
        st=str(len(green))+'/'+str(len(red))+'/'+str(len(green)+len(red))
        status.append(st)
        ## loop for preparing the main table of Regression report from different files
        for z in xrange(len(x)): 
            if(z==(len(x)-1)):               
               s='\n'.join([str(x[z]),'</tr>'])
            else:
               s='\n'.join([str(x[z])])            
            f.write(s)
            f.write('\n')
    if(i==len(hreflist[0])-1):
         s='\n'.join(['</table>','</footer>',colorinfo,tabledata,'</body>','</html>'])
         f.write(s)
         f.write('\n')
    
    f.close()
    
    ## get the size of the result files directory
    resultsize=directorysize(dir1)
    
    ## open the file to print the final status of the compared files
    stat = BeautifulSoup(open(logfile1))
    dat=stat.find_all('td',{"id":"status"})
    hst=stat.find_all('td',{"id":"hstatus"})
    pst=stat.find_all('td',{"id":"pstatus"})
    totalvar=stat.find_all('td',{"id":"var"})
    ressize=stat.find_all('td',{"id":"resultdir"})

    totalvar[0].string=str(sum(comparevar))+' ('+str(sum(comparevar)-sum(differedvar))+' passed'+', '+str(sum(differedvar))+' failed)'
    ressize[0].string=str(resultsize)+' '+'MB'
    
    ## condition for updating the percentage status and color code in first and  second row
    colorpercent=int(pstatus[0])
    
    ## green color
    if(colorpercent==100):   
      hst[0]['bgcolor']="#00FF00"
      hst[0].string=hstatus[0]
      pst[0]['bgcolor']="#00FF00"
      pst[0].string=str(colorpercent)+'%'
    
    ## orange color
    if(colorpercent>=51 and colorpercent<=99):
      hst[0]['bgcolor']="#FFA500"
      hst[0].string=hstatus[0]
      pst[0]['bgcolor']="#FFA500"
      pst[0].string=str(colorpercent)+'%' 
      
    ## red color
    if(colorpercent<=50):
       hst[0]['bgcolor']="#FF0000"
       hst[0].string=hstatus[0]
       pst[0]['bgcolor']="#FF0000"
       pst[0].string=str(colorpercent)+'%'
    
    ## loop for updating the status and color code of individual files in different directory, row comparison
    for i in xrange(len(dat)):
        d=str(status[i]).split('/')
        percentage=int(d[0])*100/int(d[2])   
        if (percentage==100):
          ## green color
          dat[i]['bgcolor']="#00FF00"
          dat[i].string=d[0]+' / '+d[1]
        if(percentage>=51 and percentage<=99):
          ## orange color
          dat[i]['bgcolor']="#FFA500"
          dat[i].string=d[0]+' / '+d[1]
        if (percentage<=50):
          ## red color
          dat[i]['bgcolor']="#FF0000"
          dat[i].string=d[0]+' / '+d[1]
    #html = stat.prettify("utf-8")
    html = str(stat)
    #html = html.replace('&lt;b&gt;','<b>').replace('&lt;/b&gt;','</b>')
    f=open(logfile1,'w') 
    f.write(html)
    f.close()
    print "Regression report generated"
    webbrowser.open(logfile1)       
    
  else:
    print 'Regression Report failed'
