#!/bin/bash
# Parches mínimos para que dw_decomp compile correctamente

echo "=== Aplicando parches mínimos al Makefile y linker script ==="

cd /home/radi/Proyectos/Github/dw_decomp

# 1. PYTHON: usar python del sistema (no .venv)
sed -i 's|^PYTHON := python3$|PYTHON := /usr/bin/python3|' Makefile
echo "✓ PYTHON path corregido"

# 2. MAIN_SRC: quitar utils.c (no compila con Metrowerks)
grep -q "utils.c" Makefile && sed -i '/src\/main\/utils.c \\/d' Makefile && echo "✓ utils.c eliminado de MAIN_SRC"

# 3. MAIN_ASM_SRC: no excluir anim.s (necesitamos compilar anim.s)
# El original tiene -not -name 'anim.s', lo quitamos
sed -i 's/-not -name .anim.s. //' Makefile
echo "✓ anim.s ya no está excluido de MAIN_ASM_SRC"

# 4. PYTHON en gen_bss rules
sed -i 's|\ttools/gen_bss.py|$(PYTHON) tools/gen_bss.py|g' Makefile
echo "✓ gen_bss.py ahora usa PYTHON variable"

# 5. Linker script: anim.c.o -> anim.s.o
sed -i 's|build/src/main/anim\.c\.o|build/asm/main/anim.s.o|g' config/main.ld
echo "✓ anim.c.o -> anim.s.o en linker script"

# 6. Linker script: utils.c.o -> utils.s.o
sed -i 's|build/src/main/utils\.c\.o|build/asm/main/utils.s.o|g' config/main.ld
echo "✓ utils.c.o -> utils.s.o en linker script"

# 7. Añadir reglas para asm/ con -G8 (necesario para GP-relative)
# Insertar justo después de la regla general %.s.o
LINE=$(grep -n '^$(BUILDDIR)/%.s.o: %.s' Makefile | head -1 | cut -d: -f1)
if [ -n "$LINE" ]; then
    sed -i "$((LINE+5)) a\\
# Los .s generados por Metrowerks necesitan -G8 (equivalente a -sdata 8)\\
\$(BUILDDIR)/asm/%.s.o: asm/%.s\\
\t@mkdir -p \$(dir \$@)\\
\t\$(CC) \$(CFLAGS) \$(CPPFLAGS) \$(DEPFLAGS) \$<\\
\t\$(CC) -c \$(CFLAGS) -G8 \$(CPPFLAGS) -o \$@ \$<\\
\t@\$(OBJCOPY) --set-section-alignment .text=4 --set-section-alignment .data=4 --set-section-alignment .rodata=4 --set-section-alignment .bss=4 --set-section-alignment .sbss=4 --set-section-alignment .sdata=4 \$@\\
\\
\$(BUILDDIR)/asm/%.rodata.s.o: asm/%.rodata.s\\
\t@mkdir -p \$(dir \$@)\\
\t\$(CC) \$(CFLAGS) -G8 \$(CPPFLAGS) -Wa,--defsym,_RODATA=1 -o \$@ \$<\\
\\
\$(BUILDDIR)/asm/%.data.s.o: asm/%.data.s\\
\t@mkdir -p \$(dir \$@)\\
\t\$(CC) \$(CFLAGS) -G8 \$(CPPFLAGS) -Wa,--defsym,_DATA=1 -o \$@ \$<\\
\\
\$(BUILDDIR)/asm/%.sdata.s.o: asm/%.sdata.s\\
\t@mkdir -p \$(dir \$@)\\
\t\$(CC) \$(CFLAGS) -G8 \$(CPPFLAGS) -Wa,--defsym,_SDATA=1 -o \$@ \$<" Makefile
    echo "✓ Reglas asm/ con -G8 añadidas"
fi

echo "=== Parches aplicados ==="
