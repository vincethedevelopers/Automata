"""
Soal 2 - Fighting game FSM - Combo detector
Kelompok: Group-4

Terminal:
python3 fighting_fsm.py
"""

import time
from typing import List, Optional, Tuple
from enum import Enum
from dataclasses import dataclass

# -------------------------
# DEFINISI INPUTKEY
# - Enum yang merepresentasikan tombol-tombol yang dipakai.
# - Digunakan untuk menyamakan nama tombol di seluruh kode.
# -------------------------
class InputKey(Enum):
    UP = "↑"
    DOWN = "↓"
    LEFT = "←"
    RIGHT = "→"
    SPACE = "Space"

# -------------------------
# DEFINISI COMBO
# - ComboDefinition: nama combo, urutan InputKey, dan optional special_name.
# - Semua combo didefinisikan pada bagian FSM utama.
# -------------------------
@dataclass
class ComboDefinition:
    name: str
    sequence: List[InputKey]
    special_name: Optional[str] = None

# -------------------------
# STATE TRACKER UNTUK TIAP COMBO
# - ComboState menyimpan progres saat ini, waktu input terakhir, dan mekanik hold SPACE.
# - awaiting_space: flag ketika urutan non-space selesai dan menunggu SPACE untuk upgrade.
# -------------------------
class ComboState:
    def __init__(self, combo_def: ComboDefinition):
        self.combo_def = combo_def
        self.current_position: int = 0
        self.last_input_time: float = 0.0
        # Untuk simulasi hold SPACE
        self.space_press_start: float = 0.0
        self.space_is_held: bool = False
        # Setelah sequence non-space selesai, bisa menunggu SPACE untuk special
        self.awaiting_space: bool = False
        self.awaiting_since: float = 0.0

    # -------------------------
    # RESET STATE
    # - Mengembalikan semua flag ke kondisi awal.
    # -------------------------
    def reset(self) -> None:
        self.current_position = 0
        self.last_input_time = 0.0
        self.space_press_start = 0.0
        self.space_is_held = False
        self.awaiting_space = False
        self.awaiting_since = 0.0

    # -------------------------
    # TIMEOUT CHECK
    # - Jika lebih lama dari timeout (default 1s) sejak input terakhir, state dianggap kadaluarsa.
    # -------------------------
    def is_timeout(self, now: float, timeout: float = 1.0) -> bool:
        if self.last_input_time == 0.0:
            return False
        return (now - self.last_input_time) > timeout

    # -------------------------
    # PROCESS INPUT
    # - Menerima satu InputKey dan memperbarui state.
    # - Mengembalikan tuple: (is_complete, is_valid_progress, combo_name_if_complete)
    # - Catatan: SPECIAL tidak langsung di-return; SPACE akan disimulasikan sebagai hold.
    # -------------------------
    def process_input(self, key: InputKey, now: float) -> Tuple[bool, bool, Optional[str]]:
        # timeout -> reset state
        if self.is_timeout(now):
            self.reset()

        # safety bounds
        if self.current_position >= len(self.combo_def.sequence):
            self.current_position = 0

        # Jika sedang menunggu SPACE dan user menekan SPACE -> mulai hold
        if self.awaiting_space and key == InputKey.SPACE and self.combo_def.special_name:
            self.space_press_start = now
            self.space_is_held = True
            # jangan keluarkan special langsung; cek durasi di check_space_hold()
            self.last_input_time = now
            return False, True, None

        # Expected key pada posisi saat ini
        expected = None
        if self.current_position < len(self.combo_def.sequence):
            expected = self.combo_def.sequence[self.current_position]

        if expected is not None and key == expected:
            # Kecocokan: maju posisi
            self.current_position += 1
            self.last_input_time = now

            # Jika sequence berakhir dengan SPACE dan kita baru saja menyelesaikan bagian non-space:
            if (len(self.combo_def.sequence) >= 1
                and self.combo_def.sequence[-1] == InputKey.SPACE
                and self.current_position == len(self.combo_def.sequence) - 1):
                # Combo normal selesai — tunggu SPACE untuk upgrade menjadi special
                self.awaiting_space = True
                self.awaiting_since = now
                # jangan reset current_position agar mismatch handling dapat bekerja
                return True, True, self.combo_def.name

            # Jika sequence tidak berakhiran SPACE dan sudah selesai:
            if self.current_position >= len(self.combo_def.sequence):
                combo_name = self.combo_def.name
                self.current_position = 0
                return True, True, combo_name

            return False, True, None

        # Mismatch handling:
        if self.awaiting_space:
            # Batalkan awaiting jika input tidak sesuai
            self.awaiting_space = False
            self.awaiting_since = 0.0
            self.current_position = 0
            return False, False, None

        # Jika ada progress tapi input salah -> reset progress
        if self.current_position > 0:
            self.current_position = 0

        return False, False, None

    # -------------------------
    # CHECK SPACE HOLD
    # - Memeriksa apakah SPACE ditahan dalam rentang waktu untuk memicu special.
    # - Default rentang: 1.9 - 3.1 detik.
    # - Jika special terpenuhi, reset state penuh.
    # -------------------------
    def check_space_hold(self, now: float, lower: float = 1.9, upper: float = 3.1) -> Optional[str]:
        if self.space_is_held and self.combo_def.special_name:
            dur = now - self.space_press_start
            if lower <= dur <= upper:
                special_name = self.combo_def.special_name
                self.reset()
                return special_name
            if dur > upper:
                # terlalu lama, batalkan hold
                self.space_is_held = False
                self.space_press_start = 0.0
                self.awaiting_space = False
                return None
        # Jika waiting SPACE timeout, batalkan awaiting_space
        if self.awaiting_space and self.last_input_time and (now - self.last_input_time) > 1.0:
            self.awaiting_space = False
            self.awaiting_since = 0.0
            self.current_position = 0
        return None

