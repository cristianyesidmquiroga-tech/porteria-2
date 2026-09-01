# Manual de Usuario — Fichas de Formación (solo rol Admin)

Las fichas existen para que el **programa** y la **fecha de finalización** se
registren **una sola vez por ficha**, en lugar de que cada aprendiz los
escriba en su perfil (antes, dos aprendices de la misma ficha podían salir
con datos distintos en el carnet).

## Cómo se conecta con el resto del sistema

- El aprendiz **elige su ficha de una lista** en "Mi Perfil" y **hereda** de
  ella el programa y la fecha de finalización que se imprimen en su carnet.
  No puede teclear la fecha por su cuenta.
- Al crear o importar usuarios, si el número de ficha escrito ya existe en
  esta pantalla, el aprendiz queda enlazado y hereda los datos
  automáticamente. Si no existe, se guarda solo el texto y su carnet sale
  **sin fecha** hasta que la ficha se registre (el sistema nunca inventa una
  ficha a partir de un Excel).

## Pantalla

Menú lateral → **"Fichas de Formación"**. Lista todas las fichas (activas
primero) con **cuántos aprendices cuelgan de cada una** — para dimensionar el
efecto de editarla antes de tocarla.

### Crear
- **Número:** 4 a 12 dígitos, único.
- **Programa:** obligatorio, hasta 150 caracteres.
- **Fecha de finalización:** opcional (es lo que se imprime en el carnet).

### Editar
Cambiar el programa o la fecha de una ficha **cambia de inmediato lo que sale
en el carnet de todos sus aprendices**. Por eso la pantalla es exclusiva del
rol Admin.

### Archivar / reactivar
Una ficha que terminó **no se borra** (sus aprendices la siguen
referenciando): se **archiva**, con lo que deja de aparecer en el selector
del perfil. Quien ya la tenía elegida la conserva. Se puede reactivar.

## Preguntas frecuentes

**Un aprendiz dice que su ficha no aparece en el selector.** O no está creada
aquí, o está archivada. Créela/reactívela y pídale que la elija en su perfil.

**¿Por qué el carnet de un aprendiz sale sin fecha de finalización?** Su
ficha no está registrada aquí (tiene solo el texto histórico) o la ficha no
tiene fecha cargada.

**¿Puedo borrar una ficha creada por error?** No hay borrado; corrija sus
datos o archívela.

---

**Institución:** SENA — Centro de Gestión Agroempresarial del Oriente
**Última revisión contra el código:** septiembre de 2026
