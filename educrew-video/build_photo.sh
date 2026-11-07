#!/usr/bin/env bash
# Build the 30 s spot from the six miniature scene images: slow camera moves (bottom-anchored so
# the captions baked into the images stay in frame), cross-fades, logo watermark, final logo, music.
# usage: ./build_photo.sh music.wav out.mp4
set -e
cd "$(dirname "$0")"
MUSIC=${1:-music.wav}; OUT=${2:-EduCrew_Miniature_30s.mp4}
S=assets/scenes; F=30
FONT=/usr/share/fonts/truetype/crosextra/Caladea-Bold.ttf; [ -f $FONT ] || FONT=/usr/share/fonts/truetype/crosextra/Caladea-Regular.ttf
# zoompan per clip: z0->z1, horizontal focus fx0->fx1 (0..1), bottom-anchored (fy=1)
zp() { # frames z0 z1 fx0 fx1 fy
  local n=$1; echo "scale=2304:4096,zoompan=z='$2+($3-$2)*on/$n':x='(iw-iw/zoom)*($4+($5-$4)*on/$n)':y='(ih-ih/zoom)*$6':d=1:s=1080x1920:fps=$F,setsar=1"
}
L=165
ffmpeg -loglevel error -y \
 -framerate 30 -loop 1 -t 5.5 -i $S/1_welcome.jpg -framerate 30 -loop 1 -t 5.5 -i $S/2_curriculum.jpg -framerate 30 -loop 1 -t 5.5 -i $S/3_storyboard.jpg \
 -framerate 30 -loop 1 -t 5.5 -i $S/4_lms.jpg -framerate 30 -loop 1 -t 5.5 -i $S/5_assessment.jpg -framerate 30 -loop 1 -t 5.0 -i $S/6_final.jpg \
 -loop 1 -i assets/logo.png -i "$MUSIC" -filter_complex "
 [0]$(zp $L 1.00 1.12 0.75 0.80 1.0)[c0];
 [1]$(zp $L 1.14 1.04 0.15 0.70 1.0)[c1];
 [2]$(zp $L 1.02 1.18 0.30 0.10 0.85),drawbox=x=0:y=1700:w=1080:h=220:color=black@0.35:t=fill,drawtext=fontfile=$FONT:text='Instructional Design & Storyboarding':fontcolor=white:fontsize=54:x=(w-tw)/2:y=1785:shadowcolor=black@0.6:shadowx=2:shadowy=2[c2];
 [3]$(zp $L 1.16 1.06 0.20 0.75 1.0)[c3];
 [4]$(zp $L 1.03 1.15 0.50 0.50 1.0)[c4];
 [5]$(zp 150 1.20 1.00 0.50 0.50 1.0)[c5];
 [c0][c1]xfade=transition=fade:duration=0.5:offset=5.0[x1];
 [x1][c2]xfade=transition=smoothleft:duration=0.5:offset=10.0[x2];
 [x2][c3]xfade=transition=fade:duration=0.5:offset=15.0[x3];
 [x3][c4]xfade=transition=smoothleft:duration=0.5:offset=20.0[x4];
 [x4][c5]xfade=transition=fade:duration=0.5:offset=25.0,trim=duration=30[v];
 [6]split[l1][l2];
 [l1]scale=150:-1,format=rgba[wm];
 [l2]scale=440:-1,format=rgba,fade=t=in:st=26.3:d=1.0:alpha=1[big];
 [v][wm]overlay=W-w-34:34:shortest=1[v1];
 [v1][big]overlay=(W-w)/2:180:enable='gte(t,26.3)':shortest=1,fade=t=in:st=0:d=0.4,format=yuv420p[vout]" \
 -map "[vout]" -map 7:a -t 30 -c:v libx264 -preset veryfast -b:v 9M -maxrate 12M -bufsize 18M -r $F -movflags +faststart -c:a aac -b:a 192k "$OUT"
