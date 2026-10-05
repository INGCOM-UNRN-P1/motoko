#include <stdlib.h>
#include "pila.h"
struct pila { int datos[10]; int tope; char *nombre; };
Pila *pila_crear(void) { return calloc(1, sizeof(Pila)); }
int *pila_tope(Pila *p) { return &p->tope; }
char *pila_nombre(Pila *p) { return p->nombre; }
const char *pila_nombre_lectura(Pila *p) { return p->nombre; }
int pila_cantidad(const Pila *p) { return p->tope; }
static int *interna(Pila *p) { return p->datos; }
