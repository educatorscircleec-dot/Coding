import numpy as np, soundfile as sf
A="/home/user/Coding/episode01/build/audio/"; SR=44100; T=60.0
L=np.zeros(int(SR*T)); R=np.zeros(int(SR*T))
def load(n):
    a,sr=sf.read(A+n+".wav"); a=a.mean(1) if a.ndim>1 else a
    assert sr==SR,(n,sr); return a
def place(n,t,db,pan=0.0,fin=0.3,fout=0.5,dur=None):
    a=load(n).copy()
    if dur: a=a[:int(dur*SR)]
    i=int(fin*SR); o=int(fout*SR)
    if i: a[:i]*=np.linspace(0,1,i)
    if o: a[-o:]*=np.linspace(1,0,o)
    a*=10**(db/20); s=int(t*SR); e=min(len(L),s+len(a)); a=a[:e-s]
    L[s:e]+=a*np.sqrt((1-pan)/2)*1.414; R[s:e]+=a*np.sqrt((1+pan)/2)*1.414
def bed(names,t0,t1,db,pan=0.0):
    t=t0; k=0
    while t<t1-0.2:
        d=min(5.0,t1-t); place(names[k%len(names)],t,db,pan,fin=0.6,fout=0.6,dur=d); t+=4.4; k+=1
# --- ambience beds ---
bed(["chirping_birds_0","chirping_birds_1","chirping_birds_2"],0,30,-20,-0.3)   # day outdoors/indoors
bed(["chirping_birds_1","chirping_birds_0"],54.5,60,-19,0.3)
bed(["crickets_4","crickets_0"],30,50,-25,0.2)                                   # evening
bed(["wind_1","wind_5"],50,55.5,-24)                                              # rooftop breeze
# --- spot effects synced to picture ---
place("crow_3",0.4,-24,0.6); place("footsteps_4",0.6,-12,0.0,dur=4.2)              # shot1 running
place("hen_3",2.5,-30,-0.7,dur=2.0)
place("pouring_water_5",5.3,-18,0.3,dur=4.5)                                      # shot2 kitchen
place("clock_tick_3",10.2,-22,-0.4,dur=9.6)                                       # shot3-4 interior quiet
place("water_drops_0",20.3,-24,0.4,dur=4.4)                                       # shot5
place("laughing_2",25.4,-20,-0.3,dur=4.5); place("laughing_1",27.0,-26,0.5,dur=3.0)  # shot6 hopscotch
place("door_wood_creaks_0",30.0,-22,-0.2,dur=2.0)                                 # shot7 doorway
place("laughing_2",35.2,-28,0.4,dur=2.5)                                          # shot8 children outside
place("pouring_water_5",41.2,-20,0.2,dur=3.6)                                     # shot9 meal: water jug
place("clapping_1",45.6,-17,0.0,dur=3.8); place("laughing_1",47.4,-24,-0.3,dur=2.4)  # shot10 birthday
place("crow_0",51.0,-30,0.7,dur=3.0)                                              # shot11 rooftop
place("rooster_5",55.4,-32,-0.6,dur=2.5); place("crow_3",57.0,-27,0.5,dur=2.8)   # shot12 morning lane
# --- dialogue (diegetic) ---
place("mom",31.0,-7,-0.15,fin=0.02,fout=0.15)
place("kid",36.4,-6,0.2,fin=0.02,fout=0.1)
# --- narration (centre, upfront) ---
for n,t in [("n1",0.9),("n2",10.4),("n3",20.6),("n4",50.7),("n5",55.6)]:
    place(n,t,-1.5,0.0,fin=0.02,fout=0.1)
# master: ducking-free since beds are low; normalise peak, short fades
st=np.stack([L,R],1); st[:int(.4*SR)]*=np.linspace(0,1,int(.4*SR))[:,None]; st[-int(1.2*SR):]*=np.linspace(1,0,int(1.2*SR))[:,None]
st*=0.89/np.abs(st).max(); sf.write("/home/user/Coding/episode01/build/soundtrack.wav",st,SR)
print("ok")
