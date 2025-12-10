from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt
import requests

API_BASE_URL = "http://localhost:8000/api/caso"

@csrf_exempt
def caso_template(request):
    """
    Vista principal para gestión de casos
    """
    contexto = {
        "especializaciones": [],
        "cliente": None,
        "casos_cliente": [],
        "caso_activo": None,
        "caso_nuevo": None,
        "mensaje": None,
        "error": None
    }

    # Cargar especializaciones (siempre disponibles)
    try:
        res = requests.get(f"{API_BASE_URL}/especializaciones/")
        if res.ok:
            contexto["especializaciones"] = res.json()
    except Exception as e:
        contexto["error"] = f"Error al cargar especializaciones: {str(e)}"

    if request.method == "POST":
        accion = request.POST.get("accion")

        # ==================================================
        # ACCIÓN: BUSCAR CLIENTE
        # ==================================================
        if accion == "buscar_cliente":
            nombre = request.POST.get("nombre", "").strip()
            apellido = request.POST.get("apellido", "").strip()
            
            if not nombre or not apellido:
                contexto["error"] = "Debe ingresar nombre y apellido"
                return render(request, "cliente.html", contexto)
            
            try:
                res = requests.get(
                    f"{API_BASE_URL}/buscar_cliente/",
                    params={"nombre": nombre, "apellido": apellido}
                )
                
                if res.ok:
                    data = res.json()
                    contexto["cliente"] = data["cliente"]
                    contexto["casos_cliente"] = data["casos_cliente"]
                    contexto["caso_activo"] = data.get("caso_activo")
                    contexto["especializaciones"] = data.get("especializaciones", contexto["especializaciones"])
                else:
                    error_data = res.json()
                    contexto["error"] = error_data.get("error", "Cliente no encontrado")
            
            except requests.exceptions.RequestException as e:
                contexto["error"] = f"Error de conexión: {str(e)}"
            except Exception as e:
                contexto["error"] = f"Error inesperado: {str(e)}"

        # ==================================================
        # ACCIÓN: CREAR CASO (GENERAR CONSECUTIVO)
        # ==================================================
        elif accion == "crear_caso":
            codcliente = request.POST.get("codcliente")
            nomcliente = request.POST.get("nomcliente")
            apellcliente = request.POST.get("apellcliente")
            
            if not codcliente:
                contexto["error"] = "Debe seleccionar un cliente primero"
                return render(request, "cliente.html", contexto)
            
            try:
                # Obtener documento del cliente
                res_buscar = requests.get(
                    f"{API_BASE_URL}/buscar_cliente/",
                    params={"nombre": nomcliente, "apellido": apellcliente}
                )
                
                doc_cliente = ""
                if res_buscar.ok:
                    doc_cliente = res_buscar.json()["cliente"]["doc"]
                
                res = requests.post(
                    f"{API_BASE_URL}/crear_caso/",
                    json={
                        "codcliente": codcliente,
                        "nomcliente": nomcliente,
                        "apellcliente": apellcliente,
                        "ndocumento": doc_cliente
                    }
                )
                
                if res.ok:
                    data = res.json()
                    # Reconstruir contexto del cliente
                    contexto["cliente"] = data["cliente"]
                    contexto["caso_nuevo"] = {
                        "nocaso": data["nocaso"],
                        "inicio": data["fecha_inicio"],
                        "esp": None,
                        "valor": None
                    }
                    contexto["mensaje"] = f"Nuevo caso #{data['nocaso']} creado. Complete los datos y guarde."
                    
                    # Recargar casos del cliente
                    res_cliente = requests.get(
                        f"{API_BASE_URL}/buscar_cliente/",
                        params={"nombre": nomcliente, "apellido": apellcliente}
                    )
                    if res_cliente.ok:
                        cliente_data = res_cliente.json()
                        contexto["casos_cliente"] = cliente_data["casos_cliente"]
                        contexto["especializaciones"] = cliente_data.get("especializaciones", contexto["especializaciones"])
                else:
                    error_data = res.json()
                    contexto["error"] = error_data.get("error", "Error al crear caso")
            
            except Exception as e:
                contexto["error"] = f"Error al crear caso: {str(e)}"

        # ==================================================
        # ACCIÓN: LIMPIAR / BUSCAR OTRO CLIENTE
        # ==================================================
        elif accion == "limpiar":
            # Simplemente retornar contexto vacío
            return render(request, "cliente.html", contexto)

        # ==================================================
        # ACCIÓN: GUARDAR CASO
        # ==================================================
        elif accion == "guardar_caso":
            nocaso = request.POST.get("nocaso")
            codcliente = request.POST.get("codcliente")
            especializacion = request.POST.get("especializacion")
            valor = request.POST.get("valor")
            fecha_inicio = request.POST.get("fechaInicio")
            
            # Validaciones
            if not all([nocaso, codcliente, especializacion, valor, fecha_inicio]):
                contexto["error"] = "Todos los campos son obligatorios"
                # Reconstruir contexto
                contexto["cliente"] = {
                    "cod": codcliente,
                    "nom": request.POST.get("nomcliente"),
                    "ape": request.POST.get("apellcliente")
                }
                return render(request, "cliente.html", contexto)
            
            try:
                valor_float = float(valor)
                if valor_float <= 0:
                    contexto["error"] = "El valor debe ser mayor a cero"
                    return render(request, "cliente.html", contexto)
            except ValueError:
                contexto["error"] = "Valor inválido"
                return render(request, "cliente.html", contexto)
            
            try:
                res = requests.post(
                    f"{API_BASE_URL}/guardar_caso/",
                    json={
                        "nocaso": int(nocaso),
                        "codcliente": codcliente,
                        "especializacion": especializacion,
                        "valor": valor_float,
                        "fechaInicio": fecha_inicio
                    }
                )
                
                if res.ok:
                    contexto["mensaje"] = f"✓ Caso #{nocaso} guardado exitosamente"
                    
                    # Recargar datos del cliente
                    nomcliente = request.POST.get("nomcliente")
                    apellcliente = request.POST.get("apellcliente")
                    
                    res_cliente = requests.get(
                        f"{API_BASE_URL}/buscar_cliente/",
                        params={"nombre": nomcliente, "apellido": apellcliente}
                    )
                    
                    if res_cliente.ok:
                        cliente_data = res_cliente.json()
                        contexto["cliente"] = cliente_data["cliente"]
                        contexto["casos_cliente"] = cliente_data["casos_cliente"]
                        contexto["caso_activo"] = cliente_data.get("caso_activo")
                        contexto["especializaciones"] = cliente_data.get("especializaciones", contexto["especializaciones"])
                else:
                    error_data = res.json()
                    contexto["error"] = error_data.get("error", "Error al guardar caso")
                    contexto["cliente"] = {
                        "cod": codcliente,
                        "nom": request.POST.get("nomcliente"),
                        "ape": request.POST.get("apellcliente")
                    }
            
            except Exception as e:
                contexto["error"] = f"Error al guardar: {str(e)}"
                contexto["cliente"] = {
                    "cod": codcliente,
                    "nom": request.POST.get("nomcliente"),
                    "ape": request.POST.get("apellcliente")
                }

    return render(request, "cliente.html", contexto)