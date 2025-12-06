"""
Soal 1 - Pushdown Automata: Validasi & Konversi Notasi Matematika
Kelompok: Group-4

Terminal:
python3 automata.py
"""

import re
from typing import List, Tuple, Optional
from enum import Enum

class NotationType(Enum):
    INFIX = "infix"
    PREFIX = "prefix"
    POSTFIX = "postfix"


class PushdownAutomata:
    def __init__(self):
        # Operator dan prioritas
        self.operators = {'+', '-', '*', '/'}
        self.precedence = {'+': 1, '-': 1, '*': 2, '/': 2}
        # regex token: angka (int/float), variabel (huruf), operator atau kurung
        self.token_re = re.compile(r'\d+(\.\d+)?|[A-Za-z]+|[()+\-*/]')

    # -------------------------
    # Tokenisasi
    # - Fungsi tokenize: memecah ekspresi jadi token terurut
    # - Mendukung angka multi-digit (contoh: 12, 3.14) dan variabel (x, abc)
    # - Menghapus spasi sebelum tokenisasi
    # -------------------------
    def tokenize(self, expr: str) -> List[str]:
        s = expr.replace(" ", "")
        return [m.group(0) for m in self.token_re.finditer(s)]

    def is_operand(self, tok: str) -> bool:
        # operand: angka (integer/float) atau variabel berbasis huruf
        return bool(re.fullmatch(r'\d+(\.\d+)?|[A-Za-z]+', tok))

    def is_operator(self, tok: str) -> bool:
        return tok in self.operators

    # -------------------------
    # VALIDASI INFIX
    # - Cek keseimbangan kurung
    # - Cek urutan operand/operator
    # - Berikan pesan error yang jelas (posisi token)
    # -------------------------
    def validate_infix(self, expr: str) -> Tuple[bool, str]:
        tokens = self.tokenize(expr)
        if not tokens:
            return False, "Empty expression"

        stack_paren = []
        expect_operand = True  # awalnya harus operand

        for i, tok in enumerate(tokens):
            if tok == '(':
                if not expect_operand:
                    return False, f"Unexpected '(' at token {i}"
                stack_paren.append('(')
                expect_operand = True
            elif tok == ')':
                if expect_operand:
                    return False, f"Unexpected ')' at token {i}"
                if not stack_paren:
                    return False, f"Unmatched ')' at token {i}"
                stack_paren.pop()
                expect_operand = False
            elif self.is_operand(tok):
                if not expect_operand:
                    return False, f"Unexpected operand '{tok}' at token {i}"
                expect_operand = False
            elif self.is_operator(tok):
                if expect_operand:
                    return False, f"Unexpected operator '{tok}' at token {i}"
                expect_operand = True
            else:
                return False, f"Invalid token '{tok}' at token {i}"

        if stack_paren:
            return False, "Unmatched opening parenthesis"
        if expect_operand:
            return False, "Expression ends with operator"

        return True, "Valid infix expression"

    # -------------------------
    # VALIDASI PREFIX
    # - Tidak boleh ada kurung untuk prefix (karena prefix tidak memerlukan kurung)
    # - Proses dari kanan ke kiri: hitung jumlah operand yang tersedia
    # - Jika operator kehabisan operand -> invalid
    # -------------------------
    def validate_prefix(self, expr: str) -> Tuple[bool, str]:
        tokens = self.tokenize(expr)
        if not tokens:
            return False, "Empty expression"
        if '(' in tokens or ')' in tokens:
            return False, "Prefix should not contain parentheses (input likely infix)"
        stack_count = 0
        for tok in reversed(tokens):
            if self.is_operand(tok):
                stack_count += 1
            elif self.is_operator(tok):
                if stack_count < 2:
                    return False, "Invalid prefix: not enough operands"
                stack_count -= 1
            else:
                return False, f"Invalid token '{tok}'"
        return (True, "Valid prefix expression") if stack_count == 1 else (False, "Invalid prefix structure")

    # -------------------------
    # VALIDASI POSTFIX
    # - Tidak boleh ada kurung untuk postfix
    # - Proses kiri->kanan: maintain operand count
    # -------------------------
    def validate_postfix(self, expr: str) -> Tuple[bool, str]:
        tokens = self.tokenize(expr)
        if not tokens:
            return False, "Empty expression"
        if '(' in tokens or ')' in tokens:
            return False, "Postfix should not contain parentheses (input likely infix)"
        stack_count = 0
        for tok in tokens:
            if self.is_operand(tok):
                stack_count += 1
            elif self.is_operator(tok):
                if stack_count < 2:
                    return False, "Invalid postfix: not enough operands"
                stack_count -= 1
            else:
                return False, f"Invalid token '{tok}'"
        return (True, "Valid postfix expression") if stack_count == 1 else (False, "Invalid postfix structure")

    # -------------------------
    # KONVERSI INFIX -> POSTFIX (SHUNTING-YARD)
    # - Kembalikan string token dipisah spasi
    # -------------------------
    def infix_to_postfix(self, expr: str) -> str:
        valid, msg = self.validate_infix(expr)
        if not valid:
            raise ValueError(f"Infix invalid: {msg}")
        tokens = self.tokenize(expr)
        out = []
        op_stack = []
        for tok in tokens:
            if self.is_operand(tok):
                out.append(tok)
            elif tok == '(':
                op_stack.append(tok)
            elif tok == ')':
                while op_stack and op_stack[-1] != '(':
                    out.append(op_stack.pop())
                op_stack.pop()
            elif self.is_operator(tok):
                while (op_stack and op_stack[-1] != '(' and
                       op_stack[-1] in self.precedence and
                       self.precedence[op_stack[-1]] >= self.precedence[tok]):
                    out.append(op_stack.pop())
                op_stack.append(tok)
            else:
                raise ValueError(f"Invalid token '{tok}' in infix")
        while op_stack:
            top = op_stack.pop()
            if top in ('(', ')'):
                raise ValueError("Mismatched parentheses")
            out.append(top)
        return ' '.join(out)

    # -------------------------
    # KONVERSI INFIX -> PREFIX
    # - Reverse tokens, swap parens, shunting-yard, reverse hasil
    # - Kembalikan token dipisah spasi
    # -------------------------
    def infix_to_prefix(self, expr: str) -> str:
        valid, msg = self.validate_infix(expr)
        if not valid:
            raise ValueError(f"Infix invalid: {msg}")
        tokens = self.tokenize(expr)
        rev = []
        for tok in reversed(tokens):
            if tok == '(':
                rev.append(')')
            elif tok == ')':
                rev.append('(')
            else:
                rev.append(tok)
        out = []
        op_stack = []
        for tok in rev:
            if self.is_operand(tok):
                out.append(tok)
            elif tok == '(':
                op_stack.append(tok)
            elif tok == ')':
                while op_stack and op_stack[-1] != '(':
                    out.append(op_stack.pop())
                op_stack.pop()
            elif self.is_operator(tok):
                while (op_stack and op_stack[-1] != '(' and
                       op_stack[-1] in self.precedence and
                       self.precedence[op_stack[-1]] > self.precedence[tok]):
                    out.append(op_stack.pop())
                op_stack.append(tok)
            else:
                raise ValueError(f"Invalid token '{tok}' in infix->prefix")
        while op_stack:
            top = op_stack.pop()
            if top in ('(', ')'):
                raise ValueError("Mismatched parentheses")
            out.append(top)
        prefix_tokens = list(reversed(out))
        return ' '.join(prefix_tokens)

    # -------------------------
    # KONVERSI POSTFIX -> INFIX
    # - Gunakan stack: pop dua operand, gabungkan jadi '(a op b)'
    # - Kembalikan string infix (dengan spasi untuk keterbacaan)
    # -------------------------
    def postfix_to_infix(self, expr: str) -> str:
        valid, msg = self.validate_postfix(expr)
        if not valid:
            raise ValueError(f"Postfix invalid: {msg}")
        tokens = self.tokenize(expr)
        stack = []
        for tok in tokens:
            if self.is_operand(tok):
                stack.append(tok)
            elif self.is_operator(tok):
                b = stack.pop()
                a = stack.pop()
                stack.append(f"({a} {tok} {b})")
            else:
                raise ValueError(f"Invalid token '{tok}' in postfix->infix")
        return stack[0]

    # -------------------------
    # KONVERSI PREFIX -> INFIX
    # - Mirip postfix->infix tapi baca dari belakang
    # -------------------------
    def prefix_to_infix(self, expr: str) -> str:
        valid, msg = self.validate_prefix(expr)
        if not valid:
            raise ValueError(f"Prefix invalid: {msg}")
        tokens = self.tokenize(expr)
        stack = []
        for tok in reversed(tokens):
            if self.is_operand(tok):
                stack.append(tok)
            elif self.is_operator(tok):
                a = stack.pop()
                b = stack.pop()
                stack.append(f"({a} {tok} {b})")
            else:
                raise ValueError(f"Invalid token '{tok}' in prefix->infix")
        return stack[0]

    def postfix_to_prefix(self, expr: str) -> str:
        inf = self.postfix_to_infix(expr)
        return self.infix_to_prefix(inf)

    def prefix_to_postfix(self, expr: str) -> str:
        inf = self.prefix_to_infix(expr)
        return self.infix_to_postfix(inf)

