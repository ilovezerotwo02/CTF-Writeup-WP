import numpy as np
from PIL import Image, ImageDraw, ImageFont
chart=Image.open('bl/b14.png').convert('L')
ca=np.array(chart.point(lambda p:255 if p<150 else 0))
letters=[[15,50],[63,92],[109,139],[153,187],[201,231],[249,275],[291,325],[337,371],[393,407],[436,454],[475,509],[523,552],[561,604]]
centers=[(a+b)/2 for a,b in letters]
bounds=[0]+[(centers[i]+centers[i+1])/2 for i in range(len(centers)-1)]+[617]
cells=[(bounds[i],bounds[i+1]) for i in range(13)]
AZ='ABCDEFGHIJKLMNOPQRSTUVWXYZ'
pos={}
for i,ch in enumerate(AZ[:13]): pos[ch]=(cells[i][0],cells[i][1],64,113)
for i,ch in enumerate(AZ[13:]): pos[ch]=(cells[i][0],cells[i][1],193,239)
def crop(ch):
    x0,x1,y0,y1=pos[ch]
    sub=ca[y0:y1+1,int(x0):int(x1)+1]
    ys,xs=np.nonzero(sub)
    return chart.crop((int(x0)+xs.min()-2, y0+ys.min()-2, int(x0)+xs.max()+3, y0+ys.max()+3))
src=Image.open(r'C:/Users/ASUS/.workbuddy/clipboard-images/clipboard-2026-10-24T01-08-27-833Z-280fe0a9.png').convert('L')
sa=np.array(src.point(lambda p:255 if p<150 else 0))
runs=[(51,111),(116,171),(193,232),(247,311),(335,365),(393,447),(460,506),(527,573),(597,655)]
ours=[]
for x0,x1 in runs:
    ys,xs=np.nonzero(sa[78:166,x0-2:x1+3])
    ours.append(src.crop((x0-2+xs.min(),78+ys.min(),x0-2+xs.max()+1,78+ys.max()+1)))
dec='HTUISCOOL'
W=9*150; H=340
cv=Image.new('RGB',(W,H),'white'); d=ImageDraw.Draw(cv)
try: f=ImageFont.truetype('arial.ttf',34); fs=ImageFont.truetype('arial.ttf',20)
except: f=fs=None
for i,(g,ch) in enumerate(zip(ours,dec)):
    x=i*150+25
    g2=g.copy(); g2.thumbnail((110,110)); cv.paste(g2,(x+20,20))
    d.text((x+45,145),ch,fill='red',font=f)
    c=crop(ch); c.thumbnail((110,110)); cv.paste(c,(x+20,200))
d.text((10,300),'top: glyph in slide   bottom: matched chart letter',fill='black',font=fs)
cv.save('verify.png'); print('saved', cv.size, dec)
