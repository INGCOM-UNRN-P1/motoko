---
title: "Manual de Referencia: motoko"
subtitle: "Motoko — Verificador de Encapsulamiento Estricto, Opacidad de Structs e Invariantes de TDA"
author: "Cátedra de Algoritmos y Programación"
date: "2026-08-31"
---

(manual-motoko)=
# Motoko — Verificador de Encapsulamiento Estricto, Opacidad de Structs e Invariantes de TDA

````{abstract}
**Rol en el ecosistema:** Auditoría de modularidad en C para garantizar que los tipos de datos abstractos (TDAs) mantengan sus estructuras opacas (incomplete types en .h) y ningún código cliente acceda a miembros privados.
````

---

(manual-motoko-proposito)=
## 1. Propósito y Filosofía Pedagógica

La herramienta **`motoko`** forma parte del ecosistema oficial de software de la cátedra. Su diseño sigue principios pedagógicos rigurosos:

1. **Evidencia Técnica Directa**: Todo diagnóstico se fundamenta en la norma ISO C (C11/C23), en el modelo de memoria del sistema o en convenciones arquitectónicas formales.
2. **Acción Correctiva Concreta**: Cada advertencia incluye la prescripción técnica inmediata para resolver el defecto sin recurrir a conjeturas.
3. **Autonomía del Estudiante**: Facilita la autoevaluación local antes de la entrega final del trabajo práctico.
4. **Objetividad Docente**: Estandariza la corrección automática eliminando discrepancias subjetivas en la evaluación.

---

(manual-motoko-instalacion)=
## 2. Instalación y Diagnóstico del Entorno

````{important}
Asegurate de contar con el compilador GCC/Clang y las librerías del sistema instaladas antes de ejecutar `motoko`.
````

Para comprobar el estado de salud de tu entorno de trabajo y las dependencias auxiliares:

````{code-block} bash
# Comprobación de dependencias del sistema
motoko doctor
````

Si se detecta la falta de alguna utilidad (como `gdb`, `valgrind`, `clang-format` o `typst`), el comando indicará el paquete exacto a instalar según tu distribución GNU/Linux o entorno MSYS2.

---

(manual-motoko-comandos)=
## 3. Referencia Completa de Comandos CLI

A continuación se detallan los subcomandos principales disponibles en `motoko`:

| Sintaxis del Comando | Descripción y Efecto |
| :--- | :--- |
| `motoko check include/ src/` | Verifica que los clientes no rompan la encapsulación de los TDAs. |
| `motoko opacify include/lista.h` | Convierte una struct pública en un tipo opaco forward-declared. |
| `motoko invariants src/tda_pila.c` | Audita que las funciones públicas preserven los invariantes del TDA. |
| `motoko doctor` | Comprueba el analizador AST de C. |

````{tip}
Podés agregar el flag `--json` a la mayoría de los comandos para exportar resultados en formato estructurado o `--md` para generar reportes Markdown para el informe de entrega.
````

---

(manual-motoko-tutorial)=
## 4. Tutorial Paso a Paso con Ejemplos Reales

### Caso de Estudio

Considerá el siguiente fragmento de código representativo:

````{code-block} c
:linenos:
// include/lista.h (Encapsulado estricto con Motoko)
typedef struct lista t_lista; // Tipo opaco: cliente NO ve los campos

t_lista* lista_crear(void);
void lista_destruir(t_lista *lista);

// src/lista.c (Implementación privada)
struct lista {
    struct nodo *primero;
    size_t cantidad;
};
````

### Ejecución de la Herramienta

Ejecutá el análisis desde tu terminal:

````{code-block} bash
motoko check include/ src/
````

### Salida Obtenida en Consola

````{code-block} text
[!] MOTOKO ENCAPSULATION VIOLATION en src/main.c:15:10:
    Acceso prohibido al miembro privado 'lista->cantidad'.
    Los campos internos de 'struct lista' son opacos para el código cliente.
    Sugerencia: Utilizá la función pública 'size_t lista_cantidad(const t_lista *l);'.
````

````{note}
Prestá atención a la explicación pedagógica generada: la herramienta no solo señala la línea del problema, sino que explica la causa raíz y el impacto en memoria o arquitectura.
````

---

(manual-motoko-ejercicios)=
## 5. Ejercicios Prácticos y Desafíos

Practicá el uso avanzado de **`motoko`** resolviendo los siguientes ejercicios:

````{exercise} Desafío 1: Detección de Violaciones de Encapsulamiento
Verificar que `src/cliente.c` solo interactúe mediante la API pública del TDA.

**Instrucción de ejecución:**
```bash
motoko check include/ src/
```
````

````{solution} Desafío 1
```bash
motoko check include/ src/
# Verificá que la operación concluya exitosamente con código de salida 0.
```
````

````{exercise} Desafío 2: Opacificación de Headers de Cátedra
Ocultar la definición interna de nodos en `include/arbol.h`.

**Instrucción de ejecución:**
```bash
motoko opacify include/arbol.h
```
````

````{solution} Desafío 2
```bash
motoko opacify include/arbol.h
# Revisá el archivo generado o el informe en terminal para confirmar la resolución del problema.
```
````

````{exercise} Desafío 3: Auditoría de Invariantes de Estado
Asegurar que `pila_desapilar()` actualice siempre el tope y el contador.

**Instrucción de ejecución:**
```bash
motoko invariants src/pila.c
```
````

````{solution} Desafío 3
```bash
motoko invariants src/pila.c
# Comprobá que la salida confirme la ausencia de advertencias o errores pendientes.
```
````

---

(manual-motoko-makefile)=
## 6. Integración en el Flujo de Trabajo y Makefile

Para incorporar `motoko` de forma automática a tu flujo de desarrollo, agregá la siguiente regla en el `Makefile` de tu proyecto:

````{code-block} makefile
check-motoko:
	@echo "=== Ejecutando verificación con motoko ==="
	motoko check src/ include/

.PHONY: check-motoko
````

Ejecutá `make check-motoko` antes de cada commit para asegurar que tu código conserve el estado de aprobación.