# -------------------------
# FSM UTAMA
# - Menyimpan daftar combo, state tracker untuk tiap combo, dan mapping key.
# - Menyediakan fungsi process_key untuk menerima input dan check_specials untuk hold detection.
# -------------------------
class FightingGameFSM:
    def __init__(self):
        self.combos: List[ComboDefinition] = [
            ComboDefinition("Hadoken", [InputKey.RIGHT, InputKey.RIGHT, InputKey.RIGHT, InputKey.SPACE], "SUPER HADOKEN"),
            ComboDefinition("Shoryuken", [InputKey.UP, InputKey.DOWN, InputKey.UP, InputKey.RIGHT, InputKey.SPACE], "SUPER SHORYUKEN"),
            ComboDefinition("Tatsumaki", [InputKey.LEFT, InputKey.RIGHT, InputKey.LEFT, InputKey.RIGHT, InputKey.SPACE], "SUPER TATSUMAKI"),
            ComboDefinition("Dragon Punch", [InputKey.UP, InputKey.UP, InputKey.DOWN, InputKey.RIGHT, InputKey.SPACE], "SUPER DRAGON PUNCH"),
            ComboDefinition("Hurricane Kick", [InputKey.RIGHT, InputKey.DOWN, InputKey.RIGHT, InputKey.RIGHT, InputKey.SPACE], "SUPER HURRICANE KICK"),
            ComboDefinition("Giga Hadoken", [InputKey.RIGHT, InputKey.RIGHT, InputKey.RIGHT, InputKey.DOWN, InputKey.UP, InputKey.RIGHT, InputKey.SPACE], "ULTRA GIGA HADOKEN"),
            ComboDefinition("Ultra Shoryuken", [InputKey.RIGHT, InputKey.RIGHT, InputKey.DOWN, InputKey.RIGHT, InputKey.UP, InputKey.DOWN, InputKey.RIGHT, InputKey.SPACE], "MEGA ULTRA SHORYUKEN"),
            ComboDefinition("Mega Tatsumaki", [InputKey.UP, InputKey.UP, InputKey.DOWN, InputKey.RIGHT, InputKey.RIGHT, InputKey.RIGHT, InputKey.RIGHT, InputKey.SPACE], "HYPER MEGA TATSUMAKI"),
            ComboDefinition("Final Dragon Punch", [InputKey.LEFT, InputKey.UP, InputKey.RIGHT, InputKey.RIGHT, InputKey.DOWN, InputKey.UP, InputKey.RIGHT, InputKey.SPACE], "ULTIMATE DRAGON PUNCH"),
            ComboDefinition("Ultimate Hurricane Kick", [InputKey.RIGHT, InputKey.RIGHT, InputKey.UP, InputKey.DOWN, InputKey.RIGHT, InputKey.UP, InputKey.RIGHT, InputKey.RIGHT, InputKey.SPACE], "GODLIKE HURRICANE KICK"),
        ]
        self.states: List[ComboState] = [ComboState(c) for c in self.combos]
        self.buffer: List[Tuple[InputKey, float]] = []
        self.max_buffer = 50

        # Mapping dari input karakter ke InputKey
        self.key_map = {
            'w': InputKey.UP, 's': InputKey.DOWN, 'a': InputKey.LEFT, 'd': InputKey.RIGHT,
            ' ': InputKey.SPACE, 'space': InputKey.SPACE, 'up': InputKey.UP, 'down': InputKey.DOWN,
            'left': InputKey.LEFT, 'right': InputKey.RIGHT
        }

    # -------------------------
    # RESET SEMUA STATE
    # -------------------------
    def reset_all(self) -> None:
        for st in self.states:
            st.reset()

    # -------------------------
    # PROCESS_KEY
    # - Menerima sebuah token (mis. 'd' atau 'space'), memproses untuk semua combo secara paralel.
    # - Mengembalikan nama combo normal bila terdeteksi.
    # -------------------------
    def process_key(self, ch: str) -> Optional[str]:
        now = time.time()
        key = self.key_map.get(ch.lower())
        if not key:
            return None

        # buffer untuk debugging
        self.buffer.append((key, now))
        if len(self.buffer) > self.max_buffer:
            self.buffer.pop(0)

        detected: Optional[str] = None
        valid_any = False

        # Proses semua state paralel
        for st in self.states:
            complete, valid, name = st.process_input(key, now)
            if complete and name:
                detected = name
            if valid:
                valid_any = True

        # Jika input tidak valid untuk state yang sedang on-progress, reset mereka (kecuali awaiting_space)
        if not valid_any:
            for st in self.states:
                if st.current_position > 0 and not st.awaiting_space:
                    st.reset()

        return detected

    # -------------------------
    # CHECK SPECIALS
    # - Iterasi semua state untuk memeriksa apakah ada special yang terpenuhi (hold SPACE).
    # -------------------------
    def check_specials(self) -> Optional[str]:
        now = time.time()
        for st in self.states:
            special = st.check_space_hold(now)
            if special:
                return special
        return None

    # -------------------------
    # RESET SPECIFIC COMBO
    # - Jika combo menunggu SPACE, jangan reset full agar special masih dapat diproses.
    # -------------------------
    def reset_combo(self, name: str) -> None:
        for st in self.states:
            if st.combo_def.name == name:
                if st.awaiting_space:
                    st.current_position = 0
                    st.last_input_time = st.awaiting_since
                else:
                    st.reset()
                return

    # -------------------------
    # CHECK IF A COMBO IS AWAITING SPACE
    # -------------------------
    def is_awaiting_space(self, name: str) -> bool:
        for st in self.states:
            if st.combo_def.name == name:
                return st.awaiting_space
        return False

    # -------------------------
    # PROGRESS LIST (UNTUK DEBUG)
    # - Menampilkan progres tiap combo yang sedang berjalan.
    # -------------------------
    def progress_list(self) -> List[str]:
        out: List[str] = []
        for st in self.states:
            if st.current_position > 0 or st.awaiting_space:
                pos = st.current_position
                if st.awaiting_space:
                    pos = len(st.combo_def.sequence) - 1
                out.append(f"{st.combo_def.name}: {pos}/{len(st.combo_def.sequence)}")
        return out

    # -------------------------
    # TAMPILKAN DAFTAR COMBO
    # -------------------------
    def show_combos(self) -> None:
        print("\n" + "=" * 60)
        print("DAFTAR COMBO")
        print("=" * 60)
        for i, c in enumerate(self.combos, 1):
            seq = ' '.join([k.value for k in c.sequence])
            special = f" -> {c.special_name}" if c.special_name else ""
            print(f"{i:2d}. {c.name:25s} {seq}{special}")
        print("=" * 60)
        print("Catatan:")
        print(" - Jeda antar input maksimal 1 detik.")
        print(" - Untuk simulasi hold SPACE gunakan syntax: space:<detik> mis. space:2.5")
        print(" - Contoh input interaktif: ddd space:2.5")
        print("=" * 60)

