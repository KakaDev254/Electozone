from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.shortcuts import render
from .utils import lipa_na_mpesa
import json

@require_POST
def initiate_stk_push(request):
    try:
        phone = request.POST.get("phone")
        amount = request.POST.get("amount")

        if not phone or not amount:
            return JsonResponse({"error": "Phone number and amount are required."}, status=400)

        response = lipa_na_mpesa(phone, int(amount))

        # Ensure response is JSON serializable
        if isinstance(response, dict):
            return JsonResponse(response)
        else:
            return JsonResponse({"error": "Unexpected response format from lipa_na_mpesa"}, status=500)

    except ValueError:
        return JsonResponse({"error": "Amount must be a valid number."}, status=400)
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)

@csrf_exempt
def mpesa_callback(request):
    if request.method != "POST":
        return JsonResponse({"ResultCode": 1, "ResultDesc": "Method not allowed"}, status=405)

    try:
        data = json.loads(request.body)
        print("M-Pesa Callback Received:", data)

        # Optional: Save data to database

        return JsonResponse({"ResultCode": 0, "ResultDesc": "Accepted"})
    except json.JSONDecodeError:
        return JsonResponse({"ResultCode": 1, "ResultDesc": "Invalid JSON"}, status=400)
    except Exception as e:
        return JsonResponse({"ResultCode": 1, "ResultDesc": str(e)}, status=500)
def payment_page(request):
    return render(request, 'mpesa/payment.html')
