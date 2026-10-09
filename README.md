# Musgravite Mosaic

Full-colour Python 3 neon 2x2 shard-rotator arcade for ElbowOS.

Slide a gold frame over a vertical mosaic. Space twists that 2x2 block. Three or more teal, coral, gold, violet, or ice shards clear, fall, and score. Not a swap-match clone and not a Nintendo ROM.

## Play

```
pip install -r requirements.txt
python3 musgravite_mosaic.py --play
```

Arrows or WASD move the frame. Space / Enter twists. R restarts.

## Record a 9:16 reel

```
python3 musgravite_mosaic.py --record
```

Writes a 1080x1920 h264 clip (15s @ 30fps, CRF 20, yuv420p, +faststart) with title, score, and `x.com/ElbowOS` burned into the frames. Override the path with `ELBOWOS_MP4`.

- Featured account: https://x.com/ElbowOS
- Drive reel: https://drive.google.com/file/d/13oUzyL3O_-yYelpqr1PysMAHcMUXr5Ze/view