# -------------------------
# Wrapper: NotationConverter
# - Tugas: deteksi notasi + panggil fungsi konversi yang cocok
# - Deteksi prioritas: jika ada kurung -> coba INFIX dulu; else coba POSTFIX -> PREFIX -> INFIX
# -------------------------
class NotationConverter:
    def __init__(self):
        self.pda = PushdownAutomata()

    def detect_notation(self, expr: str) -> Optional[NotationType]:
        tokens = self.pda.tokenize(expr)
        if not tokens:
            return None
        if '(' in tokens or ')' in tokens:
            valid, _ = self.pda.validate_infix(expr)
            return NotationType.INFIX if valid else None
        valid, _ = self.pda.validate_postfix(expr)
        if valid:
            return NotationType.POSTFIX
        valid, _ = self.pda.validate_prefix(expr)
        if valid:
            return NotationType.PREFIX
        valid, _ = self.pda.validate_infix(expr)
        if valid:
            return NotationType.INFIX
        return None

    def convert(self, expr: str, from_type: NotationType, to_type: NotationType) -> str:
        if from_type == to_type:
            return expr
        map_conv = {
            (NotationType.INFIX, NotationType.POSTFIX): self.pda.infix_to_postfix,
            (NotationType.INFIX, NotationType.PREFIX): self.pda.infix_to_prefix,
            (NotationType.POSTFIX, NotationType.INFIX): self.pda.postfix_to_infix,
            (NotationType.POSTFIX, NotationType.PREFIX): self.pda.postfix_to_prefix,
            (NotationType.PREFIX, NotationType.INFIX): self.pda.prefix_to_infix,
            (NotationType.PREFIX, NotationType.POSTFIX): self.pda.prefix_to_postfix,
        }
        func = map_conv.get((from_type, to_type))
        if not func:
            raise ValueError("Invalid conversion type")
        return func(expr)



