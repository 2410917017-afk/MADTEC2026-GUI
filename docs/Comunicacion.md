# Explicación y fundamentos sobre la comunicación industrial utilizada en el proyecto

PARTE 1 — Configuración en RobotStudio
1. Verificar la opción PROFINET instalada
Desde RobotStudio online:
Controller → Properties → Installed Options
Busca 888-2. Si no está, no puedes continuar sin comprarla a ABB.
2. Configurar IP del robot
Desde el FlexPendant:
ABB Menu → Control Panel → Configuration → 
Topics: Communication → IP Setting
Configura:
IP Address:  192.168.0.2
Subnet Mask: 255.255.255.0
Gateway:     192.168.0.1
El S7-1200 en este ejemplo estaría en 192.168.0.1. Usa el rango que ya tengan definido.
3. Configurar el dispositivo PROFINET
En RobotStudio:
Controller → Configuration → I/O System
Haz doble clic en DeviceNet o busca PROFINET — verás una entrada de tipo PNIO_DEVICE. Configura:
Name:            PN_Device
PROFINET Name:   abb-robot-1        ← anota esto, lo usarás en TIA
Address:         192.168.0.2
Input Size:      2                  ← bytes que el PLC envía al robot
Output Size:     2                  ← bytes que el robot envía al PLC

Por qué 2 bytes: Con 2 bytes tienes 16 bits por dirección, suficientes para tu ciclo de soldadura y room para crecer.

4. Crear las señales y mapearlas a PROFINET
Aún en I/O System, crea las señales individuales. Cada una necesita:

Name: nombre que usarás en RAPID
Type: DI o DO
Device: el PN_Device que creaste
Device Mapping: el bit exacto dentro del bloque

Señal           Tipo  Device      Mapping
──────────────────────────────────────────────
diStartCycle    DI    PN_Device   0           ← bit 0 del byte de entrada
diWeldDone      DI    PN_Device   1           ← bit 1 del byte de entrada
doInPosition    DO    PN_Device   0           ← bit 0 del byte de salida
doRobotHome     DO    PN_Device   1           ← bit 1 del byte de salida
doFault         DO    PN_Device   2           ← bit 2, útil para diagnóstico
⚠️ Después de guardar la configuración, reinicia el controlador. Los cambios de I/O en IRC5 no aplican sin reinicio.

PARTE 2 — Configuración en TIA Portal
1. Instalar el GSDML
Opciones → Administrar archivos de descripción 
de dispositivos (GSD) → Origen: [carpeta con el .xml] 
→ seleccionar el archivo ABB → Instalar
Cierra y vuelve a abrir el proyecto para que TIA Portal lo reconozca en el catálogo.
2. Configurar la IP del S7-1200
En la vista de dispositivos, clic en el PLC:
Propiedades → Interfaz PROFINET → Dirección IP
IP:      192.168.0.1
Máscara: 255.255.255.0
3. Agregar el robot a la red
Vista de red → catálogo de hardware → 
buscar "ABB IRC5" → arrastrar al área de red
Conecta el robot al PLC con el cable PROFINET virtual (clic y arrastra entre los puertos).
4. Asignar nombre PROFINET al robot
Clic derecho sobre el ícono del robot → Asignar nombre de dispositivo PROFINET:
Nombre: abb-robot-1    ← exactamente igual al configurado en RobotStudio

Este paso también se hace físicamente la primera vez. Con TIA Portal y el robot conectados a la misma red, en ese mismo diálogo puedes hacer clic en Actualizar lista para que detecte el robot y le asigne el nombre.

5. Configurar los módulos de I/O del robot
Haz doble clic en el robot → pestaña Vista de dispositivos. En los slots verás opciones de módulos. Debes añadir un módulo que coincida con lo configurado en RobotStudio:
Slot 1: Input module  → 2 bytes   (lo que el robot manda al PLC)
Slot 2: Output module → 2 bytes   (lo que el PLC manda al robot)
TIA Portal asignará las direcciones automáticamente, algo así:
%IB100, %IB101   → datos que vienen del robot  
%QB100, %QB101   → datos que van hacia el robot
6. Verificar el cruce de señales
Este es el punto que más confunde. Desde el punto de vista de TIA:
TIA Portal                          Robot ABB
──────────────────────────────────────────────
%Q100.0 (salida del PLC) ────────►  diStartCycle  (entrada del robot)
%Q100.1 (salida del PLC) ────────►  diWeldDone    (entrada del robot)
%I100.0 (entrada al PLC) ◄────────  doInPosition  (salida del robot)
%I100.1 (entrada al PLC) ◄────────  doRobotHome   (salida del robot)

PARTE 3 — Verificación de la comunicación
Checklist antes de compilar y cargar

 Robot y PLC en el mismo segmento de red (192.168.0.x)
 Nombre PROFINET idéntico en ambos lados (abb-robot-1)
 Tamaño de módulos coincide (2 bytes entrada, 2 bytes salida en ambos lados)
 Controlador ABB reiniciado después de configurar I/O
 GSDML instalado en TIA Portal

Cómo diagnosticar si algo falla
En el FlexPendant:
ABB Menu → I/O → View all signals
Si la comunicación está activa, las señales responderán. Si el dispositivo PROFINET aparece como Disconnected, el problema es de red (nombre o IP).
En TIA Portal, online con el PLC:
Online → Diagnóstico → Topología de dispositivos
El robot debe aparecer en verde. Si aparece en rojo o no aparece, revisa el nombre PROFINET y que físicamente estén en el mismo switch.

El programa RAPID completo para tu ciclo
rapidMODULE WeldModule

    CONST robtarget pHome := [...];    ! capturar con robot real
    CONST robtarget pWeldPos := [...]; ! capturar con robot real
    
    VAR bool bTimeout := FALSE;

    PROC main()
        MoveJ pHome, v500, fine, tWeldGun;
        WHILE TRUE DO
            WeldCycle;
        ENDWHILE
    ENDPROC

    PROC WeldCycle()
        ! 1. Esperar orden del PLC
        WaitDI diStartCycle, 1 \MaxTime:=60 \TimeFlag:=bTimeout;
        IF bTimeout THEN
            Set doFault;
            STOP;
        ENDIF
        
        ! 2. Ir a posición de soldadura
        Reset doRobotHome;
        MoveJ pWeldPos, v300, fine, tWeldGun;
        
        ! 3. Avisar al PLC que estamos en posición
        Set doInPosition;
        
        ! 4. Esperar que el PLC termine la soldadura
        WaitDI diWeldDone, 1 \MaxTime:=15 \TimeFlag:=bTimeout;
        Reset doInPosition;
        IF bTimeout THEN
            Set doFault;
            STOP;
        ENDIF
        
        ! 5. Volver a HOME y avisar
        MoveJ pHome, v500, fine, tWeldGun;
        Set doRobotHome;
        
    ENDPROC

ENDMODULE
