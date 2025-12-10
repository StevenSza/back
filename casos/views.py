from rest_framework.decorators import api_view
from rest_framework.response import Response
from django.db import connection
from datetime import datetime

# ==============================
# UTILIDADES
# ==============================

def single_result(query, params=[]):
    with connection.cursor() as cursor:
        cursor.execute(query, params)
        return cursor.fetchone()

def many_results(query, params=[]):
    with connection.cursor() as cursor:
        cursor.execute(query, params)
        return cursor.fetchall()

def execute(query, params=[]):
    with connection.cursor() as cursor:
        cursor.execute(query, params)

# ==============================
# API GESTIÓN CASO
# ==============================

@api_view(['GET'])
def buscar_cliente(request):
    """
    Buscar cliente por nombre y apellido.
    Parámetros: ?nombre=Luis&apellido=Martínez
    """
    nom = request.GET.get("nombre", "").strip()
    ape = request.GET.get("apellido", "").strip()

    if not (nom and ape):
        return Response({"error": "Debe ingresar nombre y apellido"}, status=400)

    cliente = single_result("""
        SELECT CODCLIENTE, NOMCLIENTE, APECLIENTE, NDOCUMENTO
        FROM CLIENTE
        WHERE UPPER(NOMCLIENTE) = UPPER(%s)
          AND UPPER(APECLIENTE) = UPPER(%s)
    """, [nom, ape])

    if not cliente:
        return Response({"error": "Cliente no encontrado"}, status=404)

    # Casos del cliente
    casos = many_results("""
        SELECT NOCASO, CODESPECIALIZACION, FCHINICIO, VALOR
        FROM CASO
        WHERE CODCLIENTE = %s
        ORDER BY NOCASO
    """, [cliente[0]])

    casos_cliente = [
        {"nocaso": c[0], "especializacion": c[1], "inicio": c[2], "valor": c[3]}
        for c in casos
    ]

    # Último caso activo
    caso_activo = single_result("""
        SELECT NOCASO, CODESPECIALIZACION, FCHINICIO, VALOR
        FROM CASO
        WHERE CODCLIENTE = %s AND FCHFIN IS NULL
        ORDER BY NOCASO DESC
    """, [cliente[0]])

    caso = None
    if caso_activo:
        caso = {
            "nocaso": caso_activo[0],
            "esp": caso_activo[1],
            "inicio": caso_activo[2],
            "valor": caso_activo[3],
            "es_nuevo": False
        }

    # Especializaciones
    esp_rows = many_results("""
        SELECT CODESPECIALIZACION, NOMESPECIALIZACION
        FROM ESPECIALIZACION
        ORDER BY CODESPECIALIZACION
    """)
    especializaciones = [{"codigo": e[0], "nombre": e[1]} for e in esp_rows]

    return Response({
        "cliente": {
            "cod": cliente[0],
            "nom": cliente[1],
            "ape": cliente[2],
            "doc": cliente[3]
        },
        "casos_cliente": casos_cliente,
        "caso_activo": caso,
        "especializaciones": especializaciones
    })


@api_view(['POST'])
def crear_caso(request):
    """
    Crear un nuevo caso para un cliente.
    Body JSON:
    {
        "codcliente": "C002",
        "nomcliente": "Luis",
        "apellcliente": "Martínez"
    }
    """
    codcli = request.data.get("codcliente", "").strip()
    nom = request.data.get("nomcliente", "").strip()
    ape = request.data.get("apellcliente", "").strip()

    if not codcli:
        return Response({"error": "Debe seleccionar un cliente"}, status=400)

    # Consecutivo funcional: max(nocaso) + 1
    ultimo = single_result("""
        SELECT NVL(MAX(NOCASO),0)
        FROM CASO
    """)[0]

    nuevo_consec = ultimo + 1

    return Response({
        "caso": {
            "nocaso": nuevo_consec,
            "es_nuevo": True
        },
        "cliente": {
            "cod": codcli,
            "nom": nom,
            "ape": ape
        }
    })


@api_view(['POST'])
def guardar_caso(request):
    """
    Guardar un nuevo caso en la base de datos.
    Body JSON:
    {
        "nocaso": 5,
        "codcliente": "C002",
        "especializacion": "E001",
        "valor": 1500
    }
    """
    nocaso = request.data.get("nocaso")
    codcli = request.data.get("codcliente")
    esp = request.data.get("especializacion")
    valor = request.data.get("valor")
    inicio = datetime.now().strftime("%Y-%m-%d")

    if not (nocaso and codcli and esp and valor):
        return Response({"error": "Todos los campos son obligatorios"}, status=400)

    execute("""
        INSERT INTO CASO (NOCASO, CODCLIENTE, CODESPECIALIZACION, FCHINICIO, FCHFIN, VALOR)
        VALUES (%s, %s, %s, TO_DATE(%s,'YYYY-MM-DD'), NULL, %s)
    """, [nocaso, codcli, esp, inicio, valor])

    return Response({"mensaje": "Caso creado correctamente"})


