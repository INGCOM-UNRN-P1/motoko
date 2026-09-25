# Manual de Uso y Referencia Técnica: motoko

> **MOTOKO** — Verificador de encapsulamiento estricto y opacidad de Tipos Abstractos de Datos (TDAs) en C
> **Versión:** `0.1.0` · **CLI principal:** `motoko` · **Plugin Ripley:** `tda_encapsulation`

---

## 1. Arquitectura y Propósito Pedagógico

`motoko` forma parte del ecosistema de herramientas de la cátedra de Programación 1 (UNRN). Su objetivo central es resolver de forma modular, determinista y automatizada las tareas asociadas a su dominio específico dentro del ciclo de desarrollo, evaluación y aprendizaje de software en C.

### Alcance Funcional (Qué cubre)
- Verificación estática de encapsulamiento y tipos opacos en Tipos de Datos Abstractos (TDAs) de C.
- Regla `MOT001`: Verificación de que la definición completa de estructuras de datos (`struct`) resida exclusivamente en archivos de implementación (`.c`), manteniendo únicamente declaraciones incompletas (`typedef struct tda tda_t;`) en archivos de cabecera (`.h`).
- Regla `MOT002`: Prohibición estricta de desreferencia directa de campos privados en archivos cliente.
- Manejo defensivo y resiliente de entregas y carpetas de estudiantes sin archivos `.h`.

### Límites de Responsabilidad y Delegación (Qué no cubre)
- Linter de estilo y formato de código (delegado a `gaff`).
- Demostración formal de contratos matemáticos del TDA (delegado a `callahan`).
- Verificación de fugas de memoria o memory leaks en el TDA (delegado a `nostromo` / `tetsuo`).

### Principios de Diseño
- **Enfoque Pedagógico:** Diagnósticos y mensajes en español rioplatense orientados a facilitar la comprensión de errores conceptuales.
- **Salida Estructurada Dual:** Soporte nativo para visualización enriquecida en terminal (Rich) y salida parseable para orquestadores (`--json`).
- **Integración Contractual:** Capacidad de emitir secciones de reporte para `dredd` (`dredd-section`) y actuar como satélite orquestado por `ripley`.
- **Idempotencia y Robustez:** Validación de precondiciones y comandos de autodiagnóstico (`doctor`) para verificación del entorno.

---

## 2. Instalación y Requisitos

