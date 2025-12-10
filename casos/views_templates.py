from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt
import requests  # Para llamar a tu API REST interna

@csrf_exempt
def caso_template(request):
    contexto = {}

    if request.method == "POST":
        accion = request.POST.get("accion")

        if accion == "buscar_cliente":
            nombre = request.POST.get("nombre")
            apellido = request.POST.get("apellido")
            # Llamada a tu API interna
            res = requests.get(
                "http://localhost:8000/api/caso/buscar_cliente/",
                params={"nombre": nombre, "apellido": apellido}
            )
            if res.ok:
                data = res.json()
                contexto["cliente"] = data["cliente"]
                contexto["casos_cliente"] = data["casos_cliente"]
                contexto["caso_activo"] = data.get("caso_activo")
                contexto["especializaciones"] = data.get("especializaciones", [])
            else:
                contexto["error"] = res.json().get("error", "Error al buscar cliente")

        elif accion == "crear_caso":
            codcliente = request.POST.get("codcliente")
            nomcliente = request.POST.get("nomcliente")
            apellcliente = request.POST.get("apellcliente")
            res = requests.post(
                "http://localhost:8000/api/caso/crear_caso/",
                json={"codcliente": codcliente, "nomcliente": nomcliente, "apellcliente": apellcliente}
            )
            if res.ok:
                data = res.json()
                contexto["mensaje"] = f"Nuevo caso creado: {data['caso']['nocaso']}"
                contexto["cliente"] = data["cliente"]
            else:
                contexto["error"] = res.json().get("error", "Error al crear caso")

        elif accion == "guardar_caso":
            nocaso = request.POST.get("nocaso")
            codcliente = request.POST.get("codcliente")
            especializacion = request.POST.get("especializacion")
            valor = request.POST.get("valor")
            res = requests.post(
                "http://localhost:8000/api/caso/guardar_caso/",
                json={
                    "nocaso": nocaso,
                    "codcliente": codcliente,
                    "especializacion": especializacion,
                    "valor": valor
                }
            )
            if res.ok:
                contexto["mensaje"] = res.json().get("mensaje", "Caso guardado")
            else:
                contexto["error"] = res.json().get("error", "Error al guardar caso")

    # Siempre enviamos especializaciones (por si no hay POST)
    if "especializaciones" not in contexto:
        res = requests.get("http://localhost:8000/api/caso/especializaciones/")
        if res.ok:
            contexto["especializaciones"] = res.json()
        else:
            contexto["especializaciones"] = []

    return render(request, "cliente.html", contexto)
