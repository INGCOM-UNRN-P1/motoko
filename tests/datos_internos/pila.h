#ifndef PILA_H
#define PILA_H
typedef struct pila Pila;
Pila *pila_crear(void);
int *pila_tope(Pila *p);
char *pila_nombre(Pila *p);
const char *pila_nombre_lectura(Pila *p);
int pila_cantidad(const Pila *p);
#endif
