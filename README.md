# MOTOKO — Verificador de Encapsulamiento y Opacidad de TDAs en C

**MOTOKO** analiza archivos de cabecera e implementaciones en C para asegurar el ocultamiento de información y encapsulamiento estricto de Tipos Abstractos de Datos (TDAs), detectando accesos directos a campos internos desde código cliente.

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
