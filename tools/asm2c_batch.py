#!/usr/bin/env python3
"""
Decompilación batch asm→C para Digimon World (PS1)
Procesa funciones nonmatching y genera código C equivalente.

Uso:
  python3 tools/asm2c_batch.py                              # Analiza todo
  python3 tools/asm2c_batch.py --decompile <function_name>   # Decompila una función
  python3 tools/asm2c_batch.py --decompile-all               # Decompila todo (peligroso)
  python3 tools/asm2c_batch.py --status                      # Ver estado actual
"""

import os
import re
import sys
import json
import subprocess
from pathlib import Path

BASE_DIR = Path("/home/radi/Proyectos/Github/dw_decomp")
ASM_DIR = BASE_DIR / "asm"
SRC_DIR = BASE_DIR / "src"
CONFIG_DIR = BASE_DIR / "config"

# Mapeo de registros MIPS
REGS = {
    '$zero': '0', '$at': 'at', '$v0': 'v0', '$v1': 'v1',
    '$a0': 'a0', '$a1': 'a1', '$a2': 'a2', '$a3': 'a3',
    '$t0': 't0', '$t1': 't1', '$t2': 't2', '$t3': 't3',
    '$s0': 's0', '$s1': 's1', '$s2': 's2', '$s3': 's3',
    '$s4': 's4', '$s5': 's5', '$s6': 's6', '$s7': 's7',
    '$sp': 'sp', '$ra': 'ra', '$gp': 'gp', '$fp': 'fp',
}

# Estructuras conocidas del juego (offset → campo)
ENTITY_FIELDS = {
    0x00: 'type', 0x04: 'posData', 0x08: 'animPtr',
    0x34: 'isOnMap', 0x35: 'isOnScreen',
}

def parse_asm_file(filepath):
    """Parsea un archivo .s de nonmatching y extrae funciones."""
    functions = []
    with open(filepath) as f:
        content = f.read()
    
    # Buscar funciones nonmatching
    pattern = r'nonmatching\s+(\w+),\s*(0x[0-9A-Fa-f]+)\s*\n\s*glabel\s+\1(.*?)(?=endlabel\s+\1|$)'
    for match in re.finditer(pattern, content, re.DOTALL):
        name = match.group(1)
        size = int(match.group(2), 16)
        body = match.group(3).strip()
        functions.append({'name': name, 'size': size, 'body': body})
    
    return functions

def analyze_function(asm_body):
    """Analiza una función assembly y extrae metadatos."""
    lines = asm_body.strip().split('\n')
    info = {
        'stack_size': 0,
        'saved_regs': [],
        'calls': [],
        'mem_access': [],
        'has_delay_slots': False,
    }
    
    for line in lines:
        line = line.strip()
        # Extraer instrucción (ignorar comentarios y direcciones)
        asm_match = re.search(r'/\*\s*[0-9A-F]+\s+[0-9A-F]+\s+\*/\s*(.*?)(?:\s+#|//|$)', line)
        if not asm_match:
            continue
        instr = asm_match.group(1).strip()
        
        # Analizar tipo de instrucción
        if instr.startswith('addiu $sp, $sp, -'):
            info['stack_size'] = int(instr.split('-')[1].rstrip(')'))
        elif instr.startswith('sw $ra'):
            info['saved_regs'].append('ra')
        elif instr.startswith('sw $s'):
            reg = instr.split(',')[0].split()[-1]
            if reg not in info['saved_regs']:
                info['saved_regs'].append(reg)
        elif 'jal' in instr:
            callee = instr.split()[-1]
            info['calls'].append(callee)
        elif 'lw' in instr or 'lb' in instr or 'lbu' in instr or 'lh' in instr:
            info['mem_access'].append(instr)
    
    return info

