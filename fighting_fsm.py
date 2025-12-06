"""
Soal 2 - Finite State Machine: Fighting Game Combo Detector
Kelompok: Group-4

Terminal:
python3 fighting_fsm.py
"""

import time
from typing import List, Optional, Tuple
from enum import Enum
from dataclasses import dataclass

class InputKey(Enum):
    UP = "↑"
    DOWN = "↓"
    LEFT = "←"
    RIGHT = "→"
    SPACE = "Space"

# -------------------------
# Definisi combo
# - name: nama combo
# - sequence: urutan InputKey yang diperlukan
# - special_name: nama special jika SPACE di-hold
# -------------------------
@dataclass
class ComboDefinition:
    name: str
    sequence: List[InputKey]
    special_name: Optional[str] = None

# -------------------------
# State tracker untuk tiap combo
# - current_position: posisi saat ini dalam sequence
# - last_input_time: waktu input terakhir (untuk timeout)
# - space_press_start: waktu ketika SPACE terdaftar (untuk simulasi hold)
# - space_is_held: flag bahwa SPACE sedang "ditekan" (disimulasikan)
# -------------------------
class ComboState:
    def __init__(self, combo_def: ComboDefinition):
        self.combo_def = combo_def
        self.current_position: int = 0
        self.last_input_time: float = 0.0
        self.space_press_start: float = 0.0
        self.space_is_held: bool = False

    def reset(self) -> None:
        self.current_position = 0
        self.last_input_time = 0.0
        self.space_press_start = 0.0
        self.space_is_held = False

    def is_timeout(self, now: float, timeout: float = 1.0) -> bool:
        if self.last_input_time == 0.0:
            return False
        return (now - self.last_input_time) > timeout

    def process_input(self, key: InputKey, now: float) -> Tuple[bool, bool, Optional[str]]:
        """
        Proses satu input
        Return: (is_complete, is_valid_progress, combo_name_if_complete)
        """
        # reset bila timeout
        if self.is_timeout(now):
            self.reset()

        # safety: jika posisi melebihi, kembalikan 0
        if self.current_position >= len(self.combo_def.sequence):
            self.current_position = 0

        expected = self.combo_def.sequence[self.current_position]

        if key == expected:
            # cocok, maju ke posisi berikutnya
            self.current_position += 1
            self.last_input_time = now

            # jika selesai seluruh sequence
            if self.current_position >= len(self.combo_def.sequence):
                combo_name = self.combo_def.name

                # jika tombol terakhir adalah SPACE dan combo punya special
                if expected == InputKey.SPACE and self.combo_def.special_name:
                    self.space_press_start = now
                    self.space_is_held = True

                # reset posisi untuk deteksi berikutnya (state internal tetap simpan hold)
                self.current_position = 0
                return True, True, combo_name

            return False, True, None

        # tidak cocok
        return False, False, None

    def check_space_hold(self, now: float, lower: float = 1.9, upper: float = 3.1) -> Optional[str]:
        """
        Cek apakah SPACE ditahan dalam rentang yang dianggap special.
        (toleransi dibuat sedikit longgar: 1.9 - 3.1 detik)
        """
        if self.space_is_held and self.combo_def.special_name:
            dur = now - self.space_press_start
            if lower <= dur <= upper:
                self.release_space()
                return self.combo_def.special_name
        return None

    def release_space(self) -> None:
        self.space_is_held = False
        self.space_press_start = 0.0

# -------------------------
# FSM utama: daftar combo + state tracker
# -------------------------
class FightingGameFSM:
    def __init__(self):
        # daftar combo. Sesuaikan urutan dan definisi sesuai soal.
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

        # map input keyboard ke InputKey
        self.key_map = {
            'w': InputKey.UP, 's': InputKey.DOWN, 'a': InputKey.LEFT, 'd': InputKey.RIGHT,
            ' ': InputKey.SPACE, 'space': InputKey.SPACE, 'up': InputKey.UP, 'down': InputKey.DOWN,
            'left': InputKey.LEFT, 'right': InputKey.RIGHT
        }

    def reset_all(self) -> None:
        for st in self.states:
            st.reset()

    def process_key(self, ch: str) -> Optional[str]:
        """
        Terima satu karakter/keyword (mis. 'd' atau 'space').
        Mengembalikan nama combo bila terdeteksi.
        """
        now = time.time()
        key = self.key_map.get(ch.lower())
        if not key:
            return None

        # buffer (opsional, untuk debugging)
        self.buffer.append((key, now))
        if len(self.buffer) > self.max_buffer:
            self.buffer.pop(0)

        detected: Optional[str] = None
        valid_any = False

        # proses semua state paralel
        for st in self.states:
            complete, valid, name = st.process_input(key, now)
            if complete:
                detected = name
            if valid:
                valid_any = True

        # jika input ini tidak valid untuk state yang on-progress, reset mereka
        if not valid_any:
            for st in self.states:
                if st.current_position > 0:
                    expected = None
                    if st.current_position < len(st.combo_def.sequence):
                        expected = st.combo_def.sequence[st.current_position]
                    if expected is not None and key != expected:
                        st.reset()

        return detected

    def check_specials(self) -> Optional[str]:
        """Cek semua state apakah ada special yang memenuhi kondisi hold"""
        now = time.time()
        for st in self.states:
            special = st.check_space_hold(now)
            if special:
                return special
        return None

    def reset_combo(self, name: str) -> None:
        for st in self.states:
            if st.combo_def.name == name:
                st.reset()
                return

    def progress_list(self) -> List[str]:
        out: List[str] = []
        for st in self.states:
            if st.current_position > 0:
                out.append(f"{st.combo_def.name}: {st.current_position}/{len(st.combo_def.sequence)}")
        return out

    def show_combos(self) -> None:
        print("\n" + "=" * 60)
        print("DAFTAR COMBO")
        print("=" * 60)
        for i, c in enumerate(self.combos, 1):
            seq = ' '.join([k.value for k in c.sequence])
            print(f"{i:2d}. {c.name:25s} {seq}")
        print("=" * 60)
        print("Catatan:")
        print(" - Jeda antar input maksimal 1 detik.")
        print(" - Untuk simulasi hold SPACE gunakan syntax: space:<detik> mis. space:2.5")
        print(" - Contoh input interaktif: ddd space:2.5")
        print("=" * 60)

