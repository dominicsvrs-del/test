"""Aligns script words to voiceover speech segments (silence-based) via DP; writes words.json."""
import re, json, subprocess, sys
AUDIO=sys.argv[1]; TEXT=open(sys.argv[2]).read().split()
log=subprocess.run(['ffmpeg','-i',AUDIO,'-af','silencedetect=noise=-35dB:d=0.12','-f','null','-'],capture_output=True,text=True).stderr
st=[float(x) for x in re.findall(r'silence_start: ([\d.]+)',log)]; en=[float(x) for x in re.findall(r'silence_end: ([\d.]+)',log)]
dur=float(re.search(r'Duration: (\d+):(\d+):([\d.]+)',log).group(3))+60*int(re.search(r'Duration: (\d+):(\d+)',log).group(2))
segs=[]; cur=0.03
for s,e in zip(st,en):
    if s-cur>0.08: segs.append((cur,s))
    cur=e
if dur-cur>0.08: segs.append((cur,dur))
def syl(w):
    w=w.lower().replace('ki','kaii') if w.lower().strip('.,!?:"„“')=='ki' or w.lower().startswith('ki-') else w.lower()
    w=re.sub(r'(ei|ie|au|eu|äu|ai)','a',w); return max(1,len(re.findall(r'[aeiouäöüy]+',w)))
S=[syl(w) for w in TEXT]; punct=[bool(re.search(r'[.,!?:]$|["“]$',w)) for w in TEXT]
rate=float(sys.argv[4]) if len(sys.argv)>4 else sum(S)/sum(b-a for a,b in segs)
N,M=len(TEXT),len(segs); INF=1e18
pre=[0]
for s in S: pre.append(pre[-1]+s)
dp=[[INF]*(M+1) for _ in range(N+1)]; bk=[[0]*(M+1) for _ in range(N+1)]; dp[0][0]=0
for j in range(1,M+1):
    d=segs[j-1][1]-segs[j-1][0]
    for i in range(1,N+1):
        for k in range(max(0,i-25),i):
            if dp[k][j-1]>=INF: continue
            import math
            r=(pre[i]-pre[k])/d; c=4*math.log(r/rate)**2
            pause=(segs[j][0]-segs[j-1][1]) if j<M else 1
            wd=TEXT[i-1]
            if i<N:
                if re.search(r'[.?!:]["“]?$',wd): c-=0.4*pause
                elif wd.endswith(','): c+=0.2
                else: c+=0.8+3*pause
            if j==M and i!=N: c=INF
            if dp[k][j-1]+c<dp[i][j]: dp[i][j]=dp[k][j-1]+c; bk[i][j]=k
out=[]; i=N
for j in range(M,0,-1):
    k=bk[i][j]; a,b=segs[j-1]; tot=pre[i]-pre[k]; acc=0
    chunk=[]
    for w in range(k,i): chunk.append([TEXT[w],round(a+(b-a)*acc/tot,3)]); acc+=S[w]
    out=chunk+out; print(f'{a:6.2f}-{b:6.2f}  {" ".join(TEXT[k:i])}',file=sys.stderr); i=k
json.dump(out,open(sys.argv[3],'w'),ensure_ascii=False)
