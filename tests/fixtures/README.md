# Fotos de referencia para las pruebas

Algunas pruebas de `test_almacenamiento.py` comprueban que una foto **real** de
una persona se acepta al subirla. No se puede verificar eso con una imagen
dibujada por código: el detector (YuNet) distingue fotografías de ilustraciones
a propósito, así que una cara dibujada con elipses la rechaza, y hace bien.

Tampoco se puede versionar una foto real aquí: sería un dato biométrico de una
persona identificable dentro del repositorio, justo lo que se eliminó del
historial. Por eso esta carpeta está en `.gitignore` salvo este README.

## Cómo activar esas pruebas

Copia una o varias fotos de rostro en esta carpeta, con estos nombres:

| Archivo | Qué debe mostrar |
|---|---|
| `rostro.jpg` | Un retrato frontal, cara despejada |
| `rostro_gafas.jpg` | Un retrato de una persona **con gafas** |
| `rostro_dos_personas.jpg` | Dos personas en la misma foto (debe rechazarse) |

Sin esos archivos, las pruebas que los necesitan se **saltan** con un mensaje
que lo explica; el resto de la suite corre igual.

Usa fotos de las que tengas permiso. Al terminar puedes borrarlas: nada las
referencia fuera de las pruebas.

## Por qué importa `rostro_gafas.jpg`

Es un requisito explícito del sistema: las personas con gafas deben poder subir
su foto, porque en portería el celador compara la foto con quien tiene delante y
necesita reconocerlo. Si un cambio en la detección facial empezara a rechazar a
quien lleva gafas, esa persona se quedaría sin carnet digital y sin poder entrar
al centro. Esta prueba existe para que ese fallo salte aquí y no en la puerta.
