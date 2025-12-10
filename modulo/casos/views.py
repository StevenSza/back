from rest_framework.decorators import api_view
from rest_framework.response import Response
from django.db import connection
from datetime import datetime

# ============================================================
# UTILIDADES
# ============================================================

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

# ============================================================
# CASOS
# ============================================================

@api_view(['GET'])
def get_especializaciones(request):
    rows = many_results("""
        SELECT CODESPECIALIZACION, NOMESPECIALIZACION
        FROM ESPECIALIZACION
        ORDER BY CODESPECIALIZACION
    """)
    return Response([{"codigo": r[0], "nombre": r[1]} for r in rows])

@api_view(['POST'])
def buscar_cliente(request):
    """
    Buscar cliente y todos sus casos enviando JSON:
    {
        "nomcliente": "Nombre",
        "apellcliente": "Apellido"
    }
    """
    try:
        nom = request.data.get("nomcliente", "").strip()
        ape = request.data.get("apellcliente", "").strip()

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

        codcliente = cliente[0]

        casos = many_results("""
            SELECT NOCASO, CODESPECIALIZACION, FCHINICIO, FCHFIN, VALOR
            FROM CASO
            WHERE CODCLIENTE = %s
            ORDER BY NOCASO
        """, [codcliente])

        casos_cliente = [
            {
                "nocaso": c[0],
                "especializacion": c[1],
                "inicio": c[2].strftime("%Y-%m-%d") if c[2] else "",
                "fin": c[3].strftime("%Y-%m-%d") if c[3] else None,
                "valor": c[4],
                "activo": (c[3] is None)
            } for c in casos
        ]

        caso_activo = next((c for c in casos_cliente if c["activo"]), None)
        if caso_activo:
            caso_activo = {
                "nocaso": caso_activo["nocaso"],
                "esp": caso_activo["especializacion"],
                "inicio": caso_activo["inicio"],
                "valor": caso_activo["valor"],
                "es_nuevo": False
            }

        return Response({
            "cliente": {
                "cod": codcliente,
                "nom": cliente[1],
                "ape": cliente[2],
                "doc": cliente[3]
            },
            "casos_cliente": casos_cliente,
            "caso_activo": caso_activo
        })

    except Exception as e:
        import traceback
        print(traceback.format_exc())
        return Response({"error": "Ocurrió un error al buscar el cliente"}, status=500)

@api_view(['POST'])
def crear_caso(request):
    codcli = request.data.get("codcliente", "").strip()

    if not codcli:
        return Response({"error": "Debe seleccionar un cliente"}, status=400)

    ultimo = single_result("SELECT NVL(MAX(NOCASO),0) FROM CASO")[0]
    nuevo_consec = ultimo + 1

    return Response({
        "nocaso": nuevo_consec,
        "es_nuevo": True,
        "cliente": {
            "cod": codcli,
            "nom": request.data.get("nomcliente", ""),
            "ape": request.data.get("apellcliente", ""),
            "doc": request.data.get("ndocumento", "")
        }
    })

@api_view(['POST'])
def guardar_caso(request):
    nocaso = request.data.get("nocaso")
    codcli = request.data.get("codcliente")
    esp = request.data.get("especializacion")
    valor = request.data.get("valor")
    inicio = datetime.now().strftime("%Y-%m-%d")

    if not (nocaso and codcli and esp and valor):
        return Response({"error": "Todos los campos son obligatorios"}, status=400)

    try:
        nocaso = int(nocaso)
        execute("""
            INSERT INTO CASO (NOCASO, CODCLIENTE, CODESPECIALIZACION, FCHINICIO, FCHFIN, VALOR)
            VALUES (%s, %s, %s, TO_DATE(%s,'YYYY-MM-DD'), NULL, %s)
        """, [nocaso, codcli, esp, inicio, valor])
    except Exception as e:
        import traceback
        print(traceback.format_exc())
        return Response({"error": f"Error al guardar el caso: {str(e)}"}, status=500)

    return Response({"mensaje": "Caso creado correctamente"})

# ============================================================
# EXPEDIENTES
# ============================================================

@api_view(['GET'])
def buscar_caso(request, nocaso):
    caso = single_result("""
        SELECT NOCASO, CODCLIENTE, CODESPECIALIZACION, FCHINICIO, FCHFIN
        FROM CASO
        WHERE NOCASO = %s
    """, [nocaso])

    if not caso:
        return Response({"error": "Caso no encontrado"}, status=404)

    exps = many_results("""
        SELECT CONSECEXPE, IDTIPOCASO2, CODLUGAR, CEDULA, FCHETAPA
        FROM EXPEDIENTE
        WHERE NOCASO = %s
        ORDER BY CONSECEXPE
    """, [nocaso])

    lista_expedientes = [
        {"consec": e[0], "etapa": e[1], "lugar": e[2], "abogado": e[3], "fecha": e[4].strftime("%Y-%m-%d") if e[4] else ""}
        for e in exps
    ]

    return Response({
        "caso": {
            "nocaso": caso[0],
            "cliente": caso[1],
            "esp": caso[2],
            "inicio": caso[3].strftime("%Y-%m-%d") if caso[3] else "",
            "fin": caso[4].strftime("%Y-%m-%d") if caso[4] else None
        },
        "lista_expedientes": lista_expedientes
    })