def generate_c_from_template(func_info, module_name):
    """Genera C básico a partir del análisis."""
    name = func_info['name']
    
    # Detectar patrón simple: thunk (solo j)
    if func_info['body'].strip().startswith('j ') or 'jr $ra' in func_info['body'].strip().split('\n')[0]:
        j_target = re.search(r'j\s+(\w+)', func_info['body'])
        if j_target and 'jr $ra' not in func_info['body'].split('\n')[0]:
            target = j_target.group(1)
            return f"""void {name}(void)
\t{target}();
}}"""
    
    # Detectar patrón: jr $ra, sb ... (setMapLayerEnabled)
    if 'jr $ra' in func_info['body'] and 'sb' in func_info['body']:
        # Simple store and return
        return f"""void {name}(int32_t value)
{{
\t// TODO: Implementar store a variable global
\t// sb $a0, global_variable
}}"""
    
    return None

def get_status():
    """Muestra el estado actual de la decompilación."""
    print("=== Estado de Decompilación ===")
    print()
    
    # Contar funciones por módulo
    total_nonmatching = 0
    total_matching = 0
    modules = []
    
    for asm_file in sorted((ASM_DIR / "main" / "nonmatchings").rglob("*.s")):
        module = asm_file.parent.name
        total_nonmatching += 1
    
    for asm_file in sorted((ASM_DIR / "main" / "matchings").rglob("*.s")):
        total_matching += 1
    
    # Contar INCLUDE_ASM en src/
    include_asms = 0
    for c_file in SRC_DIR.rglob("*.c"):
        with open(c_file) as f:
            content = f.read()
            include_asms += content.count("INCLUDE_ASM")
    
    print(f"  Módulos: main, dget")
    print(f"  Funciones nonmatching: {total_nonmatching}")
    print(f"  Funciones matching: {total_matching}")
    print(f"  INCLUDE_ASM restantes: {include_asms}")
    print()
    
    # Mostrar funciones por módulo
    for module_path in sorted((ASM_DIR / "main" / "nonmatchings").iterdir()):
        if module_path.is_dir():
            funcs = list(module_path.glob("*.s"))
            if funcs:
                c_file = SRC_DIR / "main" / f"{module_path.name}.c"
                c_exists = "✅" if c_file.exists() else "❌"
                print(f"  {c_exists} {module_path.name}/: {len(funcs)} funciones")
    
    print()
    print(f"  Archivos .s completos SIN .c:")
    for asm_file in sorted((ASM_DIR / "main").glob("*.s")):
        name = asm_file.stem
        if name == "data": continue
        c_file = SRC_DIR / "main" / f"{name}.c"
        if not c_file.exists():
            glabels = count_labels(asm_file)
            print(f"    {name}.s ({glabels} funciones)")
    
    return include_asms

def count_labels(asm_file):
    with open(asm_file) as f:
        content = f.read()
    return len(re.findall(r'^glabel\s+\w+', content, re.MULTILINE))

def main():
    if len(sys.argv) < 2:
        get_status()
        return
    
    cmd = sys.argv[1]
    
    if cmd == '--status':
        get_status()
    elif cmd == '--decompile-all':
        print("⚠️  Auto-decompilación masiva no implementada todavía.")
        print("Usa --decompile <function_name> para funciones individuales.")
    elif cmd == '--decompile':
        if len(sys.argv) < 3:
            print("Especifica el nombre de la función.")
            return
        func_name = sys.argv[2]
        # Buscar la función en nonmatchings
        found = False
        for asm_file in (ASM_DIR / "main" / "nonmatchings").rglob("*.s"):
            with open(asm_file) as f:
                content = f.read()
            if f'glabel {func_name}' in content:
                print(f"Encontrada en: {asm_file}")
                funcs = parse_asm_file(asm_file)
                for func in funcs:
                    if func['name'] == func_name:
                        print(f"Tamaño: {func['size']} bytes")
                        info = analyze_function(func['body'])
                        print(f"Stack: {info['stack_size']} bytes")
                        print(f"Llamadas: {', '.join(info['calls'])}")
                        print()
                        print("=== CÓDIGO C SUGERIDO ===")
                        c_code = generate_c_from_template(func, asm_file.parent.name)
                        if c_code:
                            print(c_code)
                        break
                found = True
                break
        if not found:
            print(f"No se encontró la función '{func_name}'")
    else:
        print(f"Comando desconocido: {cmd}")
        print("Usa: --status, --decompile <func>, --decompile-all")

if __name__ == '__main__':
    main()
