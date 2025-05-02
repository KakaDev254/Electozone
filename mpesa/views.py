import json
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.shortcuts import render, get_object_or_404
from django.utils.dateparse import parse_datetime
from .utils import lipa_na_mpesa
from .models import MpesaPayment

@require_POST
def initiate_stk_push(request):
    try:
        phone = request.POST.get("phone")
        amount = request.POST.get("amount")

        if not phone or not amount:
            return JsonResponse({"error": "Phone number and amount are required."}, status=400)

        amount = int(amount)
        response = lipa_na_mpesa(phone, amount)

        if isinstance(response, dict) and response.get("ResponseCode") == "0":
            MpesaPayment.objects.create(
                user=request.user if request.user.is_authenticated else None,
                phone_number=phone,
                amount=amount,
                merchant_request_id=response.get("MerchantRequestID"),
                checkout_request_id=response.get("CheckoutRequestID"),
                response_code=response.get("ResponseCode"),
                response_description=response.get("ResponseDescription"),
                status="Pending"
            )
            return JsonResponse({"message": "STK Push sent successfully", **response})
        else:
            return JsonResponse({"error": "Failed to initiate STK Push", **response}, status=400)

    except ValueError:
        return JsonResponse({"error": "Amount must be a valid number."}, status=400)
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)


@csrf_exempt
@require_POST
def mpesa_callback(request):
    """
    Handles the callback from M-Pesa after a payment is processed.
    Updates the payment status in the database based on the response.
    """
    try:
        # Parse the callback data from M-Pesa
        data = json.loads(request.body)
        print("M-Pesa Callback Received:", data)

        # Extract relevant data from the callback
        checkout_request_id = data.get("CheckoutRequestID")
        result_code = data.get("ResultCode")
        result_desc = data.get("ResultDesc")
        merchant_request_id = data.get("MerchantRequestID")

        # Check if the payment record exists based on the CheckoutRequestID
        payment = MpesaPayment.objects.get(checkout_request_id=checkout_request_id)

        # Update the payment status based on the result code
        if result_code == "0":
            # Payment was successful
            payment.status = "Completed"
            payment.result_code = result_code
            payment.result_description = result_desc
        else:
            # Payment failed
            payment.status = "Failed"
            payment.result_code = result_code
            payment.result_description = result_desc

        # Update additional fields if necessary
        payment.response_code = result_code
        payment.response_description = result_desc
        payment.transaction_date = data.get("TransactionDate")

        # Save the updated payment record
        payment.save()

        # Log or process any additional logic here, like sending an email or notification.

        # Respond with success message
        return JsonResponse({"ResultCode": 0, "ResultDesc": "Accepted"})

    except json.JSONDecodeError:
        # Handle invalid JSON in the callback data
        return JsonResponse({"ResultCode": 1, "ResultDesc": "Invalid JSON in callback."}, status=400)
    except MpesaPayment.DoesNotExist:
        # Handle case where payment record is not found
        return JsonResponse({"ResultCode": 1, "ResultDesc": "Payment record not found."}, status=404)
    except Exception as e:
        # Handle any other exceptions that may occur
        return JsonResponse({"ResultCode": 1, "ResultDesc": str(e)}, status=500)
    
def check_payment_status(request):
    """
    View to check the payment status by CheckoutRequestID.
    This will be called periodically from the frontend to check the payment status.
    """
    # Extract the CheckoutRequestID from the GET request
    checkout_request_id = request.GET.get('checkoutRequestID')

    if not checkout_request_id:
        return JsonResponse({"error": "CheckoutRequestID is required."}, status=400)

    # Get the MpesaPayment object by CheckoutRequestID (or other unique identifier)
    payment = get_object_or_404(MpesaPayment, checkout_request_id=checkout_request_id)

    # Return the current status of the payment
    status = payment.status
    if status == "Pending":
        # If the status is still pending, you can return an ongoing status or similar
        return JsonResponse({"status": "Pending", "message": "Your payment is still being processed."})
    elif status == "Completed":
        return JsonResponse({"status": "Completed", "message": "Payment completed successfully!"})
    elif status == "Failed":
        return JsonResponse({"status": "Failed", "message": "Payment failed. Please try again."})

    return JsonResponse({"status": "Unknown", "message": "Unknown payment status."})    


def payment_page(request):
    return render(request, 'mpesa/payment.html')
