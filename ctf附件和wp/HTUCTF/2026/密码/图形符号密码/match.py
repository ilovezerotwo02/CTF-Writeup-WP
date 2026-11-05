import numpy as np
from PIL import Image, ImageFilter

chart=np.array(Image.open('bl/b14.png').convert('L').point(lambda p:255 if p<150 else 0))
# cell boundaries from row1 letters
letters=[[15,50],[63,92],[109,139],[153,187],[201,231],[249,275],[291,325],[337,371],[393,407],[436,454],[475,509],[523,552],[561,604]]
centers=[(a+b)/2 for a,b in letters]
bounds=[0]+[ (centers[i]+centers[i+1])/2 for i in range(len(centers)-1) ]+[chart.shape[1]]
cells=list(zip(bounds[:-1],bounds[1:]))
print([f'{b:.0f}' for b in bounds])

def bbox_norm(img, size=56):
    ys,xs=np.nonzero(img)
    if len(ys)==0: return np.zeros((size,size),np.float32)
    y0,y1,x0,x1=ys.min(),ys.max(),xs.min(),xs.max()
    sub=img[y0:y1+1, x0:x1+1].astype(np.uint8)*255
    im=Image.fromarray(sub)
    # keep aspect, pad to square
    w,h=im.size; s=max(w,h)
    canvas=Image.new('L',(s,s),0); canvas.paste(im,((s-w)//2,(s-h)//2))
    canvas=canvas.resize((size,size), Image.LANCZOS).filter(ImageFilter.GaussianBlur(1.6))
    arr=np.array(canvas,dtype=np.float32)
    arr=arr-arr.mean()
    n=np.linalg.norm(arr)
    return arr/n if n>0 else arr

def glyph_from_band(y0,y1,x0,x1):
    sub=chart[y0:y1+1, int(x0):int(x1)+1]
    return sub

lettersAZ='ABCDEFGHIJKLMNOPQRSTUVWXYZ'
tmpl={}
for i,ch in enumerate(lettersAZ[:13]):
    x0,x1=cells[i]
    tmpl[ch]=bbox_norm(glyph_from_band(64,113,x0,x1))
for i,ch in enumerate(lettersAZ[13:]):
    x0,x1=cells[i]
    tmpl[ch]=bbox_norm(glyph_from_band(193,239,x0,x1))

# our glyphs
src=Image.open(r'C:/Users/ASUS/.workbuddy/clipboard-images/clipboard-2026-10-24T01-08-27-833Z-280fe0a9.png').convert('L')
arr=np.array(src.point(lambda p:255 if p<150 else 0))
runs=[(51,111),(116,171),(193,232),(247,311),(335,365),(393,447),(460,506),(527,573),(597,655)]
ours=[]
for x0,x1 in runs:
    sub=arr[78:166, x0-2:x1+3]
    ours.append(bbox_norm(sub))

print('\n--- best matches per glyph ---')
res=[]
for gi,g in enumerate(ours,1):
    sc=sorted(((float(np.sum(g*tmpl[c])),c) for c in lettersAZ), reverse=True)
    res.append(sc)
    print(f'#{gi}: ' + ', '.join(f'{c}={s:.3f}' for s,c in sc[:4]))
# also print matrix for top letters
