#!/usr/bin/env python3
"""Musgravite Mosaic — neon 2x2 shard rotator for ElbowOS. Python 3 + pygame."""
import os, sys, math, random, subprocess

PLAY = "--play" in sys.argv
if not PLAY:
    os.environ["SDL_VIDEODRIVER"] = "dummy"
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
import pygame

W, H, FPS, SECS = 1080, 1920, 30, 15
OUT = os.environ.get("ELBOWOS_MP4", "/workspace/artifacts/MUSGRAVITE_MOSAIC_ElbowOS.mp4")
TITLE, HANDLE = "MUSGRAVITE MOSAIC", "x.com/ElbowOS"
COLS, ROWS, CELL = 6, 8, 148
OX, OY = (W - COLS * CELL) // 2, 390
NAVY, TEAL, MINT = (7, 16, 32), (40, 210, 190), (186, 255, 214)
CORAL, GOLD, VIOLET, ICE = (255, 94, 122), (255, 196, 72), (176, 92, 255), (110, 220, 255)
GEMS = (TEAL, CORAL, GOLD, VIOLET, ICE)
NAMES = ("TEAL", "CORAL", "GOLD", "VIOLET", "ICE")

def clamp(v, a, b):
    return a if v < a else b if v > b else v

class Game:
    def __init__(self):
        pygame.init()
        pygame.font.init()
        flags = 0 if PLAY else pygame.HIDDEN
        try:
            self.screen = pygame.display.set_mode((W, H), flags)
        except pygame.error:
            os.environ["SDL_VIDEODRIVER"] = "dummy"
            pygame.display.init()
            self.screen = pygame.display.set_mode((W, H), pygame.HIDDEN)
        pygame.display.set_caption(TITLE)
        self.font = pygame.font.SysFont("dejavusans", 64, bold=True)
        self.mid = pygame.font.SysFont("dejavusans", 42, bold=True)
        self.small = pygame.font.SysFont("dejavusans", 32, bold=True)
        self.rng = random.Random(11)
        self.reset()

    def reset(self):
        self.grid = [[self.rng.randrange(5) for _ in range(COLS)] for _ in range(ROWS)]
        self.dy = [[0.0] * COLS for _ in range(ROWS)]
        self.cr, self.cc = 3, 2
        self.score = 0
        self.clears = 0
        self.parts = []
        self.spin = None
        self.cool = 0
        self.t = 0
        self.banner = "ROTATE 2x2"
        for _ in range(4):
            self._strip()

    def _rot(self, g, r, c):
        a, b = g[r][c], g[r][c + 1]
        d, e = g[r + 1][c], g[r + 1][c + 1]
        g[r][c], g[r][c + 1] = d, a
        g[r + 1][c], g[r + 1][c + 1] = e, b

    def _matches(self, g):
        hit = [[False] * COLS for _ in range(ROWS)]
        for r in range(ROWS):
            c = 0
            while c < COLS:
                k, v = c, g[r][c]
                if v < 0:
                    c += 1
                    continue
                while k < COLS and g[r][k] == v:
                    k += 1
                if k - c >= 3:
                    for i in range(c, k):
                        hit[r][i] = True
                c = k
        for c in range(COLS):
            r = 0
            while r < ROWS:
                k, v = r, g[r][c]
                if v < 0:
                    r += 1
                    continue
                while k < ROWS and g[k][c] == v:
                    k += 1
                if k - r >= 3:
                    for i in range(r, k):
                        hit[i][c] = True
                r = k
        return hit

    def _strip(self):
        hit = self._matches(self.grid)
        n = sum(sum(row) for row in hit)
        if not n:
            return False
        for r in range(ROWS):
            for c in range(COLS):
                if hit[r][c]:
                    self.grid[r][c] = -1
                    self._burst(OX + c * CELL + CELL // 2, OY + r * CELL + CELL // 2, GEMS[0])
        self.score += 40 * n + 20 * (n - 2)
        self.clears += n
        self.banner = f"+{n} SHARDS"
        self._fall()
        return True

    def _fall(self):
        for c in range(COLS):
            stack = [self.grid[r][c] for r in range(ROWS) if self.grid[r][c] >= 0]
            missing = ROWS - len(stack)
            fresh = [self.rng.randrange(5) for _ in range(missing)]
            col = fresh + stack
            for r in range(ROWS):
                if self.grid[r][c] != col[r]:
                    self.dy[r][c] = -CELL * (1 + (missing - r if r < missing else 0) * 0.35)
                self.grid[r][c] = col[r]

    def _burst(self, x, y, col):
        for i in range(10):
            ang = self.rng.random() * math.tau
            sp = 2 + self.rng.random() * 7
            self.parts.append([x, y, math.cos(ang) * sp, math.sin(ang) * sp - 2, col, 18])

    def spin_at(self, r, c):
        r = clamp(r, 0, ROWS - 2)
        c = clamp(c, 0, COLS - 2)
        self.cr, self.cc = r, c
        if self.spin:
            return
        self.spin = [r, c, 0]
        self.banner = "TWIST"

    def _commit(self):
        r, c, _ = self.spin
        self._rot(self.grid, r, c)
        self.spin = None
        self.cool = 6
        guard = 0
        while self._strip() and guard < 6:
            guard += 1

    def _gain(self, r, c):
        g = [row[:] for row in self.grid]
        best = 0
        for _ in range(3):
            self._rot(g, r, c)
            n = sum(sum(row) for row in self._matches(g))
            best = max(best, n)
        return best

    def auto(self):
        if self.spin or self.cool:
            return
        if self.t % 11:
            return
        best, pick = 0, None
        for r in range(ROWS - 1):
            for c in range(COLS - 1):
                n = self._gain(r, c)
                if n > best:
                    best, pick = n, (r, c)
        if pick is None:
            pick = (self.rng.randrange(ROWS - 1), self.rng.randrange(COLS - 1))
        self.spin_at(*pick)

    def step(self, autoplay=False):
        self.t += 1
        if self.cool:
            self.cool -= 1
        if autoplay:
            self.auto()
        if self.spin:
            self.spin[2] += 1
            if self.spin[2] >= 8:
                self._commit()
        for row in self.dy:
            for i, v in enumerate(row):
                if v < 0:
                    row[i] = min(0.0, v + 18)
        alive = []
        for p in self.parts:
            p[0] += p[2]
            p[1] += p[3]
            p[3] += 0.25
            p[5] -= 1
            if p[5] > 0:
                alive.append(p)
        self.parts = alive

    def draw(self, surf):
        surf.fill(NAVY)
        for i in range(8):
            y = (self.t * 6 + i * 240) % (H + 80) - 40
            pygame.draw.line(surf, (16, 40, 58), (80, y), (W - 80, y), 2)
        pulse = 0.5 + 0.5 * math.sin(self.t * 0.18)
        title = self.font.render(TITLE, True, MINT)
        surf.blit(title, title.get_rect(center=(W // 2, 120)))
        sub = self.small.render("2x2 SHARD TWIST", True, TEAL)
        surf.blit(sub, sub.get_rect(center=(W // 2, 190)))
        sc = self.mid.render(f"SCORE  {self.score}", True, GOLD)
        surf.blit(sc, sc.get_rect(center=(W // 2, 270)))
        pygame.draw.rect(surf, (12, 36, 48), (OX - 18, OY - 18, COLS * CELL + 36, ROWS * CELL + 36), border_radius=28)
        pygame.draw.rect(surf, TEAL, (OX - 18, OY - 18, COLS * CELL + 36, ROWS * CELL + 36), 4, border_radius=28)
        ang = 0
        if self.spin:
            ang = self.spin[2] / 8 * math.pi / 2
        for r in range(ROWS):
            for c in range(COLS):
                v = self.grid[r][c]
                if v < 0:
                    continue
                cx = OX + c * CELL + CELL // 2
                cy = OY + r * CELL + CELL // 2 + self.dy[r][c]
                twist = 0
                if self.spin and self.spin[0] <= r <= self.spin[0] + 1 and self.spin[1] <= c <= self.spin[1] + 1:
                    ox = OX + self.spin[1] * CELL + CELL
                    oy = OY + self.spin[0] * CELL + CELL
                    dx, dy = cx - ox, (OY + r * CELL + CELL // 2) - oy
                    ca, sa = math.cos(ang), math.sin(ang)
                    cx = ox + dx * ca - dy * sa
                    cy = oy + dx * sa + dy * ca
                    twist = ang
                col = GEMS[v]
                glow = (min(255, col[0] + 40), min(255, col[1] + 40), min(255, col[2] + 40))
                self._gem(surf, cx, cy, 52, col, glow, twist)
        rr, cc = self.cr, self.cc
        box = pygame.Rect(OX + cc * CELL - 6, OY + rr * CELL - 6, CELL * 2 + 12, CELL * 2 + 12)
        pygame.draw.rect(surf, GOLD if self.spin else MINT, box, 5, border_radius=16)
        for p in self.parts:
            pygame.draw.circle(surf, p[4], (int(p[0]), int(p[1])), max(2, p[5] // 4))
        ban = self.mid.render(self.banner, True, CORAL if self.clears else MINT)
        surf.blit(ban, ban.get_rect(center=(W // 2, H - 250)))
        hint = self.small.render("ARROWS MOVE   SPACE TWIST", True, (170, 220, 210))
        surf.blit(hint, hint.get_rect(center=(W // 2, H - 180)))
        handle = self.mid.render(HANDLE, True, (255, 255, 255))
        chip = handle.get_rect(center=(W // 2, H - 100))
        pygame.draw.rect(surf, (8, 28, 36), chip.inflate(36, 18), border_radius=16)
        surf.blit(handle, chip)
        pygame.draw.circle(surf, MINT, (70, 70), int(10 + 6 * pulse))

    def _gem(self, surf, x, y, rad, col, glow, twist):
        pygame.draw.circle(surf, (col[0] // 5, col[1] // 5, col[2] // 5), (int(x), int(y) + 6), rad)
        pts = []
        for i in range(6):
            a = twist + math.pi / 6 + i * math.tau / 6
            pts.append((x + math.cos(a) * rad, y + math.sin(a) * rad * 0.92))
        pygame.draw.polygon(surf, col, pts)
        inner = []
        for i in range(6):
            a = twist + i * math.tau / 6
            inner.append((x + math.cos(a) * rad * 0.45, y + math.sin(a) * rad * 0.4))
        pygame.draw.polygon(surf, glow, inner)

    def play_interactive(self):
        clock = pygame.time.Clock()
        running = True
        while running:
            for ev in pygame.event.get():
                if ev.type == pygame.QUIT:
                    running = False
                elif ev.type == pygame.KEYDOWN:
                    if ev.key in (pygame.K_ESCAPE, pygame.K_q):
                        running = False
                    elif ev.key in (pygame.K_LEFT, pygame.K_a):
                        self.cc = clamp(self.cc - 1, 0, COLS - 2)
                    elif ev.key in (pygame.K_RIGHT, pygame.K_d):
                        self.cc = clamp(self.cc + 1, 0, COLS - 2)
                    elif ev.key in (pygame.K_UP, pygame.K_w):
                        self.cr = clamp(self.cr - 1, 0, ROWS - 2)
                    elif ev.key in (pygame.K_DOWN, pygame.K_s):
                        self.cr = clamp(self.cr + 1, 0, ROWS - 2)
                    elif ev.key in (pygame.K_SPACE, pygame.K_RETURN):
                        self.spin_at(self.cr, self.cc)
                    elif ev.key == pygame.K_r:
                        self.reset()
            self.step(False)
            self.draw(self.screen)
            pygame.display.flip()
            clock.tick(FPS)
        pygame.quit()

    def record(self):
        os.makedirs(os.path.dirname(OUT), exist_ok=True)
        cmd = ["ffmpeg", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}",
               "-r", str(FPS), "-i", "-", "-an", "-c:v", "libx264", "-pix_fmt", "yuv420p",
               "-crf", "20", "-movflags", "+faststart", OUT]
        proc = subprocess.Popen(cmd, stdin=subprocess.PIPE, stderr=subprocess.PIPE)
        frames = FPS * SECS
        try:
            for i in range(frames):
                self.step(True)
                self.draw(self.screen)
                proc.stdin.write(pygame.image.tobytes(self.screen, "RGB"))
                if i % 30 == 0:
                    print(f"frame {i}/{frames} score {self.score}", flush=True)
        finally:
            proc.stdin.close()
        err = proc.stderr.read().decode("utf-8", "ignore")
        rc = proc.wait()
        if rc != 0:
            raise SystemExit(f"ffmpeg failed ({rc}):\n{err[-1200:]}")
        print("wrote", OUT, "score", self.score, "clears", self.clears)
        pygame.quit()

def main():
    g = Game()
    if PLAY:
        g.play_interactive()
    else:
        g.record()

if __name__ == "__main__":
    main()
