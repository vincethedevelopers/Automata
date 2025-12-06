"""
Soal 2 Fighting Game Combo Detector - Finite State Machine
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

@dataclass
class ComboDefinition:
    name: str
    sequence: List[InputKey]
    special_name: Optional[str] = None  # nama special jika SPACE di-hold

# -------------------------
# State tracker untuk tiap combo
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

    def is_timeout(self, current_time: float, timeout: float = 1.0) -> bool:
        if self.last_input_time == 0.0:
            return False
        return (current_time - self.last_input_time) > timeout

    def process_input(self, key: InputKey, current_time: float) -> Tuple[bool, bool, Optional[str]]:
        """
        Proses input untuk combo ini.
        Returns:
            (is_complete, is_valid_input, combo_name_or_None)
        """
        # timeout -> reset posisi jika sudah lebih dari timeout
        if self.is_timeout(current_time):
            self.reset()

        # safety: jika current_position out-of-range, reset
        if self.current_position >= len(self.combo_def.sequence):
            self.current_position = 0

        expected_key = self.combo_def.sequence[self.current_position]

        if key == expected_key:
            self.current_position += 1
            self.last_input_time = current_time

            if self.current_position >= len(self.combo_def.sequence):
                combo_name = self.combo_def.name

                # jika tombol terakhir adalah SPACE dan ada special_name -> mulai mode hold
                if key == InputKey.SPACE and self.combo_def.special_name:
                    self.space_press_start = current_time
                    self.space_is_held = True

                # reset posisi agar siap untuk deteksi ulang
                self.current_position = 0

                return True, True, combo_name

            return False, True, None
        else:
            return False, False, None

    def check_space_hold(self, current_time: float) -> Optional[str]:
        """
        Jika SPACE sedang di-hold dan durasinya antara 2-3 detik, kembalikan special_name.
        Setelah memberikan efek, release space.
        """
        if self.space_is_held and self.combo_def.special_name:
            hold_duration = current_time - self.space_press_start
            if 2.0 <= hold_duration <= 3.0:
                self.release_space()
                return self.combo_def.special_name
        return None

    def release_space(self) -> None:
        self.space_is_held = False
        self.space_press_start = 0.0

# -------------------------
# FSM utama
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
        self.combo_states: List[ComboState] = [ComboState(c) for c in self.combos]
        self.input_buffer: List[Tuple[InputKey, float]] = []
        self.max_buffer_size: int = 50
        self.key_map = {
            'w': InputKey.UP, 's': InputKey.DOWN, 'a': InputKey.LEFT, 'd': InputKey.RIGHT,
            ' ': InputKey.SPACE, 'up': InputKey.UP, 'down': InputKey.DOWN, 'left': InputKey.LEFT, 'right': InputKey.RIGHT, 'space': InputKey.SPACE
        }

    def reset_all_states(self) -> None:
        for st in self.combo_states:
            st.reset()

    def process_key_input(self, key_char: str) -> Optional[str]:
        """
        Terima input karakter string (misal 'w','a','d',' ') -> kembalikan nama combo jika terdeteksi.
        """
        current_time = time.time()
        key = self.key_map.get(key_char.lower())
        if not key:
            return None

        # simpan di buffer 
        self.input_buffer.append((key, current_time))
        if len(self.input_buffer) > self.max_buffer_size:
            self.input_buffer.pop(0)

        detected_combo: Optional[str] = None
        valid_for_any: bool = False

        # proses tiap state combo
        for state in self.combo_states:
            is_complete, is_valid, combo_name = state.process_input(key, current_time)
            if is_complete:
                detected_combo = combo_name
            if is_valid:
                valid_for_any = True

        # jika input tidak valid untuk combo yang sedang progress -> reset those
        if not valid_for_any:
            for state in self.combo_states:
                if state.current_position > 0:
                    expected = state.combo_def.sequence[state.current_position] if state.current_position < len(state.combo_def.sequence) else None
                    if expected is not None and key != expected:
                        state.reset()

        return detected_combo

    def check_space_hold_effects(self) -> Optional[str]:
        now = time.time()
        for state in self.combo_states:
            special = state.check_space_hold(now)
            if special:
                return special
        return None

    def get_current_progress(self) -> List[str]:
        prog: List[str] = []
        for st in self.combo_states:
            if st.current_position > 0:
                prog.append(f"{st.combo_def.name}: {st.current_position}/{len(st.combo_def.sequence)}")
        return prog

    def display_combo_list(self) -> None:
        print("\n" + "="*70)
        print("DAFTAR COMBO")
        print("="*70)
        for i, combo in enumerate(self.combos, 1):
            seq = ' '.join([k.value for k in combo.sequence])
            print(f"{i:2d}. {combo.name:25s} {seq}")
        print("="*70)
        print("Tips: Jeda antar input maksimal 1 detik. Hold SPACE 2-3 detik untuk special effect.")
        print("="*70)

# -------------------------
# Simulator / CLI
# -------------------------
class GameSimulator:
    def __init__(self):
        self.fsm = FightingGameFSM()
        self.detected_count: int = 0

    def run_interactive(self) -> None:
        print("\n" + "="*60)
        print("FIGHTING GAME - Interactive")
        print("="*60)
        self.fsm.display_combo_list()
        print("\nMode nyata: gunakan W/A/S/D untuk arah, ketik 'space' atau tekan spasi.")
        print("Ketik 'help' untuk daftar, 'reset' untuk reset, 'quit' untuk keluar.")

        try:
            while True:
                cmd = input("\nInput: ").strip().lower()
                if cmd == 'quit':
                    print("Total combos detected:", self.detected_count)
                    break
                if cmd == 'help':
                    self.fsm.display_combo_list()
                    continue
                if cmd == 'reset':
                    self.fsm.reset_all_states()
                    print("All states reset.")
                    continue

                # process each token (support words like "ddd " or "space")
                tokens: List[str] = []
                if cmd == 'space':
                    tokens = [' ']
                else:
                    # if contains spaces (like "d d d "), split; else iterate chars
                    if ' ' in cmd and len(cmd) > 1:
                        parts = cmd.split()
                        for p in parts:
                            if p == 'space':
                                tokens.append(' ')
                            else:
                                tokens.extend(list(p))
                    else:
                        tokens = list(cmd)

                for t in tokens:
                    res = self.fsm.process_key_input(t)
                    if res:
                        print(f"🔥 COMBO DETECTED: {res} 🔥")
                        self.detected_count += 1
                    time.sleep(0.02)

                # cek hold SPACE effect shortly after
                special = self.fsm.check_space_hold_effects()
                if special:
                    print(f"⭐ SPECIAL EFFECT: {special} ⭐")

                prog = self.fsm.get_current_progress()
                if prog:
                    print("Progress:", ', '.join(prog))

        except KeyboardInterrupt:
            print("\nInterrupted. Total combos:", self.detected_count)

    def run_test_mode(self) -> None:
        print("\n" + "="*60)
        print("TEST MODE - Automated")
        print("="*60)
        tests: List[Tuple[str, str]] = [
            ("ddd ", "Hadoken"),
            ("wswds ", "Shoryuken"),
            ("adad ", "Tatsumaki"),
            ("wwds ", "Dragon Punch"),
            ("dsdd ", "Hurricane Kick"),
        ]
        for seq, expected in tests:
            self.fsm.reset_all_states()
            print(f"Testing input: {seq} expecting {expected}")
            detected: Optional[str] = None
            for ch in seq:
                time.sleep(0.1)
                r = self.fsm.process_key_input(ch)
                if r:
                    detected = r
            print("Result:", detected, "->", "PASS" if detected == expected else "FAIL")
            print("-"*40)

def main() -> None:
    sim = GameSimulator()
    print("\n1. Interactive\n2. Test Mode\n3. Show Combo List\n4. Exit")
    choice = input("Choose (1-4): ").strip()
    if choice == '1':
        sim.run_interactive()
    elif choice == '2':
        sim.run_test_mode()
    elif choice == '3':
        sim.fsm.display_combo_list()
    else:
        print("Goodbye.")

if __name__ == "__main__":
    main()
