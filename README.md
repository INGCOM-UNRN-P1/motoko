# MOTOKO — Verificador de Encapsulamiento y Opacidad de TDAs en C

> 📖 **Manual de Usuario:** Para una guía exhaustiva de comandos, banderas, arquitectura y ejemplos, consultá el [Manual de Uso](MANUAL.md).

**MOTOKO** analiza archivos de cabecera e implementaciones en C para asegurar el ocultamiento de información y encapsulamiento estricto de Tipos Abstractos de Datos (TDAs), detectando accesos directos a campos internos desde código cliente.

---

## 🎯 Alcance

### Qué cubre
- Verificación estática de encapsulamiento y tipos opacos en Tipos de Datos Abstractos (TDAs) de C.
- Regla `MOT001`: Verificación de que la definición completa de estructuras de datos (`struct`) resida exclusivamente en archivos de implementación (`.c`), manteniendo únicamente declaraciones incompletas (`typedef struct tda tda_t;`) en archivos de cabecera (`.h`).
- Regla `MOT002`: Prohibición estricta de desreferencia directa de campos privados en archivos cliente.
- Regla `MOT003`: Funciones públicas que devuelven punteros a la memoria interna del TDA.
- Un resumen por TDA en el lenguaje de la consigna («Tu TDA Pila expone 2 campos en pila.h (tope, datos) y el código cliente los usa directamente en main.c:12»), en la salida, el JSON (`resumen`) y la sección Markdown.
- Manejo defensivo y resiliente de entregas y carpetas de estudiantes sin archivos `.h`.

### Qué no cubre (Límites y Delegación)
- Linter de estilo y formato de código (delegado a `gaff`).
- Demostración formal de contratos matemáticos del TDA (delegado a `callahan`).
- Verificación de fugas de memoria o memory leaks en el TDA (delegado a `nostromo` / `tetsuo`).

---

## 📋 Requisitos

### Requisitos de Sistema y Entorno
- Multiplataforma. Python >= 3.10.

### Dependencias Externas y Binarios
- Ninguno obligatorio (análisis estático con Tree-Sitter AST).

### Integración en el Ecosistema
- CLI `motoko`. Plugin registrado en `ripley.plugins` (`tda_encapsulation`). Subcomando `motoko doctor`.

---

## 🚀 Uso Rápido

```bash
# Verificar encapsulamiento de cabeceras en el directorio
motoko verify tda_pila.h

# Especificar archivo cliente e implementación
motoko verify tda_pila.h --client main.c --impl tda_pila.c

# Auditar todos los TDAs de un proyecto (directorio) de una vez
motoko audit-all proyecto/

# Salida estructurada JSON
motoko verify tda_pila.h --json

# Versión (opción global) y sección de reporte para Dredd (exit 1 si hay violaciones)
motoko --version
motoko report tda_pila.h -o motoko.md
```

---

## 🔍 Reglas Auditadas

- **`MOT001`**: TDAs que exponen sus campos dentro del `.h` público (debe usarse declaración incompleta).
- **`MOT002`**: Código cliente que desreferencia directamente campos del TDA (`tda->campo`) en lugar de invocar primitivas públicas.
- **`MOT003`**: Función pública (declarada en el `.h`) que devuelve un puntero no `const` a la memoria interna: la dirección de un campo (`return &p->tope;`, error) o un campo arreglo o puntero (`return p->datos;`, advertencia). Un `const char *` de solo lectura no se marca.

<!-- p1:referencia:inicio — generado por p1-tools/scripts/readme_generado.py: no editar a mano -->

## Referencia rápida

### Requisitos

- Python ≥ 3.11 y [uv](https://docs.astral.sh/uv/getting-started/installation/).

### Comandos

| Comando | Descripción |
|:--|:--|
| `motoko audit-all`, `motoko check`, `motoko verify` | Verifica que los TDAs sean opacos y no sufran accesos directos a sus campos internos. |
| `motoko report` | Genera directamente la sección de reporte Markdown de MOTOKO para Dredd. |
| `motoko doctor` | Verifica el estado del entorno de auditoría de TDAs MOTOKO (Tree-Sitter C, Python, GCC). |

Ayuda de cada comando: `motoko <comando> -h`.

### Salida JSON

Con `--json`, estos comandos emiten el resultado como JSON por la salida estándar, para usarlo desde scripts, ripley o dredd: `motoko audit-all`, `motoko check`, `motoko verify`, `motoko doctor`. El de `doctor --json` lleva `schema_version` y `ok`.

### Códigos de salida

| Código | Significado |
|:--|:--|
| `0` | Terminó bien (en `doctor`: está todo lo requerido). |
| `1` | El comando encontró problemas (hallazgos, pruebas que fallan, un umbral que no se alcanza) o un dato no se pudo usar (un archivo ilegible, un formato inválido). |
| `2` | Error de uso: comando, opción o argumento inválido. |

<!-- p1:referencia:fin -->
