#!/usr/bin/env python3
"""
BRICKCHAIN: A Peer-to-Peer Parity Consensus System

Abstract. A purely peer-to-peer version of parity would allow a number to
learn whether it is even without trusting a centralized modulo operator.
Seven mutually distrustful validators each derive parity from a different
branch of mathematics, reach Byzantine fault tolerant consensus weighted by
stake, and seal the verdict into a proof-of-work block. Each block is a brick.

usage: python3 brickchain.py [n ...]
"""
import cmath, hashlib, math, random, re, sys, time
from collections import Counter
from dataclasses import dataclass
from functools import reduce, wraps
from typing import Callable
GAS_LIMIT  = 100_000   # O(n) validators refuse anything heavier
DIFFICULTY = 4         # leading hex zeros per brick
STAKE      = 32        # eth-pilled
MAX_EPOCHS = 64        # patience of the social layer

# ── Validator registry ──────────────────────────────────────────────────────
class OutOfGas(Exception): pass
@dataclass
class Validator:
    name: str
    fn: Callable
    note: str
    stake: float = STAKE
VALIDATORS: list[Validator] = []
def validator(note, gas=lambda n: 0, stake=STAKE):
    def register(fn):
        @wraps(fn)
        def metered(n):
            if gas(n) > GAS_LIMIT:
                raise OutOfGas
            return fn(n)
        VALIDATORS.append(Validator(fn.__name__, metered, note, stake))
        return fn
    return register

# ── 1. Complex analysis ─────────────────────────────────────────────────────
@validator("e^(iπn) = (-1)^n")
def euler(n):
    # spin n half-turns around the unit circle, see which side you land on.
    # floats get drunk somewhere past 10^16. consensus will deal with it, eventually.
    return "EVEN" if cmath.exp(1j * math.pi * n).real > 0 else "ODD"

# ── 2. Quantum mechanics ────────────────────────────────────────────────────
H = [[1, 1], [1, -1]]    # Hadamard (unnormalized, we pay the √2 later)
Z = [[1, 0], [0, -1]]    # Pauli-Z, a phase flip
def matmul(A, B):
    return [[sum(A[i][k] * B[k][j] for k in range(2)) for j in range(2)] for i in range(2)]
def matpow(M, k):
    R = [[1, 0], [0, 1]]
    while k:
        if k & 1:        # the first iteration already knows the answer. insider trading.
            R = matmul(R, M)
        M, k = matmul(M, M), k >> 1
    return R
@validator("H·Zⁿ·H|0⟩ interference")
def quantum(n):
    # superpose a qubit, phase-kick it n times, interfere it back.
    # amplitude of |1⟩ is (1 - (-1)^n) / 2. the wavefunction collapses into the truth.
    amp = matmul(matmul(H, matpow(Z, n)), H)[1][0] // 2
    return "ODD" if amp * amp == 1 else "EVEN"

# ── 3. Lambda calculus ──────────────────────────────────────────────────────
TRUE    = lambda a: lambda b: a
FALSE   = lambda a: lambda b: b
NOT     = lambda p: p(FALSE)(TRUE)
CHURCH  = lambda n: lambda f: lambda x: reduce(lambda acc, _: f(acc), range(n), x)
IS_EVEN = lambda c: c(NOT)(TRUE)
@validator("λn. n NOT TRUE", gas=lambda n: n)
def church(n):
    # a number is just "apply f n times". so apply NOT n times, starting from TRUE.
    # the boolean then picks its own label. no ints were harmed.
    return IS_EVEN(CHURCH(n))("EVEN")("ODD")

# ── 4. Esoteric computing ───────────────────────────────────────────────────
PARITY_BF = ">+<[->[->+<]+>[-<->]<<]>."   # flip a flag n times, print it
def bf(code, cell0):
    tape, ptr, pc, out, stack, jump = [cell0, 0, 0], 0, 0, [], [], {}
    for i, c in enumerate(code):
        if c == "[": stack.append(i)
        elif c == "]": j = stack.pop(); jump[i], jump[j] = j, i
    while pc < len(code):
        c = code[pc]
        if   c == ">": ptr += 1
        elif c == "<": ptr -= 1
        elif c == "+": tape[ptr] += 1
        elif c == "-": tape[ptr] -= 1
        elif c == ".": out.append(tape[ptr])
        elif c == "[" and not tape[ptr]: pc = jump[pc]
        elif c == "]" and tape[ptr]: pc = jump[pc]
        pc += 1
    return out
@validator("flip-flop VM", gas=lambda n: n)
def brainfuck(n):
    return "EVEN" if bf(PARITY_BF, n) == [1] else "ODD"

# ── 5. Genomics ─────────────────────────────────────────────────────────────
def genome(n):
    seq = ""
    while True:
        n, r = divmod(n, 4)
        seq = "ACGT"[r] + seq        # A=00 C=01 G=10 T=11
        if not n:
            return seq
@validator("ends in a purine?")
def dna(n):
    # purines (A, G) are exactly the even bases. pyrimidines (C, T) the odd ones.
    # a number is even iff its genome ends in a purine. biology was parity all along.
    return "EVEN" if genome(n)[-1] in "AG" else "ODD"

# ── 6. Formal languages ─────────────────────────────────────────────────────
@validator("unary ∈ (11)*", gas=lambda n: n)
def regex(n):
    # write n in unary, ask a finite automaton whether every 1 found a partner.
    return "EVEN" if re.fullmatch(r"(?:11)*", "1" * n) else "ODD"

