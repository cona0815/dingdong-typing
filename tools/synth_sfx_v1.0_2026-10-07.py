# 注音小手指 音效／短樂句合成 v1.0 2026-10-07
import numpy as np, wave, subprocess, os
SR=44100
rng=np.random.default_rng(7)
def t(d): return np.arange(int(SR*d))/SR
def env(d,a=0.004,decay=8.0):
    x=t(d); e=np.exp(-decay*x); n=max(1,int(SR*a)); e[:n]*=np.linspace(0,1,n); return e
def sine(f,d,ph=0):
    if callable(f):
        x=t(d); fr=f(x); return np.sin(2*np.pi*np.cumsum(fr)/SR+ph)
    return np.sin(2*np.pi*f*t(d)+ph)
def bell(f,d,decay=6,bright=1.0):
    parts=[(1,1),(2.76,.45*bright),(5.4,.22*bright),(8.93,.08*bright)]
    s=sum(a*sine(f*r,d)*env(d,0.002,decay*(1+0.6*i)) for i,(r,a) in enumerate(parts)); return s
def marimba(f,d=0.45):
    return (sine(f,d)*env(d,0.003,7)+0.35*sine(f*4,d)*env(d,0.002,22)+0.12*sine(f*9.9,d)*env(d,0.001,40))
def kalimba(f,d=0.7):
    return sine(f,d)*env(d,0.006,4.5)+0.25*sine(f*5.4,d)*env(d,0.003,18)
def steel(f,d=0.5):
    return sine(f,d)*env(d,0.004,5)+0.5*sine(f*2.01,d)*env(d,0.004,7)+0.3*sine(f*3.0,d)*env(d,0.003,10)+0.15*sine(f*4.2,d)*env(d,0.002,14)
def pluck(f,d=1.0,bright=0.5):
    N=int(SR/f); buf=rng.uniform(-1,1,N)*bright+ (1-bright)*np.sin(np.linspace(0,2*np.pi,N))
    out=np.zeros(int(SR*d)); 
    for i in range(len(out)):
        out[i]=buf[i%N]; buf[i%N]=0.497*(buf[i%N]+buf[(i+1)%N])
    return out*env(d,0.001,2.5)
def toy_trumpet(f,d=0.18):
    x=t(d); vib=1+0.006*np.sin(2*np.pi*6*x)
    s=sum((1/k)*np.sin(2*np.pi*f*k*np.cumsum(vib)/SR) for k in (1,2,3,4,5))
    e=np.minimum(1,x/0.015)*np.exp(-3*x); e[-int(SR*0.03):]*=np.linspace(1,0,int(SR*0.03)); return s*e*0.6
def noise(d): return rng.uniform(-1,1,int(SR*d))
def lowpass(x,a=0.15):
    y=np.zeros_like(x); 
    for i in range(1,len(x)): y[i]=y[i-1]+a*(x[i]-y[i-1])
    return y
def highpass(x,a=0.15): return x-lowpass(x,a)
def place(dst,src,at):
    i=int(at*SR); j=min(len(dst),i+len(src)); dst[i:j]+=src[:j-i]; return dst
def canvas(d): return np.zeros(int(SR*d))
def reverb(x,mix=0.18):
    y=x.copy()
    for dl,g in ((0.031,.5),(0.047,.4),(0.071,.3),(0.113,.22),(0.157,.15)):
        n=int(SR*dl); z=np.zeros_like(x); z[n:]=x[:-n]*g; y+=z*mix/0.5
    return y
def fin(x,peak_db=-3,tail=0.01):
    n=int(SR*tail); x=x.copy(); x[-n:]*=np.linspace(1,0,n)
    x=x/ (np.max(np.abs(x))+1e-9) * 10**(peak_db/20); return x