# -------------------------
# Simulator / Interface (terminal)
# - support interactive + test mode
# - untuk terminal: hold SPACE harus disimulasikan dengan space:<dur>
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

                # parse input baris:
                # - mendukung "ddd", "d d d", "space", "space:2.5", "wswds space:2.5"
                tokens: List[str] = []
                if ' ' in cmd and len(cmd) > 1:
                    parts = cmd.split()
                    for p in parts:
                        if p.startswith('space:'):
                            tokens.append(p)   # special token
                        elif p.lower() == 'space':
                            tokens.append('space')
                        else:
                            # pecah string "ddd" jadi ['d','d','d']
                            tokens.extend(list(p))
                else:
                    tokens = list(cmd)

                # proses token berurutan
                for t in tokens:
                    # handle simulated hold: "space:2.5"
                    if isinstance(t, str) and t.startswith('space:'):
                        try:
                            dur = float(t.split(':', 1)[1])
                        except Exception:
                            print("Format space invalid. Gunakan space:<detik> mis. space:2.5")
                            continue

                        # register space press
                        detected = self.fsm.process_key('space')
                        if detected:
                            print(f"\n🔥 COMBO DETECTED: {detected} 🔥")
                            self.count_detected += 1
                            # jangan reset sekarang; tunggu cek hold

                        # simulasikan hold
                        time.sleep(dur)

                        # cek special sebelum reset
                        special = self.fsm.check_specials()
                        if special:
                            print(f"\n⭐ SPECIAL EFFECT: {special} ⭐")

                        # setelah cek special, reset combo yang terdeteksi (bersihkan progress)
                        if detected:
                            self.fsm.reset_combo(detected)
                        continue

                    # normal token: single char atau 'space'
                    keytoken = t
                    if t == 'space':
                        keytoken = 'space'  # map ke 'space'

                    detected = self.fsm.process_key(keytoken)
                    if detected:
                        print(f"\n🔥 COMBO DETECTED: {detected} 🔥")
                        self.count_detected += 1
                        self.fsm.reset_combo(detected)

                    # sedikit delay agar progres lebih realistis
                    time.sleep(0.02)

                # cek apakah ada special triggered tanpa simulasi (jarang di terminal)
                special = self.fsm.check_specials()
                if special:
                    print(f"\n⭐ SPECIAL EFFECT: {special} ⭐")

                # tampilkan progress singkat
                prog = self.fsm.progress_list()
                if prog:
                    print("Progress:", ', '.join(prog))

        except KeyboardInterrupt:
            print("\nInterrupted. Total combos:", self.count_detected)

    def run_test_mode(self) -> None:
        print("\nAutomated Test Mode\n")
        tests: List[Tuple[str, str]] = [
            ("ddd ", "Hadoken"),
            ("wswds ", "Shoryuken"),
            ("adad ", "Tatsumaki"),
            ("wwds ", "Dragon Punch"),
            ("dsdd ", "Hurricane Kick"),
        ]
        for seq, expect in tests:
            self.fsm.reset_all()
            print(f"Test input: {seq.strip()}  expecting: {expect}")
            detected: Optional[str] = None
            for ch in seq:
                time.sleep(0.08)
                r = self.fsm.process_key(ch)
                if r:
                    detected = r
            print("Result:", detected, "->", "PASS" if detected == expect else "FAIL")
            print("-" * 40)

# -------------------------
# Main
# -------------------------
def main() -> None:
    sim = GameSimulator()
    print("\n1. Interactive\n2. Test Mode\n3. Show Combo List\n4. Exit")
    choice = input("Choose (1-4): ").strip()
    if choice == '1':
        sim.run_interactive()
    elif choice == '2':
        sim.run_test_mode()
    elif choice == '3':
        sim.fsm.show_combos()
    else:
        print("Goodbye.")

if __name__ == "__main__":
    main()
