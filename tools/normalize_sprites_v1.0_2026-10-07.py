# 叮咚序列圖正規化 v1.0 2026-10-07：切格→統一 256px 格→底線對齊→輸出 WebP 橫向序列圖
import json, sys, numpy as np
from PIL import Image
SRC='/home/claude/assets_in/dingdong_assets/'
OUT='/home/claude/sprites_out/'
man=json.load(open(SRC+'manifest.json'))
CELL=256
def segments(a, expect):
    col=(a>40).sum(0)>0
    segs=[];inrun=False
    for x,v in enumerate(col):
        if v and not inrun: s=x;inrun=True
        if not v and inrun: segs.append([s,x]);inrun=False
    if inrun: segs.append([s,len(col)])
    # 去掉太窄的碎片（星星、小點）併入最近的格
    W=a.shape[1]/max(expect,1)
    while len(segs)>expect:
        widths=[e-s for s,e in segs]; i=int(np.argmin(widths))
        if i==0: j=1
        elif i==len(segs)-1: j=i-1
        else: j=i-1 if segs[i][0]-segs[i-1][1] < segs[i+1][0]-segs[i][1] else i+1
        a0,b0=min(segs[i][0],segs[j][0]),max(segs[i][1],segs[j][1]); 
        segs=[sg for k,sg in enumerate(segs) if k not in (i,j)]+[[a0,b0]]; segs.sort()
    while len(segs)<expect:
        widths=[e-s for s,e in segs]; i=int(np.argmax(widths)); s,e=segs[i]
        # 從最寬的格中，找 alpha 最少的欄位切開
        sub=(a[:,s:e]>40).sum(0); lo=int((e-s)*.3); hi=int((e-s)*.7)
        cut=s+lo+int(np.argmin(sub[lo:hi])); segs[i:i+1]=[[s,cut],[cut,e]]
    return segs
report=[]
for an in man['animations']:
    f=an['file']; n=an['frames']; name=f.split('/')[-1].replace('.png','')
    im=Image.open(SRC+f).convert('RGBA'); a=np.array(im)[:,:,3]
    segs=segments(a,n)
    boxes=[]
    for s,e in segs:
        rows=np.where((a[:,s:e]>40).sum(1)>0)[0]; boxes.append((s,rows[0],e,rows[-1]+1))
    maxH=max(b[3]-b[1] for b in boxes); maxW=max(b[2]-b[0] for b in boxes)
    base=max(b[3] for b in boxes)
    top=min(b[1] for b in boxes)
    span=base-top
    cell=128 if 'runner' in name else CELL
    medH=float(np.median([b[3]-b[1] for b in boxes]))
    sc=min(cell*(0.62 if cell==256 else 0.8)/medH, cell*0.97/span, cell*0.97/maxW)
    sheet=Image.new('RGBA',(cell*n,cell),(0,0,0,0))
    for i,(x0,y0,x1,y1) in enumerate(boxes):
        fr=im.crop((x0,y0,x1,y1)); w,h=fr.size
        fr=fr.resize((max(1,round(w*sc)),max(1,round(h*sc))),Image.LANCZOS)
        px=i*cell+(cell-fr.size[0])//2
        py=round(cell*0.97 - (base-y0)*sc)   # 保留相對高度（跳躍）並把共同底線放在格子 97% 處
        sheet.alpha_composite(fr,(px,max(0,py)))
    sheet.save(OUT+name+'.webp','WEBP',quality=90,method=6)
    sheet.save(OUT+name+'.png')
    report.append((name,n,len(segs),cell,round(sc,3)))
for r in report: print(r)