C5,D5,E5,F5,G5,A5,B5=523.25,587.33,659.25,698.46,783.99,880.0,987.77
C6,D6,E6,G6,A6,C7,E7=1046.5,1174.66,1318.51,1567.98,1760.0,2093.0,2637.0
S={}
# 按對：木頭太鼓＋小鈴
d=0.14; drum=sine(lambda x:70+110*np.exp(-x*40),d)*env(d,0.001,30)
click=lowpass(noise(0.012),0.5)*env(0.012,0.0005,250)*0.4
S['sfx_hit']=fin(place(place(drum*1.0+0,click,0),bell(C7,0.1,25,0.4)*0.22,0.004))
# 按錯：柔和 boop
d=0.26; x=t(d); S['sfx_miss']=fin(sine(lambda x:220-80*x/0.26+6*np.sin(2*np.pi*14*x),d)*env(d,0.01,9)+0.3*sine(lambda x:110-40*x/0.26,d)*env(d,0.01,9),-6)
# 完成一個字：兩音鐵琴上行
c=canvas(0.45); place(c,bell(C6,0.4,9),0); place(c,bell(G6,0.38,9),0.08); S['sfx_char']=fin(reverb(c))
# 完成一個詞句：馬林巴四音琶音
c=canvas(0.75); [place(c,marimba(f,0.45),i*0.07) for i,f in enumerate((C5,E5,G5,C6))]; S['sfx_unit']=fin(reverb(c))
# 叮咚吃到字：啵＋咕嚕
d=0.07; pop=sine(lambda x:300+900*x/0.07,d)*env(d,0.001,30)
d2=0.1; gul=sine(lambda x:200-90*x/0.1,d2)*env(d2,0.004,25)*0.6
c=canvas(0.2); place(c,pop,0); place(c,gul,0.075); S['sfx_gulp']=fin(c,-4)
# 連擊里程碑：玩具小號＋閃光
c=canvas(0.75); [place(c,toy_trumpet(f,0.16 if i<3 else 0.32),i*0.09) for i,f in enumerate((G5,C6,E6,G6))]
for k in range(8): place(c,bell(rng.choice([C7,E7,2349.3,3136]),0.18,22,0.3)*0.25,0.3+k*0.045)
S['sfx_combo']=fin(reverb(c,0.12))
# 進入狂熱：上升呼嘯＋鋼鼓
d=0.55; x=t(d); sw=noise(d); 
y=np.zeros(len(sw)); a=0.02
for i in range(1,len(sw)):
    a=0.02+0.5*(i/len(sw))**2; y[i]=y[i-1]+a*(sw[i]-y[i-1])
wh=highpass(y,0.05)*np.minimum(1,x/0.4)*0.6
c=canvas(1.1); place(c,wh,0); [place(c,steel(f,0.45),0.5+i*0.07) for i,f in enumerate((G5,C6,E6,G6,C7))]
S['sfx_fever']=fin(reverb(c))
# 星星：閃亮鈴聲
c=canvas(0.45); place(c,bell(E7,0.4,10,0.6),0); place(c,bell(3520,0.3,14,0.5)*0.6,0.05); place(c,bell(C7,0.25,16,0.4)*0.4,0.1)
S['sfx_star']=fin(reverb(c,0.25),-4)
# 點擊：木頭喀
d=0.07; S['sfx_click']=fin(lowpass(noise(d),0.35)*env(d,0.0005,120)+0.5*sine(1200,d)*env(d,0.0005,90),-6)
# 開始短樂句：上行琶音＋鈴聲
c=canvas(2.2); [place(c,marimba(f,0.5),i*0.11) for i,f in enumerate((C5,E5,G5,C6,E6))]
place(c,bell(C7,1.4,3.5,0.7)*0.8,0.6); place(c,bell(G6,1.4,3.5,0.5)*0.5,0.6)
S['jingle_start']=fin(reverb(c,0.25))
# 過關短樂句：烏克麗麗刷弦＋馬林巴主旋律＋鐘聲＋鈸
c=canvas(5.2)
chords=[(0,(261.63,329.63,392.0,523.25)),(0.9,(349.23,440.0,523.25,698.46)),(1.8,(392.0,493.88,587.33,783.99)),(2.7,(261.63,329.63,392.0,523.25))]
for at,ch in chords:
    for k,f in enumerate(ch): place(c,pluck(f,1.2,0.6)*0.5,at+k*0.018)
mel=[(0,C6),(0.22,E6),(0.45,G6),(0.9,A6),(1.12,G6),(1.35,E6),(1.8,D6),(2.02,E6),(2.25,G6),(2.7,C7)]
for at,f in mel: place(c,marimba(f,0.6)*0.8,at)
for k in range(10): place(c,bell(rng.choice([C7,E7,G6*2,A6*2]),0.5,8,0.4)*0.18,2.75+k*0.07)
cy=highpass(noise(2.3),0.6)*np.minimum(1,t(2.3)/0.9)*np.exp(-np.maximum(0,t(2.3)-1.2)*2.5)*0.25
place(c,cy,2.5)
S['jingle_clear']=fin(reverb(c,0.2))
# 沒過關短樂句：卡林巴下行再上揚（溫暖鼓勵）
c=canvas(3.2); notes=[(0,G5),(0.25,E5),(0.5,D5),(0.75,C5),(1.25,E5),(1.5,G5),(1.85,C6)]
for at,f in notes: place(c,kalimba(f,1.0),at)
place(c,bell(C7,1.2,4,0.4)*0.3,1.85)
S['jingle_retry']=fin(reverb(c,0.22),-4)
os.makedirs('wav',exist_ok=True); os.makedirs('mp3',exist_ok=True)
for k,v in S.items():
    pcm=(np.clip(v,-1,1)*32767).astype(np.int16)
    with wave.open(f'wav/{k}.wav','wb') as w: w.setnchannels(1);w.setsampwidth(2);w.setframerate(SR);w.writeframes(pcm.tobytes())
    subprocess.run(['ffmpeg','-v','quiet','-y','-i',f'wav/{k}.wav','-codec:a','libmp3lame','-b:a','128k',f'mp3/{k}.mp3'])
    print(k, round(len(v)/SR,2),'s', os.path.getsize(f'mp3/{k}.mp3'),'B')