### Requisitos del Sistema
- **Python:** `>= 3.10` (recomendado Python 3.11 o 3.12).
- **Gestor de paquetes:** [`uv`](https://github.com/astral-sh/uv) (entorno estándar de cátedra).
- **Toolchain C (si aplica):** GCC / Clang, Make, GDB y bibliotecas estándar de desarrollo.

### Instalación en el Entorno de Usuario
Para instalar la herramienta de forma global y aislada en el sistema mediante `uv tool`:
```bash
uv tool install --editable /home/mrtin/dev/tools/motoko
```

### Verificación de Instalación
Ejecutá el comando `doctor` para constatar que todas las dependencias y binarios requeridos estén presentes y operativos:
```bash
motoko doctor
```

---

## 3. Guía Integral de Comandos (CLI)

| Comando | Descripción Breve |
| :--- | :--- |
| [`motoko audit-all`](#auditall) | Verifica que los TDAs sean opacos y no sufran accesos directos a sus campos internos. |
| [`motoko check`](#check) | Verifica que los TDAs sean opacos y no sufran accesos directos a sus campos internos. |
| [`motoko verify`](#verify) | Verifica que los TDAs sean opacos y no sufran accesos directos a sus campos internos. |
| [`motoko report`](#report) | Genera directamente la sección de reporte Markdown de MOTOKO para Dredd. |
| [`motoko doctor`](#doctor) | Verifica el estado del entorno de auditoría de TDAs MOTOKO (Tree-Sitter C, Python, GCC). |

### `motoko audit-all`

Verifica que los TDAs sean opacos y no sufran accesos directos a sus campos internos.

Con un directorio como argumento audita todos los TDAs del proyecto (`audit-all`).

#### Argumentos
| Argumento | Tipo | Descripción |
| :--- | :--- | :--- |
| `headers` | `List[pathlib._local.Path]` | Archivos de cabecera (.h) o directorios a analizar |

#### Opciones y Banderas
| Opción / Banderas | Tipo | Por Defecto | Descripción |
| :--- | :--- | :--- | :--- |
| `--client`, `-c` | `List[pathlib._local.Path]` | `[]` | Archivos cliente (.c) que usan el TDA |
| `--impl`, `-i` | `List[pathlib._local.Path]` | `[]` | Archivos de implementación (.c) del TDA |
| `--json` | `<class 'bool'>` | `False` | Emitir salida en formato JSON estructurado |
| `--md`, `--output-md` | `Optional[pathlib._local.Path]` | `None` | Generar sección de reporte en formato Markdown para fusión en Dredd. |

#### Ejemplo de Invocación
```bash
motoko audit-all <headers>
```

### `motoko check`

Verifica que los TDAs sean opacos y no sufran accesos directos a sus campos internos.

Con un directorio como argumento audita todos los TDAs del proyecto (`audit-all`).

#### Argumentos
| Argumento | Tipo | Descripción |
| :--- | :--- | :--- |
| `headers` | `List[pathlib._local.Path]` | Archivos de cabecera (.h) o directorios a analizar |

#### Opciones y Banderas
| Opción / Banderas | Tipo | Por Defecto | Descripción |
| :--- | :--- | :--- | :--- |
| `--client`, `-c` | `List[pathlib._local.Path]` | `[]` | Archivos cliente (.c) que usan el TDA |
| `--impl`, `-i` | `List[pathlib._local.Path]` | `[]` | Archivos de implementación (.c) del TDA |
| `--json` | `<class 'bool'>` | `False` | Emitir salida en formato JSON estructurado |
| `--md`, `--output-md` | `Optional[pathlib._local.Path]` | `None` | Generar sección de reporte en formato Markdown para fusión en Dredd. |

#### Ejemplo de Invocación
```bash
motoko check <headers>
```

### `motoko verify`

Verifica que los TDAs sean opacos y no sufran accesos directos a sus campos internos.

Con un directorio como argumento audita todos los TDAs del proyecto (`audit-all`).

#### Argumentos
| Argumento | Tipo | Descripción |
| :--- | :--- | :--- |
| `headers` | `List[pathlib._local.Path]` | Archivos de cabecera (.h) o directorios a analizar |

#### Opciones y Banderas
| Opción / Banderas | Tipo | Por Defecto | Descripción |
| :--- | :--- | :--- | :--- |
| `--client`, `-c` | `List[pathlib._local.Path]` | `[]` | Archivos cliente (.c) que usan el TDA |
| `--impl`, `-i` | `List[pathlib._local.Path]` | `[]` | Archivos de implementación (.c) del TDA |
| `--json` | `<class 'bool'>` | `False` | Emitir salida en formato JSON estructurado |
| `--md`, `--output-md` | `Optional[pathlib._local.Path]` | `None` | Generar sección de reporte en formato Markdown para fusión en Dredd. |

#### Ejemplo de Invocación
```bash
motoko verify <headers>
```

### `motoko report`

Genera directamente la sección de reporte Markdown de MOTOKO para Dredd.

#### Argumentos
| Argumento | Tipo | Descripción |
| :--- | :--- | :--- |
| `headers` | `List[pathlib._local.Path]` | Archivos de cabecera (.h) que definen TDAs |

#### Opciones y Banderas
| Opción / Banderas | Tipo | Por Defecto | Descripción |
| :--- | :--- | :--- | :--- |
| `--output`, `-o` | `Optional[pathlib._local.Path]` | `None` | Ruta de destino del archivo Markdown. |
| `--client`, `-c` | `List[pathlib._local.Path]` | `[]` | Archivos cliente (.c) que usan el TDA |
| `--impl`, `-i` | `List[pathlib._local.Path]` | `[]` | Archivos de implementación (.c) del TDA |

#### Ejemplo de Invocación
```bash
motoko report <headers>
```

### `motoko doctor`

Verifica el estado del entorno de auditoría de TDAs MOTOKO (Tree-Sitter C, Python, GCC).

#### Opciones y Banderas
| Opción / Banderas | Tipo | Por Defecto | Descripción |
| :--- | :--- | :--- | :--- |
| `--json` | `<class 'bool'>` | `False` | Emitir diagnóstico en formato JSON estructurado. |

#### Ejemplo de Invocación
```bash
motoko doctor
```

---

## 4. Formatos de Salida e Integración con el Ecosistema

### Modo Interactivo / Terminal (Rich)
Por defecto, la herramienta renderiza paneles, árboles y tablas estilizadas para facilitar la lectura del estudiante y docente en terminales modernas con soporte ANSI.

### Modo Estructurado JSON (`--json`)
Para integración con pipelines de CI/CD, scripts de automatización u orquestadores externos, la opción `--json` emite un documento JSON estricto por la salida estándar (`stdout`), dirigiendo cualquier mensaje de logging a `stderr`:
```bash
motoko audit-all --json
```

### Integración con Dredd (`dredd-section`)
Cuando la herramienta genera reportes de evaluación para entregas de alumnos, produce una sección Markdown estandarizada conforme al contrato de integración de Dredd (v1.0.0):
```markdown
<!-- dredd-section: motoko, tool=motoko, version=0.1.0, status=ok -->
```
Este encabezado garantiza la agregación determinista de los hallazgos en la rúbrica docente.

### Integración con Ripley
`motoko` está registrada en el catálogo de plugins satélites de Ripley (`SATELLITE_CATALOG`). Puede invocarse directamente a través del motor de evaluación de Ripley configurando el análisis en `ripley.toml`.

---

## 5. Diagnóstico y Códigos de Salida

### Códigos de Retorno (`exit code`)
| Código | Significado |
| :---: | :--- |
| `0` | Ejecución exitosa sin hallazgos críticos ni errores de sintaxis. |
| `1` | Hallazgos pedagógicos detectados, infracción de reglas o advertencias activas. |
| `2` | Error de sintaxis en argumentos CLI o archivo fuente no encontrado. |
| `>2` | Error no recuperable del sistema, fallo de memoria o excepción interna. |

### Diagnóstico del Entorno (`doctor`)
Ante comportamientos inesperados, verificá el estado operativo con:
```bash
motoko doctor
```
Comprueba la presencia de las dependencias requeridas y la integridad de los componentes del paquete.