# -------------------------
# SIMULATOR / INTERFACE (TERMINAL)
# - Mode interaktif dan test mode tersedia.
# - Untuk simulasi hold SPACE gunakan syntax space:<detik> di mode interaktif.
# -------------------------
class GameSimulator:
    def __init__(self):
        self.fsm = FightingGameFSM()
        self.count_detected = 0

    def run_interactive(self) -> None:
        self.fsm.show_combos()
        print("\nMode Interactive: ketik urutan tombol satu baris lalu ENTER.")
        print("Contoh: ddd space:2.5   (tekan d d d lalu simulasikan hold space 2.5s)")
        print("Perintah: help, reset, quit\n")

        try:
            while True:
                cmd = input("Input: ").strip()
                if not cmd:
                    continue
                if cmd.lower() == 'quit':
                    print("Total combos detected:", self.count_detected)
                    break
                if cmd.lower() == 'help':
                    self.fsm.show_combos()
                    continue
                if cmd.lower() == 'reset':
                    self.fsm.reset_all()
                    print("Semua state di-reset.")
                    continue

                # Parse input baris:
                tokens: List[str] = []
                if ' ' in cmd and len(cmd) > 1:
                    parts = cmd.split()
                    for p in parts:
                        if p.startswith('space:'):
                            tokens.append(p)
                        elif p.lower() == 'space':
                            tokens.append('space')
                        else:
                            tokens.extend(list(p))
                else:
                    tokens = list(cmd)

                for t in tokens:
                    # Handle simulated hold: "space:2.5"
                    if isinstance(t, str) and t.startswith('space:'):
                        try:
                            dur = float(t.split(':', 1)[1])
                        except Exception:
                            print("Format space invalid. Gunakan space:<detik> mis. space:2.5")
                            continue

                        # register space press (this will set holding flags inside state if awaiting)
                        detected = self.fsm.process_key('space')
                        if detected:
                            # Only print normal combo. If combo is awaiting space, don't reset its state here.
                            print(f"\n🔥 COMBO DETECTED: {detected} 🔥")
                            self.count_detected += 1
                            # if combo is NOT awaiting space, safe to reset
                            if not self.fsm.is_awaiting_space(detected):
                                self.fsm.reset_combo(detected)

                        # simulate hold
                        time.sleep(dur)

                        # check special after hold
                        special = self.fsm.check_specials()
                        if special:
                            print(f"\n⭐ SPECIAL EFFECT: {special} ⭐")

                        continue

                    # Normal single key (char or 'space')
                    keytoken = t
                    if t == 'space':
                        keytoken = 'space'

                    detected = self.fsm.process_key(keytoken)
                    if detected:
                        print(f"\n🔥 COMBO DETECTED: {detected} 🔥")
                        self.count_detected += 1
                        # only reset if combo is not awaiting a SPACE for upgrade
                        if not self.fsm.is_awaiting_space(detected):
                            self.fsm.reset_combo(detected)

                    # small delay to emulate realistic input timing
                    time.sleep(0.02)

                # check specials that might have been triggered without explicit space
                special = self.fsm.check_specials()
                if special:
                    print(f"\n⭐ SPECIAL EFFECT: {special} ⭐")

                prog = self.fsm.progress_list()
                if prog:
                    print("Progress:", ', '.join(prog))

        except KeyboardInterrupt:
            print("\nInterrupted. Total combos:", self.count_detected)

    # -------------------------
    # TEST MODE OTOMATIS
    # -------------------------
    def run_test_mode(self) -> None:
        print("\nAutomated Test Mode\n")
        tests: List[Tuple[str, str]] = [
            ("ddd", "Hadoken"),
            ("wswd", "Shoryuken"),
            ("adad", "Tatsumaki"),
            ("wwds", "Dragon Punch"),
            ("dsdd", "Hurricane Kick"),
        ]
        for seq, expect in tests:
            self.fsm.reset_all()
            print(f"Test input: {seq}  expecting: {expect}")
            detected: Optional[str] = None
            for ch in seq:
                time.sleep(0.02)
                r = self.fsm.process_key(ch)
                if r:
                    detected = r
            print("Result:", detected, "->", "PASS" if detected == expect else "FAIL")
            print("-" * 40)


def main() -> None:
    sim = GameSimulator()
    print("\n📋 MENU:\n1  Interactive\n2. Test Mode\n3. Show Combo List\n4. Exit")
    choice = input("Choose (1-4): ").strip()
    if choice == '1':
        sim.run_interactive()
    elif choice == '2':
        sim.run_test_mode()
    elif choice == '3':
        sim.fsm.show_combos()
    else:
        print("Terima kasih.")

if __name__ == "__main__":
    main()
