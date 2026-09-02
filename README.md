# MOTOKO — Verificador de Encapsulamiento y Opacidad de TDAs en C

**MOTOKO** analiza archivos de cabecera e implementaciones en C para asegurar el ocultamiento de información y encapsulamiento estricto de Tipos Abstractos de Datos (TDAs), detectando accesos directos a campos internos desde código cliente.

---

## 🎯 Alcance

### Qué cubre
- Verificación estática de encapsulamiento y tipos opacos en Tipos de Datos Abstractos (TDAs) de C.
- Regla `MOT001`: Verificación de que la definición completa de estructuras de datos (`struct`) resida exclusivamente en archivos de implementación (`.c`), manteniendo únicamente declaraciones incompletas (`typedef struct tda tda_t;`) en archivos de cabecera (`.h`).
- Regla `MOT002`: Prohibición estricta de desreferencia directa de campos privados en archivos cliente.
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

# Salida estructurada JSON
motoko verify tda_pila.h --json
```

---

## 🔍 Reglas Auditadas

- **`MOT001`**: TDAs que exponen sus campos dentro del `.h` público (debe usarse declaración incompleta).
- **`MOT002`**: Código cliente que desreferencia directamente campos del TDA (`tda->campo`) en lugar de invocar primitivas públicas.