def main():
    conv = NotationConverter()
    banner = "="*60 + "\nPUSHDOWN AUTOMATA - Validator & Converter\n" + "="*60
    print(banner)
    while True:
        print("\n📋 MENU:\n1. Validate Expression\n2. Convert Expression\n3. Auto-detect and Convert\n4. Exit")
        choice = input("Pilih menu (1-4): ").strip()
        if choice == '1':
            expr = input("Masukkan expression: ").strip()
            ok, msg = conv.pda.validate_infix(expr)
            print(f"Infix:   {'✓ '+msg if ok else '✗ '+msg}")
            ok, msg = conv.pda.validate_prefix(expr)
            print(f"Prefix:  {'✓ '+msg if ok else '✗ '+msg}")
            ok, msg = conv.pda.validate_postfix(expr)
            print(f"Postfix: {'✓ '+msg if ok else '✗ '+msg}")
        elif choice == '2':
            expr = input("Masukkan expression: ").strip()
            print("From: 1.Infix 2.Prefix 3.Postfix")
            f = input("From (1-3): ").strip()
            t = input("To   (1-3): ").strip()
            map_t = {'1': NotationType.INFIX, '2': NotationType.PREFIX, '3': NotationType.POSTFIX}
            try:
                res = conv.convert(expr, map_t[f], map_t[t])
                print("Result:", res)
            except Exception as e:
                print("Error:", e)
        elif choice == '3':
            expr = input("Masukkan expression: ").strip()
            detected = conv.detect_notation(expr)
            if not detected:
                print("Cannot detect notation. Expression invalid.")
                continue
            print("Detected:", detected.value.upper())
            print("Convert to: 1.Infix 2.Prefix 3.Postfix")
            t = input("Choose (1-3): ").strip()
            try:
                res = conv.convert(expr, detected, {'1':NotationType.INFIX,'2':NotationType.PREFIX,'3':NotationType.POSTFIX}[t])
                print("Result:", res)
            except Exception as e:
                print("Error:", e)
        elif choice == '4':
            print("Terima kasih.")
            break
        else:
            print("Pilihan tidak valid.")

if __name__ == "__main__":
    main()