@api_view(['GET'])
def get_ciudades(request):
    ciudades = many_results("""
        SELECT CODLUGAR, NOMLUGAR
        FROM LUGAR
        WHERE IDTIPOLUGAR = 'CII'
    """)
    return Response([{"cod": c[0], "nom": c[1]} for c in ciudades])

@api_view(['GET'])
def get_entidades(request):
    ciudad = request.GET.get("ciudad")
    
    if not ciudad:
        return Response([])
    
    entidades = many_results("""
        SELECT CODLUGAR, NOMLUGAR
        FROM LUGAR
        WHERE IDTIPOLUGAR = 'ENT' AND CODLUGAR_PADRE = %s
    """, [ciudad])
    
    return Response([{"cod": e[0], "nom": e[1]} for e in entidades])

@api_view(['GET'])
def get_abogados(request):
    esp = request.GET.get("esp")
    query = """
        SELECT A.CEDULA, A.NOMABOGADO, A.APEABOGADO
        FROM ABOGADO A
    """
    params = []
    if esp:
        query += " JOIN ABOGADO_ESPECIALIZACION AE ON A.CEDULA = AE.CEDULA WHERE AE.CODESPECIALIZACION = %s"
        params = [esp]
    abogados = many_results(query, params)
    return Response([{"ced": a[0], "nom": f"{a[1]} {a[2]}"} for a in abogados])

@api_view(['POST'])
def crear_expediente(request):
    nocaso = request.data.get("nocaso")
    esp = request.data.get("esp")

    if not (nocaso and esp):
        return Response({"error": "Datos incompletos"}, status=400)

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

    abs_ = many_results("""
        SELECT A.CEDULA, A.NOMABOGADO, A.APEABOGADO
        FROM ABOGADO A
        JOIN ABOGADO_ESPECIALIZACION AE
            ON A.CEDULA = AE.CEDULA
        WHERE AE.CODESPECIALIZACION = %s
    """, [esp])
    abogados = [{"ced": a[0], "nom": f"{a[1]} {a[2]}"} for a in abs_]

    ciudades = many_results("""
        SELECT CODLUGAR, NOMLUGAR
        FROM LUGAR
        WHERE IDTIPOLUGAR = 'CII'
    """)
    ciudades = [{"cod": c[0], "nom": c[1]} for c in ciudades]

    imp = many_results("""
        SELECT ID, NOMBRE
        FROM IMPUGNACION
        WHERE ESPECIALIZACION = %s
    """, [esp])
    impugnaciones = [{"codigo": i[0], "nombre": i[1]} for i in imp]

    return Response({
        "expediente": {
            "consec": nuevo,
            "idetapa": idetapa,
            "fecha": datetime.now().strftime("%Y-%m-%d")
        },
        "abogados": abogados,
        "ciudades": ciudades,
        "impugnaciones": impugnaciones,
        "entidades": []
    })

@api_view(['POST'])
def guardar_expediente(request):
    nocaso = request.data.get("nocaso")
    abogado = request.data.get("abogado")
    ciudad = request.data.get("ciudad")
    entidad = request.data.get("entidad")
    noEtapa = request.data.get("noEtapa", 1)
    
    if not (nocaso and abogado and ciudad and entidad):
        return Response({"error": "Todos los campos son obligatorios"}, status=400)

    try:
        # Obtener el consecutivo del expediente
        ultimo = single_result("""
            SELECT NVL(MAX(CONSECEXPE),0)
            FROM EXPEDIENTE
            WHERE NOCASO = %s
        """, [nocaso])[0]
        nuevo_consec = ultimo + 1

        # Obtener especialización del caso
        esp = single_result("""
            SELECT CODESPECIALIZACION FROM CASO WHERE NOCASO = %s
        """, [nocaso])[0]

        execute("""
            INSERT INTO EXPEDIENTE
            (NOCASO, CONSECEXPE, CODESPECIALIZACION, IDTIPOCASO2, CODLUGAR, CEDULA, FCHETAPA)
            VALUES (%s, %s, %s, %s, %s, %s, SYSDATE)
        """, [nocaso, nuevo_consec, esp, noEtapa, entidad, abogado])

        return Response({
            "mensaje": "Expediente guardado correctamente",
            "nuevoNo": nuevo_consec
        })
    except Exception as e:
        import traceback
        print(traceback.format_exc())
        return Response({"error": f"Error al guardar: {str(e)}"}, status=500)