# ==============================
# API GESTIÓN EXPEDIENTE
# ==============================

@api_view(['GET'])
def listar_ciudades(request):
    """
    Listar ciudades para desplegable.
    """
    ciudades = many_results("""
        SELECT CODLUGAR, NOMLUGAR
        FROM LUGAR
        WHERE IDTIPOLUGAR = 'CII'
    """)
    return Response([{"cod": c[0], "nom": c[1]} for c in ciudades])


@api_view(['GET'])
def buscar_caso(request, nocaso):
    """
    Buscar caso por NOCASO y listar expedientes.
    """
    caso = single_result("""
        SELECT NOCASO, CODCLIENTE, CODESPECIALIZACION, FCHINICIO, FCHFIN
        FROM CASO
        WHERE NOCASO = %s
    """, [nocaso])

    if not caso:
        return Response({"error": "Caso no encontrado"}, status=404)

    # Expedientes del caso
    exps = many_results("""
        SELECT CONSECEXPE, IDTIPOCASO2, CODLUGAR, CEDULA, FCHETAPA
        FROM EXPEDIENTE
        WHERE NOCASO = %s
        ORDER BY CONSECEXPE
    """, [nocaso])

    lista_expedientes = [
        {"consec": e[0], "etapa": e[1], "lugar": e[2], "abogado": e[3], "fecha": e[4]}
        for e in exps
    ]

    return Response({
        "caso": {
            "nocaso": caso[0],
            "cliente": caso[1],
            "esp": caso[2],
            "inicio": caso[3],
            "fin": caso[4]
        },
        "lista_expedientes": lista_expedientes
    })


@api_view(['POST'])
def crear_expediente(request):
    """
    Crear nuevo expediente.
    Body JSON:
    {
        "nocaso": 5,
        "esp": "E001"
    }
    """
    nocaso = request.data.get("nocaso")
    esp = request.data.get("esp")

    if not (nocaso and esp):
        return Response({"error": "Datos incompletos"}, status=400)

    # Consecutivo
    ultimo = single_result("""
        SELECT NVL(MAX(CONSECEXPE),0)
        FROM EXPEDIENTE
        WHERE NOCASO = %s
    """, [nocaso])[0]
    nuevo = ultimo + 1

    det_etapa = single_result("""
        SELECT IDTIPOCASO2, CODETAPA
        FROM ESPECIA_ETAPA
        WHERE CODESPECIALIZACION = %s AND IDTIPOCASO2 = 1
    """, [esp])

    idetapa = det_etapa[0] if det_etapa else None

    # Abogados de la especialidad
    abs_ = many_results("""
        SELECT A.CEDULA, A.NOMABOGADO, A.APEABOGADO
        FROM ABOGADO A
        JOIN ABOGADO_ESPECIALIZACION AE
            ON A.CEDULA = AE.CEDULA
        WHERE AE.CODESPECIALIZACION = %s
    """, [esp])

    abogados = [{"ced": a[0], "nom": f"{a[1]} {a[2]}"} for a in abs_]

    return Response({
        "expediente": {
            "consec": nuevo,
            "idetapa": idetapa,
            "fecha": datetime.now().strftime("%Y-%m-%d")
        },
        "abogados": abogados
    })


@api_view(['POST'])
def guardar_expediente(request):
    """
    Guardar expediente en la BD.
    Body JSON:
    {
        "nocaso": 5,
        "consec": 2,
        "idetapa": 1,
        "codlugar": "L001",
        "cedula": "90005"
    }
    """
    nocaso = request.data.get("nocaso")
    consec = request.data.get("consec")
    idetapa = request.data.get("idetapa")
    codlugar = request.data.get("codlugar")
    cedula = request.data.get("cedula")

    if not (nocaso and consec and idetapa and codlugar and cedula):
        return Response({"error": "Todos los campos son obligatorios"}, status=400)

    execute("""
        INSERT INTO EXPEDIENTE
        (NOCASO, CONSECEXPE, CODESPECIALIZACION, IDTIPOCASO2, CODLUGAR, CEDULA, FCHETAPA)
        VALUES (%s, %s,
               (SELECT CODESPECIALIZACION FROM CASO WHERE NOCASO=%s),
               %s, %s, %s, SYSDATE)
    """, [nocaso, consec, nocaso, idetapa, codlugar, cedula])

    return Response({"mensaje": "Etapa guardada correctamente"})