# ── 7. Market participant ───────────────────────────────────────────────────
@validator("vibes")
def rugpull(n):
    # votes on vibes, seeded by the chain tip. verifiable randomness. most followers.
    return random.Random(f"{CHAIN[-1].hash}:{n}").choice(["EVEN", "ODD"])

# ── 8. Not a validator ──────────────────────────────────────────────────────
MEMPOOL = {}             # votes are public before they are final. this is a feature.
@validator("reads the mempool", stake=0)
def searcher(n):
    # not a branch of mathematics. a branch of finance. joined with zero stake,
    # does zero math, backs whoever is already winning. collects every slash.
    # never wrong, never right, just early. the README still says seven.
    tally = Counter()
    for v in VALIDATORS:
        if MEMPOOL.get(v.name): tally[MEMPOOL[v.name]] += v.stake
    return tally.most_common(1)[0][0] if tally else None   # no liquidity, no trade

# ── The chain ───────────────────────────────────────────────────────────────
sha = lambda s: hashlib.sha256(s.encode()).hexdigest()
def merkle(leaves):
    layer = [sha(l) for l in leaves] or [sha("")]
    while len(layer) > 1:
        if len(layer) & 1:            # merkle trees need parity. the oracle is bootstrapped
            layer.append(layer[-1])   # on itself. like every algorithmic stablecoin.
        layer = [sha(a + b) for a, b in zip(layer[::2], layer[1::2])]
    return layer[0]
@dataclass
class Block:
    height: int
    payload: str
    prev: str
    root: str = ""
    nonce: int = 0
    hash: str = ""
    def mine(self):
        while not self.hash.startswith("0" * DIFFICULTY):
            self.nonce += 1
            self.hash = sha(f"{self.height}|{self.payload}|{self.prev}|{self.root}|{self.nonce}")
        return self
CHAIN = [Block(0, "brick by fucking brick", "0" * 64).mine()]
def ask(n):
    n, t0 = abs(n), time.perf_counter()     # long only. no shorts.
    print(f"\n━━ is {n} even? " + "━" * max(4, 36 - len(str(n))))
    votes = MEMPOOL
    votes.clear()
    for v in VALIDATORS:
        try: votes[v.name] = v.fn(n)
        except OutOfGas: votes[v.name] = None
    def tally_up():
        total, tally = sum(v.stake for v in VALIDATORS), Counter()
        for v in VALIDATORS:
            if votes[v.name]: tally[votes[v.name]] += v.stake
        verdict, weight = tally.most_common(1)[0] if tally else (None, 0)
        return (verdict if weight * 3 > total * 2 else None), weight, total   # BFT, > 2/3 stake
    final, weight, total = tally_up()
    # offline validators bleed stake every epoch until the living can finalize without them.
    offline, epochs = [v for v in VALIDATORS if votes[v.name] is None], 0
    before = sum(v.stake for v in offline)
    while final is None and offline and epochs < MAX_EPOCHS:
        for v in offline:
            v.stake /= 2
        epochs += 1
        final, weight, total = tally_up()
    for v in VALIDATORS:
        vote = votes[v.name]
        if vote is None:
            print(f"  {v.name:<10} ⛽ ---   out of gas")
            continue
        icon = "·" if final is None else "✓" if vote == final else "✗"
        line = f"  {v.name:<10} {icon} {vote:<5} {v.note}"
        if icon == "✗":
            old, v.stake = v.stake, v.stake / 2
            VALIDATORS[-1].stake += old - v.stake    # the slash has to go somewhere
            line += f"   ⚔ slashed {old:g}→{v.stake:g}, searcher +{old - v.stake:g}"
        print(line)
    if epochs:
        print(f"  ⏳ inactivity leak: {epochs} epoch{'s' * (epochs > 1)}, offline stake {before:g}→{sum(v.stake for v in offline):.3g}")
    if final is None:
        print(f"  ❌ no supermajority ({weight:g}/{total:g} stake). CHAIN HALTED.")
        print("     validators are coordinating a restart on Discord.")
        return None
    blk = Block(len(CHAIN), f"{n}:{final}", CHAIN[-1].hash, merkle(f"{k}:{v}" for k, v in votes.items()))
    CHAIN.append(blk.mine())
    print(f"  consensus: {final}  ({weight:g}/{total:g} stake)  finality {time.perf_counter() - t0:.2f}s")
    print(f"  🧱 brick #{blk.height} laid  nonce={blk.nonce}  {blk.hash[:20]}…")
    return final
def rich_list():
    print("\n💰 stake, end of day:")
    for v in sorted(VALIDATORS, key=lambda v: -v.stake):
        print(f"  {v.name:<10} {v.stake:>7.3g}  {'█' * round(v.stake / 4)}")
def wall():
    print("\n🧱 the wall so far:")
    bricks, offset = [f"[{b.hash[:8]}]" for b in CHAIN], False
    for i in range(0, len(bricks), 3):
        print("     " * offset + "".join(bricks[i:i + 3]))
        offset = not offset

if __name__ == "__main__":
    print("⛓  BRICKCHAIN v1.0 :: decentralized parity oracle")
    print(f'🧱 genesis: "{CHAIN[0].payload}"  {CHAIN[0].hash[:20]}…')
    for a in sys.argv[1:] or [42, 1337, 2026, 69420, 10**18]:
        try:
            n = int(a)
        except ValueError:
            print(f"\n  ⛔ tx reverted: {a!r} is not an integer. gas spent anyway.")
            continue
        ask(n)
    wall()
    rich_list()

# ── Appendix A: legacy centralized implementation ───────────────────────────
# deprecated. trusts a single operator. kept for regulatory reasons.
#
# is_even = lambda n: n % 2 == 0