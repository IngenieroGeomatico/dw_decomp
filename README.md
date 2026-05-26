# Digimon World decomp

A work in progress decompilation of Digimon World for PS1.

## Dependencies

Install the following packages:
```
binutils-mipsel-linux-gnu gcc-mipsel-linux-gnu git make python3 python3-venv unzip wget
```

Install Python dependencies:
```
python3 -m venv .venv
. .venv/bin/activate
pip3 install -r requirements.txt
```

Download tools:
```
tools/dl_deps.sh
```

Download CodeWarrior for PlayStation Release 4 and copy cc_mips.dll to bin/cc_mips/cc_mips_40.dll.

## Build

```
# Update submodules
git submodule update --init --recursive

# Dump original PSX Digimon World (USA) ISO
bin/mkpsxiso-2.20-Linux/bin/dumpsxiso -x disks/us -s disks/us/us.xml "/path/to/Digimon World (USA).bin"

# Disassemble original binaries
make -j$(nproc) regenerate

# (Optional) Create file local.mk to override defaults
MWCCWRAP := /path/to/mwccwrap.exe
MWCCWRAP_FLAGS := -dll "/path/to/cc_mips.dll"
METROWRAP := /path/to/mw
METROWRAP_FLAGS := --use-wibo --wibo-path /path/to/wibo
TOOLCHAIN := /path/to/mipsel-linux-gnu-

# Build new binaries
make -j$(nproc)

# Compare original vs new binaries
make compare

# Generate objdiff config
make objdiff
```

## Links

Symbols and reverse engineering is based on work by SydMontague:  
https://github.com/SydMontague/DW1-SydPatches  
https://github.com/SydMontague/DW1-Code



-------

Aquí tienes la guía completa para colaborar con el proyecto:
Paso 1: Instalar dependencias del sistema

En Linux (Ubuntu/Debian), instala los paquetes necesarios:

sudo apt install binutils-mipsel-linux-gnu gcc-mipsel-linux-gnu git make python3 python3-venv unzip wget clang clangd

README.md:7-10
Paso 2: Clonar el repositorio y los submódulos

git clone https://github.com/jype0/dw_decomp  
cd dw_decomp  
git submodule update --init --recursive

README.md:29-30
Paso 3: Configurar el entorno Python

python3 -m venv .venv  
source .venv/bin/activate  
pip3 install -r requirements.txt

README.md:13-16
Paso 4: Descargar las herramientas automáticas

tools/dl_deps.sh

Esto descarga: mwccwrap, metrowrap, mkpsxiso, objdiff y wibo. README.md:19-22
Paso 5: Obtener el compilador Metrowerks (manual, obligatorio)

Debes conseguir por tu cuenta CodeWarrior for PlayStation Release 4 y copiar el archivo cc_mips.dll a:

bin/cc_mips/cc_mips_40.dll  

Esto es necesario porque el compilador tiene licencia privada y no se puede distribuir. README.md:24
Paso 6: Extraer la ISO original del juego

Necesitas una copia de Digimon World (USA) en formato .bin:

bin/mkpsxiso-2.20-Linux/bin/dumpsxiso -x disks/us -s disks/us/us.xml "/ruta/a/Digimon World (USA).bin"

README.md:32-33
Paso 7: Desensamblar los binarios originales

make -j$(nproc) regenerate

Esto usa splat para generar los archivos .s de ensamblador en la carpeta asm/. README.md:35-36
Paso 8: Compilar y verificar

# Compilar  
make -j$(nproc)  
  
# Comparar tu build con el original  
make compare  
  
# Generar config de objdiff para ver diferencias función a función  
make objdiff

README.md:45-52
Ciclo de trabajo para descompilar una función

Una vez que el entorno está listo, el flujo para contribuir es:

    Elegir una función en asm/ que aún esté en ensamblador (no tiene .c equivalente en src/)
    Escribir el C equivalente en src/ que reproduzca la lógica del ensamblador
    Compilar con make -j$(nproc)
    Verificar con make compare o make objdiff para ver si el binario generado es idéntico al original
    Si no coincide, puedes usar el permuter (tools/permute.sh) para buscar variantes de C que compilen igual README.md:45-52

Nota importante: El proyecto corre en Linux. Si usas Windows, hay un Dockerfile disponible en la raíz del repo que configura el entorno automáticamente. Dockerfile:1



--------

# 1. Descargar dependencias
./tools/dl_deps.sh

# 2. Extraer ISO (si no lo has hecho)
./tools/docker_run.sh bin/mkpsxiso-2.20-Linux/bin/dumpsxiso -x disks/us -s disks/us/us.xml "/dw/Digimon World (USA).bin"

# 3. Regenerar archivos ASM
./tools/docker_run.sh make -j$(nproc) regenerate

# 4. Dar permisos (importante para Docker)
sudo chmod -R 777 external/ build/ src/  asm/

# 5. Compilar
./tools/docker_run.sh make -j$(nproc)


./tools/docker_run.sh make compare  
./tools/docker_run.sh make objdiff